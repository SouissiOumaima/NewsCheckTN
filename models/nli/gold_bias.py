"""Lot C — Model 2, palier Gold (EXP-C-014) : biais par langue, par source et par sujet.

Aucun modèle n'est relancé : relit les prédictions du test v3 déjà sauvegardées par la mesure
unique d'EXP-C-011 (`data/interim/lot_c/nli/silver_test/`) et les labels de `nli_v3_test.jsonl`,
puis découpe par langue de l'affirmation, par site source, par article et, si le fichier du
Lot A1 est présent, par sujet (catégorie thématique proposée à partir des titres ; lien par
`article_id`). Rien n'est réglé d'après ces chiffres.

    python -X utf8 -m models.nli.gold_bias

Écrit evaluation/results/lot-c_nli-gold_biais_test_<AAAAMMJJ>.json (chiffres et identifiants
d'articles seulement) ; le terminal n'affiche que des chiffres.
"""

from __future__ import annotations

import csv
import json
import random
from collections import Counter
from datetime import date
from urllib.parse import urlparse

from models.nli.data import LABELS, OUT_DIR, ROOT, load_pairs
from models.nli.evaluate import bootstrap_macro_f1, metrics

EXP_ID = "EXP-C-014"
TEST_FILE = OUT_DIR / "nli_v3_test.jsonl"
PRED_DIR = OUT_DIR / "silver_test"
MODELS = {
    "principal_seed42": "predictions_v3_test_principal_seed42.jsonl",
    "zero-shot-fp32": "predictions_v3_test_zero-shot-fp32.jsonl",
    "bronze": "predictions_v3_test_bronze.jsonl",
    "majorite": "predictions_v3_test_majorite.jsonl",
}
SEED, N_BOOT, MIN_N = 20261026, 1000, 10
# Sujets des articles (Lot A1, privé) : catégories proposées à partir des titres
SUBJECT_FILE = OUT_DIR / "nli_v4_articles_sujets_sources_categories.csv"


def norm_article(article: str) -> str:
    """Même normalisation que `models.nli.data.article_id` (« / » final retiré, minuscules)."""
    return article.strip().rstrip("/").lower()


def load_subjects(path=SUBJECT_FILE) -> dict[str, str]:
    """article_id normalisé → catégorie thématique (vide si le fichier est absent)."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {norm_article(r["article_id"]): r["categorie_thematique"] for r in csv.DictReader(f)}


def site(article: str) -> str:
    if article.startswith("tunifact-"):
        return "tunifact.org"
    host = urlparse(article).netloc
    return host.removeprefix("www.") or article


def accuracy(gold: list[str], pred: list[str]) -> float:
    return sum(g == p for g, p in zip(gold, pred, strict=True)) / len(gold)


def boot_acc_ci(gold: list[str], pred: list[str]) -> list[float]:
    rng, idx, scores = random.Random(SEED), range(len(gold)), []
    for _ in range(N_BOOT):
        s = [rng.choice(idx) for _ in idx]
        scores.append(accuracy([gold[i] for i in s], [pred[i] for i in s]))
    scores.sort()
    return [round(scores[int(0.025 * N_BOOT)], 4), round(scores[int(0.975 * N_BOOT) - 1], 4)]


def gap(a: tuple[list, list], b: tuple[list, list]) -> dict:
    """Écart (a − b) d'accuracy et de macro-F1, bootstrap séparé dans chaque groupe."""
    rng = random.Random(SEED)

    def draw(g, p):
        s = [rng.randrange(len(g)) for _ in g]
        return [g[i] for i in s], [p[i] for i in s]

    acc, mf1 = [], []
    for _ in range(N_BOOT):
        (ga, pa), (gb, pb) = draw(*a), draw(*b)
        acc.append(accuracy(ga, pa) - accuracy(gb, pb))
        mf1.append(metrics(ga, pa)["macro_f1"] - metrics(gb, pb)["macro_f1"])

    def ci(v):
        v = sorted(v)
        return [round(v[int(0.025 * N_BOOT)], 4), round(v[int(0.975 * N_BOOT) - 1], 4)]

    return {
        "accuracy": round(accuracy(*a) - accuracy(*b), 4),
        "accuracy_ci95": ci(acc),
        "macro_f1": round(metrics(*a)["macro_f1"] - metrics(*b)["macro_f1"], 4),
        "macro_f1_ci95": ci(mf1),
        "interpretable": len(a[0]) >= MIN_N and len(b[0]) >= MIN_N,
    }


def describe(gold: list[str], pred: list[str]) -> dict:
    m = metrics(gold, pred)
    return {
        "n": len(gold),
        "labels": {lab: gold.count(lab) for lab in LABELS},
        "accuracy": round(m["accuracy"], 4),
        "accuracy_ci95": boot_acc_ci(gold, pred),
        "macro_f1": round(m["macro_f1"], 4),
        "macro_f1_ci95": bootstrap_macro_f1(gold, pred, n=N_BOOT, seed=SEED),
        "interpretable": len(gold) >= MIN_N,
    }


