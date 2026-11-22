"""Lot D — Gold, EXP-D-018 : règle d'abstention R-abst sur le dev.

Protocole : `docs/lot-d_protocole_gold.md`.

Plan fixé avant la mesure (commit du protocole : fe97fdc, da06966) :
- jeu : dev du Lot D = 20 affirmations fictives + 10 phrases hors sujet
  (`data/interim/lot_d/claims_dev_hors_sujet.jsonl`, SHA-256 vérifié ci-dessous) ;
  **jamais le test** ;
- système : Falcon-H1-3B, prompt v1, JSON imposé, 3 graines (13, 42, 2026), recherche hybride top 5,
  NLI affiné du Lot C (`NLI_BACKEND=fine-tuned`, EXP-C-011) ; le LLM ne voit pas les positions NLI ;
- R-abst : si **tous** les passages cités par un verdict émis sont `neutre` pour le NLI, le verdict
  devient `preuves_insuffisantes` ; aucun seuil ; appliquée après le LLM (mêmes générations) ;
- décision (graine 42, graine principale du Lot D) : R-abst adoptée pour le test v2 si
  (1) l'abstention justifiée augmente (affirmations sans preuve + phrases hors sujet) **et**
  (2) l'exactitude sur les affirmations qui ont une preuve ne baisse pas de plus d'une affirmation ;
  les 3 graines sont rapportées ;
- en plus : nombre d'affirmations avec preuve transformées à tort en abstention (avertissement du
  Lot C, EXP-C-016) ; bootstrap apparié de l'exactitude (10 000 tirages, graine 42).

Sorties (non versionnées, `evaluation/results/`) :
- `lot-d_gold_abstention_dev_<AAAAMMJJ>.json` : configuration, métriques, décision, détail ;
- `lot-d_annotation_hadil_dev.csv` (30 verdicts, graine 42, sans R-abst) et
  `lot-d_annotation_wiem_dev.csv` (10 de ces verdicts, tirés avec la graine 42), pour l'annotation
  du protocole (section 4) ; le verdict de référence n'y figure pas.

Usage : `rag_llm/exp_d_018_gold_abstention.ps1` (Ollama, Falcon) ; `--limit 3` pour un essai.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
from collections import Counter
from datetime import date
from pathlib import Path

from common.schemas import Stance
from data.loaders import load_evidence_corpus
from rag_llm import llm_verdict as lv
from rag_llm.bronze_report import NEI
from rag_llm.evaluate_retrieval import RESULTS_DIR, ROOT, load_claims
from rag_llm.evaluate_verdict import compute_metrics
from rag_llm.silver_retrieval import SPLITS, paired_bootstrap
from rag_llm.silver_verdict import MAIN_SEED, SEEDS, CachedGenerator, K, prepare, run_llm

EXP_ID = "EXP-D-018"
HORS_SUJET = ROOT / "data" / "interim" / "lot_d" / "claims_dev_hors_sujet.jsonl"
HORS_SUJET_SHA256 = "16006c440c9089663a6f309bc26201885e54ae68e67a3b543b464850ccc4ecc2"
NLI_REQUIRED = "fine-tuned"
N_SECOND_ANNOTATOR = 10
ANNOTATION_SEED = 42


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_dev_claims(limit: int | None = None) -> list[dict]:
    """20 affirmations du dev + 10 phrases hors sujet (empreinte vérifiée)."""
    if not HORS_SUJET.exists():
        raise SystemExit(f"Fichier absent : {HORS_SUJET}")
    got = sha256(HORS_SUJET)
    if got != HORS_SUJET_SHA256:
        raise SystemExit(
            f"Phrases hors sujet modifiées (SHA-256 {got}) : arrêt, voir le protocole."
        )
    claims = load_claims(SPLITS["dev"][1]) + load_claims(HORS_SUJET)
    return claims[:limit] if limit else claims


# ---------------------------------------------------------------------------
# R-abst
# ---------------------------------------------------------------------------


def stance_map(prepared: dict) -> dict[str, dict[str, str]]:
    """claim_id → {doc_id: position NLI} pour les passages proposés au LLM."""
    return {
        cid: {s.evidence.doc_id: s.stance.value for s in stances[:K]}
        for cid, (_, _, stances) in prepared.items()
    }


def apply_rabst(rows: list[dict], stances: dict[str, dict[str, str]]) -> list[dict]:
    """Verdict émis dont tous les passages cités sont neutres → preuves insuffisantes."""
    out = []
    for r in rows:
        cited = [stances[r["claim_id"]].get(d) for d in r["citations"]]
        hit = not r["abstained"] and bool(cited) and all(s == Stance.NEUTRAL.value for s in cited)
        new = dict(r, cited_stances=cited, rabst_applied=hit)
        if hit:
            new.update(pred=NEI, abstained=True)
        out.append(new)
    return out


def counts(rows: list[dict]) -> dict:
    with_ev = [r for r in rows if r["gold"] != NEI]
    no_ev = [r for r in rows if r["gold"] == NEI]
    return {
        "n_with_evidence": len(with_ev),
        "correct_with_evidence": sum(r["pred"] == r["gold"] for r in with_ev),
        "n_without_evidence": len(no_ev),
        "abstained_without_evidence": sum(r["abstained"] for r in no_ev),
    }


def subset_metrics(rows: list[dict]) -> dict:
    hs = [r for r in rows if r["claim_id"].startswith("dev-hs")]
    dev = [r for r in rows if not r["claim_id"].startswith("dev-hs")]
    return {
        "all": {**compute_metrics(rows), **counts(rows)},
        "dev_20": compute_metrics(dev),
        "hors_sujet_10": compute_metrics(hs),
    }


def compare_rabst(base: list[dict], rabst: list[dict]) -> dict:
    """Effet de R-abst sur une graine, et application de la règle de décision."""
    cb, cr = counts(base), counts(rabst)
    lost = [
        b["claim_id"]
        for b, r in zip(base, rabst, strict=True)
        if b["gold"] != NEI and b["pred"] == b["gold"] and r["pred"] != r["gold"]
    ]
    wrongly = [r["claim_id"] for r in rabst if r["rabst_applied"] and r["gold"] != NEI]
    gained = [r["claim_id"] for r in rabst if r["rabst_applied"] and r["gold"] == NEI]
    cond1 = cr["abstained_without_evidence"] > cb["abstained_without_evidence"]
    cond2 = cb["correct_with_evidence"] - cr["correct_with_evidence"] <= 1
    return {
        "applied": sum(r["rabst_applied"] for r in rabst),
        "justified_abstentions_gained": gained,
        "with_evidence_turned_to_abstention": wrongly,
        "correct_answers_lost": lost,
        "condition_1_justified_abstention_up": cond1,
        "condition_2_at_most_one_correct_lost": cond2,
        "adopted": cond1 and cond2,
        "bootstrap_accuracy": paired_bootstrap(
            [float(r["pred"] == r["gold"]) for r in base],
            [float(r["pred"] == r["gold"]) for r in rabst],
        ),
    }


# ---------------------------------------------------------------------------
# Fichiers d'annotation (protocole, section 4)
# ---------------------------------------------------------------------------

COLUMNS = (
    ["claim_id", "affirmation", "verdict", "explication", "citations"]
    + [f"P{i}" for i in range(1, K + 1)]
    + [f"pertinence_P{i}" for i in range(1, K + 1)]
    + ["invente", "fidelite", "commentaire"]
)


def annotation_rows(claims: list[dict], prepared: dict, rows: list[dict]) -> list[dict]:
    text = {c["claim_id"]: c["text"] for c in claims}
    out = []
    for r in rows:
        evidences = prepared[r["claim_id"]][1][:K]
        pos = {e.doc_id: f"P{i}" for i, e in enumerate(evidences, 1)}
        line = {c: "" for c in COLUMNS}
        line.update(
            claim_id=r["claim_id"],
            affirmation=text[r["claim_id"]],
            verdict=r["pred"],
            explication=r.get("explanation") or "",
            citations=", ".join(pos.get(d, d) for d in r["citations"]),
        )
        for i, e in enumerate(evidences, 1):
            line[f"P{i}"] = e.text
        out.append(line)
    return out


def write_csv(path: Path, lines: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:  # utf-8-sig : lisible par Excel
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(lines)


def second_annotator_sample(lines: list[dict], n: int = N_SECOND_ANNOTATOR) -> list[dict]:
    rng = random.Random(ANNOTATION_SEED)
    picked = sorted(rng.sample(range(len(lines)), min(n, len(lines))))
    return [lines[i] for i in picked]


# ---------------------------------------------------------------------------
# Exécution
# ---------------------------------------------------------------------------


def evaluate(claims, corpus, generator, predict_stances, method: str = "hybrid") -> dict:
    prepared = prepare(corpus, claims, method, predict_stances)
    stances = stance_map(prepared)
    per_seed = {}
    for seed in SEEDS:
        base = run_llm(claims, prepared, generator, K, False, seed, method)
        rabst = apply_rabst(base, stances)
        per_seed[seed] = {
            "sans_rabst": subset_metrics(base),
            "avec_rabst": subset_metrics(rabst),
            "effet": compare_rabst(base, rabst),
            "llm_rows": base,
            "per_claim": rabst,
        }
    return {"prepared": prepared, "per_seed": per_seed}


def print_results(res: dict) -> None:
    print(
        f"\n{'graine':<8}{'système':<12}{'exact.':>8}{'couv.':>7}{'sél.':>7}{'abst.just.':>12}"
        f"{'corrects avec preuve':>22}"
    )
    for seed, r in res["per_seed"].items():
        for name in ("sans_rabst", "avec_rabst"):
            m = r[name]["all"]
            print(
                f"{seed:<8}{name:<12}{m['accuracy']:>8}{m['coverage']:>7}"
                f"{str(m['selective_accuracy']):>7}{str(m['justified_abstention']):>12}"
                f"{m['correct_with_evidence']:>12} / {m['n_with_evidence']}"
            )
        e = r["effet"]
        print(
            f"        R-abst appliquée {e['applied']} fois ;"
            f" gagnées {e['justified_abstentions_gained']} ;"
            f" avec preuve → abstention {e['with_evidence_turned_to_abstention']} ;"
            f" bons verdicts perdus {e['correct_answers_lost']}"
        )
    e = res["per_seed"][MAIN_SEED]["effet"]
    b = e["bootstrap_accuracy"]
    print(
        f"\nDécision (graine {MAIN_SEED}) : condition 1 {e['condition_1_justified_abstention_up']},"
        f" condition 2 {e['condition_2_at_most_one_correct_lost']} → R-abst "
        f"{'ADOPTÉE' if e['adopted'] else 'NON ADOPTÉE'}"
    )
    print(f"Bootstrap exactitude (avec − sans) : {b['diff']:+.3f} {b['ci95']} p={b['p_one_sided']}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--limit", type=int, default=None, help="essai rapide sur N phrases")
    args = p.parse_args()

    from models.nli.stance import backend_info, predict_stances

    nli = backend_info()
    if nli.get("backend") != NLI_REQUIRED or nli.get("status") != "loaded":
        raise SystemExit(f"NLI attendu : {NLI_REQUIRED} chargé ; obtenu : {nli}")

    claims = load_dev_claims(args.limit)
    corpus = load_evidence_corpus(SPLITS["dev"][0])
    generator = CachedGenerator(lv.get_generator())
    res = evaluate(claims, corpus, generator, predict_stances)
    print_results(res)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    llm42 = res["per_seed"][MAIN_SEED]["llm_rows"]  # Falcon tel quel (sans R-abst), graine 42
    lines = annotation_rows(claims, res["prepared"], llm42)
    suffix = f"_limit{args.limit}" if args.limit else ""
    write_csv(RESULTS_DIR / f"lot-d_annotation_hadil_dev{suffix}.csv", lines)
    write_csv(
        RESULTS_DIR / f"lot-d_annotation_wiem_dev{suffix}.csv", second_annotator_sample(lines)
    )

    payload = {
        "exp_id": EXP_ID,
        "date": date.today().isoformat(),
        "llm": generator.name,
        "prompt_version": lv.PROMPT_VERSION,
        "prompt_sha": lv.prompt_fingerprint(),
        "temperature": lv.TEMPERATURE,
        "top_p": lv.TOP_P,
        "seeds": SEEDS,
        "retrieval": "hybrid",
        "nli": nli,
        "hors_sujet_sha256": HORS_SUJET_SHA256,
        "limit": args.limit,
        "per_seed": res["per_seed"],
    }
    slug = re.sub(r"[^A-Za-z0-9.]+", "-", generator.name.split("/")[-1]).strip("-")
    out = RESULTS_DIR / f"lot-d_gold_abstention_dev_{slug}_{date.today():%Y%m%d}{suffix}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Résultats : {out.relative_to(ROOT)}")
    print(f"Annotation : evaluation/results/lot-d_annotation_{{hadil,wiem}}_dev{suffix}.csv")
    print(f"Cache : {generator.hits} réutilisées, {generator.misses} générées")
    print("Verdicts de Falcon (graine 42) :", dict(Counter(r["pred"] for r in llm42)))


if __name__ == "__main__":
    main()
