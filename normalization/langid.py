"""Lot A2 — Identification de langue : marques dialectales en lettres arabes.

Ce module répond à une seule question : un texte en lettres arabes contient-il
des formes qui ne sont pas de l'arabe standard ? Il ne lit que des mots-outils
tunisiens très fréquents ("برشا", "باش", "موش", "اللي"...), rangés dans
`resources/tn_markers.txt`, plus la négation en "ما ... ش".

C'est une règle, pas un modèle appris : elle est rapide, lisible, sans
dépendance, et sert de point de comparaison obligatoire pour tout classifieur.

Convention : les fonctions reçoivent un texte DÉJÀ passé par `normalize_arabic`
(sans diacritiques, alef / ya / ta marbuta unifiés). Le lexique est écrit sous
cette même forme, ce qu'un test vérifie.
"""

from __future__ import annotations

import math
import re
from functools import lru_cache
from pathlib import Path

_MARKERS_FILE = Path(__file__).parent / "resources" / "tn_markers.txt"

# Un mot écrit en lettres arabes.
_ARABIC_WORD = re.compile(r"[\u0621-\u064A\u066E-\u06D3]+")

# Une lettre répétée 3 fois ou plus ("ماااسط") : ramenée à une seule pour
# comparer au lexique. Deux lettres identiques sont conservées : "اللي" doit
# rester distinct de "الي", qui est le plus souvent "إلى" mal écrit.
_LONG_RUN = re.compile(r"(.)\1{2,}")

# Négation tunisienne collée : "ما" + au moins 2 lettres + "ش" en un seul mot
# ("ماعادش", "مانحبش", "مايعجبنيش").
_NEGATION_ONE_WORD = re.compile(r"\u0645\u0627.{2,}\u0634")

# Verbes d'arabe standard dont la racine finit par la lettre chin : "ما يعيش",
# "ما يناقش" sont du standard, pas une négation tunisienne.
_STANDARD_SH_VERBS = frozenset(
    {
        "\u064A\u0639\u064A\u0634",
        "\u062A\u0639\u064A\u0634",
        "\u0646\u0639\u064A\u0634",
        "\u0627\u0639\u064A\u0634",
        "\u064A\u0646\u0627\u0642\u0634",
        "\u062A\u0646\u0627\u0642\u0634",
        "\u0646\u0646\u0627\u0642\u0634",
        "\u064A\u062F\u0647\u0634",
        "\u062A\u062F\u0647\u0634",
        "\u064A\u0641\u062A\u0634",
        "\u062A\u0641\u062A\u0634",
        "\u064A\u0646\u0639\u0634",
        "\u064A\u063A\u0634",
        "\u062A\u063A\u0634",
    }
)

# Part minimale de mots dialectaux pour déclarer le texte dialectal. Un seul
# mot suffit pour un commentaire court ; pour un long article, on évite qu'UN
# mot cité ou ambigu fasse basculer tout le texte. Valeur de départ, à régler.
_DIALECT_MIN_RATIO = 0.02


def _key(word: str) -> str:
    """Forme de comparaison d'un mot : lettres étirées ramenées à une seule."""
    return _LONG_RUN.sub(r"\1", word)


@lru_cache(maxsize=1)
def load_markers() -> frozenset[str]:
    """Charge le lexique une seule fois (lru_cache garde le résultat en mémoire)."""
    markers = set()
    with _MARKERS_FILE.open(encoding="utf-8") as handle:
        for line in handle:
            word = line.strip()
            if word and not word.startswith("#"):
                markers.add(_key(word))
    return frozenset(markers)


def find_dialect_markers(folded_text: str) -> list[str]:
    """Renvoie les formes dialectales trouvées, dans l'ordre du texte.

    Renvoyer les mots (et pas seulement vrai / faux) permet d'expliquer chaque
    décision et d'analyser les erreurs.
    """
    markers = load_markers()
    words = [_key(word) for word in _ARABIC_WORD.findall(folded_text)]
    found = []
    for index, word in enumerate(words):
        previous = words[index - 1] if index else ""
        if word in markers or _NEGATION_ONE_WORD.fullmatch(word):
            found.append(word)
        # Négation en deux mots : "ما" suivi d'un mot de 4 lettres ou plus en "ش"
        # ("ما شفتش", "ما نحبش").
        elif (
            previous == "\u0645\u0627"
            and len(word) >= 4
            and word.endswith("\u0634")
            and word not in _STANDARD_SH_VERBS
        ):
            found.append("\u0645\u0627 " + word)
    return found


def is_dialectal_arabic(folded_text: str) -> bool:
    """Dit si le texte (lettres arabes, déjà normalisé) est dialectal."""
    n_words = len(_ARABIC_WORD.findall(folded_text))
    n_found = len(find_dialect_markers(folded_text))
    return n_found > 0 and n_found >= math.ceil(_DIALECT_MIN_RATIO * n_words)
