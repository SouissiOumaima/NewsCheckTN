"""Lot A2 — Échantillons annotés à la main : tirage, copie vierge, comptage, kappa.

Usage (depuis la racine du dépôt) :
    python -m normalization.annotation sample arabic         # échantillon en lettres arabes
    python -m normalization.annotation sample latin          # en lettres latines sans chiffre
    python -m normalization.annotation sample latin --check  # le tirage redonne-t-il le fichier ?
    python -m normalization.annotation blank FICHIER         # copie sans étiquettes (annotateur 2)
    python -m normalization.annotation count FICHIER         # nombre de lignes par étiquette
    python -m normalization.annotation kappa FICHIER_1 FICHIER_2

Format des fichiers (voir docs/lot-a2_guide_annotation.md) : une ligne par texte,
l'étiquette, une tabulation, puis le texte. "?" = pas encore annoté.

Les corpus bruts restent dans data/raw/ et les échantillons dans data/interim/ :
ni les uns ni les autres ne sont versionnés. Le script n'écrase jamais un fichier.
"""

from __future__ import annotations

import argparse
import random
import sys
from collections import Counter
from pathlib import Path

from normalization.normalize import (
    _ARABIC_PRESENTATION,
    detect_script_by_rules,
    normalize,
)

TSAC = Path("data/raw/langid/TSAC")
SAMPLES = {
    "arabic": Path("data/interim/langid/tsac_arabic_sample.tsv"),
    "latin": Path("data/interim/langid/tsac_latin_sample.tsv"),
}
SEED = 13  # graine des deux tirages : même graine, même échantillon
SIZE = 100  # textes par échantillon
MIN_WORDS = 3  # les textes plus courts ne permettent pas de décider


# ---------------------------------------------------------------------------
# Lecture et écriture des fichiers d'annotation
# ---------------------------------------------------------------------------


def read_annotations(path: Path) -> list[tuple[str, str]]:
    """Lit un fichier d'annotation : liste de (étiquette, texte)."""
    rows = []
    # utf-8-sig : accepte un fichier enregistré avec une marque d'ordre d'octets (BOM).
    with path.open(encoding="utf-8-sig") as handle:
        for line in handle:
            if "\t" in line:
                label, text = line.rstrip("\r\n").split("\t", 1)
                rows.append((label.strip().lower(), text))
    return rows


def write_annotations(path: Path, rows: list[tuple[str, str]]) -> None:
    """Écrit (étiquette, texte) ligne par ligne ; refuse d'écraser un fichier existant."""
    if path.exists():
        sys.exit(f"ARRÊT : {path} existe déjà, je ne l'écrase pas (annotations perdues sinon)")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for label, text in rows:
            handle.write(f"{label}\t{text}\n")


# ---------------------------------------------------------------------------
# Tirage
# ---------------------------------------------------------------------------


def load_tsac() -> list[str]:
    """Tous les commentaires TSAC, sans doublon, dans l'ordre des fichiers."""
    texts = []
    for name in ("train_pos.txt", "train_neg.txt", "test_pos.txt", "test_neg.txt"):
        with (TSAC / name).open(encoding="utf-8-sig", errors="replace") as handle:
            texts += [line.strip() for line in handle]
    # dict.fromkeys retire les doublons en gardant l'ordre d'origine.
    return list(dict.fromkeys(text for text in texts if text))


def candidates(texts: list[str], script: str) -> list[str]:
    """Textes qui peuvent entrer dans l'échantillon d'un alphabet donné.

    - "arabic" : texte brut en lettres arabes ;
    - "latin" : texte normalisé en lettres latines SANS chiffre d'arabizi, c'est-à-dire
      ce que les règles classent "français", à tort ou à raison.
    Règles seules (pas de modèle appris) : le tirage ne change pas quand le modèle change.

    Une graine fixe ne suffit pas : si la liste de candidats change d'un seul texte,
    le mélange change entièrement. Or les tirages du 2026-10-07 ont été faits avant que
    le code compte les lettres arabes "déjà dessinées" (anciens codes Unicode, comme
    "ﻻ"). On les ignore donc ici, comme à l'époque, pour retrouver les mêmes échantillons
    (17 textes de TSAC seraient sinon ajoutés aux candidats en lettres arabes).
    """
    pool = []
    for text in texts:
        if len(text.split()) < MIN_WORDS or "\t" in text:
            continue
        # Lettres arabes : texte brut, sans les lettres "dessinées" (voir ci-dessus).
        # Lettres latines : texte normalisé, comme dans le pipeline.
        arabic = script == "arabic"
        seen = _ARABIC_PRESENTATION.sub(" ", text) if arabic else normalize(text).text
        if detect_script_by_rules(seen) == script:
            pool.append(text)
    return pool


def draw_sample(texts: list[str], script: str) -> list[str]:
    """Mélange les candidats avec la graine fixe et garde les SIZE premiers."""
    pool = candidates(texts, script)
    random.Random(SEED).shuffle(pool)
    return pool[:SIZE]


# ---------------------------------------------------------------------------
# Accord entre annotateurs
# ---------------------------------------------------------------------------


