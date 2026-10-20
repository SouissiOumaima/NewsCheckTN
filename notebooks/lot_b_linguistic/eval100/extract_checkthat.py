"""Extrait les seuls TSV (texte + labels) d'une archive CheckThat! 2021 (tâche 1A).

Les JSON de l'archive (objets tweets complets, profils des comptes) ne sont jamais extraits.
Avec `--delete-archive`, l'archive est supprimée après extraction.

Usage :
    python -I extract_checkthat.py --archive <CT21-AR-Train-T1-v2.zip> --out-dir <dossier>
"""

from __future__ import annotations

import argparse
import csv
import zipfile
from collections import Counter
from pathlib import Path

csv.field_size_limit(10**9)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--delete-archive", action="store_true")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.archive) as z:
        for name in z.namelist():
            if name.endswith(".tsv") and "/" not in name and ".." not in name:
                (args.out_dir / name).write_bytes(z.read(name))
    if args.delete_archive:
        args.archive.unlink()
    for tsv in sorted(args.out_dir.glob("*.tsv")):
        with tsv.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
        print(tsv.name, len(rows), "lignes ; claim", dict(Counter(r.get("claim") for r in rows)))


if __name__ == "__main__":
    main()
