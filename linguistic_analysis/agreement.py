"""Lot B — Accord inter-annotateurs entre deux fichiers annotés.

Formats acceptés (reconnus à l'extension) :
- JSONL au format `eval_30` / `eval_100` (`gold.is_claim`, `gold.modality`, triplet…) ;
- CSV d'annotation du lot de double annotation (`id ; texte ; contexte ; label ; modalite`,
  séparateur `;` ou `,`) : `label` AFFIRMATION → `is_claim` vrai, OPINION et AUTRE → faux.

Les phrases sont appariées par `id` ; seules les phrases présentes dans les deux fichiers sont
comparées. Langue d'une phrase : champ `lang` du JSONL, sinon fichier `--langs` (JSONL avec `id`
et `lang` ou `lang_source`, ex. la correspondance du lot), sinon « inconnue ». Mesures,
globalement et par langue :
- `is_claim`, `modality` et, si les deux fichiers sont des CSV, `label` (3 classes) : accord brut
  (pourcentage) et kappa de Cohen ; effectifs par classe de chaque annotateur, avec un
  avertissement si une classe est rare (le kappa est alors instable) ;
- `subject`, `predicate`, `obj` (JSONL des deux côtés) : accord exact (formes repliées) sur les
  phrases que les deux annotateurs jugent vérifiables ; `resolved_text` quand les deux l'ont rempli.
Les désaccords sont listés pour la discussion (protocole eval_100, section 4.4).

Usage (depuis la racine du dépôt) :
    python -m linguistic_analysis.agreement a.jsonl b.jsonl
    python -m linguistic_analysis.agreement a.csv b.csv --langs correspondance.jsonl
    python -m linguistic_analysis.agreement a.jsonl b.csv --json rapport.json
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from linguistic_analysis.evaluate import ROLES, exact_match, load_eval_set, validate_eval_set
from linguistic_analysis.types import MODALITY_LABELS

KAPPA_FIELDS = ("is_claim", "modality")
LABELS = {"AFFIRMATION": True, "OPINION": False, "AUTRE": False}
CSV_COLUMNS = ("id", "texte", "label", "modalite")
UNKNOWN_LANG = "inconnue"
# Une classe est jugée rare sous ce seuil (part ou effectif) : kappa instable.
RARE_SHARE = 0.2
RARE_COUNT = 5


class _Semicolon(csv.excel):
    """Dialecte de repli (séparateur du CSV transmis à l'annotateur)."""

    delimiter = ";"


def _fold_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))


_MODALITIES = {_fold_accents(m).casefold(): m for m in MODALITY_LABELS}


def convert_label(label: str) -> bool:
    """Label du CSV (AFFIRMATION / OPINION / AUTRE, casse indifférente) → `is_claim`."""
    key = (label or "").strip().upper()
    if key not in LABELS:
        raise ValueError(f"label {label!r} inconnu (attendu : {', '.join(LABELS)})")
    return LABELS[key]


def _modality(value: str) -> str:
    key = _fold_accents((value or "").strip()).casefold()
    if key not in _MODALITIES:
        raise ValueError(f"modalité {value!r} inconnue (attendu : {', '.join(MODALITY_LABELS)})")
    return _MODALITIES[key]


def read_csv_annotation(path: Path) -> tuple[list[dict], list[str]]:
    """Lit un CSV d'annotation ; renvoie (phrases au format commun, problèmes)."""
    text = Path(path).read_text(encoding="utf-8-sig")
    try:
        dialect = csv.Sniffer().sniff(text.splitlines()[0] if text else "", delimiters=";,\t")
    except csv.Error:
        dialect = _Semicolon
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    reader.fieldnames = [(f or "").strip().lower() for f in reader.fieldnames or []]
    missing = [c for c in CSV_COLUMNS if c not in reader.fieldnames]
    if missing:
        return [], [f"colonnes manquantes {missing} (trouvées : {reader.fieldnames})"]
    items, problems, seen = [], [], set()
    for number, row in enumerate(reader, start=2):
        item_id = (row["id"] or "").strip()
        label = f"ligne {number}" + (f" ({item_id})" if item_id else "")
        if not item_id:
            problems.append(f"{label} : id vide")
            continue
        if item_id in seen:
            problems.append(f"{label} : id en double")
        seen.add(item_id)
        try:
            is_claim = convert_label(row["label"])
            modality = _modality(row["modalite"])
        except ValueError as e:
            problems.append(f"{label} : {e}")
            continue
        items.append({
            "id": item_id, "text": row["texte"], "lang": None,
            "gold": {"is_claim": is_claim, "modality": modality,
                     "label": row["label"].strip().upper()},
        })
    return items, problems


