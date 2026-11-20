"""Lot B — Question de recherche 1 : extracteur gelé du Lot B contre les classifieurs du Lot C.

Tâche : détection binaire (AFFIRMATION contre OPINION / AUTRE), à l'unité texte.

Entrées (toutes hors dépôt) :
- `--gold` : fichier tabulé du format de `evaluate_double` (`id`, `texte`, `label`, `modalite` ;
  colonnes facultatives `langue` et `script`, langue déclarée par le jeu) ;
- `--ids` : identifiants mesurés, sous forme de fichier JSON de split (clé `test_ids`) ou de liste
  (un identifiant par ligne). Seuls les identifiants présents dans le gold sont gardés ;
- `--tfidf` : prédictions du Model 1 TF-IDF du Lot C, produites à part par la commande d'EXP-C-010.
  Format : CSV / TSV avec `id` et `label` (ou `label_predit`), ou le JSON de sortie d'EXP-C-010
  (liste `predictions`, colonne `predicted_label`) ;
- `--xlmr` (facultatif) : un fichier de prédictions par graine, même format.

Les identifiants sont rapprochés par préfixe et valeur numérique (`P25` = `P025`).

Mesures :
- Lot B : `is_claim` au niveau du texte (`evaluate_double.predict_text`), en mode règles et en mode
  parseurs ;
- baseline « tout = affirmation » ;
- macro-F1 binaire avec IC percentile à 95 % (graine 20261015, 1000 tirages) ;
- différences appariées (mêmes tirages de textes ; graine 42, 2000 tirages) : Lot B − chaque
  classifieur et − baseline, classifieur − baseline ;
- ventilation par groupe de langue déclaré (fr, ar, tn-arabe, tn-arabizi, tn-mixte), à défaut
  par la langue du Lot A2 ; un groupe de moins de 15 textes est signalé non interprétable ;
- XLM-R : une mesure par graine, puis moyenne ± écart-type.

Sorties : `qr1_resultats.json` et `qr1_resultats.md` (identifiants et chiffres, aucun texte).

Usage (depuis la racine du dépôt ; dossier de sortie hors du dépôt) :
    python -X utf8 notebooks/lot_b_linguistic/mesures/qr1_compare.py --gold <test.tsv> \\
        --ids <split.json> --tfidf <prédictions> [--xlmr <graine1> <graine2> <graine3>] \\
        --out-dir <dossier>
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from linguistic_analysis import evaluate_double as ed  # noqa: E402

CI_SEED, CI_RESAMPLES = 20261015, 1000
PAIRED_SEED, PAIRED_RESAMPLES = 42, 2000
MIN_GROUP = 15
GROUP_ORDER = ("fr", "ar", "tn-arabe", "tn-arabizi", "tn-mixte")
_A2_GROUPS = {"tn-arabic": "tn-arabe", "tn-mixed": "tn-mixte"}
_ID = re.compile(r"(\D*)(\d+)")
_PRED_COLUMNS = ("predicted_label", "label_predit", "label")  # par ordre de priorité


def default_settings() -> dict:
    return {"seed": CI_SEED, "resamples": CI_RESAMPLES, "paired_seed": PAIRED_SEED,
            "paired_resamples": PAIRED_RESAMPLES}


def id_key(item_id: str) -> str:
    """Clé de rapprochement : préfixe + valeur numérique (`P25` et `P025` → `P#25`)."""
    m = _ID.fullmatch(str(item_id).strip())
    return f"{m.group(1)}#{int(m.group(2))}" if m else str(item_id).strip()


def read_ids(path: Path) -> list[str]:
    """Identifiants d'un split JSON (`test_ids`), d'une liste JSON ou d'un fichier texte."""
    text = Path(path).read_text(encoding="utf-8-sig")
    if Path(path).suffix.lower() == ".json":
        data = json.loads(text)
        return [str(i) for i in (data["test_ids"] if isinstance(data, dict) else data)]
    return [line.strip() for line in text.splitlines() if line.strip()]


