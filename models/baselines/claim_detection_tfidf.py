"""Baseline reproductible TF-IDF + régression logistique pour le Lot C.

Ce script apprend la *check-worthiness* binaire : ``AFFIRMATION`` est la
classe positive; ``OPINION`` et ``AUTRE`` sont la classe négative. Il accepte
les JSONL de Lot A1 sans modifier les annotations originales.

Exemple :
    python -m models.baselines.claim_detection_tfidf \
      --input data/annotations/normalized/tarc_review_30.jsonl \
      --input data/annotations/normalized/tunifact_review_30.jsonl \
      --split-file data/splits/claim_detection_pilot_seed42.json \
      --output evaluation/results/claim_detection_tfidf_seed42.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


POSITIVE_LABEL = "AFFIRMATION"
NEGATIVE_LABELS = frozenset({"OPINION", "AUTRE"})


@dataclass(frozen=True)
class Example:
    """Une phrase annotée prête pour la baseline."""

    identifier: str
    text: str
    lang: str
    target: int


def _annotation(row: dict) -> str | None:
    """Accepte le nom de colonne A1 actuel et le nom générique futur."""
    value = row.get("annotation", row.get("label"))
    return value.strip().upper() if isinstance(value, str) else None


def load_examples(paths: Iterable[Path]) -> list[Example]:
    """Charge seulement les lignes avec un label Lot B utilisable."""
    examples: list[Example] = []
    seen: set[str] = set()
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                annotation = _annotation(row)
                if annotation not in NEGATIVE_LABELS | {POSITIVE_LABEL}:
                    continue
                identifier = str(row.get("id", f"{path.stem}-{line_number}"))
                # Le même extrait ne doit jamais se retrouver des deux côtés du split.
                if identifier in seen:
                    continue
                text = str(row.get("text", "")).strip()
                if not text:
                    continue
                seen.add(identifier)
                examples.append(
                    Example(
                        identifier=identifier,
                        text=text,
                        lang=str(row.get("lang", "unk")),
                        target=int(annotation == POSITIVE_LABEL),
                    )
                )
    if not examples:
        raise ValueError("Aucune annotation AFFIRMATION/OPINION/AUTRE exploitable.")
    if len({item.target for item in examples}) < 2:
        raise ValueError("La baseline exige au moins une affirmation et un exemple non-affirmation.")
    return examples


def make_split(examples: list[Example], seed: int, test_size: float) -> tuple[list[Example], list[Example]]:
    """Crée un split stratifié uniquement sur la cible binaire."""
    indices = list(range(len(examples)))
    targets = [item.target for item in examples]
    train_indices, test_indices = train_test_split(
        indices, test_size=test_size, random_state=seed, stratify=targets
    )
    return [examples[i] for i in train_indices], [examples[i] for i in test_indices]


def split_from_ids(examples: list[Example], test_ids: set[str]) -> tuple[list[Example], list[Example]]:
    """Réutilise un test gelé, afin de ne pas le choisir après les résultats."""
    test = [item for item in examples if item.identifier in test_ids]
    train = [item for item in examples if item.identifier not in test_ids]
    if not test or not train or len({item.target for item in test}) < 2:
        raise ValueError("Le split gelé doit contenir train/test et les deux classes dans le test.")
    return train, test


def build_model() -> Pipeline:
    """Baseline classique adaptée aux écritures latines et arabes."""
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1, sublinear_tf=True)),
            ("classifier", LogisticRegression(max_iter=1_000, class_weight="balanced", random_state=42)),
        ]
    )


def metrics_by_language(model: Pipeline, examples: list[Example]) -> dict[str, float]:
    """Macro-F1 par langue, avec les deux labels fixes même si un manque dans un groupe."""
    result: dict[str, float] = {}
    for lang in sorted({item.lang for item in examples}):
        group = [item for item in examples if item.lang == lang]
        predicted = model.predict([item.text for item in group])
        result[lang] = round(f1_score([item.target for item in group], predicted, labels=[0, 1], average="macro", zero_division=0), 4)
    return result


def run(examples: list[Example], *, seed: int, test_size: float, split_file: Path | None) -> tuple[dict, list[Example]]:
    """Entraîne sans toucher au test et renvoie métriques + IDs du test à geler."""
    if split_file and split_file.exists():
        frozen = json.loads(split_file.read_text(encoding="utf-8"))
        train, test = split_from_ids(examples, set(frozen["test_ids"]))
    else:
        train, test = make_split(examples, seed, test_size)

    model = build_model()
    model.fit([item.text for item in train], [item.target for item in train])
    predicted = model.predict([item.text for item in test])
    report = {
        "task": "claim_detection_binary",
        "model": "char_tfidf_3_5 + logistic_regression",
        "seed": seed,
        "n_train": len(train),
        "n_test": len(test),
        "macro_f1": round(f1_score([item.target for item in test], predicted, labels=[0, 1], average="macro", zero_division=0), 4),
        "macro_f1_by_lang": metrics_by_language(model, test),
        "test_ids": [item.identifier for item in test],
    }
    return report, test


def main() -> None:
    parser = argparse.ArgumentParser(description="Baseline TF-IDF + Logistic Regression du Lot C")
    parser.add_argument("--input", type=Path, action="append", required=True, help="JSONL annoté de Lot A1 (répéter l'option)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--split-file", type=Path, help="Fichier d'IDs de test gelé, créé s'il n'existe pas")
    parser.add_argument("--output", type=Path, required=True, help="Rapport JSON de l'expérience")
    args = parser.parse_args()

    examples = load_examples(args.input)
    report, _ = run(examples, seed=args.seed, test_size=args.test_size, split_file=args.split_file)
    if args.split_file and not args.split_file.exists():
        args.split_file.parent.mkdir(parents=True, exist_ok=True)
        args.split_file.write_text(json.dumps({"seed": args.seed, "test_ids": report["test_ids"]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
