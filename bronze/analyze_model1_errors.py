"""Catégorise un fichier d'erreurs Model 1 et produit le rapport de revue."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def category(row: dict) -> str:
    """Catégorie déterministe à partir du label gold et de la modalité."""
    modality = row.get("modalite", "").casefold()
    gold = row["label"]
    prediction = row["predicted_label"]
    if gold == "OPINION":
        return "opinion_non_reconnue" if prediction == "AFFIRMATION" else "opinion_pris_pour_autre"
    if modality == "hypothétique":
        return "hypothese_non_reconnue"
    if modality == "souhait":
        return "souhait_non_reconnu"
    if modality == "interrogatif":
        return "question_non_reconnue"
    if modality == "rapporté":
        return "discours_rapporte_non_reconnu"
    if gold == "AFFIRMATION":
        return "affirmation_non_reconnue"
    return "autre_confusion"


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def enrich(rows: list[dict]) -> list[dict]:
    result = []
    for row in rows:
        if row.get("correct") is not False:
            raise ValueError(f"{row.get('id')}: le fichier doit contenir uniquement des erreurs")
        result.append({**row, "error_category": category(row)})
    return result


def markdown(rows: list[dict]) -> str:
    counts = Counter(row["error_category"] for row in rows)
    seed_counts = Counter(row["model_seed"] for row in rows)
    lines = [
        "# Analyse de 30 erreurs — Model 1", "",
        "Source : `errors_30_cross_seed.jsonl`. Chaque ligne est une prédiction fausse ; "
        "les catégories sont dérivées du gold label et de la modalité, puis restent à relire "
        "pour l'oral.", "",
        f"- Nombre d'erreurs : **{len(rows)}**",
        "- Seeds : " + ", ".join(f"{seed} = {n}" for seed, n in sorted(seed_counts.items())), "",
        "## Répartition", "", "| Catégorie | n |", "| --- | ---: |",
    ]
    lines.extend(f"| {name.replace('_', ' ')} | {count} |" for name, count in sorted(counts.items()))
    lines.extend(["", "## Exemples à présenter", ""])
    seen: set[str] = set()
    for row in rows:
        name = row["error_category"]
        if name in seen:
            continue
        seen.add(name)
        lines.append(
            f"- **{name.replace('_', ' ')}** — `{row['id']}` : gold `{row['label']}`, "
            f"prédit `{row['predicted_label']}` ; « {row['text']} »"
        )
    lines.extend(["", "## Registre complet", "", "| ID | Gold | Prédit | Modalité | Seed | Catégorie |", "| --- | --- | --- | --- | --- | --- |"])
    lines.extend(
        f"| {row['id']} | {row['label']} | {row['predicted_label']} | {row['modalite']} | "
        f"{row['model_seed']} | {row['error_category'].replace('_', ' ')} |"
        for row in rows
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Produit l'analyse des 30 erreurs Model 1.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--jsonl-output", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    args = parser.parse_args()
    rows = enrich(load(args.input))
    args.jsonl_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.jsonl_output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    args.report_output.write_text(markdown(rows), encoding="utf-8")
    print(json.dumps({"errors": len(rows), "categories": Counter(row["error_category"] for row in rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
