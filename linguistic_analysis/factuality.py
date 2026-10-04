"""Lot B — Distinction affirmation factuelle / opinion.

`classify_factuality(sentence)` combine des lexiques (`resources/opinion_<langue>.txt`) et, si
l'arbre de dépendances est disponible, des patrons syntaxiques. Elle renvoie
`(is_opinion, confiance, indices)`, où `is_opinion` signifie « phrase non factuelle » :
opinion, question ou souhait. Les indices sont préfixés (`opinion:`, `question:`, `souhait:`,
`fait:`) pour l'analyse d'erreurs.

Score : chaque catégorie d'indice compte une seule fois, avec le poids ci-dessous.

    Indices d'opinion (score o)                      Indices factuels (score f)
    expression d'opinion (« à mon avis », نحس)  0.6  nombre                       0.3
    verbe d'opinion à la 1re personne           0.6  pourcentage                  0.2
      + complétive (ccomp, arbre requis)        0.2  date (année, nom de mois)    0.2
    évaluatif en position d'attribut            0.5  entité nommée (PROPN)        0.2
    évaluatif ailleurs                          0.3  verbe au passé (arbre requis) 0.2
    intensifieur / superlatif sans nombre       0.3
    question (?, ؟, « est-ce que », هل)         1.0
    souhait / impératif                         0.8

Décision : `is_opinion = o >= 0.5 and o > f`. Confiance : `min(1, 0.5 + |o - f| / 2)`.
Une phrase avec un verbe d'opinion mais des données précises (« je pense que le chômage a atteint
16 % en 2023 ») reste donc factuelle : elle contient une affirmation vérifiable.

Lexiques utilisés selon la langue de la phrase : FR → fr ; AR → ar + tn (le Lot A2 étiquette le
tunisien en lettres arabes `ar`) ; TN → tn + fr (code-switching).
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from common.schemas import Lang
from linguistic_analysis.preprocessing import Sentence, Token, fold

RESOURCES = Path(__file__).resolve().parent / "resources"

WEIGHTS = {
    "expression": 0.6,
    "verbe_1re_personne": 0.6,
    "complétive": 0.2,
    "évaluatif_attribut": 0.5,
    "évaluatif": 0.3,
    "intensifieur": 0.3,
    "question": 1.0,
    "souhait": 0.8,
    "nombre": 0.3,
    "pourcentage": 0.2,
    "date": 0.2,
    "entité": 0.2,
    "passé": 0.2,
}
OPINION_THRESHOLD = 0.5

LEXICONS_BY_LANG = {
    Lang.FR: ("fr",),
    Lang.AR: ("ar", "tn"),
    Lang.TN: ("tn", "fr"),
    Lang.UNKNOWN: ("fr", "ar", "tn"),
}
FIRST_PERSON = {"je", "j'", "nous", "on", "moi"}
COPULAS = {"est", "sont", "était", "etait", "étaient", "c'est", "هو", "هي", "راهو", "راهي"}
PERCENT_WORDS = ("pour cent", "pourcent", "بالمئه", "بالمائه", "في المئه", "fel miya", "fil miya")
_YEAR = re.compile(r"^(1[89]|20)\d{2}$")
_NUMBER = re.compile(r"^[\d٠-٩]+(?:[.,][\d٠-٩]+)*$")
_ARABIC = re.compile(r"[؀-ۿ]")


def _norm(text: str) -> str:
    return fold(text).replace("’", "'")


@lru_cache(maxsize=None)
def load_lexicon(lang: str) -> dict[str, tuple[str, ...]]:
    """Charge `opinion_<lang>.txt` : section -> entrées repliées."""
    sections: dict[str, list[str]] = {}
    current = None
    path = RESOURCES / f"opinion_{lang}.txt"
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            sections.setdefault(current, [])
        elif current is None:
            raise ValueError(f"{path.name} : entrée {line!r} hors section")
        else:
            sections[current].append(_norm(line))
    return {name: tuple(entries) for name, entries in sections.items()}


def _entries(lang: Lang, section: str) -> list[str]:
    out: list[str] = []
    for code in LEXICONS_BY_LANG.get(lang, LEXICONS_BY_LANG[Lang.UNKNOWN]):
        out.extend(load_lexicon(code).get(section, ()))
    return out


def _pattern(entry: str, anchored: bool = False) -> re.Pattern[str]:
    """Entrée entourée de frontières de mot ; préfixes arabes و / ف tolérés."""
    prefix = "(?:[وف])?" if _ARABIC.search(entry) else ""
    start = r"^\s*" if anchored else r"(?<![\w'])"
    end = "" if entry.endswith("'") else r"(?!\w)"
    return re.compile(start + prefix + re.escape(entry) + end)


def _find(text: str, entries: list[str], anchored: bool = False) -> str | None:
    for entry in entries:
        if _pattern(entry, anchored).search(text):
            return entry
    return None


def _has_tree(sentence: Sentence) -> bool:
    return sentence.parser != "rules"


def _children(sentence: Sentence, tok: Token) -> list[Token]:
    return [t for t in sentence.tokens if t.head == tok.i]


def _previous(sentence: Sentence, tok: Token, n: int = 2) -> set[str]:
    return {_norm(t.text) for t in sentence.tokens[max(0, tok.i - n) : tok.i]}


def _content_tokens(sentence: Sentence) -> list[Token]:
    return [t for t in sentence.tokens if t.upos not in ("PUNCT", "SYM")]


def _opinion_cues(sentence: Sentence, text: str) -> list[tuple[str, str]]:
    """Liste de (catégorie de poids, indice)."""
    lang, cues = sentence.lang, []

    if text.rstrip().endswith(("?", "؟")):
        cues.append(("question", "question:?"))
    elif marker := _find(text, _entries(lang, "questions"), anchored=True):
        cues.append(("question", f"question:{marker}"))

    if marker := _find(text, _entries(lang, "souhaits")):
        cues.append(("souhait", f"souhait:{marker}"))
    elif _has_tree(sentence) and any(
        t.deprel == "root" and t.feats.get("Mood") == "Imp" for t in sentence.tokens
    ):
        cues.append(("souhait", "souhait:impératif"))

    if marker := _find(text, _entries(lang, "expressions")):
        cues.append(("expression", f"opinion:{marker}"))

    verbs = set(_entries(lang, "verbes"))
    for tok in sentence.tokens:
        forms = {_norm(tok.text), _norm(tok.lemma)}
        if forms & verbs and (
            tok.feats.get("Person") == "1" or _previous(sentence, tok) & FIRST_PERSON
        ):
            cues.append(("verbe_1re_personne", f"opinion:1re_personne:{_norm(tok.text)}"))
            if _has_tree(sentence) and any(c.deprel == "ccomp" for c in _children(sentence, tok)):
                cues.append(("complétive", "opinion:complétive"))
            break

    evaluatives = set(_entries(lang, "evaluatifs"))
    content = _content_tokens(sentence)
    best = None
    for tok in content:
        if _norm(tok.text) not in evaluatives and _norm(tok.lemma) not in evaluatives:
            continue
        if _has_tree(sentence):
            attribute = any(c.deprel == "cop" for c in _children(sentence, tok))
        else:
            attribute = bool(_previous(sentence, tok) & COPULAS)
        attribute = attribute or tok is content[-1]
        category = "évaluatif_attribut" if attribute else "évaluatif"
        if best is None or WEIGHTS[category] > WEIGHTS[best[0]]:
            best = (category, f"opinion:{category.replace('_', ':')}:{_norm(tok.text)}")
    if best is None and (marker := _find(text, [e for e in evaluatives if " " in e])):
        best = ("évaluatif", f"opinion:évaluatif:{marker}")
    if best:
        cues.append(best)
    return cues


def _factual_cues(sentence: Sentence, text: str) -> list[tuple[str, str]]:
    cues = []
    numbers = [t for t in sentence.tokens if t.upos == "NUM" or _NUMBER.match(t.text)]
    if numbers:
        cues.append(("nombre", "fait:nombre"))
    if any(t.text in ("%", "٪") for t in sentence.tokens) or any(w in text for w in PERCENT_WORDS):
        cues.append(("pourcentage", "fait:pourcentage"))
    if any(_YEAR.match(t.text) for t in numbers) or _find(text, _entries(sentence.lang, "dates")):
        cues.append(("date", "fait:date"))
    if _has_tree(sentence):
        entity = any(t.upos == "PROPN" for t in sentence.tokens)
        past = any(
            t.upos in ("VERB", "AUX")
            and (t.feats.get("Tense") == "Past" or t.feats.get("Aspect") == "Perf")
            for t in sentence.tokens
        )
    else:
        # Sans parseur : mot inconnu du lexique, en majuscule, hors début de phrase.
        entity = any(t.i > 0 and t.upos == "X" and t.text[:1].isupper() for t in sentence.tokens)
        past = False
    if entity:
        cues.append(("entité", "fait:entité"))
    if past:
        cues.append(("passé", "fait:passé"))
    return cues


def classify_factuality(sentence: Sentence) -> tuple[bool, float, list[str]]:
    """Retourne (is_opinion, confiance dans [0, 1], indices déclencheurs)."""
    text = _norm(sentence.text)
    opinion = _opinion_cues(sentence, text)
    factual = _factual_cues(sentence, text)
    has_number = any(category == "nombre" for category, _ in factual)
    intensifier = _find(text, _entries(sentence.lang, "intensifieurs"))
    if intensifier and not has_number:
        opinion.append(("intensifieur", f"opinion:intensifieur:{intensifier}"))

    o = sum(WEIGHTS[category] for category, _ in opinion)
    f = sum(WEIGHTS[category] for category, _ in factual)
    is_opinion = o >= OPINION_THRESHOLD and o > f
    confidence = min(1.0, 0.5 + abs(o - f) / 2)
    return is_opinion, round(confidence, 3), [cue for _, cue in opinion + factual]
