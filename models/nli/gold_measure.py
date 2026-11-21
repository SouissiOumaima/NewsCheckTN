"""Lot C — Model 2, palier Gold : mesure unique d'EXP-C-012 (tunisien) ou d'EXP-C-013 (paraphrases).

PRÉPARÉ, PAS ENCORE LANCÉ. Mesure, une seule fois par expérience, les affirmations réécrites du
fichier figé, avec exactement `predict_stances` (même code que l'API) pour trois moteurs : le
zero-shot float32, le modèle affiné Silver (graine 42) et les règles Bronze. Sur les affirmations
d'origine, aucune nouvelle inférence : on relit les prédictions de la mesure unique d'EXP-C-011.

Refus (aucun modèle n'est lancé) :
  - SHA-256 du fichier figé non noté dans EXPERIMENTS (à reporter d'experiments.md au gel) ou
    différent du fichier ;
  - fichier figé qui n'a pas exactement les 56 paires du test v3, avec la même preuve et le même
    label (seule l'affirmation peut changer) ;
  - réécriture non vérifiée (`verificateur` vide), sauf avec --exploratoire : le résultat est
    alors marqué exploratoire, et la mesure unique est consommée quand même ;
  - mesure déjà faite (marqueur MESURE_FAITE_<exp>.json, écrit avant la première inférence).

Paires gardées : texte non vide, `statut` ≠ « ecarte », et, si le vérificateur est rempli,
`verif_sens_identique` = `verif_label_tient` = « oui ». Moins de 40 paires gardées pour une
variante : résultat exploratoire (règle des deux protocoles).

    python -X utf8 -m models.nli.gold_measure --exp tn --dry-run           # vérifications seules
    python -X utf8 -m models.nli.gold_measure --exp paraphrases            # la mesure (une fois)

Écrit evaluation/results/lot-c_nli-gold_<exp>_test_<AAAAMMJJ>.json (chiffres et identifiants,
aucun texte) et les prédictions privées dans data/interim/lot_c/nli/gold/.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import time
from collections.abc import Callable
from datetime import date

from models.nli.compare import paired_bootstrap
from models.nli.data import OUT_DIR, ROOT, load_pairs
from models.nli.evaluate import bootstrap_macro_f1, metrics

TEST_FILE = OUT_DIR / "nli_v3_test.jsonl"
PRED_DIR = OUT_DIR / "silver_test"
GOLD_DIR = OUT_DIR / "gold"
RESULTS = ROOT / "evaluation" / "results"
N_TEST, MIN_KEPT = 56, 40

# sha256 : None tant que le fichier n'est pas figé ; à remplir au gel, avec la valeur notée
# AVANT la mesure dans l'entrée d'experiments.md.
EXPERIMENTS = {
    "tn": {
        "exp_id": "EXP-C-012",
        "file": "reecritures_tn_v1_gele.csv",
        "sha256": None,
        "variants": {"tn_arabe": "claim_tn_arabe", "arabizi": "claim_arabizi"},
        "claim_lang": "tn",
        "group_by": "evidence_lang",  # affirmation tunisienne / preuve fr ou ar
        "expected_tag": {"tn_arabe": ("tn", "arabic"), "arabizi": ("tn", "arabizi")},
    },
    "paraphrases": {
        "exp_id": "EXP-C-013",
        "file": "paraphrases_v1_gele.csv",
        "sha256": None,
        "variants": {"paraphrase_1": "claim_paraphrase_1", "paraphrase_2": "claim_paraphrase_2"},
        "claim_lang": None,  # langue d'origine gardée
        "group_by": "claim_lang",
        "expected_tag": {},
    },
}
# Modèle → (moteur NLI_BACKEND, prédictions déjà sauvegardées sur les affirmations d'origine)
MODELS = {
    "zero-shot-fp32": ("zero-shot", "predictions_v3_test_zero-shot-fp32.jsonl"),
    "principal_seed42": ("fine-tuned", "predictions_v3_test_principal_seed42.jsonl"),
    "bronze": ("bronze", "predictions_v3_test_bronze.jsonl"),
}

Predictor = Callable[[list[dict]], list[str]]


def sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def marker(exp: str):
    return GOLD_DIR / f"MESURE_FAITE_{exp}.json"


def read_frozen(exp: str) -> list[dict]:
    with open(GOLD_DIR / EXPERIMENTS[exp]["file"], encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def unverified(rows: list[dict], exp: str) -> int:
    """Lignes avec au moins une réécriture non vide et un vérificateur vide."""
    cols = EXPERIMENTS[exp]["variants"].values()
    return sum(
        1
        for r in rows
        if any((r.get(c) or "").strip() for c in cols) and not (r.get("verificateur") or "").strip()
    )


def checks(exp: str, exploratoire: bool) -> list[str]:
    """Vérifications avant mesure ; aucun modèle n'est lancé."""
    cfg, errors = EXPERIMENTS[exp], []
    path = GOLD_DIR / cfg["file"]
    if marker(exp).exists():
        errors.append(f"mesure déjà faite ({marker(exp).name}) : refusée")
    if not path.exists():
        return errors + [f"{cfg['file']} absent (fichier pas encore figé)"]
    if not cfg["sha256"]:
        errors.append(f"SHA-256 de {cfg['file']} non noté (gel à faire dans experiments.md)")
    elif sha256(path) != cfg["sha256"]:
        errors.append(f"{cfg['file']} : SHA-256 différent de la valeur gelée")
    rows = read_frozen(exp)
    test = {p["pair_id"]: p for p in load_pairs(TEST_FILE)}
    if len(test) != N_TEST or sorted(r["pair_id"] for r in rows) != sorted(test):
        errors.append(f"{cfg['file']} : pas exactement les {N_TEST} paires du test v3")
    else:
        # intégrité seulement : seule l'affirmation peut changer (rien n'est choisi d'après ça)
        if any(
            r["label"] != test[r["pair_id"]]["label"]
            or r["evidence"] != test[r["pair_id"]]["evidence"]
            for r in rows
        ):
            errors.append(f"{cfg['file']} : preuve ou label différent du test v3")
    n = unverified(rows, exp)
    if n and not exploratoire:
        errors.append(
            f"{n} lignes sans vérificateur : refusé (relecture humaine manquante) ; "
            "--exploratoire pour mesurer quand même, résultat marqué exploratoire"
        )
    return errors


