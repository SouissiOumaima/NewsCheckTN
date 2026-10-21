"""Réduit X-FACT à l'arabe et au français (fichier `xfact_ar_fr.tsv`).

Les fichiers X-FACT sont multilingues : avec `--delete-originals`, les TSV d'origine sont
supprimés une fois filtrés, pour ne garder que les langues utiles.

Usage :
    python -I filter_xfact.py --xfact-dir <dossier des TSV X-FACT> [--delete-originals]
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

SPLITS = ("train.all.tsv", "dev.all.tsv", "test.all.tsv", "ood.tsv", "zeroshot.tsv")
LANGS = ("ar", "fr")

csv.field_size_limit(10**9)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--xfact-dir", type=Path, required=True)
    parser.add_argument("--delete-originals", action="store_true")
    args = parser.parse_args()

    out_path = args.xfact_dir / "xfact_ar_fr.tsv"
    kept = 0
    with out_path.open("w", encoding="utf-8", newline="") as out:
        writer = None
        for name in SPLITS:
            with (args.xfact_dir / name).open(encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
                for row in reader:
                    if row["language"] not in LANGS:
                        continue
                    if writer is None:
                        writer = csv.DictWriter(
                            out, fieldnames=[*reader.fieldnames, "split"], delimiter="\t",
                            quoting=csv.QUOTE_NONE, escapechar="\\",
                        )
                        writer.writeheader()
                    writer.writerow({**row, "split": name})
                    kept += 1
    if args.delete_originals:
        for name in SPLITS:
            (args.xfact_dir / name).unlink()
    print(f"{kept} lignes {'/'.join(LANGS)} -> {out_path.name}"
          + (" ; fichiers d'origine supprimés" if args.delete_originals else ""))


if __name__ == "__main__":
    main()
