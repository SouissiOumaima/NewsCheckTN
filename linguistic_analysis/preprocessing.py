"""Lot B — Prétraitement linguistique : tokenisation, POS, dépendances.

Les pipelines sont chargés à la demande et mis en cache :
- FR : spaCy `fr_core_news_md` ;
- AR : Stanza `ar` (tokenize, mwt, pos, lemma, depparse) ;
- TN, ou bibliothèque/modèle absent : `None`, et le module bascule sur les règles.

Aucun import de spaCy ou de Stanza n'a lieu à l'import de ce module, pour que
l'API et la CI restent légères.

Représentation commune (indépendante du parseur) :
- `Token.i` est l'indice du token dans sa phrase (à partir de 0) ;
- `Token.head` est l'indice du gouverneur dans la phrase, `-1` pour la racine ou en
  l'absence d'arbre (mode règles) ;
- `Token.start` / `Token.end` sont des offsets de caractères dans `Document.text`.
  Pour un mot syntaxique issu d'un token multi-mots (Stanza `mwt`, ex. وقال → و + قال),
  ce sont les offsets du token d'origine : plusieurs mots partagent alors le même span.
"""

from __future__ import annotations

import importlib.util
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from common.schemas import Document, Lang

SPACY_FR_MODEL = "fr_core_news_md"
STANZA_AR_PROCESSORS = "tokenize,mwt,pos,lemma,depparse"
TN_LEXICON = Path(__file__).resolve().parent / "resources" / "tn_lexicon.json"

_SENT_SPLIT = re.compile(r"(?<=[.!?؟])\s+")


@dataclass
class Token:
    i: int
    text: str
    lemma: str
    upos: str
    feats: dict[str, str] = field(default_factory=dict)
    head: int = -1
    deprel: str = "dep"
    start: int = 0
    end: int = 0


@dataclass
class Sentence:
    text: str
    start: int
    end: int
    tokens: list[Token]
    lang: Lang
    parser: str  # "spacy-fr" | "stanza-ar" | "rules"


# ---------------------------------------------------------------------------
# Chargement des parseurs
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Segmentation et détection de langue par phrase
# ---------------------------------------------------------------------------


def split_sentences(text: str) -> list[tuple[str, tuple[int, int]]]:
    """Découpe en phrases avec leurs positions (début, fin) dans le texte."""
    sentences, start = [], 0
    for part in _SENT_SPLIT.split(text):
        idx = text.find(part, start)
        if part.strip():
            sentences.append((part.strip(), (idx, idx + len(part))))
        start = idx + len(part)
    return sentences


_ARABIC_LETTER = re.compile(r"[ء-يٱ-ۓ]")
_LATIN_LETTER = re.compile(r"[A-Za-zÀ-ÿ]")
# Chiffre collé à des lettres latines : 9al, 3and, 7koma, as3ar...
_ARABIZI_WORD = re.compile(r"\b[A-Za-z]*[235679][A-Za-z]+\b|\b[A-Za-z]+[235679]\b")


def detect_sentence_lang(text: str) -> Lang:
    """Langue d'une phrase (hypothèse locale au Lot B, utilisée si doc.script == "mixed")."""
    n_ar = len(_ARABIC_LETTER.findall(text))
    n_lat = len(_LATIN_LETTER.findall(text))
    if n_ar == 0 and n_lat == 0:
        return Lang.UNKNOWN
    if n_ar >= n_lat:
        return Lang.AR
    return Lang.TN if _ARABIZI_WORD.search(text) else Lang.FR


# ---------------------------------------------------------------------------
# Analyse par règles (tunisien, repli)
# ---------------------------------------------------------------------------

_RULE_TOKEN = re.compile(
    r"(?P<num>\d+(?:[.,]\d+)*(?![A-Za-zÀ-ÿ]))"
    r"|(?P<elision>\b(?:[cdjlmnst]|qu)['’])"
    r"|(?P<word>[A-Za-zÀ-ÿ0-9]+(?:-[A-Za-zÀ-ÿ]+)*)"
    r"|(?P<arabic>[ء-يٱ-ۓ٠-٩]+)"
    r"|(?P<punct>[^\s])",
    re.IGNORECASE,
)
_ARABIC_DIACRITICS = re.compile(r"[ً-ْـ]")


def _fold(text: str) -> str:
    """Clé de recherche lexicale : minuscules, arabe sans diacritiques, alef/ya/ta unifiés."""
    text = _ARABIC_DIACRITICS.sub("", text.lower())
    text = re.sub("[إأآ]", "ا", text)
    return text.replace("ى", "ي").replace("ة", "ه")


