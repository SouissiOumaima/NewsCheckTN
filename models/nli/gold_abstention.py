"""Lot C — Model 2, palier Gold (EXP-C-015) : choix du seuil d'abstention, sans le test.

Calcule les probabilités du NLI avec le même chargement et la même conversion que l'API
(`stance._load_zero_shot`, `stance._to_result`, float32), puis applique la règle fixée avant calcul
dans experiments.md : sous le seuil τ, une réponse « supports » ou « refutes » devient « neutral ».

  - modèle affiné (principal, graine 42) : val v3 seulement (il a appris sur le train) ;
  - zero-shot float32 : train + val v3 (comparaison seulement).

Le test v3 n'est jamais lu. Contrôle : sans seuil, le modèle affiné doit redonner exactement les
prédictions de val de son journal (`kept_val_predictions`).

    python -X utf8 -m models.nli.gold_abstention

Écrit les probabilités dans data/interim/lot_c/nli/gold/ (privé) et les chiffres dans
evaluation/results/lot-c_nli-gold_abstention_val_<AAAAMMJJ>.json (non versionné).
"""

from __future__ import annotations

import json
from datetime import date

from common.schemas import Evidence
from models.nli import stance
from models.nli.data import LABELS, OUT_DIR, ROOT, load_pairs
from models.nli.evaluate import metrics

