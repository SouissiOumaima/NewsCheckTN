"""Lot D — Évaluation bout-en-bout du verdict : retrieval → NLI → verdict par gabarit.

Métriques :
- exactitude et macro-F1 sur les 4 labels (l'abstention compte comme `preuves_insuffisantes`) ;
- couverture : part des affirmations pour lesquelles le système ose un verdict ;
- précision sélective : exactitude parmi les verdicts émis (hors abstentions) ;
- abstention justifiée : part des affirmations SANS preuve dans le corpus où le système s'abstient ;
- citations invalides : doc_id cités qui ne font pas partie des preuves retrouvées (doit valoir 0) ;
- répartition des raisons d'abstention.

Usage (depuis la racine du dépôt) :
    python -m rag_llm.evaluate_verdict                  # NLI par règles (rag_llm.baseline_stance)
    python -m rag_llm.evaluate_verdict --stance lot-c   # NLI du Lot C (models.nli.stance)
    python -m rag_llm.evaluate_verdict --method hybrid  # retrieval hybride (sentence-transformers)
Résultat : `evaluation/results/lot-d_verdict_<méthode>_<stance>_<AAAAMMJJ>.json`.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from common.schemas import Claim, Label, Lang
from data.loaders import load_evidence_corpus
from evaluation.metrics import macro_f1
from rag_llm.evaluate_retrieval import FIXTURES, RESULTS_DIR, ROOT, load_claims
from rag_llm.retrieval import hybrid
from rag_llm.retrieval.hybrid import METHODS, min_relevance_score, retrieve
from rag_llm.verdict import generate_verdict_with_reason

NEI = Label.NOT_ENOUGH_INFO.value


def _stance_fn(name: str):
    if name == "lot-c":
        from models.nli.stance import predict_stances
    else:
        from rag_llm.baseline_stance import predict_stances
    return predict_stances


def run(
    corpus, claims: list[dict], stance: str = "rules", k: int = 5, method: str = "bm25"
) -> list[dict]:
    predict_stances = _stance_fn(stance)
    threshold = min_relevance_score(method)
    rows = []
    for c in claims:
        claim = Claim(text=c["text"], lang=Lang(c["lang"]))
        evidences = retrieve(claim, corpus, k=k, method=method)
        verdict, reason = generate_verdict_with_reason(
            claim, predict_stances(claim, evidences), min_score=threshold
        )
        retrieved = {e.doc_id for e in evidences}
        rows.append({
            "claim_id": c["claim_id"],
            "group": f"{c['lang']}-{c.get('script', '?')}",
            "gold": c["gold_label"],
            "pred": verdict.label.value,
            "abstained": verdict.abstained,
            "reason": reason,
            "citations": verdict.citations,
            "invalid_citations": [d for d in verdict.citations if d not in retrieved],
            "uncertainty": verdict.uncertainty,
        })
    return rows


def compute_metrics(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0}
    emitted = [r for r in rows if not r["abstained"]]
    no_evidence = [r for r in rows if r["gold"] == NEI]
    return {
        "n": len(rows),
        "accuracy": round(sum(r["pred"] == r["gold"] for r in rows) / len(rows), 3),
        "macro_f1": round(macro_f1([r["gold"] for r in rows], [r["pred"] for r in rows]), 3),
        "coverage": round(len(emitted) / len(rows), 3),
        "selective_accuracy": (
            round(sum(r["pred"] == r["gold"] for r in emitted) / len(emitted), 3)
            if emitted else None
        ),
        "justified_abstention": (
            round(sum(r["abstained"] for r in no_evidence) / len(no_evidence), 3)
            if no_evidence else None
        ),
        "invalid_citations": sum(len(r["invalid_citations"]) for r in rows),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--corpus", type=Path, default=FIXTURES / "evidence_dev.jsonl")
    p.add_argument("--claims", type=Path, default=FIXTURES / "claims_dev.jsonl")
    p.add_argument("--stance", choices=["rules", "lot-c"], default="rules")
    p.add_argument("--method", choices=METHODS, default="bm25")
    p.add_argument("--model", default=None, help="modèle d'embeddings (défaut : EMBEDDING_MODEL)")
    p.add_argument("--exp-id", default="EXP-D-002")
    p.add_argument("--split", default="dev-fictif-v2")
    args = p.parse_args()

    if args.model:
        hybrid.set_encoder(hybrid.SentenceTransformerEncoder(args.model))
    corpus = load_evidence_corpus(args.corpus)
    rows = run(corpus, load_claims(args.claims), stance=args.stance, method=args.method)
    overall = compute_metrics(rows)
    groups = defaultdict(list)
    for r in rows:
        groups[r["group"]].append(r)
    by_group = {g: compute_metrics(v) for g, v in sorted(groups.items())}

    print(f"\nVerdict par gabarit — retrieval : {args.method} — NLI : {args.stance}")
    print(f"{'id':<9}{'groupe':<12}{'attendu':<24}{'prédit':<24}raison / citations")
    for r in rows:
        mark = "✓" if r["pred"] == r["gold"] else "✗"
        info = r["reason"] or ", ".join(r["citations"])
        print(f"{r['claim_id']:<9}{r['group']:<12}{r['gold']:<24}{r['pred']:<22}{mark} {info}")

    cols = ["n", "accuracy", "coverage", "selective_accuracy", "justified_abstention"]
    print(f"\n{'groupe':<12}" + "".join(f"{c:>22}" for c in cols))
    for name, m in [("GLOBAL", overall), *by_group.items()]:
        print(f"{name:<12}" + "".join(f"{str(m.get(c)):>22}" for c in cols))
    print(f"\nMacro-F1 : {overall['macro_f1']}")
    print(f"Citations invalides : {overall['invalid_citations']}")
    reasons = Counter(r["reason"] for r in rows if r["reason"])
    print(f"Raisons d'abstention : {dict(reasons)}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"lot-d_verdict_{args.method}_{args.stance}_{date.today():%Y%m%d}.json"
    payload = {
        "exp_id": args.exp_id, "lot": "D", "task": "verdict",
        "model": f"{args.method}+gabarit+{args.stance}",
        "split": args.split,
        "metrics": {**overall, "by_group": by_group, "abstention_reasons": dict(reasons)},
        "per_claim": rows,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Résultats : {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
