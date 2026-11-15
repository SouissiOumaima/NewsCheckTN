"""Lot D — Silver : verdict avec le NLI affiné du Lot C (EXP-D-011).

Question : le modèle NLI affiné du Lot C (PR #21, EXP-C-011, `NLI_BACKEND=fine-tuned`) améliore-t-il
le verdict du Lot D par rapport au NLI Bronze (règles par lexique) utilisé dans EXP-D-010 ?

Configurations **fixées avant la mesure** (mail à Achref du 15/11, rien n'est réglé ici) :
- même recherche qu'EXP-D-010 (hybride BM25 + e5-base, top 5), mêmes passages pour tous les
  systèmes (recherche faite une seule fois) ;
- même gabarit (mêmes seuils A1–A4) et même LLM (Aya Expanse 8B, prompt v1, graine 42) ;
- seul change le moteur NLI qui donne les positions (soutient / contredit / neutre).

Systèmes (graine 42 pour le LLM) :
- `gabarit + NLI Bronze`         référence = EXP-D-010 ;
- `gabarit + NLI affiné`         **H1** : meilleur que la référence ;
- `LLM sans indices`             référence = configuration principale d'EXP-D-010 (sans NLI) ;
- `LLM + indices NLI Bronze`     référence = ablation d'EXP-D-010 ;
- `LLM + indices NLI affiné`     **H2** : meilleur que `LLM + indices NLI Bronze`.
Les références sont recalculées dans la même exécution : on vérifie qu'elles redonnent EXP-D-010.

Bootstrap apparié (10 000 tirages, graine 42), exactitude et macro-F1 : H1, H2, et
`LLM + indices NLI affiné` contre `LLM sans indices`. En plus : accord des deux NLI sur les
passages (part de positions identiques, répartition des positions).

Le checkpoint affiné doit être chargé pour de vrai : si le moteur répond « neutre » par défaut
(checkpoint absent), l'exécution s'arrête au lieu de produire de faux chiffres.

    python -X utf8 -m rag_llm.silver_verdict_nli --limit 3          # essai rapide (dev)
    python -X utf8 -m rag_llm.silver_verdict_nli                    # dev
    python -X utf8 -m rag_llm.silver_verdict_nli --splits test      # test gelé, une seule fois
Sortie : `evaluation/results/lot-d_silver_verdict_nli_<split>_<AAAAMMJJ>.json` (non versionné).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from datetime import date
from pathlib import Path

from common.schemas import Claim, Lang
from data.loaders import load_evidence_corpus
from rag_llm import llm_verdict as lv
from rag_llm import silver_verdict as sv
from rag_llm.evaluate_retrieval import RESULTS_DIR, ROOT, load_claims
from rag_llm.freeze_test import check as check_freeze
from rag_llm.retrieval import hybrid
from rag_llm.silver_retrieval import SPLITS

EXP_ID = "EXP-D-011"
BACKENDS = {"bronze": "NLI Bronze", "fine-tuned": "NLI affiné"}
REFERENCE, CANDIDATE = "bronze", "fine-tuned"

# (nom, moteur NLI montré au LLM ou None = sans indices)
LLM_SYSTEMS = [
    ("LLM sans indices", None),
    ("LLM + indices NLI Bronze", REFERENCE),
    ("LLM + indices NLI affiné", CANDIDATE),
]
# (candidat, référence) : comparaisons fixées à l'avance
COMPARISONS = [
    ("gabarit + NLI affiné", "gabarit + NLI Bronze"),  # H1
    ("LLM + indices NLI affiné", "LLM + indices NLI Bronze"),  # H2
    ("LLM + indices NLI affiné", "LLM sans indices"),
]


# ---------------------------------------------------------------------------
# Moteurs NLI
# ---------------------------------------------------------------------------


def activate(backend: str) -> dict:
    """Charge un moteur NLI du Lot C et vérifie qu'il est vraiment chargé (sinon arrêt)."""
    from models.nli import stance

    os.environ["NLI_BACKEND"] = backend
    stance.set_classifier(None)  # oublie le moteur précédent
    info = stance.backend_info()
    if info.get("backend") != backend or info.get("status") != "loaded":
        raise SystemExit(
            f"NLI {backend!r} non chargé ({info}). Pour le modèle affiné : code de la PR #21 et "
            "checkpoint dans models/checkpoints/nli_mdeberta-ft_v3_lr1e-05_e6_seed42/ "
            "(ou NLI_FINETUNED_MODEL=<dossier>)."
        )
    if backend == "fine-tuned":
        info["weights_sha256"] = _weights_sha256(Path(info.get("model", "")))
    return info


def _weights_sha256(folder: Path) -> str | None:
    weights = folder / "model.safetensors"
    if not weights.is_file():
        return None
    h = hashlib.sha256()
    with weights.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Préparation : recherche une fois, positions par moteur
# ---------------------------------------------------------------------------


def retrieve_all(corpus, claims: list[dict], method: str) -> dict:
    out = {}
    for c in claims:
        claim = Claim(text=c["text"], lang=Lang(c["lang"]))
        out[c["claim_id"]] = (claim, hybrid.retrieve(claim, corpus, k=sv.K, method=method))
    return out


def stances_for(retrieved: dict, predict_stances) -> dict:
    return {cid: predict_stances(claim, evs) for cid, (claim, evs) in retrieved.items()}