@lru_cache(maxsize=1)
def _tn_lexicon() -> dict[str, str]:
    """Lexique forme -> UPOS (les clés sont repliées avec `_fold`)."""
    data = json.loads(TN_LEXICON.read_text(encoding="utf-8"))
    lexicon: dict[str, str] = {}
    for upos, forms in data["upos"].items():
        for form in forms:
            key = _fold(form)
            if key in lexicon and lexicon[key] != upos:
                raise ValueError(f"{TN_LEXICON.name} : {form!r} à la fois {lexicon[key]} et {upos}")
            lexicon[key] = upos
    return lexicon


def _rule_upos(kind: str, text: str) -> str:
    if kind == "num":
        return "NUM"
    if kind == "punct":
        return "SYM" if text in "%٪$€" else "PUNCT"
    key = _fold(text)
    if kind == "elision":
        return _tn_lexicon().get(key, "DET")
    return _tn_lexicon().get(key, "X")


def _analyze_rules(text: str, offset: int) -> list[Token]:
    tokens = []
    for m in _RULE_TOKEN.finditer(text):
        kind = m.lastgroup or "punct"
        tokens.append(
            Token(
                i=len(tokens),
                text=m.group(0),
                lemma=_fold(m.group(0)),
                upos=_rule_upos(kind, m.group(0)),
                start=offset + m.start(),
                end=offset + m.end(),
            )
        )
    return tokens


# ---------------------------------------------------------------------------
# Adaptateurs spaCy (FR) et Stanza (AR)
# ---------------------------------------------------------------------------


def _analyze_spacy(nlp: Any, text: str, offset: int) -> list[Token]:
    tokens = []
    for tok in nlp(text):
        if tok.is_space:
            continue
        is_root = tok.head.i == tok.i
        tokens.append(
            Token(
                i=tok.i,
                text=tok.text,
                lemma=tok.lemma_,
                upos=tok.pos_,
                feats=tok.morph.to_dict(),
                head=-1 if is_root else tok.head.i,
                deprel="root" if is_root else tok.dep_,
                start=offset + tok.idx,
                end=offset + tok.idx + len(tok.text),
            )
        )
    return _reindex(tokens)


def _parse_feats(feats: str | None) -> dict[str, str]:
    if not feats:
        return {}
    return dict(item.split("=", 1) for item in feats.split("|") if "=" in item)


def _analyze_stanza(nlp: Any, text: str, offset: int) -> list[Token]:
    """Les phrases Stanza éventuelles sont fusionnées : la segmentation reste celle du module."""
    tokens: list[Token] = []
    for sent in nlp(text).sentences:
        base = len(tokens)  # indice du premier mot de cette phrase Stanza
        for tok in sent.tokens:
            for word in tok.words:  # plusieurs mots si token multi-mots (mwt)
                tokens.append(
                    Token(
                        i=base + word.id - 1,
                        text=word.text,
                        lemma=word.lemma or word.text,
                        upos=word.upos or "X",
                        feats=_parse_feats(word.feats),
                        head=-1 if word.head == 0 else base + word.head - 1,
                        deprel=word.deprel or "dep",
                        start=offset + tok.start_char,
                        end=offset + tok.end_char,
                    )
                )
    return tokens


def _reindex(tokens: list[Token]) -> list[Token]:
    """Renumérote après suppression d'espaces (spaCy) en conservant les liens de dépendance."""
    mapping = {t.i: new for new, t in enumerate(tokens)}
    for t in tokens:
        t.i = mapping[t.i]
        t.head = mapping.get(t.head, -1) if t.head != -1 else -1
    return tokens


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------


def analyze(doc: Document) -> list[Sentence]:
    """Segmente et analyse un document ; chaque phrase est traitée par le parseur de sa langue."""
    sentences = []
    for text, (start, _) in split_sentences(doc.text):
        start = doc.text.index(text, start)
        lang = detect_sentence_lang(text) if doc.script == "mixed" else doc.lang
        nlp = get_parser(lang)
        if nlp is not None and lang == Lang.FR:
            tokens, parser = _analyze_spacy(nlp, text, start), "spacy-fr"
        elif nlp is not None and lang == Lang.AR:
            tokens, parser = _analyze_stanza(nlp, text, start), "stanza-ar"
        else:
            tokens, parser = _analyze_rules(text, start), "rules"
        sentences.append(
            Sentence(
                text=text,
                start=start,
                end=start + len(text),
                tokens=tokens,
                lang=lang,
                parser=parser,
            )
        )
    return sentences
