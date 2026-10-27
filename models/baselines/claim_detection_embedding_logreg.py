"""Baseline neuronale fixe : embeddings multilingues + régression logistique.

Elle est volontairement distincte de XLM-R + LoRA : l'encodeur n'est jamais
fine-tuné. Elle répond au prérequis « baseline neuronale » du module.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score

from models.baselines.claim_detection_multiclass_tfidf import LABELS, load_rows

DEFAULT_ENCODER = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def main() -> None:
    parser = argparse.ArgumentParser(description="Embeddings figés + Logistic Regression")
    parser.add_argument("input", type=Path)
    parser.add_argument("--split-file", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--encoder", default=DEFAULT_ENCODER)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as error:
        raise SystemExit("Installer sentence-transformers pour la baseline neuronale.") from error

    rows = load_rows(args.input)
    test_ids = set(json.loads(args.split_file.read_text(encoding="utf-8"))["test_ids"])
    train = [row for row in rows if row["id"] not in test_ids]
    test = [row for row in rows if row["id"] in test_ids]
    if not train or not test:
        raise ValueError("Split invalide : train ou test vide.")

    # L'encodeur est gelé : seul le classifieur linéaire est entraîné.
    encoder = SentenceTransformer(args.encoder)
    vectors = encoder.encode(
        [row["text"] for row in train], normalize_embeddings=True, show_progress_bar=True
    )
    test_vectors = encoder.encode(
        [row["text"] for row in test], normalize_embeddings=True, show_progress_bar=True
    )
    classifier = LogisticRegression(
        max_iter=2_000, class_weight="balanced", solver="saga", random_state=args.seed, n_jobs=1
    )
    classifier.fit(vectors, [row["label"] for row in train])
    predicted = classifier.predict(test_vectors)
    gold = [row["label"] for row in test]
    probabilities = classifier.predict_proba(test_vectors)

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
            "affirmation_probability": float(
                probability[list(classifier.classes_).index("AFFIRMATION")]
            ),
        }
        for row, prediction, probability in zip(test, predicted, probabilities, strict=True)
    ]
    report = {
        "exp_id": "EXP-C-004",
        "lot": "C",
        "task": "claim_detection_multiclass",
        "model": "frozen_multilingual_minilm + logistic_regression",
        "encoder": args.encoder,
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
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {key: report[key] for key in ("seed", "n_train", "n_test", "macro_f1")},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
