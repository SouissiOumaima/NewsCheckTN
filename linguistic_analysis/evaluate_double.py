"""Lot B — Mesure sur un jeu en double annotation (deux annotateurs, unité : le texte).

Entrées : un fichier par annotateur, mêmes `id` et mêmes textes. Format : UTF-8 (BOM toléré),
séparateur tabulation, une ligne par texte ; colonnes obligatoires `id`, `texte`, `label`
(AFFIRMATION / OPINION / AUTRE), `modalite` (une des 7 modalités) ; facultatives `sujet`,
`predicat`, `objet` (triplet gold, extraits exacts du texte, vides si absents), `source`, `langue`,
`date` (informatives). Un `.xlsx` (première feuille, mêmes colonnes) est aussi accepté.

Prédiction par texte (`predict_text`) :
- affirmation = au moins une phrase candidate avec `is_claim` vrai ;
- modalité = celle de la première phrase `is_claim`, sinon de la première candidate, sinon
  `detect_modality` sur la première phrase (texte trop court) ;
- triplet = celui de la première phrase `is_claim` (le gold doit porter sur cette phrase).
Groupe de langue : langue donnée par `normalize` (Lot A2) et écriture du texte (`fr`, `ar`,
`tn-arabic`, `tn-arabizi`, `tn-mixed`).

Mesures, en mode règles et en mode parseurs, globalement et par groupe :
- accord entre annotateurs : kappa de Cohen (label 3 classes, affirmation oui/non, modalité) ;
- détection contre chaque annotateur et sur les textes d'accord de label : exactitude, précision,
  rappel, macro-F1 (affirmation / non-affirmation) ; baseline « tout = affirmation » ;
- modalité contre chaque annotateur et sur les textes d'accord de modalité : exactitude, macro-F1 ;
  baseline « tout = assertif » ;
- triplet (si les colonnes existent) : sujet, prédicat, objet, triplet exact (formes repliées) ;
- résultat principal : différence extracteur − baseline en macro-F1 (détection, modalité),
  bootstrap apparié (mêmes tirages de textes pour les deux) ;
- non-régression : `evaluate.evaluate` sur eval_30 dans chaque mode, avec le même `exp_id`.
IC : bootstrap percentile 95 % sur les textes (graine et tirages en option ; chaque mesure refait
les mêmes tirages).

Usage (depuis la racine du dépôt ; le dossier de sortie doit être hors du dépôt) :
    python -m linguistic_analysis.evaluate_double --a A.tsv --b B.tsv --name-a A --name-b B \
        --exp-id EXP-B-009 --out-dir <dossier hors dépôt>
Sorties : `<exp_id>_double.md` et `<exp_id>_double.json` (identifiants et chiffres, aucun texte).
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import random
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

from evaluation.metrics import macro_f1
from linguistic_analysis import agreement, evaluate, modality, preprocessing
from linguistic_analysis.claim_extraction import extract_claims_detailed
from normalization.normalize import normalize

ROOT = evaluate.ROOT
REQUIRED = ("id", "texte", "label", "modalite")
TRIPLET_COLUMNS = {"sujet": "subject", "predicat": "predicate", "prédicat": "predicate",
                   "objet": "obj"}
ROLES = ("subject", "predicate", "obj")
MODES = ("regles", "parseurs")
DEFAULT_SEED = evaluate.BOOTSTRAP_SEED
DEFAULT_RESAMPLES = evaluate.BOOTSTRAP_RESAMPLES
PAIRED_SEED = 42
PAIRED_RESAMPLES = 2000
_ARABIC = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")
_LATIN = re.compile(r"[A-Za-zÀ-ɏ]")
_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------


def _col_index(name: str) -> int:
    n = 0
    for ch in name:
        n = n * 26 + ord(ch) - 64
    return n - 1


def _xlsx_rows(path: Path) -> list[list[str]]:
    """Lignes de la première feuille d'un `.xlsx` (bibliothèque standard seulement)."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.iter(f"{_NS}t")) for si in root]
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows = []
    for row in sheet.iter(f"{_NS}row"):
        cells = {}
        for c in row.iter(f"{_NS}c"):
            col = _col_index(re.match(r"[A-Z]+", c.get("r")).group())
            v = c.find(f"{_NS}v")
            if c.get("t") == "s" and v is not None:
                value = shared[int(v.text)]
            elif c.get("t") == "inlineStr":
                value = "".join(t.text or "" for t in c.iter(f"{_NS}t"))
            else:
                value = v.text if v is not None else ""
            cells[col] = value or ""
        width = max(cells, default=-1) + 1
        rows.append([cells.get(i, "") for i in range(width)])
    return rows


