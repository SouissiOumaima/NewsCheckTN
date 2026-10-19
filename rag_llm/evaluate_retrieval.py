"""Lot D — Évaluation du retrieval : Recall@k, Hit@k, MRR, par groupe langue/script.

- Recall@k : part des preuves attendues retrouvées dans le top-k (`evaluation.metrics`).
- Hit@k : au moins une preuve attendue dans le top-k.
- MRR : moyenne de 1 / rang de la première preuve attendue (0 si absente du top-k).
Les affirmations sans preuve attendue (`gold_doc_ids` vide) ne comptent pas dans ces métriques :
on rapporte le score du 1er passage retrouvé, qui sert à régler le seuil d'abstention.

Usage (depuis la racine du dépôt) :
    python -m rag_llm.evaluate_retrieval                        # BM25 (sans modèle)
    python -m rag_llm.evaluate_retrieval --method all           # BM25, dense et hybride
    python -m rag_llm.evaluate_retrieval --method dense --model intfloat/multilingual-e5-small
    python -m rag_llm.evaluate_retrieval --corpus data/processed/evidence_corpus.jsonl \\
        --claims chemin/claims.jsonl --exp-id EXP-D-00N
Les méthodes `dense` et `hybrid` demandent `pip install sentence-transformers` (modèle
téléchargé au premier lancement).
Résultat : `evaluation/results/lot-d_retrieval_<méthode>_<AAAAMMJJ>.json`.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from common.schemas import Claim, Evidence, Lang
from data.loaders import load_evidence_corpus
from evaluation.metrics import recall_at_k
from rag_llm.retrieval import hybrid
from rag_llm.retrieval.hybrid import METHODS, retrieve

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "rag_llm"
RESULTS_DIR = ROOT / "evaluation" / "results"
KS = (1, 5, 10)


def load_claims(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def mrr(relevant: list[set[str]], retrieved: list[list[str]]) -> float:
    rr = []
    for rel, ret in zip(relevant, retrieved, strict=True):
        rank = next((i + 1 for i, d in enumerate(ret) if d in rel), None)
        rr.append(1.0 / rank if rank else 0.0)
    return sum(rr) / len(rr) if rr else 0.0


def hit_at_k(relevant: list[set[str]], retrieved: list[list[str]], k: int) -> float:
    hits = [bool(rel & set(ret[:k])) for rel, ret in zip(relevant, retrieved, strict=True)]
    return sum(hits) / len(hits) if hits else 0.0


def compute_metrics(rows: list[dict]) -> dict:
    rows = [r for r in rows if r["gold"]]
    if not rows:
        return {"n": 0}
    rel = [set(r["gold"]) for r in rows]
    ret = [r["retrieved"] for r in rows]
    out: dict = {"n": len(rows)}
    for k in KS:
        out[f"recall@{k}"] = round(recall_at_k(rel, ret, k), 3)
        out[f"hit@{k}"] = round(hit_at_k(rel, ret, k), 3)
    out["mrr"] = round(mrr(rel, ret), 3)
    return out


def run(
    corpus: list[Evidence], claims: list[dict], k: int = max(KS), method: str = "bm25"
) -> list[dict]:
    rows = []
    for c in claims:
        claim = Claim(text=c["text"], lang=Lang(c["lang"]))
        results = retrieve(claim, corpus, k=k, method=method)
        rows.append({
            "claim_id": c["claim_id"],
            "group": f"{c['lang']}-{c.get('script', '?')}",
            "gold": c.get("gold_doc_ids", []),
            "retrieved": [e.doc_id for e in results],
            "top_score": round(results[0].score, 3) if results else 0.0,
        })
    return rows


def report(method: str, model: str, corpus: list[Evidence], rows: list[dict], args) -> dict:
    groups = defaultdict(list)
    for r in rows:
        groups[r["group"]].append(r)
    by_group = {g: compute_metrics(v) for g, v in sorted(groups.items())}
    overall = compute_metrics(rows)

    cols = ["n", "hit@1", "hit@5", "recall@5", "mrr"]
    label = method.upper() if method == "bm25" else f"{method.upper()} ({model})"
    print(f"\n=== {label} — {len(corpus)} passages, {len(rows)} affirmations")
    print(f"{'groupe':<14}" + "".join(f"{c:>10}" for c in cols))
    for name, m in [("GLOBAL", overall), *by_group.items()]:
        if m["n"]:
            print(f"{name:<14}" + "".join(f"{m[c]:>10}" for c in cols))

    misses = [r for r in rows if r["gold"] and not set(r["gold"]) & set(r["retrieved"][:5])]
    print("Échecs (aucune preuve attendue dans le top 5) : "
          + (", ".join(f"{r['claim_id']} [{r['group']}]" for r in misses) or "aucun"))
    # Calibration du seuil d'abstention : scores du 1er passage, avec et sans preuve existante.
    found = [r["top_score"] for r in rows if r["retrieved"][:1] and r["retrieved"][0] in r["gold"]]
    no_gold = {r["claim_id"]: r["top_score"] for r in rows if not r["gold"]}
    if found:
        print(f"Score du 1er passage quand il est correct : min={min(found)} max={max(found)}")
    print(f"Affirmations sans preuve dans le corpus (score du 1er passage) : {no_gold}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"lot-d_retrieval_{method}_{date.today():%Y%m%d}.json"
    payload = {
        "exp_id": args.exp_id, "lot": "D", "task": "retrieval",
        "model": method if method == "bm25" else f"{method}:{model}",
        "split": args.split,
        "metrics": {**overall, "by_group": by_group},
        "no_gold_top_scores": no_gold,
        "per_claim": rows,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Résultats : {out.relative_to(ROOT)}")
    return overall


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--corpus", type=Path, default=FIXTURES / "evidence_dev.jsonl")
    p.add_argument("--claims", type=Path, default=FIXTURES / "claims_dev.jsonl")
    p.add_argument("--method", choices=[*METHODS, "all"], default="bm25")
    p.add_argument("--model", default=None, help="modèle d'embeddings (défaut : EMBEDDING_MODEL)")
    p.add_argument("--exp-id", default="EXP-D-003")
    p.add_argument("--split", default="dev-fictif-v2")
    args = p.parse_args()

    if args.model:
        hybrid.set_encoder(hybrid.SentenceTransformerEncoder(args.model))
    corpus = load_evidence_corpus(args.corpus)
    claims = load_claims(args.claims)
    methods = METHODS if args.method == "all" else (args.method,)
    model = args.model or hybrid.SentenceTransformerEncoder().name

    summary = {}
    for method in methods:
        summary[method] = report(method, model, corpus, run(corpus, claims, method=method), args)

    if len(summary) > 1:
        print("\n=== Comparaison (GLOBAL)")
        cols = ["hit@1", "recall@5", "mrr"]
        print(f"{'méthode':<10}" + "".join(f"{c:>10}" for c in cols))
        for method, m in summary.items():
            print(f"{method:<10}" + "".join(f"{m[c]:>10}" for c in cols))


if __name__ == "__main__":
    main()
