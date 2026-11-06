"""Lot A2 — Identification de langue : tunisien en lettres arabes et en arabizi.

Deux outils, un par alphabet :
  1. lettres arabes : une règle à lexique de marques dialectales ;
  2. lettres latines sans chiffre d'arabizi : un petit modèle appris, qui
     distingue le français de l'arabizi (voir la seconde moitié du fichier).

Partie 1. La règle répond à une seule question : un texte en lettres arabes contient-il
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

import json
import math
import re
from functools import lru_cache
from pathlib import Path

_MARKERS_FILE = Path(__file__).parent / "resources" / "tn_markers.txt"

# Un mot écrit en lettres arabes (public : aussi utilisé par lexicon.py).
ARABIC_WORD = re.compile(r"[\u0621-\u064A\u066E-\u06D3]+")

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


# Affixes collés aux mots tunisiens ("ولقيتها" = "و" + "لقيت" + "ها").
# Silver (EXP-A2-012) : si un mot n'est pas dans le lexique, on retire au plus un
# préfixe et un suffixe, puis on compare de nouveau. Désactivé par défaut : le
# réglage (silver_tuning.py) décide s'il faut l'activer.
_PREFIXES = ("\u0648", "\u0641", "\u0628", "\u0644", "\u0643")  # و ف ب ل ك
_SUFFIXES = (  # du plus long au plus court : "ها" est retiré avant "ه"
    "\u0643\u0645",  # كم
    "\u0647\u0645",  # هم
    "\u0647\u0627",  # ها
    "\u0646\u0627",  # نا
    "\u0646\u064A",  # ني
    "\u0643",  # ك
    "\u0647",  # ه
)
_MIN_STEM = 3  # en dessous, des mots courts deviendraient des marques par hasard
STRIP_AFFIXES = False


def affix_variants(word: str) -> list[str]:
    """Formes du mot sans un préfixe, sans un suffixe, puis sans les deux (3 lettres ou plus)."""
    without_prefix = [word[1:] for prefix in _PREFIXES if word.startswith(prefix)]
    without_suffix = [word[: -len(s)] for s in _SUFFIXES if word.endswith(s)][:1]
    both = [w[: -len(s)] for w in without_prefix for s in _SUFFIXES if w.endswith(s)][:1]
    return [v for v in (*without_prefix, *without_suffix, *both) if len(v) >= _MIN_STEM]


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


def find_dialect_markers(
    folded_text: str,
    markers: frozenset[str] | None = None,
    strip_affixes: bool | None = None,
) -> list[str]:
    """Renvoie les formes dialectales trouvées, dans l'ordre du texte.

    Renvoyer les mots (et pas seulement vrai / faux) permet d'expliquer chaque
    décision et d'analyser les erreurs. `markers` et `strip_affixes` servent au
    réglage (silver_tuning.py) ; sans eux : lexique du dépôt et STRIP_AFFIXES.
    """
    markers = load_markers() if markers is None else markers
    strip = STRIP_AFFIXES if strip_affixes is None else strip_affixes
    words = [_key(word) for word in ARABIC_WORD.findall(folded_text)]
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
        # Silver : mot absent du lexique, mais sa forme sans affixe y est ("ولقيتها").
        elif strip:
            stem = next((v for v in affix_variants(word) if v in markers), None)
            if stem:
                found.append(stem)
    return found


def is_dialectal_arabic(
    folded_text: str,
    markers: frozenset[str] | None = None,
    strip_affixes: bool | None = None,
) -> bool:
    """Dit si le texte (lettres arabes, déjà normalisé) est dialectal."""
    n_words = len(ARABIC_WORD.findall(folded_text))
    n_found = len(find_dialect_markers(folded_text, markers, strip_affixes))
    return n_found > 0 and n_found >= math.ceil(_DIALECT_MIN_RATIO * n_words)


# ---------------------------------------------------------------------------
# Partie 2. Arabizi sans chiffres : modèle appris à n-grammes de caractères
# ---------------------------------------------------------------------------
#
# Les règles de normalize.py reconnaissent l'arabizi à ses chiffres ("3lech").
# Mais plus d'un tiers des textes en arabizi n'en contiennent aucun
# ("chnowa el jaw lyoum"). Pour ceux-là, on utilise un modèle appris hors ligne
# par `train_langid.py` (scikit-learn), puis exporté dans un petit fichier JSON :
# un poids par n-gramme de caractères. Poids positif = "tire vers l'arabizi",
# poids négatif = "tire vers le français".
#
# Ici, on ne fait que LIRE ce fichier et additionner des poids : aucune
# dépendance, donc l'API et la CI fonctionnent sans scikit-learn.

_ARABIZI_MODEL_FILE = Path(__file__).parent / "resources" / "arabizi_ngrams.json"
_NEUTRAL_WORDS_FILE = Path(__file__).parent / "resources" / "neutral_latin_words.txt"

# Toute lettre répétée ("bravooo", "merciii") : ramenée à une seule pour reconnaître un mot neutre.
_ANY_RUN = re.compile(r"(.)\1+")

# Il faut au moins 2 mots de 2 lettres ou plus pour que le modèle se prononce : sur "19h15"
# ou sur un seul mot, il n'y a pas assez d'indices.
_MIN_WORDS = 2


@lru_cache(maxsize=1)
def load_neutral_words() -> frozenset[str]:
    """Mots communs au français et à l'arabizi des commentaires, ignorés par le modèle."""
    words = set()
    with _NEUTRAL_WORDS_FILE.open(encoding="utf-8") as handle:
        for line in handle:
            word = line.strip()
            if word and not word.startswith("#"):
                words.add(word)
    return frozenset(words)