def read_annotation(path: Path, ids: set[str] | None = None) -> tuple[list[dict], list[str]]:
    """Fichier d'annotation → (textes, problèmes de format). `ids` : filtre facultatif."""
    path = Path(path)
    if path.suffix.lower() == ".xlsx":
        rows = _xlsx_rows(path)
    else:
        rows = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8-sig")),
                               delimiter="\t"))
    if not rows:
        return [], [f"{path.name} : fichier vide"]
    header = [h.strip().lower() for h in rows[0]]
    missing = [c for c in REQUIRED if c not in header]
    if missing:
        return [], [f"{path.name} : colonnes manquantes {missing} (trouvées : {header})"]
    col = {h: i for i, h in enumerate(header)}
    triplet_cols = [h for h in TRIPLET_COLUMNS if h in col]
    items, problems, seen = [], [], set()
    for number, row in enumerate(rows[1:], start=2):
        row = row + [""] * (len(header) - len(row))
        item_id = row[col["id"]].strip()
        if not item_id and not any(cell.strip() for cell in row):
            continue
        if ids is not None and item_id not in ids:
            continue
        where = f"{path.name} ligne {number} ({item_id or 'id vide'})"
        if not item_id:
            problems.append(f"{where} : id vide")
            continue
        if item_id in seen:
            problems.append(f"{where} : id en double")
        seen.add(item_id)
        try:
            label = row[col["label"]].strip().upper()
            is_claim = agreement.convert_label(label)
            label_modality = agreement._modality(row[col["modalite"]])
        except ValueError as e:
            problems.append(f"{where} : {e}")
            continue
        gold = {"label": label, "is_claim": is_claim, "modality": label_modality}
        for h in triplet_cols:
            gold[TRIPLET_COLUMNS[h]] = row[col[h]].strip() or None
        items.append({"id": item_id, "text": row[col["texte"]], "gold": gold,
                      "has_triplet": bool(triplet_cols)})
    return items, problems


def id_range(spec: str) -> set[str]:
    """`P01-P60` → {P01, …, P60} ; sinon liste d'identifiants séparés par des virgules."""
    m = re.fullmatch(r"([A-Za-z]*)(\d+)-\1(\d+)", spec)
    if m:
        prefix, lo, hi = m.group(1), m.group(2), m.group(3)
        return {f"{prefix}{k:0{len(lo)}d}" for k in range(int(lo), int(hi) + 1)}
    return {s.strip() for s in spec.split(",") if s.strip()}


# ---------------------------------------------------------------------------
# Système
# ---------------------------------------------------------------------------


def predict_text(text: str) -> dict:
    """Sortie du Lot B pour un texte entier (voir la docstring du module)."""
    doc = normalize(text)
    claims = extract_claims_detailed(doc)
    sentences = preprocessing.analyze(doc)
    claim = next((c for c in claims if c.is_claim), None)
    if claim is not None:
        label = claim.modality
    elif claims:
        label = claims[0].modality
    else:
        label = modality.detect_modality(sentences[0])[0]
    return {"is_claim": claim is not None, "modality": label,
            "subject": claim.subject if claim else None,
            "predicate": claim.predicate if claim else None,
            "obj": claim.obj if claim else None,
            "lang": doc.lang.value,
            "parsers": sorted({s.parser for s in sentences})}


def predict_all(items: list[dict], mode: str) -> dict[str, dict]:
    ctx = evaluate.rules_only() if mode == "regles" else contextlib.nullcontext()
    with ctx:
        return {it["id"]: predict_text(it["text"]) for it in items}


def group_of(lang: str, text: str) -> str:
    ar, lat = bool(_ARABIC.search(text)), bool(_LATIN.search(text))
    script = "mixed" if ar and lat else "arabic" if ar else "latin"
    if lang in ("fr", "ar"):
        return lang
    if lang == "tn":
        return {"arabic": "tn-arabic", "latin": "tn-arabizi", "mixed": "tn-mixed"}[script]
    return f"{lang}-{script}"


# ---------------------------------------------------------------------------
# Mesures
# ---------------------------------------------------------------------------