def kept(rows: list[dict], col: str) -> tuple[list[dict], dict]:
    """Paires gardées pour une variante, et comptes des écartées et des non vérifiées."""
    out, counts = [], {"vides": 0, "ecartees": 0, "non_verifiees": 0}
    for r in rows:
        if not (r.get(col) or "").strip():
            counts["vides"] += 1
            continue
        if (r.get("statut") or "").strip().lower().startswith("ecart"):
            counts["ecartees"] += 1
            continue
        if (r.get("verificateur") or "").strip():
            if not (
                r.get("verif_sens_identique", "").strip().lower() == "oui"
                and r.get("verif_label_tient", "").strip().lower() == "oui"
            ):
                counts["ecartees"] += 1
                continue
        else:
            counts["non_verifiees"] += 1
        out.append(r)
    return out, counts


def _scores(gold: list[str], pred: list[str]) -> dict:
    m = metrics(gold, pred)
    return {
        "macro_f1": round(m["macro_f1"], 4),
        "accuracy": round(m["accuracy"], 4),
        "macro_f1_ci95": bootstrap_macro_f1(gold, pred),
    }


def measure(
    exp: str,
    rows: list[dict],
    test: dict[str, dict],
    original: dict[str, dict[str, str]],
    predictors: dict[str, Predictor],
    exploratoire: bool,
    tagger: Callable[[str], tuple[str, str]] | None = None,
) -> tuple[dict, dict]:
    """Chiffres par variante et par modèle, et prédictions (pour les fichiers privés)."""
    cfg = EXPERIMENTS[exp]
    results, preds = {}, {}
    for variant, col in cfg["variants"].items():
        keep, counts = kept(rows, col)
        if not keep:
            results[variant] = {"n_kept": 0, **counts, "measured": False}
            continue
        ids = [r["pair_id"] for r in keep]
        gold = [test[i]["label"] for i in ids]
        pairs = [
            dict(test[i], claim=r[col], claim_lang=cfg["claim_lang"] or test[i]["claim_lang"])
            for i, r in zip(ids, keep, strict=True)
        ]
        res = {
            "n_kept": len(ids),
            **counts,
            "measured": True,
            "exploratoire": exploratoire or counts["non_verifiees"] > 0 or len(ids) < MIN_KEPT,
            "models": {},
        }
        preds[variant] = {}
        for name, predict in predictors.items():
            var = predict(pairs)
            orig = [original[name][i] for i in ids]
            preds[variant][name] = dict(zip(ids, var, strict=True))
            right = [k for k, (g, o) in enumerate(zip(gold, orig, strict=True)) if g == o]
            groups = {}
            for g in sorted({test[i][cfg["group_by"]] for i in ids}):
                ix = [k for k, i in enumerate(ids) if test[i][cfg["group_by"]] == g]
                groups[g] = {
                    "n": len(ix),
                    "variant": _scores([gold[k] for k in ix], [var[k] for k in ix]),
                    "original": _scores([gold[k] for k in ix], [orig[k] for k in ix]),
                }
            boot = paired_bootstrap(gold, orig, var)  # différence variante − original
            res["models"][name] = {
                "variant": _scores(gold, var),
                "original": _scores(gold, orig),
                "paired_diff_macro_f1": round(boot["diff"], 4),
                "paired_diff_ci95": [round(x, 4) for x in boot["ci95"]],
                "paired_p_value": boot["p_value"],
                "change_rate": round(
                    sum(o != v for o, v in zip(orig, var, strict=True)) / len(ids), 4
                ),
                "change_rate_on_correct": round(
                    sum(orig[k] != var[k] for k in right) / len(right), 4
                )
                if right
                else None,
                f"by_{cfg['group_by']}": groups,
            }
        if tagger and variant in cfg["expected_tag"]:
            want = cfg["expected_tag"][variant]
            tags = [tagger(r[col]) for r in keep]
            res["tag_lang"] = {
                "expected": list(want),
                "share_lang_ok": round(sum(t[0] == want[0] for t in tags) / len(tags), 4),
                "share_lang_and_script_ok": round(sum(t == want for t in tags) / len(tags), 4),
            }
        results[variant] = res
    # deux paraphrases : accord entre leurs prédictions, par modèle, sur les paires communes
    if exp == "paraphrases" and {"paraphrase_1", "paraphrase_2"} <= set(preds):
        p1, p2 = preds["paraphrase_1"], preds["paraphrase_2"]
        results["agreement_paraphrases_1_2"] = {
            name: {
                "n": len(common := sorted(set(p1[name]) & set(p2[name]))),
                "agreement": round(sum(p1[name][i] == p2[name][i] for i in common) / len(common), 4)
                if common
                else None,
            }
            for name in predictors
        }
    return results, preds


