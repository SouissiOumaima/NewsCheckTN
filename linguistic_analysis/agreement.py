"""Lot B — Accord inter-annotateurs entre deux fichiers annotés (format `eval_30` / `eval_100`).

Les phrases sont appariées par `id` ; seules les phrases présentes dans les deux fichiers sont
comparées (la double annotation porte sur un échantillon). Mesures :
- `is_claim` et `modality` : accord observé et kappa de Cohen ;
- `subject`, `predicate`, `obj` : accord exact (formes repliées) sur les phrases que les deux
  annotateurs jugent vérifiables ;
- `resolved_text` : accord exact quand les deux l'ont rempli.
Les désaccords sont listés pour la discussion (protocole eval_100, section 4.4).

Usage (depuis la racine du dépôt) :
    python -m linguistic_analysis.agreement annotation_1.jsonl annotation_2.jsonl
    python -m linguistic_analysis.agreement a.jsonl b.jsonl --json rapport.json
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from linguistic_analysis.evaluate import ROLES, exact_match, load_eval_set, validate_eval_set

KAPPA_FIELDS = ("is_claim", "modality")


def cohen_kappa(labels_a: list, labels_b: list) -> float:
    """Kappa de Cohen entre deux annotations de mêmes éléments.

    Cas dégénéré (un seul label utilisé par les deux annotateurs, accord attendu = 1) : 1.0 si
    l'accord observé est total, 0.0 sinon.
    """
    if len(labels_a) != len(labels_b):
        raise ValueError("kappa : les deux annotations n'ont pas la même longueur")
    n = len(labels_a)
    if n == 0:
        raise ValueError("kappa : aucune phrase en commun")
    observed = sum(a == b for a, b in zip(labels_a, labels_b, strict=True)) / n
    count_a, count_b = Counter(labels_a), Counter(labels_b)
    expected = sum(count_a[label] * count_b[label] for label in count_a) / (n * n)
    if expected == 1:
        return 1.0 if observed == 1 else 0.0
    return (observed - expected) / (1 - expected)


def agreement(items_a: list[dict], items_b: list[dict]) -> dict:
    """Accord entre deux annotations ; voir la docstring du module."""
    by_id_a = {it["id"]: it for it in items_a}
    by_id_b = {it["id"]: it for it in items_b}
    common = sorted(set(by_id_a) & set(by_id_b))
    if not common:
        raise ValueError("aucune phrase commune aux deux fichiers (appariement par id)")
    pairs = [(by_id_a[i]["gold"], by_id_b[i]["gold"]) for i in common]
    report: dict = {
        "n": len(common),
        "only_a": sorted(set(by_id_a) - set(by_id_b)),
        "only_b": sorted(set(by_id_b) - set(by_id_a)),
    }
    for field in KAPPA_FIELDS:
        a = [ga[field] for ga, _ in pairs]
        b = [gb[field] for _, gb in pairs]
        report[field] = {
            "observed": round(sum(x == y for x, y in zip(a, b, strict=True)) / len(a), 3),
            "kappa": round(cohen_kappa(a, b), 3),
        }
    both_claims = [(ga, gb) for ga, gb in pairs if ga["is_claim"] and gb["is_claim"]]
    report["spo_n"] = len(both_claims)
    report["spo_exact"] = {
        role: (
            round(sum(exact_match(ga[role], gb[role]) for ga, gb in both_claims)
                  / len(both_claims), 3)
            if both_claims else None
        )
        for role in ROLES
    }
    disagreements = []
    for item_id, (ga, gb) in zip(common, pairs, strict=True):
        fields = list(KAPPA_FIELDS)
        if ga["is_claim"] and gb["is_claim"]:
            fields += list(ROLES)
        if ga.get("resolved_text") and gb.get("resolved_text"):
            fields.append("resolved_text")
        for field in fields:
            same = ga[field] == gb[field] if field in KAPPA_FIELDS else exact_match(
                ga[field], gb[field]
            )
            if not same:
                disagreements.append({
                    "id": item_id,
                    "field": field,
                    "a": ga[field],
                    "b": gb[field],
                    "text": by_id_a[item_id]["text"],
                })
    report["disagreements"] = disagreements
    return report


def summary(report: dict) -> str:
    lines = [f"Phrases comparées : {report['n']}"]
    if report["only_a"] or report["only_b"]:
        lines.append(
            f"Non appariées : {len(report['only_a'])} seulement dans A, "
            f"{len(report['only_b'])} seulement dans B"
        )
    for field in KAPPA_FIELDS:
        r = report[field]
        lines.append(f"{field:<10} accord {r['observed']:.2f}   kappa {r['kappa']:.2f}")
    spo = ", ".join(
        f"{role} {'-' if v is None else f'{v:.2f}'}" for role, v in report["spo_exact"].items()
    )
    lines.append(f"SPO exact (sur {report['spo_n']} affirmations communes) : {spo}")
    lines.append(f"Désaccords : {len(report['disagreements'])}")
    for d in report["disagreements"]:
        lines.append(f"  {d['id']:<9} {d['field']:<13} A={d['a']!r}  B={d['b']!r}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Accord inter-annotateurs (Lot B).")
    parser.add_argument("annotation_a", type=Path)
    parser.add_argument("annotation_b", type=Path)
    parser.add_argument("--json", type=Path, help="écrit aussi le rapport complet en JSON")
    args = parser.parse_args(argv)
    files = {"A": args.annotation_a, "B": args.annotation_b}
    loaded = {}
    for name, path in files.items():
        items = load_eval_set(path)
        problems = validate_eval_set(items)
        if problems:
            listing = "\n".join(f"  {p}" for p in problems)
            parser.exit(2, f"Fichier {name} ({path}) invalide :\n{listing}\n")
        loaded[name] = items
    report = agreement(loaded["A"], loaded["B"])
    print(summary(report))
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"-> {args.json}")


if __name__ == "__main__":
    main()
