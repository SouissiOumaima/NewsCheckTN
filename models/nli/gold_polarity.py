"""Lot C — Model 2, palier Gold (EXP-C-016) : inversions de polarité (supports ↔ refutes).

Aucun modèle n'est relancé : relit les prédictions du test v3 déjà sauvegardées par la mesure
unique d'EXP-C-011 (`data/interim/lot_c/nli/silver_test/`), puis donne pour chaque modèle la
matrice de confusion, le nombre d'erreurs et le nombre d'inversions de polarité (référence et
prédiction sont « supports » et « refutes »). Rien n'est réglé d'après ces chiffres.

    python -X utf8 -m models.nli.gold_polarity

Écrit evaluation/results/lot-c_nli-gold_polarite_test_<AAAAMMJJ>.json (comptes et identifiants de
paires seulement, aucun texte du corpus).
"""

from __future__ import annotations

import json
import math
from datetime import date

from models.nli.data import LABELS, OUT_DIR, ROOT, load_pairs
from models.nli.evaluate import metrics

EXP_ID = "EXP-C-016"
TEST_FILE = OUT_DIR / "nli_v3_test.jsonl"
PRED_DIR = OUT_DIR / "silver_test"
MODELS = {
    "principal_seed42": "predictions_v3_test_principal_seed42.jsonl",
    "zero-shot-fp32": "predictions_v3_test_zero-shot-fp32.jsonl",
    "bronze": "predictions_v3_test_bronze.jsonl",
}
POLAR = {"supports", "refutes"}
MIN_ERRORS = 20  # en dessous : chiffres descriptifs seulement (règle fixée avant calcul)


def error_type(gold: str, pred: str) -> str | None:
    """None si juste ; sinon « inversion », « vers neutral » ou « depuis neutral »."""
    if gold == pred:
        return None
    if {gold, pred} == POLAR:
        return "inversion"
    return "vers neutral" if pred == "neutral" else "depuis neutral"


def wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    """Intervalle de Wilson à 95 % de la proportion k / n (indicatif sur de petits effectifs)."""
    if n == 0:
        return None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4)]


def polarity(gold: list[str], pred: list[str], ids: list[str]) -> dict:
    """Matrice de confusion, erreurs par type et part des inversions parmi les erreurs."""
    types = {i: error_type(g, p) for i, g, p in zip(ids, gold, pred, strict=True)}
    errors = [i for i, t in types.items() if t]
    inv = [i for i in errors if types[i] == "inversion"]
    by_dir = {
        "supports->refutes": sum(
            1 for g, p in zip(gold, pred, strict=True) if (g, p) == ("supports", "refutes")
        ),
        "refutes->supports": sum(
            1 for g, p in zip(gold, pred, strict=True) if (g, p) == ("refutes", "supports")
        ),
    }
    return {
        "n": len(gold),
        "confusion": metrics(gold, pred)["confusion"],
        "errors": len(errors),
        "by_type": {
            t: sum(1 for i in errors if types[i] == t)
            for t in ("inversion", "vers neutral", "depuis neutral")
        },
        "inversions_by_direction": by_dir,
        "inversion_share": round(len(inv) / len(errors), 4) if errors else None,
        "inversion_share_wilson95": wilson(len(inv), len(errors)),
        "descriptive_only": len(errors) < MIN_ERRORS,
        "error_ids": {i: types[i] for i in errors},
    }


def main() -> None:
    pairs = {p["pair_id"]: p for p in load_pairs(TEST_FILE)}
    if len(pairs) != 56:
        raise SystemExit(f"{len(pairs)} paires de test au lieu de 56")
    ids = sorted(pairs)
    gold = [pairs[i]["label"] for i in ids]
    preds = {}
    for name, fname in MODELS.items():
        rows = {r["pair_id"]: r for r in load_pairs(PRED_DIR / fname)}
        if set(rows) != set(ids):
            raise SystemExit(f"{fname} : pair_id différents du test")
        if any(rows[i]["label"] != pairs[i]["label"] for i in ids):
            raise SystemExit(f"{fname} : label de référence différent du test")
        preds[name] = [rows[i]["pred"] for i in ids]

    res = {name: polarity(gold, p, ids) for name, p in preds.items()}
    a, b = preds["principal_seed42"], preds["zero-shot-fp32"]
    differ = {
        i: {
            "principal": error_type(g, x) or "juste",
            "zero-shot": error_type(g, y) or "juste",
        }
        for i, g, x, y in zip(ids, gold, a, b, strict=True)
        if x != y
    }
    out = {
        "exp_id": EXP_ID,
        "lot": "C",
        "task": "nli",
        "split": "test",
        "corpus_version": "v3",
        "date": date.today().isoformat(),
        "source_predictions": "EXP-C-011 (mesure unique du 2026-11-14), sans nouvelle inférence",
        "min_errors_interpretation": MIN_ERRORS,
        "models": res,
        "principal_vs_zero_shot_differences": differ,
    }
    path = (
        ROOT / "evaluation" / "results" / f"lot-c_nli-gold_polarite_test_{date.today():%Y%m%d}.json"
    )
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for name, r in res.items():
        print(f"\n== {name} ==  ({r['errors']} erreurs sur {r['n']})")
        print("  confusion (ligne = référence) :", " ".join(LABELS))
        for g in LABELS:
            print(f"    {g:9s}", [r["confusion"][g][p] for p in LABELS])
        share = r["inversion_share"]
        print(
            f"  par type : {r['by_type']} ; inversions {r['inversions_by_direction']} ; part "
            + (f"{share:.3f} Wilson {r['inversion_share_wilson95']}" if share is not None else "-")
            + (" (descriptif : < 20 erreurs)" if r["descriptive_only"] else "")
        )
    print("\n== principal contre zero-shot (paires où ils diffèrent) ==")
    for i, d in differ.items():
        print(f"  {i}: principal {d['principal']} | zero-shot {d['zero-shot']}")
    print(f"\n-> {path}")


if __name__ == "__main__":
    main()
