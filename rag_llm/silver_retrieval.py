"""Lot D — Palier Silver : recherche dense et hybride mesurées sur le test gelé (EXP-D-008).

Question : la recherche « par le sens » (encodeur multilingue e5) corrige-t-elle la première cause
d'erreur du Bronze, la **langue croisée** (affirmation française, preuve arabe, aucun mot commun) ?

Configurations comparées, toutes avec le même top 5 :
- `bm25`        : baseline lexicale du Bronze (EXP-D-007) ;
- `dense`       : encodeur seul (`intfloat/multilingual-e5-base`) ;
- `hybrid`      : fusion RRF de BM25 et du dense (k = 60) — **configuration retenue a priori**,
                  choisie sur le dev dans EXP-D-003, avant toute mesure sur le test ;
- ablations     : `hybrid` sans seuil de similarité dense, et l'encodeur plus petit e5-small.
Aucun paramètre n'est réglé ici : le test (gelé le 23/10/2026) ne sert qu'à mesurer.

Statistiques :
- métriques par affirmation (Rappel@5, MRR, Hit@1, Hit@5), moyenne globale et par langue
  (fr, ar, tunisien = lettres arabes + arabizi) ;
- **bootstrap apparié** : on tire 10 000 fois, avec remise, les mêmes affirmations pour les deux
  systèmes ; on rapporte la différence moyenne, l'intervalle à 95 % (percentiles) et p = part des
  tirages où la différence est ≤ 0 (test unilatéral « le candidat est meilleur ») ;
- **3 exécutions** : l'encodeur est rechargé 3 fois ; un encodeur pré-entraîné en inférence est
  déterministe, on vérifie donc que les 3 classements sont identiques (variance nulle).
  Les 3 graines d'échantillonnage s'appliquent au verdict par LLM (EXP-D-009).

Usage (depuis la racine du dépôt, après `python -m rag_llm.build_tunifact_eval`) :
    pip install sentence-transformers
    python -m rag_llm.silver_retrieval                 # dev + test, configurations ci-dessus
    python -m rag_llm.silver_retrieval --quick         # sans e5-small ni contrôle des 3 exécutions
Le modèle (~1 Go) est téléchargé au premier lancement (dossier de cache de Hugging Face).
Sortie : evaluation/results/lot-d_silver_retrieval_<AAAAMMJJ>.json (non versionné).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import tempfile
from collections import defaultdict
from contextlib import contextmanager
from datetime import date

from common.schemas import Claim, Lang
from data.loaders import load_evidence_corpus
from rag_llm.evaluate_retrieval import FIXTURES, RESULTS_DIR, ROOT, load_claims
from rag_llm.freeze_test import check as check_freeze
from rag_llm.retrieval import hybrid
from rag_llm.retrieval.dense import SentenceTransformerEncoder

K = 5
MAX_RANK = 10  # profondeur du classement pour le MRR
BASE_MODEL = "intfloat/multilingual-e5-base"
SMALL_MODEL = "intfloat/multilingual-e5-small"
REPLICATIONS = 10_000
SEED = 42
SPLITS = {
    "dev": (FIXTURES / "evidence_dev.jsonl", FIXTURES / "claims_dev.jsonl"),
    "test": (
        ROOT / "data" / "interim" / "lot_d" / "evidence_tunifact_v1.jsonl",
        FIXTURES / "claims_tunifact_v1.jsonl",
    ),
}
METRICS = ("recall@5", "mrr", "hit@1", "hit@5")
LANGS = {"fr": "français", "ar": "arabe", "tn": "tunisien (lettres arabes + arabizi)"}

# (nom, méthode, modèle, seuil dense) : 1re ligne = baseline, 3e = configuration retenue.
CONFIGS = [
    ("bm25", "bm25", None, None),
    ("dense-e5-base", "dense", BASE_MODEL, None),
    ("hybrid-e5-base", "hybrid", BASE_MODEL, None),
    ("ablation : hybrid sans seuil dense", "hybrid", BASE_MODEL, -1.0),
    ("ablation : hybrid e5-small", "hybrid", SMALL_MODEL, None),
]
PRIMARY = "hybrid-e5-base"


# ---------------------------------------------------------------------------
# Métriques par affirmation
# ---------------------------------------------------------------------------


def claim_metrics(gold: list[str], retrieved: list[str]) -> dict:
    """Rappel@5, MRR (profondeur 10), Hit@1 et Hit@5 pour une affirmation."""
    rel = set(gold)
    rank = next((i + 1 for i, d in enumerate(retrieved[:MAX_RANK]) if d in rel), None)
    return {
        "recall@5": len(rel & set(retrieved[:K])) / len(rel),
        "mrr": 1.0 / rank if rank else 0.0,
        "hit@1": float(bool(rel & set(retrieved[:1]))),
        "hit@5": float(bool(rel & set(retrieved[:K]))),
        "rank": rank,
    }


def lang_family(claim: dict) -> str:
    return claim["lang"] if claim["lang"] in LANGS else "ar"


def average(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0}
    out = {m: round(sum(r[m] for r in rows) / len(rows), 3) for m in METRICS}
    return {"n": len(rows), **out}


def summarize(rows: list[dict]) -> dict:
    by_lang = defaultdict(list)
    by_group = defaultdict(list)
    for r in rows:
        by_lang[r["lang"]].append(r)
        by_group[r["group"]].append(r)
    return {
        **average(rows),
        "by_lang": {g: average(by_lang[g]) for g in LANGS if g in by_lang},
        "by_group": {g: average(v) for g, v in sorted(by_group.items())},
    }


# ---------------------------------------------------------------------------
# Bootstrap apparié
# ---------------------------------------------------------------------------


def paired_bootstrap(
    base: list[float], cand: list[float], replications: int = REPLICATIONS, seed: int = SEED
) -> dict:
    """Différence moyenne (candidat − base), IC 95 % par percentiles, p unilatéral."""
    if len(base) != len(cand) or not base:
        raise ValueError("listes appariées de même longueur non vide attendues")
    n = len(base)
    diffs = [c - b for b, c in zip(base, cand, strict=True)]
    rng = random.Random(seed)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(replications))
    lo, hi = means[int(0.025 * replications)], means[int(0.975 * replications) - 1]
    return {
        "diff": round(sum(diffs) / n, 3),
        "ci95": [round(lo, 3), round(hi, 3)],
        "p_one_sided": round(sum(m <= 0 for m in means) / replications, 4),
        "n": n,
        "replications": replications,
        "seed": seed,
    }


# ---------------------------------------------------------------------------
# Exécution d'une configuration
# ---------------------------------------------------------------------------


@contextmanager
def configured(model: str | None, min_similarity: float | None):
    """Installe l'encodeur et le seuil dense le temps d'une configuration."""
    saved, saved_dir = hybrid.MIN_DENSE_SIMILARITY, os.environ.get("INDEX_DIR")
    # pas de cache disque : chaque exécution ré-encode vraiment le corpus
    os.environ["INDEX_DIR"] = tempfile.mkdtemp(prefix="lotd_index_")
    if model:
        hybrid.set_encoder(SentenceTransformerEncoder(model))
    if min_similarity is not None:
        hybrid.MIN_DENSE_SIMILARITY = min_similarity
    try:
        yield
    finally:
        hybrid.MIN_DENSE_SIMILARITY = saved
        hybrid.set_encoder(None)
        if saved_dir is None:
            os.environ.pop("INDEX_DIR", None)
        else:
            os.environ["INDEX_DIR"] = saved_dir


def rank_all(corpus, claims: list[dict], method: str) -> dict[str, list[str]]:
    out = {}
    for c in claims:
        claim = Claim(text=c["text"], lang=Lang(c["lang"]))
        out[c["claim_id"]] = [e.doc_id for e in hybrid.retrieve(claim, corpus, MAX_RANK, method)]
    return out


def evaluate_config(corpus, claims, method, model, min_similarity, runs: int = 1) -> dict:
    rankings = []
    for _ in range(runs):
        with configured(model, min_similarity):
            rankings.append(rank_all(corpus, claims, method))
    rows = []
    for c in claims:
        if not c.get("gold_doc_ids"):
            continue  # affirmations sans preuve : comptées par le verdict (abstention)
        retrieved = rankings[0][c["claim_id"]]
        rows.append(
            {
                "claim_id": c["claim_id"],
                "lang": lang_family(c),
                "group": f"{c['lang']}-{c.get('script', '?')}",
                "retrieved": retrieved[:K],
                **claim_metrics(c["gold_doc_ids"], retrieved),
            }
        )
    result = {"summary": summarize(rows), "per_claim": rows}
    if runs > 1:
        result["runs"] = runs
        result["identical_runs"] = all(r == rankings[0] for r in rankings[1:])
    return result


def compare(results: dict, base: str = "bm25") -> dict:
    """Bootstrap apparié de chaque configuration contre la baseline, pour chaque métrique."""
    ref = {r["claim_id"]: r for r in results[base]["per_claim"]}
    out = {}
    for name, res in results.items():
        if name == base:
            continue
        rows = res["per_claim"]
        out[name] = {
            m: paired_bootstrap([ref[r["claim_id"]][m] for r in rows], [r[m] for r in rows])
            for m in ("recall@5", "mrr")
        }
    return out


# ---------------------------------------------------------------------------
# Affichage
# ---------------------------------------------------------------------------


def print_split(name: str, results: dict, tests: dict | None) -> None:
    print(f"\n=== {name.upper()}")
    head = f"{'configuration':<38}{'R@5':>7}{'MRR':>7}{'Hit@1':>7}"
    print(head + "".join(f"{g:>7}" for g in LANGS) + "   (R@5 par langue)")
    for cfg, res in results.items():
        s = res["summary"]
        langs = "".join(f"{s['by_lang'].get(g, {}).get('recall@5', '-'):>7}" for g in LANGS)
        print(f"{cfg:<38}{s['recall@5']:>7}{s['mrr']:>7}{s['hit@1']:>7}{langs}")
    if tests:
        print("Bootstrap apparié contre BM25 (différence, IC 95 %, p unilatéral) :")
        for cfg, t in tests.items():
            r, m = t["recall@5"], t["mrr"]
            print(
                f"  {cfg:<36} R@5 {r['diff']:+.3f} {r['ci95']} p={r['p_one_sided']}"
                f" | MRR {m['diff']:+.3f} {m['ci95']} p={m['p_one_sided']}"
            )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--quick", action="store_true", help="sans e5-small ni contrôle des 3 exécutions"
    )
    p.add_argument("--splits", nargs="+", default=list(SPLITS), choices=list(SPLITS))
    args = p.parse_args()

    problems = check_freeze()
    if problems:
        raise SystemExit("Test gelé modifié : " + "; ".join(problems))

    configs = [c for c in CONFIGS if not (args.quick and c[2] == SMALL_MODEL)]
    payload = {
        "exp_id": "EXP-D-008",
        "date": date.today().isoformat(),
        "k": K,
        "primary": PRIMARY,
        "splits": {},
    }
    for split in args.splits:
        corpus_path, claims_path = SPLITS[split]
        corpus, claims = load_evidence_corpus(corpus_path), load_claims(claims_path)
        results = {}
        for name, method, model, min_sim in configs:
            runs = 3 if (name == PRIMARY and not args.quick) else 1
            results[name] = evaluate_config(corpus, claims, method, model, min_sim, runs)
        tests = compare(results)
        print_split(
            f"{split} — {len(corpus)} passages, "
            f"{results['bm25']['summary']['n']} affirmations avec preuve",
            results,
            tests,
        )
        if PRIMARY in results and "identical_runs" in results[PRIMARY]:
            print(f"3 exécutions de {PRIMARY} identiques : {results[PRIMARY]['identical_runs']}")
        payload["splits"][split] = {
            "n_passages": len(corpus),
            "results": results,
            "bootstrap_vs_bm25": tests,
        }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"lot-d_silver_retrieval_{date.today():%Y%m%d}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRésultats : {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
