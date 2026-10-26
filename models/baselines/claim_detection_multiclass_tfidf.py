"""Baseline multiclasses du Lot C : AFFIRMATION, OPINION ou AUTRE."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

LABELS = ("AFFIRMATION", "OPINION", "AUTRE")


def load_rows(path: Path) -> list[dict]:
    rows = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    invalid = [row.get("label") for row in rows if row.get("label") not in LABELS]
    if invalid:
        raise ValueError(f"Labels invalides : {sorted(set(invalid))}")
    return rows


def build_model(seed: int) -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
            (
                "classifier",
                LogisticRegression(max_iter=1_000, class_weight="balanced", random_state=seed),
            ),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--split-file", type=Path, help="IDs du test gelé; créé au premier passage")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--save-model",
        type=Path,
        help="sauvegarde le pipeline entraîné (joblib), utilisé par l'API (moteur tfidf)",
    )
    args = parser.parse_args()
    rows = load_rows(args.input)
    if args.split_file and args.split_file.exists():
        test_ids = set(json.loads(args.split_file.read_text(encoding="utf-8"))["test_ids"])
        train = [row for row in rows if row["id"] not in test_ids]
        test = [row for row in rows if row["id"] in test_ids]
    else:
        train, test = train_test_split(
            rows,
            test_size=args.test_size,
            random_state=args.seed,
            stratify=[row["label"] for row in rows],
        )
    model = build_model(args.seed)
    model.fit([row["text"] for row in train], [row["label"] for row in train])
    predicted = model.predict([row["text"] for row in test])
    gold = [row["label"] for row in test]
    by_language = {}
    for language in ("fr", "ar", "tn", "unk"):
        indices = [index for index, row in enumerate(test) if row.get("lang") == language]
        if indices:
            by_language[language] = {
                "n": len(indices),
                "macro_f1": f1_score(
                    [gold[index] for index in indices],
                    [predicted[index] for index in indices],
                    labels=LABELS,
                    average="macro",
                    zero_division=0,
                ),
            }
    predictions = [
        {
            "id": row["id"],
            "label": row["label"],
            "predicted_label": str(prediction),
            "lang": row.get("lang", "unk"),
            "correct": row["label"] == prediction,
        }
        for row, prediction in zip(test, predicted, strict=True)
    ]
    report = {
        "exp_id": "EXP-C-001",
        "lot": "C",
        "task": "claim_detection_multiclass",
        "model": "char_tfidf_3_5 + logistic_regression",
        "seed": args.seed,
        "n_train": len(train),
        "n_test": len(test),
        "accuracy": sum(item["correct"] for item in predictions) / len(predictions),
        "macro_f1": f1_score(gold, predicted, labels=LABELS, average="macro", zero_division=0),
        "per_class": classification_report(
            gold, predicted, labels=LABELS, output_dict=True, zero_division=0
        ),
        "results_by_language": by_language,
        "predictions": predictions,
        "test_ids": [row["id"] for row in test],
    }
    if args.split_file and not args.split_file.exists():
        args.split_file.parent.mkdir(parents=True, exist_ok=True)
        args.split_file.write_text(
            json.dumps(
                {"seed": args.seed, "test_ids": report["test_ids"]}, ensure_ascii=False, indent=2
            )
            + "\n",
            encoding="utf-8",
        )
    if args.save_model:
        import joblib

        args.save_model.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, args.save_model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {key: report[key] for key in ("n_train", "n_test", "macro_f1")}, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
