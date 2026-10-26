"""Lot A2 — Lexique des marques tunisiennes : d'où il vient, et s'il se trompe sur la presse.

Usage (depuis la racine du dépôt) :
    python -m normalization.lexicon candidates   # mots fréquents dans TSAC, absents de la presse
    python -m normalization.lexicon press        # fausses alertes sur la presse en arabe standard

Données attendues dans data/raw/langid/ (non versionnées) :
    TSAC/              commentaires Facebook tunisiens (GitHub, LGPL-3.0)
    UD_Arabic-PADT/    phrases de presse en arabe standard (GitHub, CC BY-NC-SA 3.0)

Les résultats détaillés sont écrits dans data/interim/langid/ (non versionné) :
des fichiers texte s'ouvrent mieux dans l'éditeur que l'arabe dans un terminal.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

from common.schemas import Lang
from normalization.annotation import SAMPLES, load_tsac, read_annotations
from normalization.langid import find_dialect_markers, load_markers
from normalization.normalize import (
    _expand_presentation_forms,
    detect_script_by_rules,
    normalize,
    normalize_arabic,
)

PADT = Path("data/raw/langid/UD_Arabic-PADT")
OUT = Path("data/interim/langid")
MIN_TEXTS = 12  # un candidat doit apparaître dans au moins 12 commentaires TSAC
ARABIC_WORD = re.compile(r"[ء-يٮ-ۓ]+")  # lettres arabes seules


def load_padt(split: str) -> list[str]:
    """Phrases de presse : lignes '# text = ...' du fichier UD (train, dev ou test)."""
    path = PADT / f"ar_padt-ud-{split}.conllu"
    with path.open(encoding="utf-8") as handle:
        return [line[len("# text = "):].strip() for line in handle if line.startswith("# text = ")]


def folded(text: str) -> str:
    """Même forme que celle que lit la règle dans le pipeline (voir detect_language)."""
    return normalize_arabic(_expand_presentation_forms(text))


def words(text: str) -> set[str]:
    """Mots arabes distincts d'un texte, sous la forme repliée de la règle."""
    return set(ARABIC_WORD.findall(folded(text)))


def write_lines(name: str, lines: list[str]) -> Path:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def command_candidates() -> None:
    # Les échantillons annotés servent à mesurer : on ne s'en sert pas pour choisir les mots.
    annotated = {text for path in SAMPLES.values() if path.exists()
                 for _, text in read_annotations(path)}
    tsac = [t for t in load_tsac()
            if detect_script_by_rules(t) == "arabic" and t not in annotated]
    padt = load_padt("train")  # dev et test restent réservés au contrôle (commande press)

    # On compte des TEXTES, pas des occurrences : "برشا برشا برشا" ne compte qu'une fois.
    in_tsac = Counter(word for text in tsac for word in words(text))
    in_padt = Counter(word for text in padt for word in words(text))
    found = sorted(((count, word) for word, count in in_tsac.items()
                    if count >= MIN_TEXTS and in_padt[word] == 0), reverse=True)

    lexicon = {folded(marker) for marker in load_markers()}
    rows = [f"{count}\t{word}\t{'oui' if word in lexicon else ''}" for count, word in found]
    path = write_lines("tn_marker_candidates.tsv", ["textes_tsac\tmot\tdans_lexique", *rows])
    kept = sum(1 for _, word in found if word in lexicon)
    # Les autres marques sont des variantes ajoutées à la main (متاعو, ماهوش…) : trop rares
    # pour passer le seuil, mais elles doivent rester absentes de la presse.
    added = sorted(word for word in lexicon if word not in {w for _, w in found})
    added_in_press = [word for word in added if in_padt[word] > 0]
    print(f"TSAC en lettres arabes, hors échantillons annotés : {len(tsac)} textes")
    print(f"presse PADT train : {len(padt)} phrases")
    print(f"candidats (>= {MIN_TEXTS} textes TSAC, 0 phrase de presse) : {len(found)}")
    print(f"marques du lexique parmi les candidats : {kept} sur {len(lexicon)}")
    print(f"autres marques (variantes ajoutées à la main) : {len(added)},"
          f" dont {len(added_in_press)} présente(s) dans la presse")
    print(f"liste complète : {path}")


def command_press() -> None:
    lines, total_hits, total = [], 0, 0
    for split in ("dev", "test"):  # jamais utilisés pour choisir les mots
        sentences = load_padt(split)
        # Décision du pipeline complet, exactement comme pour un vrai texte.
        hits = [s for s in sentences if normalize(s).lang == Lang.TN]
        seen = Counter(m for s in sentences for m in find_dialect_markers(folded(s)))
        guilty = Counter(m for s in hits for m in find_dialect_markers(folded(s)))
        print(f"presse PADT {split} : {len(hits)} phrase(s) classée(s) tunisien"
              f" sur {len(sentences)}")
        print(f"  marques rencontrées, même sous le seuil : {sum(seen.values())}"
              f" (détail dans le fichier)")
        lines.append(f"== {split} : {len(hits)} sur {len(sentences)}")
        lines.append("marques rencontrées : " + " ".join(f"{m}:{n}" for m, n in seen.most_common()))
        lines.append("marques en cause : " + " ".join(f"{m}:{n}" for m, n in guilty.most_common()))
        lines += [f"  {s}" for s in hits]
        total_hits, total = total_hits + len(hits), total + len(sentences)
    path = write_lines("tn_markers_press_check.txt", lines)
    print(f"total : {total_hits} fausse(s) alerte(s) sur {total} phrases de presse")
    print(f"détail : {path}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # accents lisibles sous Windows
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("candidates", help="mots fréquents dans TSAC, absents de la presse")
    commands.add_parser("press", help="fausses alertes sur la presse PADT dev et test")
    args = parser.parse_args()
    if args.command == "candidates":
        command_candidates()
    else:
        command_press()


if __name__ == "__main__":
    main()