def backend_predictor(backend: str) -> Predictor:
    """Prédictions par `predict_stances` avec le moteur demandé (chargé une seule fois)."""
    from models.nli import evaluate as ev
    from models.nli import stance

    loaded = {"done": False}

    def predict(pairs: list[dict]) -> list[str]:
        if not loaded["done"]:
            os.environ["NLI_BACKEND"] = backend
            os.environ.pop("NLI_MODEL", None)
            stance.set_classifier(None)
            loaded["done"] = True
        out = [s for s, _ in ev.predict(pairs)]
        info = stance.backend_info()
        if info["status"] != "loaded" or info["backend"] != backend:
            raise SystemExit(f"moteur {backend} non chargé : {info}")
        return out

    return predict


def main(argv: list[str] | None = None, predictors: dict[str, Predictor] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--exp", required=True, choices=sorted(EXPERIMENTS))
    ap.add_argument("--dry-run", action="store_true", help="vérifications seulement")
    ap.add_argument(
        "--exploratoire",
        action="store_true",
        help="accepte des lignes sans vérificateur ; résultat marqué exploratoire",
    )
    args = ap.parse_args(argv)
    cfg = EXPERIMENTS[args.exp]

    errors = checks(args.exp, args.exploratoire)
    print(f"{cfg['exp_id']} — vérifications :", "OK" if not errors else "ÉCHEC")
    for e in errors:
        print("  -", e)
    if errors:
        raise SystemExit(1)
    rows = read_frozen(args.exp)
    for variant, col in cfg["variants"].items():
        k, counts = kept(rows, col)
        print(f"  {variant:13} gardées {len(k):2d}  {counts}")
    if args.dry_run:
        print("--dry-run : rien n'a été mesuré, aucun marqueur écrit.")
        return

    # le marqueur est écrit AVANT la première inférence : une mesure interrompue compte aussi
    marker(args.exp).write_text(
        json.dumps(
            {"debut": time.strftime("%Y-%m-%d %H:%M:%S"), "exploratoire": args.exploratoire}
        ),
        encoding="utf-8",
    )
    test = {p["pair_id"]: p for p in load_pairs(TEST_FILE)}
    original = {
        name: {r["pair_id"]: r["pred"] for r in load_pairs(PRED_DIR / fname)}
        for name, (_, fname) in MODELS.items()
    }
    if predictors is None:
        predictors = {name: backend_predictor(b) for name, (b, _) in MODELS.items()}
    tagger = None
    if cfg["expected_tag"]:
        from normalization.tag_lang import tag_text

        tagger = tag_text
    results, preds = measure(args.exp, rows, test, original, predictors, args.exploratoire, tagger)

    for variant, by_model in preds.items():
        for name, p in by_model.items():
            path = GOLD_DIR / f"predictions_{args.exp}_{variant}_{name}.jsonl"
            with open(path, "w", encoding="utf-8") as f:
                for i, s in p.items():
                    f.write(json.dumps({"pair_id": i, "label": test[i]["label"], "pred": s}) + "\n")
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"lot-c_nli-gold_{args.exp}_test_{date.today():%Y%m%d}.json"
    out.write_text(
        json.dumps(
            {
                "exp_id": cfg["exp_id"],
                "lot": "C",
                "task": "nli",
                "split": "test",
                "corpus_version": "v3",
                "date": date.today().isoformat(),
                "frozen_file": cfg["file"],
                "frozen_sha256": cfg["sha256"],
                "exploratoire_demande": args.exploratoire,
                "original_predictions": "EXP-C-011 (mesure unique du 2026-11-14)",
                "results": results,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    marker(args.exp).write_text(
        json.dumps(
            {
                "fin": time.strftime("%Y-%m-%d %H:%M:%S"),
                "exploratoire": args.exploratoire,
                "resultats": str(out),
            }
        ),
        encoding="utf-8",
    )
    for variant, res in results.items():
        if not isinstance(res, dict) or not res.get("measured"):
            continue
        flag = " (exploratoire)" if res["exploratoire"] else ""
        print(f"== {variant} : {res['n_kept']} paires gardées{flag}")
        for name, m in res["models"].items():
            print(
                f"  {name:17} macro-F1 {m['variant']['macro_f1']:.3f} (original"
                f" {m['original']['macro_f1']:.3f}) diff {m['paired_diff_macro_f1']:+.3f}"
                f" {m['paired_diff_ci95']}  changements {m['change_rate']:.3f}"
            )
    print(f"-> {out}")


if __name__ == "__main__":
    main()
