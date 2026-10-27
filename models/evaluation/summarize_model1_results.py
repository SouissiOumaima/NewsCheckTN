"""Construit le tableau final langues × modèles à partir des sorties réelles."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "results_by_language" not in data:
        raise ValueError(f"{path} ne contient pas results_by_language.")
    return data


def mean_sd(values: list[float]) -> dict:
    return {
        "mean": statistics.mean(values),
        "std": statistics.stdev(values) if len(values) > 1 else 0.0,
        "n_runs": len(values),
    }


def aggregate(name: str, reports: list[dict]) -> dict:
    result = {
        "model": name,
        "overall_macro_f1": mean_sd([float(item["macro_f1"]) for item in reports]),
        "by_lang": {},
    }
    for lang in ("fr", "ar", "tn"):
        values = [
            float(item["results_by_language"][lang]["macro_f1"])
            for item in reports
            if lang in item["results_by_language"]
        ]
        counts = [
            int(item["results_by_language"][lang]["n"])
            for item in reports
            if lang in item["results_by_language"]
        ]
        if values:
            result["by_lang"][lang] = {**mean_sd(values), "n_test": counts[0]}
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tfidf", type=Path, nargs="+", required=True)
    parser.add_argument("--neural", type=Path, nargs="+", required=True)
    parser.add_argument(
        "--xlmr", type=Path, nargs="+", required=True, help="fichiers metrics.json XLM-R"
    )
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    systems = [
        aggregate("TF-IDF + Logistic Regression", [load(path) for path in args.tfidf]),
        aggregate(
            "Embeddings figés MiniLM + Logistic Regression", [load(path) for path in args.neural]
        ),
        aggregate("XLM-R + LoRA", [load(path) for path in args.xlmr]),
    ]
    report = {
        "exp_id": "EXP-C-006",
        "lot": "C",
        "task": "model1_language_comparison",
        "systems": systems,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Tableau final Model 1",
        "",
        "Macro-F1 : moyenne ± écart-type sur les runs indiqués.",
        "",
        "| Modèle | Global | FR | AR | TN |",
        "| --- | --- | --- | --- | --- |",
    ]
    for system in systems:
        overall = system["overall_macro_f1"]
        cells = [f"{overall['mean']:.4f} ± {overall['std']:.4f}"]
        for lang in ("fr", "ar", "tn"):
            value = system["by_lang"].get(lang)
            cells.append(
                "—"
                if not value
                else f"{value['mean']:.4f} ± {value['std']:.4f} (n={value['n_test']})"
            )
        lines.append(f"| {system['model']} | " + " | ".join(cells) + " |")
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
