"""Bootstrap apparié de la différence de macro-F1 entre deux modèles.

Chaque réplication rééchantillonne les mêmes IDs de test pour les deux systèmes,
ce qui préserve l'appariement et évite de confondre effet modèle et effet split.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_predictions(path: Path) -> list[dict]:
    """Accepte un JSONL de prédictions ou un rapport JSON contenant ``predictions``."""
    if path.suffix == ".jsonl":
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("predictions"), list):
        raise ValueError(f"{path} ne contient pas de liste predictions.")
    return data["predictions"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap apparié de macro-F1")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--baseline-name", default="baseline")
    parser.add_argument("--candidate-name", default="candidate")
    parser.add_argument("--replications", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        import numpy as np
        from sklearn.metrics import f1_score
    except ImportError as error:
        raise SystemExit("Installer numpy et scikit-learn.") from error

    baseline = {row["id"]: row for row in read_predictions(args.baseline)}
    candidate = {row["id"]: row for row in read_predictions(args.candidate)}
    ids = sorted(set(baseline) & set(candidate))
    if len(ids) < 2 or set(baseline) != set(candidate):
        raise ValueError("Les fichiers doivent contenir exactement les mêmes IDs de test.")
    labels = ("AFFIRMATION", "OPINION", "AUTRE")
    gold = np.array([baseline[row_id]["label"] for row_id in ids])
    base_pred = np.array([baseline[row_id]["predicted_label"] for row_id in ids])
    candidate_pred = np.array([candidate[row_id]["predicted_label"] for row_id in ids])
    baseline_f1 = f1_score(gold, base_pred, labels=labels, average="macro", zero_division=0)
    candidate_f1 = f1_score(gold, candidate_pred, labels=labels, average="macro", zero_division=0)

    rng = np.random.default_rng(args.seed)
    differences = []
    for _ in range(args.replications):
        sample = rng.integers(0, len(ids), size=len(ids))
        differences.append(
            f1_score(
                gold[sample],
                candidate_pred[sample],
                labels=labels,
                average="macro",
                zero_division=0,
            )
            - f1_score(
                gold[sample], base_pred[sample], labels=labels, average="macro", zero_division=0
            )
        )
    differences = np.asarray(differences)
    p_value = min(1.0, 2 * min(float(np.mean(differences <= 0)), float(np.mean(differences >= 0))))
    report = {
        "exp_id": "EXP-C-005",
        "lot": "C",
        "task": "paired_bootstrap_macro_f1",
        "baseline": args.baseline_name,
        "candidate": args.candidate_name,
        "n_test": len(ids),
        "replications": args.replications,
        "seed": args.seed,
        "baseline_macro_f1": baseline_f1,
        "candidate_macro_f1": candidate_f1,
        "difference_candidate_minus_baseline": candidate_f1 - baseline_f1,
        "ci_95": [float(np.quantile(differences, 0.025)), float(np.quantile(differences, 0.975))],
        "p_value_two_sided": p_value,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