def cohen_kappa(first: list[str], second: list[str]) -> tuple[float, float, float]:
    """Accord observé, accord attendu par hasard et kappa de Cohen.

    Kappa = (observé - hasard) / (1 - hasard) : 1 = accord parfait, 0 = pas mieux
    que si chacun avait tiré ses étiquettes au sort avec ses propres proportions.
    """
    if len(first) != len(second) or not first:
        raise ValueError("il faut deux listes d'étiquettes non vides et de même longueur")
    total = len(first)
    observed = sum(a == b for a, b in zip(first, second, strict=True)) / total
    share_1, share_2 = Counter(first), Counter(second)
    expected = sum(share_1[label] / total * share_2[label] / total for label in share_1)
    kappa = 1.0 if expected == 1 else (observed - expected) / (1 - expected)
    return observed, expected, kappa


# ---------------------------------------------------------------------------
# Commandes
# ---------------------------------------------------------------------------


def command_sample(script: str, check: bool) -> None:
    sample = draw_sample(load_tsac(), script)
    path = SAMPLES[script]
    if not check:
        write_annotations(path, [("?", text) for text in sample])
        print(f"échantillon écrit : {len(sample)} lignes dans {path}")
        return
    # --check : on compare les TEXTES (pas les étiquettes) au fichier déjà annoté.
    existing = [text for _, text in read_annotations(path)]
    same = sum(a == b for a, b in zip(existing, sample, strict=False))
    print(f"{path} : {same} ligne(s) identique(s) sur {len(existing)} au tirage refait")
    if same == len(existing) == len(sample):
        print("tirage reproductible : identique, ligne par ligne")
    else:
        sys.exit("tirage NON reproductible avec le code actuel")


def command_blank(path: Path) -> None:
    target = path.with_name(path.stem + "_annotateur2" + path.suffix)
    rows = read_annotations(path)
    # On garde le texte et on remet "?" : l'annotateur 2 ne doit pas voir les étiquettes.
    write_annotations(target, [("?", text) for _, text in rows])
    print(f"{len(rows)} lignes écrites dans {target}, toutes avec l'étiquette '?'")


def command_count(path: Path) -> None:
    counts = Counter(label for label, _ in read_annotations(path))
    total = sum(counts.values())
    for label, count in counts.most_common():
        print(f"  {label:3} {count:4}  ({100 * count / total:.0f} %)")
    print(f"  total {total}")


def command_kappa(path_1: Path, path_2: Path) -> None:
    first, second = read_annotations(path_1), read_annotations(path_2)
    if len(first) != len(second):
        sys.exit(f"ARRÊT : {len(first)} lignes d'un côté, {len(second)} de l'autre")
    pairs_of_rows = list(zip(first, second, strict=True))
    # .split() des deux côtés : tolère un éditeur qui aurait changé les espaces.
    changed = [n for n, (a, b) in enumerate(pairs_of_rows, 1) if a[1].split() != b[1].split()]
    if changed:
        sys.exit(f"ARRÊT : le texte diffère aux lignes {changed[:10]} (fichier modifié ?)")
    missing = [n for n, (a, b) in enumerate(pairs_of_rows, 1) if "?" in (a[0], b[0])]
    if missing:
        sys.exit(f"ARRÊT : lignes pas encore annotées ('?') : {missing[:15]}")

    labels_1, labels_2 = [a for a, _ in first], [b for b, _ in second]
    labels = sorted(set(labels_1) | set(labels_2))
    pairs = Counter(zip(labels_1, labels_2, strict=True))
    print(f"{len(first)} lignes comparées")
    print("tableau croisé (lignes = annotateur 1, colonnes = annotateur 2)")
    print("       " + "".join(f"{label:>5}" for label in labels))
    for row in labels:
        print(f"  {row:>3}  " + "".join(f"{pairs[(row, col)]:>5}" for col in labels))
    observed, expected, kappa = cohen_kappa(labels_1, labels_2)
    print(f"accord observé : {observed:.2f} | attendu par hasard : {expected:.2f}"
          f" | kappa : {kappa:.2f}")
    both = zip(labels_1, labels_2, strict=True)
    disagreements = [f"l.{n} {a}/{b}" for n, (a, b) in enumerate(both, 1) if a != b]
    print(f"{len(disagreements)} désaccord(s) : " + ", ".join(disagreements))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # accents et arabe lisibles sous Windows
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    sample = commands.add_parser("sample", help="tire un échantillon TSAC à annoter")
    sample.add_argument("script", choices=sorted(SAMPLES))
    sample.add_argument("--check", action="store_true", help="compare au fichier existant")
    blank = commands.add_parser("blank", help="copie vierge pour un second annotateur")
    blank.add_argument("path", type=Path)
    count = commands.add_parser("count", help="lignes par étiquette")
    count.add_argument("path", type=Path)
    kappa = commands.add_parser("kappa", help="accord entre deux annotateurs")
    kappa.add_argument("first", type=Path)
    kappa.add_argument("second", type=Path)
    args = parser.parse_args()

    if args.command == "sample":
        command_sample(args.script, args.check)
    elif args.command == "blank":
        command_blank(args.path)
    elif args.command == "count":
        command_count(args.path)
    else:
        command_kappa(args.first, args.second)


if __name__ == "__main__":
    main()
