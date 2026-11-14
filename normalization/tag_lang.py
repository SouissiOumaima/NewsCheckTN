"""Lot A2 — Ajoute la langue et l'écriture de chaque texte d'un jeu de données (support S8).

Usage (depuis la racine du dépôt) :
    python -X utf8 -m normalization.tag_lang FICHIER --fields claim evidence
    python -X utf8 -m normalization.tag_lang FICHIER --fields text --out autre_chemin.jsonl

Pour chaque champ demandé (par exemple `claim`), ajoute `claim_lang` (fr / ar / tn / unk) et
`claim_script` (arabic / latin / arabizi / mixed…), calculés par `normalize` (Lot A2) : la même
décision que dans le pipeline. Formats : JSONL (un objet par ligne) ou CSV (avec en-tête).

Confidentialité : le fichier de sortie est écrit à côté de l'entrée (suffixe « _lang ») ; si
l'entrée est dans data/, la sortie l'est aussi. Vérifier séparément son exclusion Git :
le dossier data/ n'est pas entièrement ignoré. Le terminal n'affiche que des
comptes par langue et par écriture, jamais un texte.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from normalization.normalize import normalize


def label(value: object) -> str:
    """Valeur lisible d'une énumération (Lang.TN -> « tn ») ou d'une chaîne."""
    return str(getattr(value, "value", value))


def tag_text(text: str) -> tuple[str, str]:
    """(langue, écriture) d'un texte, selon le pipeline du Lot A2 ; texte vide -> unk."""
    if not text or not text.strip():
        return "unk", "unk"
    document = normalize(text)
    return label(document.lang), label(document.script)


def tag_rows(rows: list[dict], fields: list[str]) -> list[dict]:
    """Copie de chaque ligne, avec <champ>_lang et <champ>_script pour chaque champ demandé."""
    # Valider toutes les lignes avant d'ajouter des champs ; ne pas transformer
    # silencieusement un champ absent en texte vide ou écraser une annotation.
    if not fields or len(set(fields)) != len(fields):
        raise ValueError("La liste des champs doit être non vide et sans doublon")
    generated = {f"{field}_{suffix}" for field in fields for suffix in ("lang", "script")}
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Ligne {index} : objet attendu")
        if any(field not in row for field in fields):
            raise KeyError(f"Ligne {index} : champ demandé absent")
        if generated.intersection(row):
            raise ValueError(f"Ligne {index} : champ langue/écriture déjà présent")
        if any(row[field] is not None and not isinstance(row[field], str) for field in fields):
            raise ValueError(f"Ligne {index} : texte ou null attendu")
    tagged = []
    for row in rows:
        new = dict(row)
        for field in fields:
            new[f"{field}_lang"], new[f"{field}_script"] = tag_text(str(row.get(field) or ""))
        tagged.append(new)
    return tagged


def read_rows(path: Path) -> list[dict]:
    """Lit un JSONL ou un CSV (utf-8, avec ou sans BOM)."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        if path.suffix.lower() == ".csv":
            return list(csv.DictReader(handle))
        return [json.loads(line) for line in handle if line.strip()]


def write_rows(path: Path, rows: list[dict]) -> None:
    """Écrit au même format que l'entrée (JSONL ou CSV)."""
    # Mode exclusif : même si le fichier apparaît après le contrôle de main(),
    # son contenu n'est jamais remplacé.
    with path.open("x", encoding="utf-8", newline="") as handle:
        if path.suffix.lower() == ".csv":
            # Conserver les métadonnées facultatives présentes après la première ligne.
            columns = list(dict.fromkeys(key for row in rows for key in row))
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        else:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def summary(rows: list[dict], fields: list[str]) -> list[str]:
    """Comptes par (langue, écriture) pour chaque champ : aucune donnée textuelle."""
    lines = []
    for field in fields:
        counts = Counter((r[f"{field}_lang"], r[f"{field}_script"]) for r in rows)
        detail = " ; ".join(f"{lang}/{script} {n}" for (lang, script), n in counts.most_common())
        lines.append(f"{field} ({len(rows)} lignes) : {detail}")
    return lines


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # accents lisibles sous Windows
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path, help="fichier JSONL ou CSV")
    parser.add_argument("--fields", nargs="+", required=True, help="champs texte à étiqueter")
    parser.add_argument("--out", type=Path, help="fichier de sortie (par défaut : *_lang)")
    args = parser.parse_args()

    out = args.out or args.path.with_name(f"{args.path.stem}_lang{args.path.suffix}")
    if out.exists():  # on n'écrase jamais un fichier existant
        sys.exit(f"ARRÊT : {out} existe déjà ; supprimez-le ou choisissez --out.")
    if args.path.suffix.lower() not in {".csv", ".jsonl"}:
        parser.error("Format d'entrée attendu : .csv ou .jsonl")
    if out.suffix.lower() != args.path.suffix.lower():
        parser.error("La sortie doit conserver le format de l'entrée")
    try:
        rows = tag_rows(read_rows(args.path), args.fields)
    except (ValueError, KeyError, csv.Error):
        # Aucun contenu ni nom de champ issu d'une ligne privée dans le diagnostic CLI.
        sys.exit("ARRÊT : structure invalide ou champs langue/écriture déjà présents.")
    if not rows:
        sys.exit("ARRÊT : fichier vide.")
    write_rows(out, rows)
    for line in summary(rows, args.fields):
        print(line)
    print(f"écrit : {out}")


if __name__ == "__main__":
    main()