def ci(seed: int, resamples: int, n: int, fn) -> tuple[float, float] | None:
    """IC percentile 95 % : `fn(indices)` sur `resamples` tirages avec remise (graine `seed`)."""
    if n == 0 or resamples <= 0:
        return None
    rng = random.Random(seed)
    values = []
    for _ in range(resamples):
        v = fn([rng.randrange(n) for _ in range(n)])
        if v is not None:
            values.append(v)
    return evaluate._interval(values, evaluate.CONFIDENCE)


def accuracy(g: list, p: list) -> float | None:
    return sum(x == y for x, y in zip(g, p, strict=True)) / len(g) if g else None


def precision(g: list[bool], p: list[bool]) -> float | None:
    pp = sum(p)
    return sum(x and y for x, y in zip(g, p, strict=True)) / pp if pp else None


def recall(g: list[bool], p: list[bool]) -> float | None:
    gp = sum(g)
    return sum(x and y for x, y in zip(g, p, strict=True)) / gp if gp else None


def detection_macro_f1(g: list[bool], p: list[bool]) -> float | None:
    """Macro-F1 sur les classes affirmation / non-affirmation présentes."""
    if not g:
        return None
    return macro_f1(["claim" if x else "non" for x in g], ["claim" if x else "non" for x in p])


def modality_macro_f1(g: list[str], p: list[str]) -> float | None:
    return macro_f1(g, p) if g else None


def mean(values: list[bool]) -> float | None:
    return sum(values) / len(values) if values else None


def _with_ci(cfg: dict, metric, g: list, p: list) -> dict:
    return {"value": metric(g, p),
            "ci": ci(cfg["seed"], cfg["resamples"], len(g),
                     lambda idx: metric([g[i] for i in idx], [p[i] for i in idx]))}


DETECTION_METRICS = {"exactitude": accuracy, "précision": precision, "rappel": recall,
                     "macro_f1": detection_macro_f1}
MODALITY_METRICS = {"exactitude": accuracy, "macro_f1": modality_macro_f1}


def detection_block(cfg: dict, gold: list[bool], pred: list[bool]) -> dict:
    base = [True] * len(gold)
    out: dict = {"n": len(gold)}
    for name, metric in DETECTION_METRICS.items():
        out[name] = _with_ci(cfg, metric, gold, pred)
        out[f"baseline_{name}"] = metric(gold, base)
    return out


def modality_block(cfg: dict, gold: list[str], pred: list[str]) -> dict:
    base = ["assertif"] * len(gold)
    out: dict = {"n": len(gold)}
    for name, metric in MODALITY_METRICS.items():
        out[name] = _with_ci(cfg, metric, gold, pred)
        out[f"baseline_{name}"] = metric(gold, base)
    return out


def triplet_block(cfg: dict, golds: list[dict], preds: list[dict]) -> dict:
    """Textes dont le gold est une affirmation munie d'au moins un élément de triplet."""
    pairs = [(g, p) for g, p in zip(golds, preds, strict=True)
             if g["is_claim"] and any(g.get(r) for r in ROLES)]
    out: dict = {"n": len(pairs)}
    for name, roles in (("sujet", ("subject",)), ("prédicat", ("predicate",)),
                        ("objet", ("obj",)), ("triplet exact", ROLES)):
        hits = [all(evaluate.exact_match(g.get(r), p.get(r)) for r in roles) for g, p in pairs]
        out[name] = {"value": mean(hits),
                     "ci": ci(cfg["seed"], cfg["resamples"], len(hits),
                              lambda idx, h=hits: mean([h[i] for i in idx]))}
    return out


def paired_vs_baseline(seed: int, resamples: int, metric, gold: list, pred: list,
                       base: list) -> dict:
    """Différence appariée système − baseline (mêmes tirages de textes), IC percentile 95 %."""
    n = len(gold)
    rng = random.Random(seed)
    diffs = []
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        g = [gold[i] for i in idx]
        diffs.append(metric(g, [pred[i] for i in idx]) - metric(g, [base[i] for i in idx]))
    system, baseline = metric(gold, pred), metric(gold, base)
    return {"n": n, "systeme": system, "baseline": baseline, "difference": system - baseline,
            "ci": evaluate._interval(diffs, evaluate.CONFIDENCE), "seed": seed,
            "resamples": resamples,
            "p_unilateral": sum(d <= 0 for d in diffs) / len(diffs) if diffs else None}