EXP_ID = "EXP-C-015"
GOLD_DIR = OUT_DIR / "gold"
PRINCIPAL = ROOT / "models" / "checkpoints" / "nli_mdeberta-ft_v3_lr1e-05_e6_seed42"
GRID = [0.0, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
DECISIVE = ("supports", "refutes")


def predict(model_name: str, pairs: list[dict]) -> list[dict]:
    """Classe et confiance exactement comme `predict_stances` (prémisse = preuve)."""
    classify = stance._load_zero_shot(model_name)
    probs = classify([(p["evidence"], p["claim"]) for p in pairs])
    rows = []
    for p, pr in zip(pairs, probs, strict=True):
        res = stance._to_result(Evidence(doc_id=p["pair_id"], text="", source=""), pr)
        rows.append(
            {
                "pair_id": p["pair_id"],
                "label": p["label"],
                "pred": res.stance.value,
                "confidence": res.confidence,
                "probs": {k: round(v, 6) for k, v in pr.items()},
            }
        )
    return rows


def apply(rows: list[dict], tau: float) -> list[str]:
    return [
        "neutral" if r["pred"] in DECISIVE and r["confidence"] < tau else r["pred"] for r in rows
    ]


def sweep(rows: list[dict]) -> list[dict]:
    gold = [r["label"] for r in rows]
    out = []
    for tau in GRID:
        pred = apply(rows, tau)
        m = metrics(gold, pred)
        decisive = [(g, p) for g, p in zip(gold, pred, strict=True) if p in DECISIVE]
        changed = [r for r, p in zip(rows, pred, strict=True) if p != r["pred"]]
        out.append(
            {
                "tau": tau,
                "macro_f1": round(m["macro_f1"], 4),
                "accuracy": round(m["accuracy"], 4),
                "f1": {lab: round(m["per_class"][lab]["f1"], 4) for lab in LABELS},
                "coverage": round(len(decisive) / len(rows), 4),
                "decisive_precision": round(sum(g == p for g, p in decisive) / len(decisive), 4)
                if decisive
                else None,
                "changed_to_neutral": len(changed),
                "changed_were_correct": sum(r["pred"] == r["label"] for r in changed),
            }
        )
    return out


def choose(results: list[dict], margin: float) -> dict:
    """Règle fixée avant calcul : meilleure macro-F1 ; dans la marge, le plus petit τ."""
    best = max(r["macro_f1"] for r in results)
    equivalent = [r for r in results if r["macro_f1"] >= best - margin - 1e-12]
    chosen = min(equivalent, key=lambda r: r["tau"])
    return {
        "best_macro_f1": best,
        "best_tau": [r["tau"] for r in results if r["macro_f1"] == best],
        "margin": margin,
        "equivalent_tau": [r["tau"] for r in equivalent],
        "chosen_tau": chosen["tau"],
        "chosen_macro_f1": chosen["macro_f1"],
        "no_abstention_in_margin": chosen["tau"] == 0.0,
    }


def show(name: str, results: list[dict], choice: dict) -> None:
    print(f"\n== {name} ==")
    print("   τ    macro-F1  acc    couverture  préc.(s/r)  →neutral (justes avant)")
    for r in results:
        mark = " <- choisi" if r["tau"] == choice["chosen_tau"] else ""
        prec = "-" if r["decisive_precision"] is None else f"{r['decisive_precision']:.3f}"
        print(
            f"  {r['tau']:.2f}  {r['macro_f1']:.3f}     {r['accuracy']:.3f}  {r['coverage']:.3f}"
            f"       {prec:>5}       {r['changed_to_neutral']:2d} ({r['changed_were_correct']})"
            f"{mark}"
        )
    print(
        f"  meilleure {choice['best_macro_f1']:.3f} (τ = {choice['best_tau']}) ; marge"
        f" {choice['margin']} ; équivalents {choice['equivalent_tau']} ;"
        f" choisi τ = {choice['chosen_tau']}"
    )


def main() -> None:
    train = load_pairs(OUT_DIR / "nli_v3_train.jsonl")
    val = load_pairs(OUT_DIR / "nli_v3_val.jsonl")
    if (len(train), len(val)) != (174, 33):
        raise SystemExit(f"train {len(train)} / val {len(val)} au lieu de 174 / 33")
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    # modèle affiné : val seulement ; contrôle contre son journal
    principal = predict(str(PRINCIPAL), val)
    log = json.loads((PRINCIPAL / "train_log.json").read_text(encoding="utf-8"))
    diff = sum(r["pred"] != log["kept_val_predictions"][r["pair_id"]] for r in principal)
    if diff:
        raise SystemExit(f"contrôle échoué : {diff} prédictions de val différentes du journal")

    # zero-shot : train + val (comparaison)
    zero = predict(stance.DEFAULT_MODEL, train + val)

    for fname, rows in {
        "probas_val_principal_seed42.jsonl": principal,
        "probas_trainval_zero-shot-fp32.jsonl": zero,
    }.items():
        with open(GOLD_DIR / fname, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    res_p, res_z = sweep(principal), sweep(zero)
    ch_p, ch_z = choose(res_p, 0.03), choose(res_z, 0.01)
    zero_val = [r for r in zero if r["pair_id"] in {p["pair_id"] for p in val}]
    out = {
        "exp_id": EXP_ID,
        "lot": "C",
        "task": "nli-abstention",
        "corpus_version": "v3",
        "date": date.today().isoformat(),
        "test_used": False,
        "grid": GRID,
        "controls": {
            "principal_val_predictions_equal_log": True,
            "principal_val_macro_f1_tau0": res_p[0]["macro_f1"],
            "principal_log_kept_val_macro_f1": round(log["kept_val_macro_f1"], 4),
            "zero_shot_val_only_macro_f1_tau0": round(
                metrics([r["label"] for r in zero_val], [r["pred"] for r in zero_val])["macro_f1"],
                4,
            ),
        },
        "principal_seed42": {"data": "val v3 (33)", "sweep": res_p, "choice": ch_p},
        "zero_shot_fp32": {"data": "train + val v3 (207)", "sweep": res_z, "choice": ch_z},
    }
    name = f"lot-c_nli-gold_abstention_val_{date.today():%Y%m%d}.json"
    path = ROOT / "evaluation" / "results" / name
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("contrôle : prédictions de val du modèle affiné = journal (0 différence sur 33)")
    print(f"contrôles : {out['controls']}")
    show("modèle affiné (graine 42), val v3, n = 33", res_p, ch_p)
    show("zero-shot float32, train + val v3, n = 207 (comparaison)", res_z, ch_z)
    print(f"\n-> {path}")


if __name__ == "__main__":
    main()
