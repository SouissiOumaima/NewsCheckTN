"""Lot B — Évaluation sur le jeu annoté `tests/fixtures/linguistic_analysis/eval_30.jsonl`.

Métriques, globales et par groupe langue/script (`fr-latin`, `ar-arabic`, `tn-arabic`,
`tn-arabizi`, `tn-mixed`) :
- détection d'affirmation : exactitude et macro-F1 (`evaluation.metrics`) ;
- modalité : exactitude ;
- triplets SPO (phrases `is_claim = true` du gold) : correspondance exacte et partielle
  (F1 de recouvrement de tokens), par rôle ;
- coréférence : exactitude de `resolved_text` sur les phrases annotées.

Les chaînes sont comparées sous forme repliée (minuscules, arabe normalisé), comme le texte
produit par la normalisation du Lot A2 ; les annotations restent lisibles.

Usage (depuis la racine du dépôt) :
    python -m linguistic_analysis.evaluate            # parseurs disponibles (spaCy / Stanza)
    python -m linguistic_analysis.evaluate --rules    # règles seules, comme en CI
    python -m linguistic_analysis.evaluate --errors   # + export des erreurs (analyse d'erreurs)
Le résultat est écrit dans `evaluation/results/lot-b_extraction_<mode>_<AAAAMMJJ>.json`
(format de `evaluation/README.md`), les erreurs dans `lot-b_erreurs_<mode>_<AAAAMMJJ>.json`.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from evaluation.metrics import macro_f1
from linguistic_analysis import modality, preprocessing
from linguistic_analysis.claim_extraction import extract_claims_detailed
from linguistic_analysis.preprocessing import fold
from normalization.normalize import normalize

ROOT = Path(__file__).resolve().parents[1]
EVAL_SET = ROOT / "tests" / "fixtures" / "linguistic_analysis" / "eval_30.jsonl"
RESULTS_DIR = ROOT / "evaluation" / "results"
EXP_ID = "EXP-B-004"
ROLES = ("subject", "predicate", "obj")
_TOKEN = re.compile(r"\w+|[^\w\s]")


def load_eval_set(path: Path = EVAL_SET) -> list[dict]:
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def group_of(item: dict) -> str:
    return f"{item['lang']}-{item['script']}"


def _norm(value: str | None) -> str | None:
    if value is None:
        return None
    return fold(value).replace("’", "'").strip(" .,;:!?؟،")


def exact_match(gold: str | None, pred: str | None) -> bool:
    return _norm(gold) == _norm(pred)


def token_f1(gold: str | None, pred: str | None) -> float:
    """F1 de recouvrement de tokens (1.0 si les deux sont absents)."""
    if gold is None or pred is None:
        return float(gold is None and pred is None)
    g, p = _TOKEN.findall(_norm(gold) or ""), _TOKEN.findall(_norm(pred) or "")
    common = sum(min(g.count(t), p.count(t)) for t in set(g))
    if not g or not p or common == 0:
        return 0.0
    precision, recall = common / len(p), common / len(g)
    return 2 * precision * recall / (precision + recall)


@contextmanager
def rules_only():
    """Force l'analyse par règles (comme en CI), quels que soient les modèles installés."""
    original = preprocessing.get_parser
    preprocessing.get_parser = lambda lang: None
    try:
        yield
    finally:
        preprocessing.get_parser = original


def predict(item: dict) -> dict:
    """Sortie du Lot B pour la phrase cible (dernière phrase du document, après le contexte)."""
    raw = f"{item['context']} {item['text']}" if item.get("context") else item["text"]
    doc = normalize(raw)
    sentences = preprocessing.analyze(doc)
    target = sentences[-1]
    claim = next((c for c in extract_claims_detailed(doc) if c.span[0] >= target.start), None)
    if claim is None:  # phrase trop courte pour être une affirmation candidate
        label = modality.detect_modality(target)[0]
        return {"is_claim": False, "modality": label, "subject": None, "predicate": None,
                "obj": None, "resolved_text": target.text, "parser": target.parser,
                "triggers": [], "resolution_log": []}
    return {
        "is_claim": claim.is_claim,
        "modality": claim.modality,
        "subject": claim.subject,
        "predicate": claim.predicate,
        "obj": claim.obj,
        "resolved_text": claim.resolved_text,
        "parser": claim.parser,
        "triggers": claim.triggers,
        "resolution_log": claim.resolution_log,
    }


def _metrics(records: list[dict]) -> dict:
    gold_claim = ["claim" if r["gold"]["is_claim"] else "non" for r in records]
    pred_claim = ["claim" if r["pred"]["is_claim"] else "non" for r in records]
    claims = [r for r in records if r["gold"]["is_claim"]]
    coref = [r for r in records if r["gold"].get("resolved_text")]
    out = {
        "n": len(records),
        "is_claim_accuracy": _mean(g == p for g, p in zip(gold_claim, pred_claim, strict=True)),
        "is_claim_macro_f1": round(macro_f1(gold_claim, pred_claim), 3) if records else None,
        "modality_accuracy": _mean(r["gold"]["modality"] == r["pred"]["modality"] for r in records),
        "spo_n": len(claims),
        "spo_exact": {
            role: _mean(exact_match(r["gold"][role], r["pred"][role]) for r in claims)
            for role in ROLES
        },
        "spo_partial": {
            role: _mean(token_f1(r["gold"][role], r["pred"][role]) for r in claims)
            for role in ROLES
        },
        "spo_all_exact": _mean(
            all(exact_match(r["gold"][role], r["pred"][role]) for role in ROLES) for r in claims
        ),
        "coref_n": len(coref),
        "coref_accuracy": _mean(
            exact_match(r["gold"]["resolved_text"], r["pred"]["resolved_text"]) for r in coref
        ),
    }
    return out