def prepare_latin(text: str) -> str:
    """Prépare un texte pour le modèle : minuscules, lettres et apostrophes seulement.

    On retire les chiffres, la ponctuation et les emojis : ils décrivent le
    genre du texte (un commentaire, un article) plus que sa langue, et le
    modèle ne doit pas s'appuyer dessus. On retire aussi les mots neutres.
    """
    kept = [char if char.isalpha() or char == "'" else " " for char in text.lower()]
    neutral = load_neutral_words()
    words = [w for w in "".join(kept).split() if _ANY_RUN.sub(r"\1", w) not in neutral]
    return " ".join(words)


def char_ngrams(prepared: str, min_n: int, max_n: int) -> list[str]:
    """Découpe chaque mot en morceaux de min_n à max_n caractères.

    Chaque mot est entouré d'espaces, pour que le modèle distingue un début
    ou une fin de mot : " ch" (début) n'est pas "ch " (fin). La même fonction
    sert à l'entraînement et ici : les deux côtés découpent donc à l'identique.
    """
    grams = []
    for word in prepared.split():
        padded = f" {word} "
        for size in range(min_n, max_n + 1):
            grams.extend(padded[start:start + size] for start in range(len(padded) - size + 1))
    return [gram for gram in grams if gram.strip()]  # on ignore les morceaux vides


@lru_cache(maxsize=1)
def load_arabizi_model() -> dict | None:
    """Charge le modèle une seule fois. Renvoie None si le fichier est absent."""
    if not _ARABIZI_MODEL_FILE.exists():
        return None
    with _ARABIZI_MODEL_FILE.open(encoding="utf-8") as handle:
        return json.load(handle)


def arabizi_score(text: str) -> float | None:
    """Score du texte : somme des poids des n-grammes présents, plus une constante.

    Chaque n-gramme compte une seule fois, qu'il apparaisse 1 ou 10 fois : c'est
    sa PRÉSENCE qui est un indice. Renvoie None quand le modèle ne peut pas se
    prononcer : fichier absent, ou trop peu de mots.
    """
    model = load_arabizi_model()
    prepared = prepare_latin(text)
    if model is None or sum(1 for w in prepared.split() if len(w) >= 2) < _MIN_WORDS:
        return None
    min_n, max_n = model["ngram_range"]
    weights = model["weights"]
    present = set(char_ngrams(prepared, min_n, max_n))
    return model["intercept"] + sum(weights.get(gram, 0.0) for gram in present)


def is_arabizi_text(text: str) -> bool:
    """Dit si un texte en lettres latines est de l'arabizi plutôt que du français."""
    score = arabizi_score(text)
    return score is not None and score >= load_arabizi_model()["threshold"]