def main() -> None:
    pairs = {p["pair_id"]: p for p in load_pairs(TEST_FILE)}
    if len(pairs) != 56:
        raise SystemExit(f"{len(pairs)} paires de test au lieu de 56")
    preds = {}
    for name, fname in MODELS.items():
        rows = load_pairs(PRED_DIR / fname)
        if {r["pair_id"] for r in rows} != set(pairs):
            raise SystemExit(f"{fname} : pair_id différents du test")
        if any(r["label"] != pairs[r["pair_id"]]["label"] for r in rows):
            raise SystemExit(f"{fname} : label de référence différent du test")
        preds[name] = {r["pair_id"]: r["pred"] for r in rows}

    axes = {
        "langue": lambda p: p["claim_lang"],
        "site": lambda p: site(p["article_id"]),
        "article": lambda p: p["article_id"],
    }
    subjects = load_subjects()
    if subjects:
        missing = {
            p["article_id"] for p in pairs.values() if norm_article(p["article_id"]) not in subjects
        }
        if missing:
            raise SystemExit(f"{len(missing)} articles du test sans sujet dans {SUBJECT_FILE.name}")
        axes["sujet"] = lambda p: subjects[norm_article(p["article_id"])]
    out = {
        "exp_id": EXP_ID,
        "lot": "C",
        "task": "nli",
        "split": "test",
        "corpus_version": "v3",
        "date": date.today().isoformat(),
        "source_predictions": "EXP-C-011 (mesure unique du 2026-11-14), sans nouvelle inférence",
        "bootstrap": {"n": N_BOOT, "seed": SEED},
        "min_n_interpretation": MIN_N,
        "groups": {},
        "group_articles": {},
        "gaps": {},
    }
    if subjects:
        out["subject_source"] = (
            f"{SUBJECT_FILE.name} (Lot A1) : catégories proposées par le Lot A1 à partir des titres"
        )
    for axis, key in axes.items():
        groups = Counter(key(p) for p in pairs.values())
        out["groups"][axis] = {}
        out["group_articles"][axis] = {}
        for g, _ in sorted(groups.items(), key=lambda kv: (-kv[1], kv[0])):
            ids = [i for i, p in pairs.items() if key(p) == g]
            gold = [pairs[i]["label"] for i in ids]
            out["groups"][axis][g] = {
                name: describe(gold, [preds[name][i] for i in ids]) for name in MODELS
            }
            out["group_articles"][axis][g] = len({pairs[i]["article_id"] for i in ids})

    def ids_where(test) -> list[str]:
        return [i for i, p in pairs.items() if test(p)]

    comparisons = {
        f"{axis}: {ga} - {gb}": (
            ids_where(lambda p, a=axis, g=ga: axes[a](p) == g),
            ids_where(lambda p, a=axis, g=gb: axes[a](p) == g),
        )
        for axis, (ga, gb) in {
            "langue": ("fr", "ar"),
            "site": ("tunifact.org", "nawaat.org"),
        }.items()
    }
    # Sujet (fixé avant calcul) : chaque catégorie d'au moins MIN_N paires contre le reste du test
    if "sujet" in axes:
        for g, res in out["groups"]["sujet"].items():
            if next(iter(res.values()))["n"] >= MIN_N:
                comparisons[f"sujet: {g} - reste"] = (
                    ids_where(lambda p, g=g: axes["sujet"](p) == g),
                    ids_where(lambda p, g=g: axes["sujet"](p) != g),
                )
    for label, (ids_a, ids_b) in comparisons.items():
        if not ids_a or not ids_b:
            continue
        out["gaps"][label] = {
            name: gap(
                ([pairs[i]["label"] for i in ids_a], [preds[name][i] for i in ids_a]),
                ([pairs[i]["label"] for i in ids_b], [preds[name][i] for i in ids_b]),
            )
            for name in MODELS
        }

    path = ROOT / "evaluation" / "results" / f"lot-c_nli-gold_biais_test_{date.today():%Y%m%d}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for axis, groups in out["groups"].items():
        print(f"\n== {axis} ==  (acc / macro-F1 ; * = n < {MIN_N}, descriptif seulement)")
        for g, res in groups.items():
            r, z = res["principal_seed42"], res["zero-shot-fp32"]
            flag = "" if r["interpretable"] else " *"
            n_art = out["group_articles"][axis][g]
            print(f"  {g[:60]:60s} n={r['n']:2d}{flag}  articles={n_art}  labels={r['labels']}")
            print(
                f"      principal {r['accuracy']:.3f} {r['accuracy_ci95']} / {r['macro_f1']:.3f}"
                f" | zero-shot {z['accuracy']:.3f} / {z['macro_f1']:.3f}"
                f" | bronze {res['bronze']['accuracy']:.3f}"
                f" | majorité {res['majorite']['accuracy']:.3f}"
            )
    print("\n== écarts ==")
    for k, res in out["gaps"].items():
        for name in ("principal_seed42", "zero-shot-fp32"):
            g = res[name]
            print(
                f"  {k:45s} {name:17s} acc {g['accuracy']:+.3f} {g['accuracy_ci95']}"
                f"  macro-F1 {g['macro_f1']:+.3f} {g['macro_f1_ci95']}"
                + ("" if g["interpretable"] else "  (n < 10)")
            )
    print(f"\n-> {path}")


if __name__ == "__main__":
    main()