def stance_agreement(stances: dict[str, dict]) -> dict:
    """Accord passage par passage entre le NLI de référence et le NLI affiné."""
    ref, cand = stances[REFERENCE], stances[CANDIDATE]
    pairs = [
        (a.stance.value, b.stance.value)
        for cid in ref
        for a, b in zip(ref[cid], cand[cid], strict=True)
    ]
    if not pairs:
        return {"n_passages": 0}
    return {
        "n_passages": len(pairs),
        "identical": round(sum(a == b for a, b in pairs) / len(pairs), 3),
        "distribution": {
            BACKENDS[REFERENCE]: dict(Counter(a for a, _ in pairs)),
            BACKENDS[CANDIDATE]: dict(Counter(b for _, b in pairs)),
        },
    }


# ---------------------------------------------------------------------------
# Évaluation
# ---------------------------------------------------------------------------


def evaluate(claims, retrieved: dict, stances: dict[str, dict], generator, method: str) -> dict:
    def prepared(backend: str) -> dict:
        return {cid: (*retrieved[cid], stances[backend][cid]) for cid in retrieved}

    rows = {}
    for backend, label in BACKENDS.items():
        rows[f"gabarit + {label}"] = sv.run_template(claims, prepared(backend), method)
    for name, backend in LLM_SYSTEMS:
        # sans indices, le NLI n'entre pas dans le prompt : positions de référence (repli)
        rows[name] = sv.run_llm(
            claims,
            prepared(backend or REFERENCE),
            generator,
            sv.K,
            show_nli=backend is not None,
            seed=sv.MAIN_SEED,
            method=method,
        )
    systems = {name: {"metrics": sv.metrics(r), "per_claim": r} for name, r in rows.items()}
    comparisons = {
        f"{cand} vs {base}": sv.compare(rows[base], rows[cand]) for cand, base in COMPARISONS
    }
    return {
        "systems": systems,
        "comparisons": comparisons,
        "stance_agreement": stance_agreement(stances),
    }


def print_split(name: str, res: dict) -> None:
    print(f"\n=== {name.upper()}")
    print(f"{'système':<30}{'exact.':>8}{'m-F1':>7}{'couv.':>7}{'sél.':>7}{'valid.':>8}")
    for sys_name, s in res["systems"].items():
        m = s["metrics"]
        print(
            f"{sys_name:<30}{m['accuracy']:>8}{m['macro_f1']:>7}{m['coverage']:>7}"
            f"{str(m.get('selective_accuracy')):>7}{str(m.get('valid_outputs', '-')):>8}"
        )
    print("Bootstrap apparié (différence, IC 95 %, p unilatéral) :")
    for comp, c in res["comparisons"].items():
        a, f = c["accuracy"], c["macro_f1"]
        print(
            f"  {comp}\n     exact. {a['diff']:+.3f} {a['ci95']} p={a['p_one_sided']}"
            f" | m-F1 {f['diff']:+.3f} {f['ci95']} p={f['p_one_sided']}"
        )
    ag = res["stance_agreement"]
    print(f"Accord des deux NLI : {ag.get('identical')} sur {ag['n_passages']} passages")
    for label, dist in ag.get("distribution", {}).items():
        print(f"  {label:<12} {dist}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--splits", nargs="+", default=["dev"], choices=list(SPLITS))
    p.add_argument("--retrieval", default="hybrid", choices=hybrid.METHODS)
    p.add_argument("--limit", type=int, default=None, help="essai rapide sur N affirmations")
    args = p.parse_args()

    if "test" in args.splits:
        problems = check_freeze()
        if problems:
            raise SystemExit("Test gelé modifié : " + "; ".join(problems))

    data, retrieved = {}, {}
    for split in args.splits:
        corpus_path, claims_path = SPLITS[split]
        corpus, claims = load_evidence_corpus(corpus_path), load_claims(claims_path)
        claims = claims[: args.limit] if args.limit else claims
        data[split] = claims
        retrieved[split] = retrieve_all(corpus, claims, args.retrieval)

    # Un moteur à la fois (le modèle affiné n'est chargé qu'une fois)
    nli_info, stances = {}, {split: {} for split in args.splits}
    for backend in BACKENDS:
        nli_info[backend] = activate(backend)
        from models.nli.stance import predict_stances

        for split in args.splits:
            stances[split][backend] = stances_for(retrieved[split], predict_stances)

    generator = sv.CachedGenerator(lv.get_generator())
    payload = {
        "exp_id": EXP_ID,
        "date": date.today().isoformat(),
        "llm": generator.name,
        "prompt_version": lv.PROMPT_VERSION,
        "prompt_sha": lv.prompt_fingerprint(),
        "temperature": lv.TEMPERATURE,
        "top_p": lv.TOP_P,
        "seed": sv.MAIN_SEED,
        "retrieval": args.retrieval,
        "nli": nli_info,
        "limit": args.limit,
    }
    for split in args.splits:
        res = evaluate(data[split], retrieved[split], stances[split], generator, args.retrieval)
        print_split(f"{split} — {len(data[split])} affirmations, LLM {generator.name}", res)
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out = RESULTS_DIR / f"lot-d_silver_verdict_nli_{split}_{date.today():%Y%m%d}.json"
        out.write_text(
            json.dumps(
                {**payload, "split": split, **res}, ensure_ascii=False, indent=2, default=str
            ),
            encoding="utf-8",
        )
        print(f"Résultats : {out.relative_to(ROOT)}")
    print(f"Cache : {generator.hits} réutilisées, {generator.misses} générées")


if __name__ == "__main__":
    main()