def measure(a_items: list[dict], b_items: list[dict], *, names: tuple[str, str] = ("A", "B"),
            modes: tuple[str, ...] = MODES, seed: int = DEFAULT_SEED,
            resamples: int = DEFAULT_RESAMPLES, paired_seed: int = PAIRED_SEED,
            paired_resamples: int = PAIRED_RESAMPLES, exp_id: str = evaluate.EXP_ID,
            eval30: bool = True) -> dict:
    """Toutes les mesures ; renvoie un document JSON (identifiants et chiffres seulement)."""
    na, nb = names
    by_a, by_b = {i["id"]: i for i in a_items}, {i["id"]: i for i in b_items}
    common = [i for i in by_a if i in by_b]
    cfg = {"seed": seed, "resamples": resamples}
    out: dict = {
        "exp_id": exp_id, "seed": seed, "resamples": resamples,
        "confidence": evaluate.CONFIDENCE, "unit": "texte", "names": [na, nb],
        "n_common": len(common), "ids_only_one_file": sorted(set(by_a) ^ set(by_b)),
        "ids_text_differs": [i for i in common
                             if by_a[i]["text"].strip() != by_b[i]["text"].strip()],
    }

    out["accord"] = {}
    for field, name in (("label", "label (3 classes)"), ("is_claim", "affirmation oui/non"),
                        ("modality", "modalité (7)")):
        x = [by_a[i]["gold"][field] for i in common]
        y = [by_b[i]["gold"][field] for i in common]
        out["accord"][name] = {
            "accord": sum(p == q for p, q in zip(x, y, strict=True)), "n": len(common),
            "kappa": agreement.cohen_kappa(x, y) if common else None,
            "ci": ci(seed, resamples, len(x), lambda idx, x=x, y=y: agreement.cohen_kappa(
                [x[i] for i in idx], [y[i] for i in idx])),
            "effectifs": {na: dict(Counter(map(str, x))), nb: dict(Counter(map(str, y)))}}
    agree_label = [i for i in common if by_a[i]["gold"]["label"] == by_b[i]["gold"]["label"]]
    agree_mod = [i for i in common if by_a[i]["gold"]["modality"] == by_b[i]["gold"]["modality"]]
    golds = ((na, by_a), (nb, by_b))

    out["modes"] = {}
    for mode in modes:
        preds = predict_all([by_a[i] for i in common], mode)
        groups = {i: group_of(preds[i]["lang"], by_a[i]["text"]) for i in common}
        res: dict = {"parsers_used": sorted({p for i in common for p in preds[i]["parsers"]}),
                     "groupes": dict(Counter(groups.values())), "par_groupe": {}}
        scopes = {"tous": common}
        scopes |= {g: [i for i in common if groups[i] == g] for g in sorted(set(groups.values()))}
        for scope, sub in scopes.items():
            sub_label = [i for i in sub if i in agree_label]
            sub_mod = [i for i in sub if i in agree_mod]
            block: dict = {"détection": {}, "modalité": {}}
            for who, by in golds:
                block["détection"][who] = detection_block(
                    cfg, [by[i]["gold"]["is_claim"] for i in sub],
                    [preds[i]["is_claim"] for i in sub])
                block["modalité"][who] = modality_block(
                    cfg, [by[i]["gold"]["modality"] for i in sub],
                    [preds[i]["modality"] for i in sub])
            block["détection"]["accord label"] = detection_block(
                cfg, [by_a[i]["gold"]["is_claim"] for i in sub_label],
                [preds[i]["is_claim"] for i in sub_label])
            block["modalité"]["accord modalité"] = modality_block(
                cfg, [by_a[i]["gold"]["modality"] for i in sub_mod],
                [preds[i]["modality"] for i in sub_mod])
            triplets = {who: triplet_block(cfg, [by[i]["gold"] for i in sub],
                                           [preds[i] for i in sub])
                        for who, by in golds if sub and by[sub[0]]["has_triplet"]}
            if triplets:
                block["triplet"] = triplets
            res["par_groupe"][scope] = block

        res["principal"] = {}
        for who, by, sub_d, sub_m in ((na, by_a, common, common), (nb, by_b, common, common),
                                      ("accord", by_a, agree_label, agree_mod)):
            gd = [by[i]["gold"]["is_claim"] for i in sub_d]
            gm = [by[i]["gold"]["modality"] for i in sub_m]
            res["principal"][who] = {
                "détection macro-F1": paired_vs_baseline(
                    paired_seed, paired_resamples, detection_macro_f1, gd,
                    [preds[i]["is_claim"] for i in sub_d], [True] * len(gd)),
                "modalité macro-F1": paired_vs_baseline(
                    paired_seed, paired_resamples, modality_macro_f1, gm,
                    [preds[i]["modality"] for i in sub_m], ["assertif"] * len(gm)),
            }
        res["predictions"] = {i: {"is_claim": preds[i]["is_claim"],
                                  "modality": preds[i]["modality"], "groupe": groups[i]}
                              for i in common}
        out["modes"][mode] = res

    out["eval_30"] = {}
    if eval30:
        items = evaluate.load_eval_set()
        for mode in modes:
            r = evaluate.evaluate(items, rules=mode == "regles", exp_id=exp_id)
            m = r["metrics"]
            out["eval_30"][mode] = {
                "exp_id": r["exp_id"], "parsers_used": r["parsers_used"],
                "is_claim_accuracy": m["is_claim_accuracy"],
                "modality_accuracy": m["modality_accuracy"], "spo_n": m["spo_n"],
                "spo_all_exact": m["spo_all_exact"],
                "spo_all_exact_count": round(m["spo_all_exact"] * m["spo_n"])}
    return out


