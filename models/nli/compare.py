"""Lot C — Model 2 : comparaison appariée de deux modèles NLI sur les mêmes paires.

Bootstrap apparié (mêmes paires rééchantillonnées pour les deux modèles) sur la différence de
macro-F1, comme pour le Model 1. Prend les fichiers de prédictions écrits par `evaluate`
(data/interim/lot_c/nli/predictions_<version>_<partie>_<modèle>.jsonl).

    python -m models.nli.compare --baseline <prédictions de la baseline> \
        --models <prédictions seed42> <prédictions seed123> <prédictions seed2026>
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path

from models.nli.data import OUT_DIR
from models.nli.evaluate import metrics

N_BOOT = 1000
SEED = 20261026


def load_predictions(path: Path) -> dict[str, tuple[str, str]]:
    """pair_id → (label, prédiction)."""
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return {r["pair_id"]: (r["label"], r["pred"]) for r in rows}


def paired_bootstrap(
    gold: list[str], a: list[str], b: list[str], n: int = N_BOOT, seed: int = SEED
) -> dict:
    """Différence macro-F1(b) − macro-F1(a), IC 95 % et p (part des tirages où b ≤ a)."""
    rng, idx = random.Random(seed), range(len(gold))
    diffs = []
    for _ in range(n):
        s = [rng.choice(idx) for _ in idx]
        g = [gold[i] for i in s]
        diffs.append(
            metrics(g, [b[i] for i in s])["macro_f1"] - metrics(g, [a[i] for i in s])["macro_f1"]
        )
    diffs.sort()
    return {
        "diff": metrics(gold, b)["macro_f1"] - metrics(gold, a)["macro_f1"],
        "ci95": [diffs[int(0.025 * n)], diffs[int(0.975 * n) - 1]],
        "p_value": sum(d <= 0 for d in diffs) / n,
    }


def _resolve(name: str) -> Path:
    p = Path(name)
    return p if p.exists() else OUT_DIR / name


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--models", nargs="+", required=True)
    args = ap.parse_args()

    base = load_predictions(_resolve(args.baseline))
    ids = sorted(base)
    gold = [base[i][0] for i in ids]
    a = [base[i][1] for i in ids]
    print(f"baseline : macro-F1 {metrics(gold, a)['macro_f1']:.4f}  (n = {len(ids)})")
    scores = []
    for name in args.models:
        other = load_predictions(_resolve(name))
        if sorted(other) != ids:
            raise SystemExit(f"{name} : pas les mêmes paires que la baseline")
        b = [other[i][1] for i in ids]
        res = paired_bootstrap(gold, a, b)
        scores.append(metrics(gold, b)["macro_f1"])
        print(
            f"{Path(name).name} : macro-F1 {scores[-1]:.4f}  différence {res['diff']:+.4f}  "
            f"IC95 [{res['ci95'][0]:+.4f} ; {res['ci95'][1]:+.4f}]  p = {res['p_value']:.3f}"
        )
    if len(scores) > 1:
        print(
            f"moyenne ± écart-type sur {len(scores)} graines : "
            f"{statistics.mean(scores):.4f} ± {statistics.stdev(scores):.4f}"
        )


if __name__ == "__main__":
    main()