def _mean(values) -> float | None:
    values = [float(v) for v in values]
    return round(sum(values) / len(values), 3) if values else None


def evaluate(items: list[dict], *, rules: bool = False) -> dict:
    """Évalue le Lot B sur `items` ; renvoie le document de résultats (métriques + prédictions)."""
    if rules:
        with rules_only():
            records = [{"item": it, "gold": it["gold"], "pred": predict(it)} for it in items]
    else:
        records = [{"item": it, "gold": it["gold"], "pred": predict(it)} for it in items]

    parsers = sorted({r["pred"]["parser"] for r in records})
    by_group: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_group[group_of(r["item"])].append(r)
    metrics = _metrics(records)
    metrics["by_lang"] = {group: _metrics(rs) for group, rs in sorted(by_group.items())}
    return {
        "exp_id": EXP_ID,
        "lot": "B",
        "task": "extraction-affirmations",
        "model": "regles" if rules else "parseurs",
        "parsers_used": parsers,
        "split": EVAL_SET.stem,
        "date": date.today().isoformat(),
        "metrics": metrics,
        "items": [
            {
                "id": r["item"]["id"],
                "group": group_of(r["item"]),
                "gold": r["gold"],
                "pred": r["pred"],
            }
            for r in records
        ],
    }


def write_results(results: dict, out_dir: Path = RESULTS_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = results["date"].replace("-", "")
    path = Path(out_dir) / f"lot-b_extraction_{results['model']}_{stamp}.json"
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def find_errors(results: dict) -> list[dict]:
    """Une entrée par (phrase, champ) en erreur, avec le contexte utile à l'analyse.

    Champs examinés : `is_claim` et `modality` (toutes les phrases), `subject` / `predicate` /
    `obj` (phrases `is_claim = true` du gold), `resolved_text` (phrases annotées).
    """
    errors = []
    for it in results["items"]:
        gold, pred = it["gold"], it["pred"]
        fields = ["is_claim", "modality"]
        if gold["is_claim"]:
            fields += list(ROLES)
        if gold.get("resolved_text"):
            fields.append("resolved_text")
        for field in fields:
            if field in ("is_claim", "modality"):
                wrong = gold[field] != pred[field]
            else:
                wrong = not exact_match(gold[field], pred[field])
            if wrong:
                errors.append({
                    "id": it["id"],
                    "group": it["group"],
                    "field": field,
                    "gold": gold[field],
                    "pred": pred[field],
                    "parser": pred["parser"],
                    "triggers": pred["triggers"],
                    "resolution_log": pred["resolution_log"],
                })
    return errors


def write_errors(results: dict, errors: list[dict], out_dir: Path = RESULTS_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = results["date"].replace("-", "")
    path = Path(out_dir) / f"lot-b_erreurs_{results['model']}_{stamp}.json"
    payload = {"exp_id": results["exp_id"], "model": results["model"], "errors": errors}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _summary(results: dict) -> str:
    m = results["metrics"]
    parsers = ", ".join(results["parsers_used"])
    lines = [f"{results['exp_id']} — mode {results['model']} ({parsers})"]
    lines.append(
        f"{'groupe':<12}{'n':>3}  {'claim':>6} {'mod.':>6}  "
        f"{'S':>5} {'P':>5} {'O':>5}  {'SPO':>5}"
    )
    rows = [("global", m), *m["by_lang"].items()]
    for name, g in rows:
        exact = g["spo_exact"]
        lines.append(
            f"{name:<12}{g['n']:>3}  "
            f"{_fmt(g['is_claim_accuracy'])} {_fmt(g['modality_accuracy'])}  "
            f"{_fmt(exact['subject'], 5)} {_fmt(exact['predicate'], 5)} {_fmt(exact['obj'], 5)}  "
            f"{_fmt(g['spo_all_exact'], 5)}"
        )
    lines.append(f"coréférence : {_fmt(m['coref_accuracy'])} sur {m['coref_n']} phrases")
    return "\n".join(lines)


def _fmt(value: float | None, width: int = 6) -> str:
    return f"{'-':>{width}}" if value is None else f"{value:>{width}.2f}"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Évaluation du Lot B sur le jeu annoté.")
    parser.add_argument("--rules", action="store_true", help="règles seules (comme en CI)")
    parser.add_argument("--eval-set", type=Path, default=EVAL_SET)
    parser.add_argument("--out-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--errors", action="store_true", help="exporte aussi les erreurs")
    args = parser.parse_args(argv)
    results = evaluate(load_eval_set(args.eval_set), rules=args.rules)
    path = write_results(results, args.out_dir)
    print(_summary(results))
    print(f"-> {path}")
    if args.errors:
        errors = find_errors(results)
        print(f"{len(errors)} erreur(s) -> {write_errors(results, errors, args.out_dir)}")
        for e in errors:
            print(f"  {e['id']:<6} {e['group']:<11} {e['field']:<13} [{e['parser']}] "
                  f"attendu={e['gold']!r} produit={e['pred']!r}")


if __name__ == "__main__":
    main()
