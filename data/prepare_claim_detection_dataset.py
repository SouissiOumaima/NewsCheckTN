"""Convertit l'annotation Excel validée en JSONL pour le modèle Lot C."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

LABELS = frozenset({"AFFIRMATION", "OPINION", "AUTRE"})
SOURCE_METADATA = {
    "original (fr)": ("fr", "latin"),
    "original (ar)": ("ar", "arabic"),
    "original (tn-arabizi)": ("tn", "arabizi"),
    "original (tn-mixed)": ("tn", "mixed"),
    "original (tn-arabic)": ("tn", "arabic"),
}

# Les 60 lignes dont la source était simplement ``original`` ont été lues une
# à une pour compléter leur langue. Cette table est volontairement séparée des
# métadonnées source : elle constitue une correction de métadonnée traçable,
# pas une modification des labels ni des textes A1.
MANUAL_LANGUAGE_METADATA = {
    "P01": ("ar", "arabic"), "P02": ("tn", "arabizi"), "P03": ("fr", "latin"),
    "P04": ("tn", "arabizi"), "P05": ("fr", "latin"), "P06": ("tn", "mixed"),
    "P07": ("fr", "latin"), "P08": ("ar", "arabic"), "P09": ("ar", "arabic"),
    "P10": ("ar", "arabic"), "P11": ("tn", "mixed"), "P12": ("ar", "arabic"),
    "P13": ("ar", "arabic"), "P14": ("tn", "arabizi"), "P15": ("tn", "mixed"),
    "P16": ("tn", "mixed"), "P17": ("fr", "latin"), "P18": ("ar", "arabic"),
    "P19": ("ar", "arabic"), "P20": ("fr", "latin"), "P21": ("fr", "latin"),
    "P22": ("fr", "latin"), "P23": ("tn", "mixed"), "P24": ("fr", "latin"),
    "P25": ("tn", "mixed"), "P26": ("tn", "arabizi"), "P27": ("tn", "arabizi"),
    "P28": ("ar", "arabic"), "P29": ("ar", "arabic"), "P30": ("tn", "mixed"),
    "P31": ("tn", "arabizi"), "P32": ("fr", "latin"), "P33": ("fr", "latin"),
    "P34": ("tn", "mixed"), "P35": ("tn", "arabizi"), "P36": ("ar", "arabic"),
    "P37": ("tn", "arabizi"), "P38": ("fr", "latin"), "P39": ("tn", "arabizi"),
    "P40": ("fr", "latin"), "P41": ("tn", "arabizi"), "P42": ("tn", "arabizi"),
    "P43": ("tn", "mixed"), "P44": ("ar", "arabic"), "P45": ("tn", "mixed"),
    "P46": ("fr", "latin"), "P47": ("fr", "latin"), "P48": ("ar", "arabic"),
    "P49": ("tn", "arabizi"), "P50": ("fr", "latin"), "P51": ("fr", "latin"),
    "P52": ("tn", "mixed"), "P53": ("ar", "arabic"), "P54": ("tn", "mixed"),
    "P55": ("fr", "latin"), "P56": ("fr", "latin"), "P57": ("fr", "latin"),
    "P58": ("fr", "latin"), "P59": ("ar", "arabic"), "P60": ("tn", "arabizi"),
}


def metadata_from_source(source: str, row_id: str | None = None) -> tuple[str, str]:
    """Déduit les métadonnées explicitement encodées par Lot A1.

    Les ``original`` sans suffixe utilisent une revue manuelle explicite par
    identifiant; un identifiant absent reste inconnu plutôt que deviné.
    """
    explicit = SOURCE_METADATA.get(source.strip().lower())
    if explicit:
        return explicit
    return MANUAL_LANGUAGE_METADATA.get(row_id or "", ("unk", "unknown"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    from openpyxl import load_workbook

    book = load_workbook(args.input, read_only=True, data_only=True)
    sheet = book.active
    rows = sheet.iter_rows(values_only=True)
    headers = {str(value).strip().lower(): index for index, value in enumerate(next(rows)) if value}
    required = {"id", "texte", "label", "modalite", "source"}
    missing = required - set(headers)
    if missing:
        raise ValueError(f"Colonnes manquantes : {sorted(missing)}")

    exported = []
    for row in rows:
        if not any(value is not None for value in row):
            continue
        label = str(row[headers["label"]] or "").strip().upper()
        if label not in LABELS:
            raise ValueError(f"Label invalide pour {row[headers['id']]} : {label!r}")
        source = str(row[headers["source"]] or "").strip()
        row_id = str(row[headers["id"]]).strip()
        lang, script = metadata_from_source(source, row_id)
        exported.append(
            {
                "id": row_id,
                "text": str(row[headers["texte"]]).strip(),
                "label": label,
                "modalite": str(row[headers["modalite"]]).strip(),
                "source": source,
                "lang": lang,
                "script": script,
            }
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in exported), encoding="utf-8")
    print(f"{len(exported)} lignes écrites dans {args.output}")


if __name__ == "__main__":
    main()
