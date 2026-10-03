"""Lot B — Prétraitement linguistique : tokenisation, POS, dépendances.

Les pipelines sont chargés à la demande et mis en cache :
- FR : spaCy `fr_core_news_md` ;
- AR : Stanza `ar` (tokenize, mwt, pos, lemma, depparse) ;
- TN, ou bibliothèque/modèle absent : `None`, et le module bascule sur les règles.

Aucun import de spaCy ou de Stanza n'a lieu à l'import de ce module, pour que
l'API et la CI restent légères.
"""

from __future__ import annotations

import importlib.util
from functools import lru_cache
from typing import Any

from common.schemas import Lang

SPACY_FR_MODEL = "fr_core_news_md"
STANZA_AR_PROCESSORS = "tokenize,mwt,pos,lemma,depparse"


def _is_installed(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


@lru_cache(maxsize=None)
def _load_spacy_fr() -> Any | None:
    if not (_is_installed("spacy") and _is_installed(SPACY_FR_MODEL)):
        return None
    import spacy

    return spacy.load(SPACY_FR_MODEL)


@lru_cache(maxsize=None)
def _load_stanza_ar() -> Any | None:
    if not _is_installed("stanza"):
        return None
    import stanza

    try:
        return stanza.Pipeline(
            "ar", processors=STANZA_AR_PROCESSORS, verbose=False, download_method=None
        )
    except Exception:  # modèle non téléchargé ou incompatible
        return None


def get_parser(lang: Lang) -> Any | None:
    """Retourne le pipeline adapté à la langue, ou None si indisponible (repli règles)."""
    if lang == Lang.FR:
        return _load_spacy_fr()
    if lang == Lang.AR:
        return _load_stanza_ar()
    return None  # TN / inconnu : pas de parseur mature, règles uniquement


def parser_name(lang: Lang) -> str:
    """Nom du parseur effectivement utilisé pour une langue."""
    if get_parser(lang) is None:
        return "rules"
    return "spacy-fr" if lang == Lang.FR else "stanza-ar"


# TODO(Lot B): représentation commune Token / Sentence et analyze(doc) -> list[Sentence].
