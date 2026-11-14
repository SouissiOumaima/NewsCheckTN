"""Lot B — Ablation : contribution de chaque composant de l'extracteur.

Chaque composant est retiré EN MÉMOIRE, le temps d'une mesure : une fonction de module est
remplacée puis restaurée. Ni le code ni les fichiers de ressources ne sont modifiés.
`extract_claims_detailed` appelle ces fonctions par l'attribut de leur module, ce qui rend le
remplacement effectif.

- sans lexiques de modalité (`resources/modality_<langue>.json`) :
  `modality.load_lexicon` renvoie un lexique vide ;
- sans coréférence (`coreference.py`) : `coreference.resolve_with_log` renvoie les phrases
  inchangées ;
- sans règles de factualité (`factuality.py`, `opinion_<langue>.txt`) :
  `factuality.classify_factuality` renvoie « factuel, sans indice » ;
- sans verbes de parole (`resources/speech_verbs.txt`) : `spo.speech_verbs` renvoie un
  ensemble vide ;
- sans parseurs (spaCy / Stanza) : mode règles (`evaluate.rules_only`).

Sans règles de factualité, les modalités interrogatif, souhait et opinion disparaissent aussi
(elles viennent des indices de factualité).

Mesures : eval_30 (`evaluate.evaluate` : détection, modalité, triplet exact, coréférence) et, si
deux fichiers d'annotation sont fournis, le jeu en double annotation (`evaluate_double`) :
macro-F1 de détection et exactitude / macro-F1 de modalité contre chaque annotateur, macro-F1 de
modalité sur les textes d'accord. Chaque variante est comparée au système complet du même mode.

Usage (depuis la racine du dépôt) :
    python -m linguistic_analysis.ablation                       # eval_30 seul
    python -m linguistic_analysis.ablation --a A.tsv --b B.tsv --name-a A --name-b B \
        [--ids P01-P60] [--out-dir <dossier hors dépôt>]
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from pathlib import Path

from evaluation.metrics import macro_f1
from linguistic_analysis import coreference, evaluate, evaluate_double, factuality, modality, spo

COMPLETE = "complet"
WITHOUT_PARSERS = "sans parseurs (= règles, complet)"


@contextlib.contextmanager
def _replace(module, name: str, value):
    original = getattr(module, name)
    setattr(module, name, value)
    try:
        yield
    finally:
        setattr(module, name, original)


def without_modality_lexicons():
    return _replace(modality, "load_lexicon", lambda lang: {})


def without_coreference():
    return _replace(coreference, "resolve_with_log", lambda sentences: [
        coreference.Resolution(resolved_text=s.text) for s in sentences])


def without_factuality():
    return _replace(factuality, "classify_factuality", lambda sentence: (False, 0.5, []))


def without_speech_verbs():
    return _replace(spo, "speech_verbs", lambda: frozenset())


VARIANTS = {
    COMPLETE: contextlib.nullcontext,
    "sans lexiques de modalité": without_modality_lexicons,
    "sans coréférence": without_coreference,
    "sans règles de factualité": without_factuality,
    "sans verbes de parole": without_speech_verbs,
}


def eval30_metrics(items: list[dict], rules: bool) -> dict:
    m = evaluate.evaluate(items, rules=rules)["metrics"]
    return {"e30 claim": m["is_claim_accuracy"], "e30 mod.": m["modality_accuracy"],
            "e30 triplet": round(m["spo_all_exact"] * m["spo_n"]),
            "e30 coref": round(m["coref_accuracy"] * m["coref_n"])}


def pilot_metrics(pair: dict, preds: dict[str, dict]) -> dict:
    out = {}
    common, agree_mod = pair["common"], pair["agree_mod"]
    for who, by in pair["golds"]:
        gold_claim = [by[i]["gold"]["is_claim"] for i in common]
        gold_mod = [by[i]["gold"]["modality"] for i in common]
        pred_mod = [preds[i]["modality"] for i in common]
        out[f"dét. F1 {who}"] = evaluate_double.detection_macro_f1(
            gold_claim, [preds[i]["is_claim"] for i in common])
        out[f"mod. exact. {who}"] = evaluate_double.accuracy(gold_mod, pred_mod)
        out[f"mod. F1 {who}"] = macro_f1(gold_mod, pred_mod)
    by_a = pair["golds"][0][1]
    out["mod. F1 consensus"] = macro_f1([by_a[i]["gold"]["modality"] for i in agree_mod],
                                        [preds[i]["modality"] for i in agree_mod])
    return out


def make_pair(a_items: list[dict], b_items: list[dict], names: tuple[str, str]) -> dict:
    by_a, by_b = {i["id"]: i for i in a_items}, {i["id"]: i for i in b_items}
    common = [i for i in by_a if i in by_b]
    return {"golds": ((names[0], by_a), (names[1], by_b)), "common": common,
            "agree_mod": [i for i in common
                          if by_a[i]["gold"]["modality"] == by_b[i]["gold"]["modality"]],
            "texts": [by_a[i] for i in common]}


def run(eval_items: list[dict] | None = None, pair: dict | None = None,
        modes: tuple[str, ...] = evaluate_double.MODES,
        variants: dict | None = None) -> list[dict]:
    """Une ligne par (mode, variante) : métriques, écarts au complet, textes changés."""
    eval_items = evaluate.load_eval_set() if eval_items is None else eval_items
    variants = VARIANTS if variants is None else variants
    rows: list[dict] = []
    rules_complete = None
    for mode in modes:
        reference = None
        for name, context in variants.items():
            with context():
                metrics = eval30_metrics(eval_items, rules=mode == "regles")
                preds = evaluate_double.predict_all(pair["texts"], mode) if pair else {}
            if pair:
                metrics |= pilot_metrics(pair, preds)
            row = {"mode": mode, "variante": name, "metrics": metrics, "preds": preds}
            reference = reference or row
            _compare(row, reference)
            rows.append(row)
            if mode == "regles" and name == COMPLETE:
                rules_complete = row
        if mode == "parseurs" and rules_complete is not None:
            row = {**rules_complete, "mode": mode, "variante": WITHOUT_PARSERS}
            _compare(row, reference)
            rows.append(row)
    return rows


def _compare(row: dict, reference: dict) -> None:
    row["ecarts"] = {k: v - reference["metrics"][k] for k, v in row["metrics"].items()
                     if v is not None and reference["metrics"][k] is not None}
    row["textes_changes"] = sorted(
        i for i in row["preds"]
        if row["preds"][i]["is_claim"] != reference["preds"][i]["is_claim"]
        or row["preds"][i]["modality"] != reference["preds"][i]["modality"])
    row["reference"] = row is reference


def to_markdown(rows: list[dict]) -> str:
    columns = list(rows[0]["metrics"])
    pilot = any(r["preds"] for r in rows)
    lines = ["| Mode | Variante | " + " | ".join(columns)
             + (" | textes changés |" if pilot else " |"),
             "|---|---|" + "---|" * (len(columns) + pilot)]
    for r in rows:
        cells = []
        for c in columns:
            value, delta = r["metrics"][c], r["ecarts"].get(c)
            if value is None:
                cells.append("—")
            elif isinstance(value, int):
                cells.append(f"{value}" if r["reference"] else f"{value} ({delta:+d})")
            else:
                cells.append(f"{value:.3f}" if r["reference"] else f"{value:.3f} ({delta:+.3f})")
        changed = ("—" if r["reference"] else str(len(r["textes_changes"]))) if pilot else None
        lines.append(f"| {r['mode']} | {r['variante']} | " + " | ".join(cells)
                     + (f" | {changed} |" if pilot else " |"))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Ablation des composants du Lot B.")
    parser.add_argument("--a", type=Path, help="annotation du premier annotateur")
    parser.add_argument("--b", type=Path, help="annotation du second annotateur")
    parser.add_argument("--name-a", default="A")
    parser.add_argument("--name-b", default="B")
    parser.add_argument("--ids", help="filtre d'identifiants, ex. P01-P60")
    parser.add_argument("--modes", default=",".join(evaluate_double.MODES))
    parser.add_argument("--out-dir", type=Path, help="écrit aussi le tableau (hors du dépôt)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if (args.a is None) != (args.b is None):
        parser.error("--a et --b vont ensemble")
    modes = tuple(m.strip() for m in args.modes.split(",") if m.strip())
    if not modes or set(modes) - set(evaluate_double.MODES):
        parser.error(f"--modes : valeurs autorisées {', '.join(evaluate_double.MODES)}")
    if args.out_dir is not None and not evaluate_double.outside_repo(args.out_dir):
        parser.error(f"--out-dir doit être hors du dépôt ({evaluate_double.ROOT})")
    pair = None
    if args.a is not None:
        a_items, b_items = evaluate_double.load_pair(parser, args)
        pair = make_pair(a_items, b_items, (args.name_a, args.name_b))
    rows = run(pair=pair, modes=modes)
    table = to_markdown(rows)
    print(table)
    if args.out_dir is not None:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "ablation.md").write_text(table, encoding="utf-8")
        summary = [{k: r[k] for k in ("mode", "variante", "metrics", "ecarts",
                                      "textes_changes")} for r in rows]
        (args.out_dir / "ablation.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
