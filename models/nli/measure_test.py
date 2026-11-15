"""Lot C — Model 2, palier Silver (EXP-C-011) : mesure unique du test v3.

Mesure, une seule fois et dans cet ordre, avec exactement `predict_stances` (même code que l'API
et le Lot D, chargement en float32) :
  - le zero-shot mDeBERTa-v3 xnli (float32) ;
  - les 3 modèles principaux affinés (lr 1e-5, époque 1 ; graines 42, 123, 2026) ;
  - les 3 modèles d'ablation mdeberta-v3-base (lr 5e-5, époque 5 ; mêmes graines) ;
puis reconstitue les prédictions déjà mesurées des règles Bronze (EXP-C-009 : CSV des erreurs,
les autres paires étant justes) et de la classe majoritaire du train. Calcule macro-F1 moyenne ±
écart-type, par langue et sur les articles du test du Lot D, et le bootstrap apparié de chaque
modèle principal contre Bronze, classe majoritaire et zero-shot float32.

Écrit :
  - evaluation/results/lot-c_nli-silver_test_<AAAAMMJJ>.json  (chiffres seulement, sans texte)
  - data/interim/lot_c/nli/silver_test/predictions_v3_test_<modèle>.jsonl  (privé)

    python -m models.nli.measure_test --dry-run    # vérifications, sans lire les labels du test
    python -m models.nli.measure_test              # la mesure (refusée si déjà faite)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import statistics
import time
from collections import Counter
from datetime import date

from models.nli import evaluate as ev
from models.nli import stance
from models.nli.compare import paired_bootstrap
from models.nli.data import OUT_DIR, ROOT, load_pairs

VERSION = "v3"
EXP_ID = "EXP-C-011"
SPLIT_FILE = ROOT / "data" / "splits" / "nli_v3_by_article_seed42.json"
SPLIT_SHA256 = "59582eb759df4cd9e15f7a17d1df7e85dfae411717a111d52d536fc1c6c3552c"  # gelé le 26/10
TEST_FILE = OUT_DIR / "nli_v3_test.jsonl"
BRONZE_ERRORS = OUT_DIR / "erreurs_bronze_v3_test.csv"
BRONZE_MACRO_F1 = 0.471  # EXP-C-009, pour contrôler la reconstitution
CK = ROOT / "models" / "checkpoints"
SEEDS = (42, 123, 2026)
MODELS = (
    {"zero-shot-fp32": (None, None)}
    | {f"principal_seed{s}": (CK / f"nli_mdeberta-ft_v3_lr1e-05_e6_seed{s}", 1) for s in SEEDS}
    | {
        f"ablation_seed{s}": (CK / f"nli_mdeberta-v3-base-ft_v3_lr5e-05_e6_seed{s}", 5)
        for s in SEEDS
    }
)
PRED_DIR = OUT_DIR / "silver_test"
RESULTS = ROOT / "evaluation" / "results"
DONE = PRED_DIR / "MESURE_FAITE.json"


def sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checks() -> list[str]:
    """Vérifications avant mesure ; ne lit que les pair_id du test, jamais les labels."""
    errors = []
    if sha256(SPLIT_FILE) != SPLIT_SHA256:
        errors.append(f"{SPLIT_FILE.name} : SHA-256 différent du gel")
    split_test = json.loads(SPLIT_FILE.read_text(encoding="utf-8"))["test"]
    with open(TEST_FILE, encoding="utf-8") as f:
        ids = [json.loads(line)["pair_id"] for line in f if line.strip()]
    if sorted(ids) != sorted(split_test):
        errors.append("nli_v3_test.jsonl : pair_id différents du découpage gelé")
    for name, (path, k) in MODELS.items():
        if path is None:
            continue
        log = path / "train_log.json"
        if not (path / "model.safetensors").exists() or not log.exists():
            errors.append(f"{name} : poids ou journal absents ({path})")
            continue
        info = json.loads(log.read_text(encoding="utf-8"))
        if not (info["model_saved"] and info["selection"] == "époque fixée"):
            errors.append(f"{name} : journal qui n'est pas celui de la relance finale")
        elif info["kept_epoch"] != k:
            errors.append(f"{name} : époque gardée {info['kept_epoch']} au lieu de {k}")
    if not BRONZE_ERRORS.exists():
        errors.append(f"{BRONZE_ERRORS.name} absent")
    if DONE.exists():
        errors.append(f"mesure déjà faite ({DONE}) : refusée")
    return errors


def run_model(path, pairs: list[dict]) -> tuple[dict, list[str]]:
    os.environ["NLI_BACKEND"] = "zero-shot"
    if path is None:
        os.environ.pop("NLI_MODEL", None)
    else:
        os.environ["NLI_MODEL"] = str(path)
    stance.set_classifier(None)  # recharge le modèle demandé
    res, preds = ev.evaluate(pairs)
    info = stance.backend_info()
    if info["status"] != "loaded":
        raise SystemExit(f"modèle non chargé : {info}")
    return res, [s for s, _ in preds]


def save_preds(name: str, pairs: list[dict], pred: list[str]) -> None:
    with open(PRED_DIR / f"predictions_v3_test_{name}.jsonl", "w", encoding="utf-8") as f:
        for p, s in zip(pairs, pred, strict=True):
            row = {"pair_id": p["pair_id"], "label": p["label"], "pred": s}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def mean_sd(values: list[float]) -> dict:
    return {"mean": statistics.mean(values), "sd": statistics.stdev(values), "values": values}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="vérifications seulement")
    args = ap.parse_args()

    errors = checks()
    print("vérifications :", "OK" if not errors else "ÉCHEC")
    for e in errors:
        print("  -", e)
    if errors:
        raise SystemExit(1)
    print(f"  découpage gelé {SPLIT_SHA256[:12]}… ; test.jsonl SHA-256 {sha256(TEST_FILE)}")
    for name, (path, k) in MODELS.items():
        print(
            f"  {name:16} {path.name if path else stance.DEFAULT_MODEL}"
            + (f" (ép. {k})" if k else "")
        )
    if args.dry_run:
        print("--dry-run : rien n'a été mesuré, labels du test non lus.")
        return

    PRED_DIR.mkdir(parents=True, exist_ok=True)
    DONE.write_text(json.dumps({"debut": time.strftime("%Y-%m-%d %H:%M:%S")}), encoding="utf-8")
    pairs = load_pairs(TEST_FILE)
    gold = [p["label"] for p in pairs]
    results, preds = {}, {}
    for name, (path, _) in MODELS.items():
        t = time.time()
        results[name], preds[name] = run_model(path, pairs)
        save_preds(name, pairs, preds[name])
        print(f"{name:16} macro-F1 {results[name]['macro_f1']:.4f}  ({time.time() - t:.0f} s)")

    # baselines déjà mesurées (EXP-C-009) : reconstitution, sans nouvelle mesure
    with open(BRONZE_ERRORS, encoding="utf-8-sig") as f:
        wrong = {r["pair_id"]: r["sortie"] for r in csv.DictReader(f)}
    preds["bronze"] = [wrong.get(p["pair_id"], p["label"]) for p in pairs]
    train = load_pairs(OUT_DIR / f"nli_{VERSION}_train.jsonl")
    majority = Counter(p["label"] for p in train).most_common(1)[0][0]
    preds["majorite"] = [majority] * len(pairs)
    for name in ("bronze", "majorite"):
        results[name] = ev.metrics(gold, preds[name])
        save_preds(name, pairs, preds[name])
    bronze_ok = round(results["bronze"]["macro_f1"], 3) == BRONZE_MACRO_F1
    print(
        f"bronze reconstitué macro-F1 {results['bronze']['macro_f1']:.4f} "
        f"(attendu 0.471 : {bronze_ok})"
    )

    groups = {
        "principal": [f"principal_seed{s}" for s in SEEDS],
        "ablation": [f"ablation_seed{s}" for s in SEEDS],
    }
    summary = {}
    for g, names in groups.items():
        langs = sorted({lang for n in names for lang in results[n]["by_lang"]})
        summary[g] = {
            "macro_f1": mean_sd([results[n]["macro_f1"] for n in names]),
            "accuracy": mean_sd([results[n]["accuracy"] for n in names]),
            "by_lang": {
                lang: mean_sd([results[n]["by_lang"][lang]["macro_f1"] for n in names])
                for lang in langs
            },
            "lot_d_articles": mean_sd([results[n]["lot_d_articles"]["macro_f1"] for n in names]),
        }
    bootstrap = {
        f"{n}_vs_{base}": paired_bootstrap(gold, preds[base], preds[n])
        for n in groups["principal"]
        for base in ("bronze", "majorite", "zero-shot-fp32")
    }

    out = RESULTS / f"lot-c_nli-silver_test_{date.today():%Y%m%d}.json"
    out.write_text(
        json.dumps(
            {
                "exp_id": EXP_ID,
                "lot": "C",
                "task": "nli",
                "split": "test",
                "corpus_version": VERSION,
                "date": f"{date.today():%Y-%m-%d}",
                "split_sha256": SPLIT_SHA256,
                "test_file_sha256": sha256(TEST_FILE),
                "majority_label": majority,
                "bronze_reconstruction_ok": bronze_ok,
                "models": {
                    n: (str(p.name) if p else stance.DEFAULT_MODEL) for n, (p, _) in MODELS.items()
                },
                "metrics": results,
                "summary": summary,
                "paired_bootstrap": bootstrap,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    DONE.write_text(
        json.dumps({"fin": time.strftime("%Y-%m-%d %H:%M:%S"), "resultats": str(out)}),
        encoding="utf-8",
    )
    for g, s in summary.items():
        print(
            f"{g:9} macro-F1 {s['macro_f1']['mean']:.3f} ± {s['macro_f1']['sd']:.3f}  "
            + "  ".join(f"{k} {v['mean']:.3f}±{v['sd']:.3f}" for k, v in s["by_lang"].items())
            + f"  Lot D {s['lot_d_articles']['mean']:.3f}±{s['lot_d_articles']['sd']:.3f}"
        )
    for k, b in bootstrap.items():
        print(
            f"  {k:36} diff {b['diff']:+.3f}  IC95 [{b['ci95'][0]:+.3f} ; {b['ci95'][1]:+.3f}]"
            f"  p = {b['p_value']:.3f}"
        )
    print(f"-> {out}")


if __name__ == "__main__":
    main()