def load_annotation(path: Path) -> tuple[list[dict], list[str]]:
    """Charge un fichier annoté (CSV ou JSONL) ; renvoie (phrases, problèmes de format)."""
    if Path(path).suffix.lower() == ".csv":
        return read_csv_annotation(path)
    items = load_eval_set(path)
    return items, validate_eval_set(items)


def load_langs(path: Path) -> dict[str, str]:
    """`id` → langue, depuis un JSONL (`lang`, sinon `lang_source`)."""
    langs = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            lang = row.get("lang") or row.get("lang_source")
            if lang:
                langs[row["id"]] = lang
    return langs


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


def _field_stats(pairs: list[tuple[dict, dict]], field: str) -> dict:
    a = [ga[field] for ga, _ in pairs]
    b = [gb[field] for _, gb in pairs]
    observed = sum(x == y for x, y in zip(a, b, strict=True)) / len(a)
    return {
        "n": len(a),
        "observed": round(observed, 3),
        "agreement_pct": round(100 * observed, 1),
        "kappa": round(cohen_kappa(a, b), 3),
        "class_counts": {
            "A": dict(sorted(Counter(map(str, a)).items())),
            "B": dict(sorted(Counter(map(str, b)).items())),
        },
    }


def _imbalance_warnings(stats: dict, field: str, scope: str) -> list[str]:
    """Une seule classe utilisée (tous les champs), ou classe rare chez un annotateur (part <
    RARE_SHARE ou effectif < RARE_COUNT ; pas pour `modality`, qui a 7 classes)."""
    warnings = []
    for who, counts in stats["class_counts"].items():
        total = sum(counts.values())
        if len(counts) < 2:
            warnings.append(f"{scope} {field} : annotateur {who} n'utilise qu'une classe "
                            f"({counts}) ; kappa non interprétable")
            continue
        if field == "modality":
            continue
        rare = {c: n for c, n in counts.items() if n / total < RARE_SHARE or n < RARE_COUNT}
        if rare:
            warnings.append(f"{scope} {field} : classe(s) rare(s) chez {who} {rare} sur {total} ; "
                            f"kappa instable")
    return warnings