# ---------------------------------------------------------------------------
# Rendu
# ---------------------------------------------------------------------------


def _f3(v: float | None) -> str:
    return "—" if v is None else f"{v:.3f}"


def _fci(d: dict) -> str:
    bounds = d["ci"]
    return (f"{_f3(d['value'])} [{_f3(bounds[0])} ; {_f3(bounds[1])}]" if bounds
            else _f3(d["value"]))


def to_markdown(out: dict) -> str:
    lines = [
        f"# {out['exp_id']} — mesure en double annotation (unité : texte)", "",
        (f"- Textes communs : {out['n_common']} ; absents d'un fichier : "
         f"{out['ids_only_one_file'] or 'aucun'} ; texte différent entre fichiers : "
         f"{out['ids_text_differs'] or 'aucun'}"),
        (f"- Bootstrap percentile {out['confidence']:.0%}, graine {out['seed']}, "
         f"{out['resamples']} tirages (sur les textes)."),
        "", "## Accord entre annotateurs", "",
        "| Champ | Accord | Kappa [IC 95 %] |", "|---|---|---|",
    ]
    for name, a in out["accord"].items():
        kappa = _fci({"value": a["kappa"], "ci": a["ci"]})
        lines.append(f"| {name} | {a['accord']}/{a['n']} | {kappa} |")
    for mode, res in out["modes"].items():
        lines += ["", f"## Mode {mode} (analyseurs : {', '.join(res['parsers_used'])})", "",
                  f"Groupes : {res['groupes']}", "",
                  "### Résultat principal : extracteur − baseline (bootstrap apparié)", "",
                  ("| Gold | Tâche | N | Extracteur | Baseline | Différence [IC 95 %] | "
                   "P(Δ ≤ 0) | graine / tirages |"), "|---|---|---|---|---|---|---|---|"]
        for who, tasks in res["principal"].items():
            for task, d in tasks.items():
                lo, hi = d["ci"] or (float("nan"), float("nan"))
                lines.append(f"| {who} | {task} | {d['n']} | {_f3(d['systeme'])} | "
                             f"{_f3(d['baseline'])} | {d['difference']:+.3f} [{lo:+.3f} ; "
                             f"{hi:+.3f}] | {_f3(d['p_unilateral'])} | "
                             f"{d['seed']} / {d['resamples']} |")
        lines += ["", "### Détection (baseline « tout = affirmation »)", "",
                  ("| Groupe | Gold | N | Exactitude [IC] | base | Précision [IC] | base | "
                   "Rappel [IC] | Macro-F1 [IC] | base |"),
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for scope, block in res["par_groupe"].items():
            for who, d in block["détection"].items():
                lines.append(f"| {scope} | {who} | {d['n']} | {_fci(d['exactitude'])} | "
                             f"{_f3(d['baseline_exactitude'])} | {_fci(d['précision'])} | "
                             f"{_f3(d['baseline_précision'])} | {_fci(d['rappel'])} | "
                             f"{_fci(d['macro_f1'])} | {_f3(d['baseline_macro_f1'])} |")
        lines += ["", "### Modalité (baseline « tout = assertif »)", "",
                  "| Groupe | Gold | N | Exactitude [IC] | base | Macro-F1 [IC] | base |",
                  "|---|---|---|---|---|---|---|"]
        for scope, block in res["par_groupe"].items():
            for who, d in block["modalité"].items():
                lines.append(f"| {scope} | {who} | {d['n']} | {_fci(d['exactitude'])} | "
                             f"{_f3(d['baseline_exactitude'])} | {_fci(d['macro_f1'])} | "
                             f"{_f3(d['baseline_macro_f1'])} |")
        if any("triplet" in b for b in res["par_groupe"].values()):
            lines += ["", "### Triplet (textes gold AFFIRMATION avec triplet)", "",
                      "| Groupe | Gold | N | Sujet | Prédicat | Objet | Triplet exact |",
                      "|---|---|---|---|---|---|---|"]
            for scope, block in res["par_groupe"].items():
                for who, d in block.get("triplet", {}).items():
                    lines.append(f"| {scope} | {who} | {d['n']} | {_fci(d['sujet'])} | "
                                 f"{_fci(d['prédicat'])} | {_fci(d['objet'])} | "
                                 f"{_fci(d['triplet exact'])} |")
        else:
            lines += ["", "Triplet : aucune colonne `sujet` / `predicat` / `objet`."]
    if out["eval_30"]:
        lines += ["", "## Non-régression eval_30 (evaluate.py)", "",
                  "| Mode | exp_id | Détection | Modalité | Triplet exact |",
                  "|---|---|---|---|---|"]
        for mode, r in out["eval_30"].items():
            lines.append(f"| {mode} | {r['exp_id']} | {_f3(r['is_claim_accuracy'])} | "
                         f"{_f3(r['modality_accuracy'])} | "
                         f"{r['spo_all_exact_count']}/{r['spo_n']} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Ligne de commande
# ---------------------------------------------------------------------------


def outside_repo(path: Path) -> bool:
    """Vrai si `path` n'est pas dans le dépôt (les sorties contiennent des mesures privées)."""
    return not Path(path).resolve().is_relative_to(ROOT.resolve())


def build_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--a", type=Path, required=True, help="annotation du premier annotateur")
    parser.add_argument("--b", type=Path, required=True, help="annotation du second annotateur")
    parser.add_argument("--name-a", default="A")
    parser.add_argument("--name-b", default="B")
    parser.add_argument("--ids", help="filtre d'identifiants, ex. P01-P60 ou id1,id2")
    return parser


def load_pair(parser: argparse.ArgumentParser, args) -> tuple[list[dict], list[dict]]:
    ids = id_range(args.ids) if args.ids else None
    a_items, problems_a = read_annotation(args.a, ids)
    b_items, problems_b = read_annotation(args.b, ids)
    if problems_a or problems_b:
        listing = "\n".join(f"  {p}" for p in problems_a + problems_b)
        parser.exit(2, f"Fichiers d'annotation invalides :\n{listing}\n")
    return a_items, b_items


def main(argv: list[str] | None = None) -> None:
    parser = build_parser("Mesure du Lot B sur un jeu en double annotation.")
    parser.add_argument("--exp-id", type=evaluate.exp_id_arg, default=evaluate.EXP_ID,
                        help="identifiant d'expérience, format EXP-B-NNN")
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="dossier de sortie, obligatoirement hors du dépôt")
    parser.add_argument("--modes", default=",".join(MODES), help="regles, parseurs ou les deux")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--resamples", type=int, default=DEFAULT_RESAMPLES)
    parser.add_argument("--paired-seed", type=int, default=PAIRED_SEED)
    parser.add_argument("--paired-resamples", type=int, default=PAIRED_RESAMPLES)
    parser.add_argument("--no-eval30", action="store_true", help="sans non-régression eval_30")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    modes = tuple(m.strip() for m in args.modes.split(",") if m.strip())
    if not modes or set(modes) - set(MODES):
        parser.error(f"--modes : valeurs autorisées {', '.join(MODES)}")
    if not outside_repo(args.out_dir):
        parser.error(f"--out-dir doit être hors du dépôt ({ROOT})")
    a_items, b_items = load_pair(parser, args)
    out = measure(a_items, b_items, names=(args.name_a, args.name_b), modes=modes,
                  seed=args.seed, resamples=args.resamples, paired_seed=args.paired_seed,
                  paired_resamples=args.paired_resamples, exp_id=args.exp_id,
                  eval30=not args.no_eval30)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.out_dir / f"{args.exp_id}_double"
    stem.with_suffix(".json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
    markdown = to_markdown(out)
    stem.with_suffix(".md").write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"-> {stem.with_suffix('.md')}\n-> {stem.with_suffix('.json')}")


if __name__ == "__main__":
    main()
