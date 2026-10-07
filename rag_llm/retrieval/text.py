"""Lot D — Prétraitement du texte pour la recherche de preuves.

Normalisation volontairement « agressive » (ة → ه, ى → ي, alef et hamzas unifiés, accents
français supprimés) : elle augmente les correspondances entre requête et preuves.
Elle est propre au Lot D et ne remplace PAS `normalization.normalize` (Lot A2), dont la
normalisation plus légère sert à l'analyse linguistique du Lot B.

TODO(Lot D): brancher la translittération arabizi du Lot A2 quand elle sera disponible.
"""

from __future__ import annotations

import re
import unicodedata

_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_TATWEEL = "\u0640"
_AR_PREFIXES = ("وال", "بال", "كال", "فال", "لل", "ال")
_TOKEN = re.compile(r"\w+")

_STOPWORDS_FR = {
    "le", "la", "les", "un", "une", "des", "de", "du", "et", "en", "au", "aux", "que", "qui",
    "est", "sont", "ce", "cette", "ces", "se", "sur", "pour", "par", "dans", "il", "elle", "ils",
    "ont", "pas", "ne", "son", "sa", "ses", "leur", "leurs", "plus", "avec", "entre", "quelle",
    "quel",
}
_STOPWORDS_AR = {
    "في", "من", "علي", "الي", "عن", "ان", "هذا", "هذه", "ذلك", "التي", "الذي", "مع", "او",
    "ثم", "قد", "لا", "ما", "كان", "خلال", "بين",
}
STOPWORDS = frozenset(_STOPWORDS_FR | _STOPWORDS_AR)


def normalize_for_retrieval(text: str) -> str:
    """Minuscules, chiffres arabes → latins, diacritiques/accents/hamzas supprimés."""
    text = text.translate(_ARABIC_DIGITS).replace(_TATWEEL, "")
    # NFKD + suppression des marques combinantes : accents (é → e), harakat, hamzas (أ → ا).
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("ى", "ي").replace("ة", "ه").replace("ٱ", "ا")
    return text.lower()


def _strip_arabic_prefix(token: str) -> str:
    for prefix in _AR_PREFIXES:
        if token.startswith(prefix) and len(token) - len(prefix) >= 2:
            return token[len(prefix):]
    return token


def tokenize(text: str) -> list[str]:
    """Tokens de recherche : normalisés, article arabe retiré, mots vides supprimés."""
    tokens = [t for t in _TOKEN.findall(normalize_for_retrieval(text)) if t not in STOPWORDS]
    tokens = [_strip_arabic_prefix(t) for t in tokens]
    return [t for t in tokens if len(t) > 1]
