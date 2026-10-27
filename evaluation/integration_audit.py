"""Audit reproductible Lot E de la chaîne Bronze intégrée.

Usage : python -m evaluation.integration_audit
Le script utilise les cas annotés versionnés et écrit une synthèse légère dans
``evaluation/results/``. Ce n'est pas une mesure scientifique générale : le
jeu contient quatre cas de contrôle servant à détecter les régressions entre
lots (vrai, faux numérique, abstention, opinion filtrée).
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from api.main import bronze_check_route, BronzeCheckIn
from evaluation.metrics import abstention_rate, citation_validity, macro_f1, recall_at_k

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "data" / "annotations" / "bronze_fr_integration_eval.jsonl"
DEFAULT_OUTPUT = ROOT / "evaluation" / "results" / "lot-e_integration_bronze_20261027.json"


def load_cases(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run(cases: list[dict]) -> dict:
    rows: list[dict] = []
    y_true: list[str] = []
    y_pred: list[str] = []
    relevant: list[set[str]] = []
    retrieved: list[list[str]] = []
    citations: list[list[str]] = []
    abstained: list[bool] = []

    for case in cases:
        trace = bronze_check_route(BronzeCheckIn(text=case["text"]))
        claims = trace["claims"]
        claim_count_ok = len(claims) == case["expected_claims"]
        trace_claim = claims[0] if claims else None
        verdict = trace_claim["verdict"] if trace_claim else None
        evidence_ids = [item["doc_id"] for item in trace_claim["evidence"]] if trace_claim else []
        cited = verdict["citations"] if verdict else []
        row = {
            "id": case["id"], "expected_claims": case["expected_claims"], "actual_claims": len(claims),
            "claim_count_ok": claim_count_ok, "gold_label": case["gold_label"],
            "predicted_label": verdict["label"] if verdict else None,
            "abstained": verdict["abstained"] if verdict else None,
            "retrieved_doc_ids": evidence_ids, "citations": cited,
            "latency_ms": trace["timings_ms"],
        }
        rows.append(row)
        if case["gold_label"] is not None and verdict is not None:
            y_true.append(case["gold_label"])
            y_pred.append(verdict["label"])
            relevant.append(set(case["relevant_doc_ids"]))
            retrieved.append(evidence_ids)
            citations.append(cited)
            abstained.append(verdict["abstained"])

    correctness = sum(row["claim_count_ok"] and (
        row["gold_label"] is None or row["gold_label"] == row["predicted_label"]
    ) for row in rows)
    latency = [row["latency_ms"]["total"] for row in rows]
    return {
        "n": len(rows), "end_to_end_success_rate": round(correctness / len(rows), 3) if rows else 0.0,
        "macro_f1": round(macro_f1(y_true, y_pred), 3) if y_true else 0.0,
        "recall_at_5": round(recall_at_k(relevant, retrieved, 5), 3) if relevant else 0.0,
        "abstention_rate": round(abstention_rate(abstained), 3),
        "latency_ms_mean": round(sum(latency) / len(latency), 2) if latency else 0.0,
        "latency_ms_max": round(max(latency), 2) if latency else 0.0,
        **citation_validity(citations, retrieved), "items": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--exp-id", default="EXP-E-002")
    args = parser.parse_args()
    metrics = run(load_cases(args.cases))
    payload = {
        "exp_id": args.exp_id, "lot": "E", "task": "integration_bronze",
        "model": "regles+bm25+nli-lexical+gabarit", "split": "integration-fr-v1 (n=4)",
        "date": str(date.today()), "metrics": metrics,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in metrics.items() if k != "items"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
