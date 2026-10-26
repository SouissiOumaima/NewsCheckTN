"""Lot C — Model 2 : évaluation du NLI sur une partie du corpus (val ou test).

Utilise exactement `predict_stances` (le même code que l'API et le Lot D), donc le moteur choisi
par NLI_BACKEND / NLI_MODEL. Mesures : accuracy, macro-F1, précision / rappel / F1 par classe,
matrice de confusion ; puis les mêmes par langue de l'affirmation et pour les articles du test du
Lot D. Écrit :
  - evaluation/results/lot-c_nli_<modèle>_<partie>_<AAAAMMJJ>.json  (format commun, sans texte)
  - data/interim/lot_c/nli/predictions_<version>_<partie>_<modèle>.jsonl  (privé)

    python -m models.nli.evaluate --version v3 --split test --exp-id EXP-C-010
"""

from __future__ import annotations

import argparse
import json
import random
import re
import time
from datetime import date

from common.schemas import Claim, Evidence, Lang
from evaluation.metrics import precision_recall_f1
from models.nli import stance as nli
from models.nli.data import LABELS, LOT_D_TEST_ARTICLES, OUT_DIR, ROOT, load_pairs

RESULTS_DIR = ROOT / "evaluation" / "results"


def metrics(gold: list[str], pred: list[str]) -> dict:
    per_class = {lab: precision_recall_f1(gold, pred, lab) for lab in LABELS}
    return {
        "n": len(gold),
        "accuracy": sum(g == p for g, p in zip(gold, pred, strict=True)) / len(gold)
        if gold
        else 0.0,
        # macro-F1 sur les 3 classes fixes (une classe absente compte 0, elle n'est pas ignorée)
        "macro_f1": sum(c["f1"] for c in per_class.values()) / len(LABELS),
        "per_class": per_class,
        "confusion": {
            g: {
                p: sum(1 for a, b in zip(gold, pred, strict=True) if (a, b) == (g, p))
                for p in LABELS
            }
            for g in LABELS
        },
    }


def bootstrap_macro_f1(
    gold: list[str], pred: list[str], n: int = 1000, seed: int = 20261026
) -> list[float]:
    """Intervalle de confiance à 95 % de la macro-F1 (rééchantillonnage des paires)."""
    rng, idx, scores = random.Random(seed), range(len(gold)), []
    for _ in range(n):
        s = [rng.choice(idx) for _ in idx]
        scores.append(metrics([gold[i] for i in s], [pred[i] for i in s])["macro_f1"])
    scores.sort()
    return [round(scores[int(0.025 * n)], 4), round(scores[int(0.975 * n) - 1], 4)]


def _lang(code: str | None) -> Lang:
    try:
        return Lang(code)
    except ValueError:
        return Lang.UNKNOWN


def predict(pairs: list[dict]) -> list[tuple[str, float]]:
    out = []
    for p in pairs:
        claim = Claim(text=p["claim"], lang=_lang(p.get("claim_lang")))
        ev = Evidence(doc_id=p.get("evidence_id", ""), text=p["evidence"], source="nli-corpus")
        res = nli.predict_stances(claim, [ev])[0]
        out.append((res.stance.value, res.confidence))
    return out


def evaluate(pairs: list[dict]) -> tuple[dict, list[tuple[str, float]]]:
    preds = predict(pairs)
    gold, pred = [p["label"] for p in pairs], [s for s, _ in preds]
    res = metrics(gold, pred)
    res["macro_f1_ci95"] = bootstrap_macro_f1(gold, pred) if pairs else [0.0, 0.0]
    for key, name in (("claim_lang", "by_lang"),):
        groups: dict[str, list[int]] = {}
        for i, p in enumerate(pairs):
            groups.setdefault(p.get(key) or "?", []).append(i)
        res[name] = {
            g: metrics([gold[i] for i in ix], [pred[i] for i in ix]) for g, ix in groups.items()
        }
    lot_d = [i for i, p in enumerate(pairs) if p.get("article_id") in LOT_D_TEST_ARTICLES]
    if lot_d:
        res["lot_d_articles"] = metrics([gold[i] for i in lot_d], [pred[i] for i in lot_d])
    return res, preds


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", required=True, help="version du corpus préparé (ex. v3)")
    ap.add_argument("--split", default="test", choices=["val", "test"])
    ap.add_argument("--exp-id", default="EXP-C-???")
    args = ap.parse_args()

    pairs = load_pairs(OUT_DIR / f"nli_{args.version}_{args.split}.jsonl")
    start = time.time()
    res, preds = evaluate(pairs)
    info = nli.backend_info()
    if info["status"] != "loaded":
        raise SystemExit(f"Le modèle NLI n'est pas chargé ({info}) : résultats non significatifs.")
    model_tag = re.sub(r"[^a-z0-9.-]+", "-", info["model"].split("/")[-1].lower())

    print(
        f"{info['backend']} · {info['model']} · {args.split} "
        f"({res['n']} paires, {time.time() - start:.0f} s)"
    )
    print(
        f"accuracy {res['accuracy']:.3f}   macro-F1 {res['macro_f1']:.3f}  "
        f"IC95 {res['macro_f1_ci95']}"
    )
    for lab, m in res["per_class"].items():
        print(f"  {lab:9} P {m['precision']:.2f}  R {m['recall']:.2f}  F1 {m['f1']:.2f}")
    print("  confusion (ligne = vrai label) :", json.dumps(res["confusion"]))
    for g, m in res["by_lang"].items():
        print(f"  langue {g:3} n={m['n']:3}  macro-F1 {m['macro_f1']:.3f}")
    if "lot_d_articles" in res:
        m = res["lot_d_articles"]
        print(f"  articles du test du Lot D n={m['n']}  macro-F1 {m['macro_f1']:.3f}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"lot-c_nli_{model_tag}_{args.split}_{date.today():%Y%m%d}.json"
    out.write_text(
        json.dumps(
            {
                "exp_id": args.exp_id,
                "lot": "C",
                "task": "nli",
                "model": info["model"],
                "backend": info["backend"],
                "split": args.split,
                "corpus_version": args.version,
                "date": f"{date.today():%Y-%m-%d}",
                "metrics": res,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    with open(
        OUT_DIR / f"predictions_{args.version}_{args.split}_{model_tag}.jsonl",
        "w",
        encoding="utf-8",
    ) as f:
        for p, (s, c) in zip(pairs, preds, strict=True):
            f.write(
                json.dumps(
                    {"pair_id": p["pair_id"], "label": p["label"], "pred": s, "confidence": c},
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"-> {out}")


if __name__ == "__main__":
    main()