def read_predictions(path: Path) -> dict[str, bool]:
    """Prédictions d'un classifieur → {clé d'identifiant : affirmation ?}.

    Dans le JSON d'EXP-C-010, `label` est le gold et `predicted_label` la prédiction : la colonne
    `predicted_label` est donc prise en priorité.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        rows = json.loads(text)["predictions"]
    else:
        dialect = csv.Sniffer().sniff(text.splitlines()[0], delimiters=",;\t")
        rows = list(csv.DictReader(io.StringIO(text), dialect=dialect))
    out = {}
    for row in rows:
        column = next((c for c in _PRED_COLUMNS if c in row), None)
        if column is None:
            raise ValueError(f"{path.name} : colonne de prédiction absente {_PRED_COLUMNS}")
        out[id_key(row["id"])] = str(row[column]).strip().upper() == "AFFIRMATION"
    return out


def declared_group(row: dict) -> str | None:
    """Groupe de langue déclaré par le jeu (colonnes `langue` et `script`), ou None."""
    lang, script = (row.get("langue") or "").strip(), (row.get("script") or "").strip()
    if lang in ("fr", "ar"):
        return lang
    if lang == "tn":
        return {"arabic": "tn-arabe", "arabizi": "tn-arabizi", "mixed": "tn-mixte"}.get(script)
    return None


def read_gold_rows(path: Path) -> dict[str, dict]:
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return {r["id"].strip(): r for r in csv.DictReader(f, delimiter="\t")}


def _f1(gold: list[bool], pred: list[bool]) -> float | None:
    return ed.detection_macro_f1(gold, pred)


def with_ci(gold: list[bool], pred: list[bool], seed: int, resamples: int) -> dict:
    return {"value": _f1(gold, pred),
            "ci": ed.ci(seed, resamples, len(gold),
                        lambda idx: _f1([gold[i] for i in idx], [pred[i] for i in idx]))}


def paired(gold: list[bool], a: list[bool], b: list[bool], seed: int, resamples: int) -> dict:
    """Différence appariée a − b de la macro-F1 binaire (mêmes tirages de textes)."""
    r = ed.paired_vs_baseline(seed, resamples, _f1, gold, a, b)
    lo, hi = r["ci"]
    return {"a": r["systeme"], "b": r["baseline"], "diff": r["difference"], "ci": [lo, hi],
            "contains_zero": lo <= 0 <= hi}


def measure_block(ids: list[str], gold: dict[str, bool], systems: dict[str, dict[str, bool]],
                  cfg: dict) -> dict:
    """Scores et différences appariées sur `ids`. `systems` : `lot_b_<mode>`, `baseline` et les
    classifieurs du Lot C."""
    out = {"n": len(ids), "n_affirmation": sum(gold[i] for i in ids),
           "interpretable": len(ids) >= MIN_GROUP, "systems": {}, "paired": {}}
    if not ids:
        return out
    g = [gold[i] for i in ids]
    preds = {name: [s[i] for i in ids] for name, s in systems.items()}
    for name, p in preds.items():
        out["systems"][name] = with_ci(g, p, cfg["seed"], cfg["resamples"])
    lot_b = [n for n in preds if n.startswith("lot_b_")]
    others = [n for n in preds if not n.startswith("lot_b_") and n != "baseline"]
    for b_name in lot_b:
        for other in [*others, "baseline"]:
            out["paired"][f"{b_name} - {other}"] = paired(
                g, preds[b_name], preds[other], cfg["paired_seed"], cfg["paired_resamples"])
    for other in others:
        out["paired"][f"{other} - baseline"] = paired(
            g, preds[other], preds["baseline"], cfg["paired_seed"], cfg["paired_resamples"])
    return out


def measure_all(ids: list[str], gold: dict[str, bool], group: dict[str, str],
                systems: dict[str, dict[str, bool]], cfg: dict) -> dict:
    res = {"global": measure_block(ids, gold, systems, cfg)}
    for name in GROUP_ORDER:
        res[name] = measure_block([i for i in ids if group[i] == name], gold, systems, cfg)
    return res


def run(gold_path: Path, ids_path: Path, tfidf_path: Path, xlmr_paths: list[Path] | None = None,
        modes: tuple[str, ...] = ed.MODES, cfg: dict | None = None) -> dict:
    cfg = cfg or default_settings()
    rows = read_gold_rows(gold_path)
    by_key = {id_key(i): i for i in rows}
    wanted = {id_key(i) for i in read_ids(ids_path)}
    ids = sorted(by_key[k] for k in wanted if k in by_key)
    items, problems = ed.read_annotation(gold_path, set(ids))
    if problems:
        raise ValueError("gold invalide : " + " ; ".join(problems[:5]))
    gold = {it["id"]: it["gold"]["is_claim"] for it in items}

    systems, parsers, langs = {}, {}, {}
    for mode in modes:
        raw = ed.predict_all(items, mode)
        systems[f"lot_b_{mode}"] = {i: p["is_claim"] for i, p in raw.items()}
        parsers[mode] = sorted({x for p in raw.values() for x in p["parsers"]})
        langs = {i: p["lang"] for i, p in raw.items()}
    group = {}
    for it in items:
        name = declared_group(rows[it["id"]])
        if name is None:  # pas de langue déclarée : langue du Lot A2
            a2 = ed.group_of(langs.get(it["id"], "unk"), it["text"])
            name = _A2_GROUPS.get(a2, a2)
        group[it["id"]] = name

    def classifier(path: Path) -> dict[str, bool]:
        preds = read_predictions(path)
        missing = [i for i in ids if id_key(i) not in preds]
        if missing:
            raise ValueError(f"{Path(path).name} : {len(missing)} identifiants absents")
        return {i: preds[id_key(i)] for i in ids}

    systems["tfidf"] = classifier(tfidf_path)
    systems["baseline"] = {i: True for i in ids}
    out = {"n": len(ids), "n_ids_demandes": len(wanted),
           "gold_sha256": hashlib.sha256(Path(gold_path).read_bytes()).hexdigest(),
           "ids": ids, "modes": list(modes), "parsers_used": parsers,
           "modes_disagree": sorted(i for i in ids
                                    if len({systems[f"lot_b_{m}"][i] for m in modes}) > 1),
           "settings": cfg, "min_group": MIN_GROUP,
           "results": measure_all(ids, gold, group, systems, cfg), "xlmr": None}
    if xlmr_paths:
        per_seed = [{"file": Path(p).name,
                     "results": measure_all(ids, gold, group,
                                            {**systems, "xlmr": classifier(p)}, cfg)}
                    for p in xlmr_paths]
        out["xlmr"] = {"per_seed": per_seed, "summary": _xlmr_summary(per_seed, modes)}
    return out


def _agg(values: list[float | None]) -> dict:
    vals = [v for v in values if v is not None]
    return {"mean": statistics.mean(vals) if vals else None,
            "sd": statistics.stdev(vals) if len(vals) > 1 else None, "values": vals}


def _xlmr_summary(per_seed: list[dict], modes: tuple[str, ...]) -> dict:
    summary = {}
    for name in ("global", *GROUP_ORDER):
        blocks = [s["results"][name] for s in per_seed]
        entry = {"xlmr_f1": _agg([b["systems"].get("xlmr", {}).get("value") for b in blocks])}
        for mode in modes:
            key = f"lot_b_{mode} - xlmr"
            entry[f"{mode}_minus_xlmr"] = _agg([b["paired"].get(key, {}).get("diff")
                                                for b in blocks])
            entry[f"{mode}_ci_contains_zero"] = [b["paired"].get(key, {}).get("contains_zero")
                                                 for b in blocks]
        summary[name] = entry
    return summary


def _fci(d: dict) -> str:
    lo, hi = d["ci"] or (None, None)
    return f"{d['value']:.3f} [{lo:.3f} ; {hi:.3f}]" if lo is not None else f"{d['value']:.3f}"


def _fdiff(d: dict) -> str:
    flag = "IC contient 0" if d["contains_zero"] else "établie"
    return f"{d['diff']:+.3f} [{d['ci'][0]:+.3f} ; {d['ci'][1]:+.3f}] ({flag})"


def to_markdown(out: dict) -> str:
    names = [f"lot_b_{m}" for m in out["modes"]] + ["tfidf", "baseline"]
    lines = [f"Textes : {out['n']} ; parseurs : {out['parsers_used']} ; "
             f"désaccords entre modes : {len(out['modes_disagree'])}", "",
             "| Groupe | n (aff.) | " + " | ".join(names) + " |",
             "|---|---|" + "---|" * len(names)]
    for name, b in out["results"].items():
        if b["n"]:
            flag = "" if b["interpretable"] else " ⚠ < 15"
            lines.append(f"| {name}{flag} | {b['n']} ({b['n_affirmation']}) | "
                         + " | ".join(_fci(b["systems"][n]) for n in names) + " |")
    pairs = list(out["results"]["global"]["paired"])
    lines += ["", "| Groupe | " + " | ".join(pairs) + " |", "|---|" + "---|" * len(pairs)]
    for name, b in out["results"].items():
        if b["n"]:
            flag = "" if b["interpretable"] else " ⚠ < 15"
            lines.append(f"| {name}{flag} | "
                         + " | ".join(_fdiff(b["paired"][p]) for p in pairs) + " |")
    if out["xlmr"]:
        lines += ["", "XLM-R, moyenne ± écart-type sur les graines :", ""]
        for name, s in out["xlmr"]["summary"].items():
            parts = [f"{k} {v['mean']:+.3f}" + (f" ± {v['sd']:.3f}" if v["sd"] is not None else "")
                     for k, v in s.items() if isinstance(v, dict) and v["mean"] is not None]
            lines.append(f"- {name} : " + " ; ".join(parts))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Question de recherche 1 (Lot B contre Lot C).")
    ap.add_argument("--gold", type=Path, required=True)
    ap.add_argument("--ids", type=Path, required=True)
    ap.add_argument("--tfidf", type=Path, required=True)
    ap.add_argument("--xlmr", type=Path, nargs="*", default=[])
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--modes", nargs="+", choices=ed.MODES, default=list(ed.MODES))
    ap.add_argument("--expect-gold-sha256", help="refuse la mesure si l'empreinte du gold diffère")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not ed.outside_repo(args.out_dir):
        ap.exit(2, "Le dossier de sortie doit être hors du dépôt.\n")
    if args.expect_gold_sha256:
        actual = hashlib.sha256(args.gold.read_bytes()).hexdigest()
        if actual != args.expect_gold_sha256.lower():
            ap.exit(2, f"Empreinte du gold inattendue : {actual}\n")
    out = run(args.gold, args.ids, args.tfidf, args.xlmr, tuple(args.modes))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "qr1_resultats.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out_dir / "qr1_resultats.md").write_text(to_markdown(out), encoding="utf-8")
    print(to_markdown(out))


if __name__ == "__main__":
    main()
