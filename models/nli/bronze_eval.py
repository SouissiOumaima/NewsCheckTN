"""Lot C — Model 2, palier Bronze : réglage, évaluation, ablation et erreurs.

    python -m models.nli.bronze_eval --version v3 --tune          # seuils sur train + val
    python -m models.nli.bronze_eval --version v3 --split test    # une seule fois sur le test

Compare au test fixé : la baseline triviale (classe majoritaire du train), les règles par lexique
(composant Bronze retenu) et, pour l'ablation, une régression logistique sur TF-IDF de n-grammes de
caractères, seule ou avec les indices lexicaux (scikit-learn ; réglage de C sur val).
Écrit le fichier de résultats commun et le CSV des erreurs des règles (data/interim, privé).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import date

from models.nli import bronze
from models.nli.data import LOT_D_TEST_ARTICLES, OUT_DIR, load_pairs
from models.nli.evaluate import RESULTS_DIR, bootstrap_macro_f1, metrics

GRID_LOW = (0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4)
GRID_HIGH = (0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
GRID_C = (0.1, 0.3, 1.0, 3.0, 10.0)


def _lang(p: dict) -> str:
    """Langue de l'affirmation, avec l'écriture pour le tunisien (tableau 2 du guide)."""
    lang = p.get("claim_lang") or "?"
    if lang == "tn":
        return "tn-arabizi" if not re.search(r"[؀-ۿ]", p["claim"]) else "tn-arabe"
    return lang


def rules_predict(
    pairs: list[dict], low: float, high: float
) -> list[tuple[str, str, bronze.Signals]]:
    out = []
    for p in pairs:
        s = bronze.signals(p["claim"], p["evidence"])
        label, _, rule = bronze.decide(s, low, high)
        out.append((label, rule, s))
    return out


def tune(version: str) -> None:
    dev = load_pairs(OUT_DIR / f"nli_{version}_train.jsonl") + load_pairs(
        OUT_DIR / f"nli_{version}_val.jsonl"
    )
    gold = [p["label"] for p in dev]
    sigs = [bronze.signals(p["claim"], p["evidence"]) for p in dev]
    scores = []
    for low in GRID_LOW:
        for high in GRID_HIGH:
            if high <= low:
                continue
            pred = [bronze.decide(s, low, high)[0] for s in sigs]
            scores.append((metrics(gold, pred)["macro_f1"], low, high))
    scores.sort(reverse=True)
    print(f"train + val : {len(dev)} paires. Meilleurs seuils (macro-F1, bas, haut) :")
    for f1, low, high in scores[:5]:
        print(f"  {f1:.3f}  LOW_OVERLAP={low}  HIGH_OVERLAP={high}")
    print("Reporter les meilleurs dans models/nli/bronze.py, puis évaluer une seule fois le test.")


def _category(p: dict, gold: str, pred: str, rule: str) -> str:
    """Catégorie proposée automatiquement (à relire à la main avant la revue)."""
    if rule.startswith("R1"):
        if p.get("claim_lang") != p.get("evidence_lang"):
            return "autre langue que la preuve"
        return "paraphrase non reconnue (recouvrement faible)"
    if rule.startswith("R2"):
        return "nombres mal comparés"
    if rule.startswith("R3"):
        return "marqueur de démenti trompeur"
    if rule.startswith("R4"):
        return "négation mal interprétée"
    if gold == "refutes":
        return "démenti implicite non détecté"
    return "recouvrement trompeur (même sujet, autre fait)"


def tfidf_ablation(train: list[dict], val: list[dict], test: list[dict]) -> dict:
    """Régression logistique : TF-IDF seul, puis TF-IDF + indices lexicaux. C choisi sur val."""
    import numpy as np
    from scipy.sparse import csr_matrix, hstack
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    def text(p: dict) -> str:
        return bronze._clean(p["claim"]) + " || " + bronze._clean(p["evidence"])

    def lex(rows: list[dict]):
        feats = []
        for p in rows:
            s = bronze.signals(p["claim"], p["evidence"])
            feats.append(
                [s.overlap, s.number_conflict, s.numbers_match, s.refute_cue, s.negation_mismatch]
            )
        return csr_matrix(np.array(feats, dtype=float))

    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)
    xs = {
        "train": vec.fit_transform([text(p) for p in train]),
        "val": vec.transform([text(p) for p in val]),
        "test": vec.transform([text(p) for p in test]),
    }
    ls = {"train": lex(train), "val": lex(val), "test": lex(test)}
    y = {
        k: [p["label"] for p in rows]
        for k, rows in (("train", train), ("val", val), ("test", test))
    }
    out = {}
    for name, build in (
        ("tfidf", lambda k: xs[k]),
        ("tfidf+lexique", lambda k: hstack([xs[k], ls[k]]).tocsr()),
    ):
        best = None
        for c in GRID_C:
            clf = LogisticRegression(C=c, max_iter=2000, class_weight="balanced")
            clf.fit(build("train"), y["train"])
            f1 = metrics(y["val"], list(clf.predict(build("val"))))["macro_f1"]
            if best is None or f1 > best[0]:
                best = (f1, c, clf)
        pred = list(best[2].predict(build("test")))
        out[name] = {"C": best[1], "val_macro_f1": best[0], "test": metrics(y["test"], pred)}
    return out


def evaluate(version: str, split: str, exp_id: str) -> None:
    train = load_pairs(OUT_DIR / f"nli_{version}_train.jsonl")
    val = load_pairs(OUT_DIR / f"nli_{version}_val.jsonl")
    pairs = load_pairs(OUT_DIR / f"nli_{version}_{split}.jsonl")
    gold = [p["label"] for p in pairs]

    majority = Counter(p["label"] for p in train).most_common(1)[0][0]
    base = metrics(gold, [majority] * len(pairs))
    preds = rules_predict(pairs, bronze.LOW_OVERLAP, bronze.HIGH_OVERLAP)
    pred = [label for label, _, _ in preds]
    res = metrics(gold, pred)
    res["macro_f1_ci95"] = bootstrap_macro_f1(gold, pred)

    groups: dict[str, list[int]] = {}
    for i, p in enumerate(pairs):
        groups.setdefault(_lang(p), []).append(i)
    by_lang = {
        g: {
            "n": len(ix),
            "rules": metrics([gold[i] for i in ix], [pred[i] for i in ix])["macro_f1"],
            "majority": metrics([gold[i] for i in ix], [majority] * len(ix))["macro_f1"],
        }
        for g, ix in sorted(groups.items())
    }
    lot_d = [i for i, p in enumerate(pairs) if p.get("article_id") in LOT_D_TEST_ARTICLES]
    rules_used = Counter(rule for _, rule, _ in preds)

    print(
        f"{split} : {len(pairs)} paires. Seuils LOW={bronze.LOW_OVERLAP} HIGH={bronze.HIGH_OVERLAP}"
    )
    print(
        f"  baseline triviale (toujours « {majority} ») : macro-F1 {base['macro_f1']:.3f}  "
        f"accuracy {base['accuracy']:.3f}"
    )
    print(
        f"  règles par lexique (Bronze) : macro-F1 {res['macro_f1']:.3f}  accuracy "
        f"{res['accuracy']:.3f}  IC95 {res['macro_f1_ci95']}"
    )
    for lab, m in res["per_class"].items():
        print(f"    {lab:9} P {m['precision']:.2f}  R {m['recall']:.2f}  F1 {m['f1']:.2f}")
    print("    confusion (ligne = vrai label) :", json.dumps(res["confusion"]))
    for g, m in by_lang.items():
        print(
            f"    langue {g:10} n={m['n']:3}  règles {m['rules']:.3f}  majorité {m['majority']:.3f}"
        )
    if lot_d:
        m = metrics([gold[i] for i in lot_d], [pred[i] for i in lot_d])
        print(f"    articles du test du Lot D n={len(lot_d)}  macro-F1 {m['macro_f1']:.3f}")
    print("    règles appliquées :", dict(rules_used))

    ablation = {}
    try:
        ablation = tfidf_ablation(train, val, pairs)
        for name, a in ablation.items():
            print(
                f"  ablation {name:14} (C={a['C']}, val {a['val_macro_f1']:.3f}) : "
                f"macro-F1 {a['test']['macro_f1']:.3f}"
            )
    except ImportError:
        print("  ablation TF-IDF ignorée : scikit-learn non installé")

    errors = [
        (p, g, pr, rule, s)
        for p, g, (pr, rule, s) in zip(pairs, gold, preds, strict=True)
        if g != pr
    ]
    path = OUT_DIR / f"erreurs_bronze_{version}_{split}.csv"
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "pair_id",
                "langue",
                "affirmation",
                "preuve",
                "reference",
                "sortie",
                "regle",
                "recouvrement",
                "categorie_proposee",
                "categorie_validee",
            ]
        )
        for p, g, pr, rule, s in errors:
            w.writerow(
                [
                    p["pair_id"],
                    _lang(p),
                    p["claim"],
                    p["evidence"],
                    g,
                    pr,
                    rule,
                    s.overlap,
                    _category(p, g, pr, rule),
                    "",
                ]
            )
    cats = Counter(_category(p, g, pr, rule) for p, g, pr, rule, _ in errors)
    print(f"  {len(errors)} erreurs -> {path}")
    for c, n in cats.most_common():
        print(f"    {n:3}  {c}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"lot-c_nli-bronze_regles-lexique_{split}_{date.today():%Y%m%d}.json"
    out.write_text(
        json.dumps(
            {
                "exp_id": exp_id,
                "lot": "C",
                "task": "nli",
                "model": "regles-lexique (Bronze)",
                "split": split,
                "corpus_version": version,
                "date": f"{date.today():%Y-%m-%d}",
                "metrics": {
                    "n": res["n"],
                    "macro_f1": res["macro_f1"],
                    "accuracy": res["accuracy"],
                    "majority_macro_f1": base["macro_f1"],
                    "macro_f1_ci95": res["macro_f1_ci95"],
                    "per_class": res["per_class"],
                    "confusion": res["confusion"],
                    "by_lang": by_lang,
                    "errors_by_category": dict(cats),
                    "ablation": {
                        k: {"C": v["C"], "macro_f1": v["test"]["macro_f1"]}
                        for k, v in ablation.items()
                    },
                },
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"-> {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", required=True)
    ap.add_argument("--split", default="test", choices=["val", "test"])
    ap.add_argument("--tune", action="store_true")
    ap.add_argument("--exp-id", default="EXP-C-009")
    args = ap.parse_args()
    if args.tune:
        tune(args.version)
    else:
        evaluate(args.version, args.split, args.exp_id)


if __name__ == "__main__":
    main()