def agreement(items_a: list[dict], items_b: list[dict],
              langs: dict[str, str] | None = None) -> dict:
    """Accord entre deux annotations ; voir la docstring du module."""
    langs = langs or {}
    by_id_a = {it["id"]: it for it in items_a}
    by_id_b = {it["id"]: it for it in items_b}
    common = sorted(set(by_id_a) & set(by_id_b))
    if not common:
        raise ValueError("aucune phrase commune aux deux fichiers (appariement par id)")
    pairs = [(by_id_a[i]["gold"], by_id_b[i]["gold"]) for i in common]
    lang_of = {
        i: by_id_a[i].get("lang") or by_id_b[i].get("lang") or langs.get(i) or UNKNOWN_LANG
        for i in common
    }
    fields = list(KAPPA_FIELDS)
    if all("label" in ga and "label" in gb for ga, gb in pairs):
        fields.append("label")
    has_spo = all(all(r in ga and r in gb for r in ROLES) for ga, gb in pairs)

    report: dict = {
        "n": len(common),
        "only_a": sorted(set(by_id_a) - set(by_id_b)),
        "only_b": sorted(set(by_id_b) - set(by_id_a)),
        "fields": fields,
    }
    warnings = []
    for field in fields:
        report[field] = _field_stats(pairs, field)
        warnings += _imbalance_warnings(report[field], field, "global")
    report["by_lang"] = {}
    groups: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    for item_id, pair in zip(common, pairs, strict=True):
        groups[lang_of[item_id]].append(pair)
    for lang, lang_pairs in sorted(groups.items()):
        report["by_lang"][lang] = {"n": len(lang_pairs)}
        for field in fields:
            stats = _field_stats(lang_pairs, field)
            report["by_lang"][lang][field] = stats
            warnings += _imbalance_warnings(stats, field, lang)
    report["warnings"] = warnings

    both_claims = [(ga, gb) for ga, gb in pairs if ga["is_claim"] and gb["is_claim"]]
    report["spo_n"] = len(both_claims) if has_spo else 0
    report["spo_exact"] = {
        role: (
            round(sum(exact_match(ga[role], gb[role]) for ga, gb in both_claims)
                  / len(both_claims), 3)
            if has_spo and both_claims else None
        )
        for role in ROLES
    }
    disagreements = []
    for item_id, (ga, gb) in zip(common, pairs, strict=True):
        checked = list(fields)
        if has_spo and ga["is_claim"] and gb["is_claim"]:
            checked += list(ROLES)
        if ga.get("resolved_text") and gb.get("resolved_text"):
            checked.append("resolved_text")
        for field in checked:
            exact = field in ("is_claim", "modality", "label")
            same = ga[field] == gb[field] if exact else exact_match(ga[field], gb[field])
            if not same:
                disagreements.append({
                    "id": item_id,
                    "lang": lang_of[item_id],
                    "field": field,
                    "a": ga[field],
                    "b": gb[field],
                    "text": by_id_a[item_id]["text"],
                })
    report["disagreements"] = disagreements
    return report


def _line(name: str, stats: dict) -> str:
    counts = " | ".join(
        f"{who} " + ", ".join(f"{c}:{n}" for c, n in stats["class_counts"][who].items())
        for who in ("A", "B")
    )
    return (f"  {name:<10} n={stats['n']:<3} accord {stats['agreement_pct']:5.1f} %   "
            f"kappa {stats['kappa']:5.2f}   effectifs {counts}")


def summary(report: dict) -> str:
    lines = [f"Phrases comparées : {report['n']}"]
    if report["only_a"] or report["only_b"]:
        lines.append(
            f"Non appariées : {len(report['only_a'])} seulement dans A, "
            f"{len(report['only_b'])} seulement dans B"
        )
    lines.append("Global :")
    lines += [_line(field, report[field]) for field in report["fields"]]
    for lang, stats in report["by_lang"].items():
        lines.append(f"Langue {lang} ({stats['n']} phrases) :")
        lines += [_line(field, stats[field]) for field in report["fields"]]
    if report["warnings"]:
        lines.append("Déséquilibre des classes :")
        lines += [f"  {w}" for w in report["warnings"]]
    if report["spo_n"]:
        spo = ", ".join(
            f"{role} {'-' if v is None else f'{v:.2f}'}" for role, v in report["spo_exact"].items()
        )
        lines.append(f"SPO exact (sur {report['spo_n']} affirmations communes) : {spo}")
    lines.append(f"Désaccords : {len(report['disagreements'])}")
    for d in report["disagreements"]:
        lines.append(f"  {d['id']:<9} {d['lang']:<9} {d['field']:<13} A={d['a']!r}  B={d['b']!r}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Accord inter-annotateurs (Lot B).")
    parser.add_argument("annotation_a", type=Path)
    parser.add_argument("annotation_b", type=Path)
    parser.add_argument("--langs", type=Path,
                        help="JSONL id -> lang (ou lang_source), pour les fichiers CSV")
    parser.add_argument("--json", type=Path, help="écrit aussi le rapport complet en JSON")
    args = parser.parse_args(argv)
    loaded = {}
    for name, path in (("A", args.annotation_a), ("B", args.annotation_b)):
        items, problems = load_annotation(path)
        if problems:
            listing = "\n".join(f"  {p}" for p in problems)
            parser.exit(2, f"Fichier {name} ({path}) invalide :\n{listing}\n")
        loaded[name] = items
    langs = load_langs(args.langs) if args.langs else None
    report = agreement(loaded["A"], loaded["B"], langs)
    print(summary(report))
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"-> {args.json}")


if __name__ == "__main__":
    main()
