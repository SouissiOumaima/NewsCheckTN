"""Évalue un checkpoint Model 1, par langue, et exporte les erreurs à relire.

Exemple (Colab) :
  python -m models.encoders.evaluate_claim_detection \
    --input data/processed/claim_detection_600.jsonl \
    --split-file data/splits/claim_detection_multiclass_600_seed42.json \
    --checkpoint models/checkpoints/claim_detection_xlmr_lora_seed42 \
    --output-dir evaluation/results/model1_seed42
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from models.encoders.train_xlmr_claim_detection import LABEL_TO_ID, LABELS, read_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Évaluation et erreurs du Model 1")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--split-file", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-errors", type=int, default=30)
    parser.add_argument("--text-mode", choices=("raw", "normalized"), default="raw")
    args = parser.parse_args()

    try:
        import torch
        from peft import PeftConfig, PeftModel
        from sklearn.metrics import classification_report, f1_score
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as error:
        raise SystemExit("Installer transformers, peft, torch et scikit-learn.") from error

    test_ids = set(json.loads(args.split_file.read_text(encoding="utf-8"))["test_ids"])
    rows = [row for row in read_rows(args.input) if row["id"] in test_ids]
    config = PeftConfig.from_pretrained(str(args.checkpoint))
    tokenizer = AutoTokenizer.from_pretrained(str(args.checkpoint))
    base = AutoModelForSequenceClassification.from_pretrained(
        config.base_model_name_or_path, num_labels=len(LABELS)
    )
    model = PeftModel.from_pretrained(base, str(args.checkpoint)).eval()

    if args.text_mode == "normalized":
        from normalization.normalize import normalize

        def model_text(row: dict) -> str:
            return normalize(row["text"]).text
    else:

        def model_text(row: dict) -> str:
            return row["text"]

    predictions: list[dict] = []
    for row in rows:
        encoded = tokenizer(model_text(row), return_tensors="pt", truncation=True, max_length=256)
        with torch.no_grad():
            probs = torch.softmax(model(**encoded).logits, dim=-1)[0].tolist()
        pred_id = max(range(len(probs)), key=probs.__getitem__)
        predictions.append(
            {
                **row,
                "predicted_label": LABELS[pred_id],
                "confidence": round(float(probs[pred_id]), 6),
                "affirmation_probability": round(float(probs[LABEL_TO_ID["AFFIRMATION"]]), 6),
                "correct": LABELS[pred_id] == row["label"],
            }
        )

    gold = [LABEL_TO_ID[row["label"]] for row in predictions]
    pred = [LABEL_TO_ID[row["predicted_label"]] for row in predictions]
    by_language: dict[str, dict] = {}
    for language in ("fr", "ar", "tn", "unk"):
        indexes = [i for i, row in enumerate(predictions) if row.get("lang") == language]
        if indexes:
            by_language[language] = {
                "n": len(indexes),
                "macro_f1": f1_score(
                    [gold[i] for i in indexes],
                    [pred[i] for i in indexes],
                    labels=list(range(len(LABELS))),
                    average="macro",
                    zero_division=0,
                ),
            }
    summary = {
        "exp_id": "EXP-C-003",
        "lot": "C",
        "task": "claim_detection_multiclass",
        "model": "xlmr_lora_r8",
        "split": "frozen_test",
        "text_mode": args.text_mode,
        "n_test": len(predictions),
        "macro_f1": f1_score(
            gold, pred, labels=list(range(len(LABELS))), average="macro", zero_division=0
        ),
        "classification_report": classification_report(
            gold,
            pred,
            target_names=LABELS,
            labels=list(range(len(LABELS))),
            output_dict=True,
            zero_division=0,
        ),
        "results_by_language": by_language,
        "unknown_language_count": sum(row.get("lang") == "unk" for row in predictions),
        "label_distribution": dict(Counter(row["label"] for row in predictions)),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "metrics.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "predictions.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in predictions), encoding="utf-8"
    )
    errors = [row for row in predictions if not row["correct"]]
    (args.output_dir / "errors_to_review_30.jsonl").write_text(
        "".join(
            json.dumps({**row, "error_category": "", "review_note": ""}, ensure_ascii=False) + "\n"
            for row in errors[: args.max_errors]
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
