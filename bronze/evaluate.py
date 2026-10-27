"""Évaluation reproductible de la chaîne complète du palier Bronze."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from common.schemas import Evidence
from evaluation.metrics import macro_f1, recall_at_k

from bronze.pipeline import check_text


def load_jsonl(path: Path) -> list[dict]:
    """Charge un fichier JSONL d'évaluation, en ignorant les commentaires."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Fichier introuvable : {path}. Utilisez les fichiers *_demo.jsonl "
            "pour vérifier l'installation, ou créez le fichier à partir du gabarit."
        )
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip() and not line.startswith("#")]


def load_corpus(path: Path) -> list[Evidence]:
    return [
        Evidence(
            doc_id=row["doc_id"], text=row["text"], source=row.get("source", ""),
            url=row.get("url"), date=row.get("date"),
        )
        for row in load_jsonl(path)
    ]


def evaluate(records: list[dict], corpus: list[Evidence], k: int = 5) -> dict:
    """Calcule Macro-F1 des verdicts et Recall@k des preuves attendues."""
    gold_labels, predicted_labels, relevant, retrieved, items = [], [], [], [], []
    for record in records:
        verdicts = check_text(record["text"], k=k, corpus=corpus)
        verdict = verdicts[0] if verdicts else None
        prediction = verdict.label.value if verdict else "aucun_verdict"
        expected_evidence = set(record.get("relevant_doc_ids", []))
        evidence_ids = verdict.citations if verdict else []
        gold_labels.append(record["gold_label"])
        predicted_labels.append(prediction)
        relevant.append(expected_evidence)
        retrieved.append(evidence_ids)
        items.append({
            "id": record["id"], "gold_label": record["gold_label"],
            "predicted_label": prediction, "relevant_doc_ids": sorted(expected_evidence),
            "retrieved_doc_ids": evidence_ids,
            "correct": prediction == record["gold_label"],
        })
    return {
        "n": len(records), "macro_f1": macro_f1(gold_labels, predicted_labels),
        "recall_at_k": recall_at_k(relevant, retrieved, k), "items": items,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Évalue le pipeline français Bronze.")
    parser.add_argument("--eval", type=Path, required=True, help="JSONL avec id, text, gold_label, relevant_doc_ids")
    parser.add_argument("--corpus", type=Path, required=True, help="corpus JSONL de preuves françaises")
    parser.add_argument("--output", type=Path, required=True, help="rapport JSON à écrire")
    parser.add_argument("-k", type=int, default=5)
    args = parser.parse_args()
    result = evaluate(load_jsonl(args.eval), load_corpus(args.corpus), args.k)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "items"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
