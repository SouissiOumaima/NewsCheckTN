"""Lot B — Extraction de triplets Sujet–Prédicat–Objet.

Avec arbre UD (spaCy FR, Stanza AR) :
- prédicat = racine verbale avec auxiliaires, réfléchis et négation (« n'a pas baissé ») ;
- sujet = sous-arbre `nsubj` / `nsubj:pass` ;
- objet = `obj`, sinon `obl*` (préposition incluse), sinon `iobj`, sinon `xcomp` / `ccomp` ;
- copule (« Le chômage est de 16 % ») : prédicat = `cop`, objet = attribut ;
- passif : rôles de surface conservés (sujet = `nsubj:pass`, objet = complément d'agent
  s'il existe), `voice = "passive"` ;
- phrase nominale arabe (racine nominale ou adjectivale sans copule) : prédicat implicite « est »,
  seul élément qui n'est pas extrait du texte (`predicate_span = None`) ;
- verbe de parole (`resources/speech_verbs.txt`) : la complétive devient l'objet, `reported = True`.

Sans arbre (tunisien, ou parseur absent) : patron `[groupe nominal] [verbe du lexique] [reste]`.
Verbe de parole suivi d'un complémenteur (elli, que, إن…) : `reported = True`, complémenteur
exclu de l'objet. En français, un auxiliaire suivi d'un participe est regroupé avec la négation
(« n'a pas baissé ») et « été » marque le passif. Verbe arabe en tête de phrase
(ordre verbe–sujet–objet) : sujet = mot suivant.

Tous les éléments (sauf le prédicat implicite) sont des extraits exacts de `Document.text`,
sans ponctuation de bord. Confiance = plafond du parseur × complétude :
plafond spaCy 0.9, Stanza 0.8 (bruit dû à la normalisation amont, point L7), règles 0.5 ;
complétude 1.0 si S, P et O sont trouvés, 0.8 avec deux éléments, 0.6 avec le prédicat seul.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from linguistic_analysis.preprocessing import Sentence, Token, fold

RESOURCES = Path(__file__).resolve().parent / "resources"

CONFIDENCE_CAP = {"spacy-fr": 0.9, "stanza-ar": 0.8, "rules": 0.5}
COMPLETENESS = {3: 1.0, 2: 0.8, 1: 0.6}
IMPLICIT_PREDICATE = "est"

_PUNCT = ("PUNCT", "SYM")
_NOMINAL = ("NOUN", "PROPN", "ADJ", "NUM", "PRON")
_NEGATION = {"ne", "n'", "pas", "plus", "jamais", "لا", "لم", "لن", "ما", "ليس"}
# Auxiliaires français (mode règles) et terminaisons de participe passé.
_FR_AUX = {
    "a", "ont", "avait", "avaient", "est", "sont", "était", "étaient", "été", "sera", "seront"
}
_PARTICIPLE = re.compile(r"(é|ée|és|ées|i|is|ie|ies|it|its|u|us|ue|ues|t|ts)$")
_COMPLEMENTIZERS = {"que", "qu'", "elli", "illi", "eli", "اللي", "الي", "ان", "انه", "بان"}


@dataclass
class SPO:
    subject: str | None = None
    predicate: str | None = None
    obj: str | None = None
    subject_span: tuple[int, int] | None = None
    obj_span: tuple[int, int] | None = None
    predicate_span: tuple[int, int] | None = None
    voice: str = "active"  # "active" | "passive"
    reported: bool = False
    confidence: float = 0.0


@lru_cache(maxsize=1)
def speech_verbs() -> frozenset[str]:
    lines = (RESOURCES / "speech_verbs.txt").read_text(encoding="utf-8").splitlines()
    entries = (line.split("#", 1)[0].strip() for line in lines)
    return frozenset(fold(entry) for entry in entries if entry)


# ---------------------------------------------------------------------------
# Outils : sous-arbres et spans
# ---------------------------------------------------------------------------


def _children(sentence: Sentence, tok: Token) -> list[Token]:
    return [t for t in sentence.tokens if t.head == tok.i and t.i != tok.i]


def _subtree(sentence: Sentence, tok: Token) -> list[Token]:
    out, stack = [], [tok]
    while stack:
        current = stack.pop()
        out.append(current)
        stack.extend(_children(sentence, current))
    return out


def _span(tokens: list[Token]) -> tuple[int, int] | None:
    """Span continu couvrant les tokens, ponctuation de bord retirée (« % », « € » conservés)."""
    ordered = sorted(tokens, key=lambda t: (t.start, t.i))
    while ordered and ordered[0].upos == "PUNCT":
        ordered.pop(0)
    while ordered and ordered[-1].upos == "PUNCT":
        ordered.pop()
    if not ordered:
        return None
    return ordered[0].start, max(t.end for t in ordered)


def _text(sentence: Sentence, span: tuple[int, int] | None) -> str | None:
    if span is None:
        return None
    return sentence.text[span[0] - sentence.start : span[1] - sentence.start] or None


def _overlaps(a: tuple[int, int] | None, b: tuple[int, int] | None) -> bool:
    return a is not None and b is not None and a[0] < b[1] and b[0] < a[1]


def _confidence(parser: str, *elements: object) -> float:
    found = sum(e is not None for e in elements)
    return round(CONFIDENCE_CAP.get(parser, 0.5) * COMPLETENESS.get(found, 0.0), 3)


# ---------------------------------------------------------------------------
# Avec arbre de dépendances
# ---------------------------------------------------------------------------


def _predicate_tokens(sentence: Sentence, head: Token, core: Token) -> list[Token]:
    """`core` (verbe ou copule) + auxiliaires, réfléchis et négation rattachés à `head`."""
    tokens = [core]
    for child in _children(sentence, head):
        if child is core:
            continue
        negation = child.feats.get("Polarity") == "Neg" or fold(child.text) in _NEGATION
        if child.deprel.startswith(("aux", "expl")) or (child.deprel == "advmod" and negation):
            tokens.append(child)
    return tokens


def _pick_object(sentence: Sentence, root: Token, passive: bool, reported: bool) -> Token | None:
    children = _children(sentence, root)
    order = [
        lambda d: d == "ccomp" and reported,
        lambda d: d == "obl:agent" and passive,
        lambda d: d == "obj",
        lambda d: d.startswith("obl") and d != "obl:agent",
        lambda d: d == "iobj",
        lambda d: d in ("xcomp", "ccomp"),
        lambda d: d == "obl:agent",
    ]
    for matches in order:
        for child in children:
            if matches(child.deprel):
                return child
    return None


def _extract_with_tree(sentence: Sentence) -> SPO | None:
    roots = [t for t in sentence.tokens if t.deprel == "root"]
    if not roots:
        return None
    root = next((t for t in roots if t.upos in ("VERB", "AUX")), roots[0])
    children = _children(sentence, root)
    subj = next((c for c in children if c.deprel.startswith("nsubj")), None)
    subject_tokens = _subtree(sentence, subj) if subj else []
    subject_span = _span(subject_tokens) if subj else None
    passive = root.feats.get("Voice") == "Pass" or any(c.deprel.endswith(":pass") for c in children)
    cop = next((c for c in children if c.deprel == "cop"), None)

    if root.upos in ("VERB", "AUX") and cop is None:
        predicate_tokens = _predicate_tokens(sentence, root, root)
        reported = fold(root.lemma) in speech_verbs() or fold(root.text) in speech_verbs()
        reported = reported and any(c.deprel == "ccomp" for c in children)
        obj_head = _pick_object(sentence, root, passive, reported)
        obj_tokens = _subtree(sentence, obj_head) if obj_head else []
        if reported and obj_head is not None:  # complémenteur exclu, comme en mode règles
            obj_tokens = [
                t for t in obj_tokens if not (t.deprel == "mark" and t.head == obj_head.i)
            ]
        obj_span = _span(obj_tokens) if obj_tokens else None
        predicate_span = _span(predicate_tokens)
        predicate = _text(sentence, predicate_span)
    elif cop is not None or root.upos in _NOMINAL:
        # Copule ou phrase nominale : l'attribut est la racine et ce qu'elle gouverne.
        reported = False
        excluded = {t.i for t in subject_tokens}
        if cop is not None:
            predicate_tokens = _predicate_tokens(sentence, root, cop)
            excluded |= {t.i for t in predicate_tokens}
            predicate_span = _span(predicate_tokens)
            predicate = _text(sentence, predicate_span)
        elif subj is not None:
            predicate_span, predicate = None, IMPLICIT_PREDICATE
        else:
            return None
        attribute = [t for t in _subtree(sentence, root) if t.i not in excluded]
        obj_span = _span(attribute)
        if _overlaps(obj_span, subject_span):  # attribut de part et d'autre du sujet
            after = [t for t in attribute if subject_span and t.start >= subject_span[1]]
            obj_span = _span(after)
    else:
        return None

    obj = _text(sentence, obj_span)
    subject = _text(sentence, subject_span)
    return SPO(
        subject=subject,
        predicate=predicate,
        obj=obj,
        subject_span=subject_span,
        obj_span=obj_span,
        predicate_span=predicate_span,
        voice="passive" if passive else "active",
        reported=reported,
        confidence=_confidence(sentence.parser, subject, predicate, obj),
    )


# ---------------------------------------------------------------------------
# Sans arbre (règles positionnelles)
# ---------------------------------------------------------------------------


def _is_verb(tok: Token) -> bool:
    return tok.upos == "VERB" or fold(tok.text) in speech_verbs()


def _extract_with_rules(sentence: Sentence) -> SPO | None:
    tokens = sentence.tokens
    verb_index = next((k for k, t in enumerate(tokens) if _is_verb(t)), None)
    if verb_index is None:
        return None
    start = verb_index
    # Négation française antéposée : « n'a », « ne sont ».
    while start > 0 and fold(tokens[start - 1].text) in _NEGATION:
        start -= 1
    predicate_tokens = tokens[start : verb_index + 1]
    after = verb_index + 1
    # Français : auxiliaire (+ négation) + participe (« a atteint », « n'a pas baissé »).
    while after < len(tokens) and fold(predicate_tokens[-1].text) in _FR_AUX:
        k = after
        while k < len(tokens) and fold(tokens[k].text) in _NEGATION:
            k += 1
        if not (
            k < len(tokens)
            and tokens[k].upos in ("X", "VERB")
            and _PARTICIPLE.search(fold(tokens[k].text))
        ):
            break
        predicate_tokens.extend(tokens[after : k + 1])
        after = k + 1
    passive = any(fold(t.text) == "été" for t in predicate_tokens[:-1])

    speech = any(fold(t.text) in speech_verbs() for t in predicate_tokens)
    subject_tokens = tokens[:start]
    # Arabe verbe–sujet–objet : verbe en tête ; sujet = mots jusqu'au complémenteur pour un
    # verbe de parole (« قال وزير الفلاحة إن … »), sinon le mot suivant.
    if start == 0 and re.search(r"[؀-ۿ]", tokens[verb_index].text):
        window = range(after, min(after + 4, len(tokens)))
        comp = next((k for k in window if fold(tokens[k].text) in _COMPLEMENTIZERS), None)
        nxt = tokens[after] if after < len(tokens) else None
        if speech and comp is not None and comp > after:
            subject_tokens = tokens[after:comp]
            after = comp
        elif nxt is not None and nxt.upos not in (*_PUNCT, "ADP", "SCONJ", "NUM"):
            subject_tokens = [nxt]
            after += 1
    # Discours rapporté : verbe de parole suivi d'un complémenteur (exclu de l'objet).
    reported = speech and after < len(tokens) and fold(tokens[after].text) in _COMPLEMENTIZERS
    if reported:
        after += 1

    subject_span = _span(subject_tokens)
    predicate_span = _span(predicate_tokens)
    obj_span = _span(tokens[after:])
    subject, predicate, obj = (
        _text(sentence, subject_span),
        _text(sentence, predicate_span),
        _text(sentence, obj_span),
    )
    return SPO(
        subject=subject,
        predicate=predicate,
        obj=obj,
        subject_span=subject_span,
        obj_span=obj_span,
        predicate_span=predicate_span,
        voice="passive" if passive else "active",
        reported=reported,
        confidence=_confidence("rules", subject, predicate, obj),
    )


def extract_spo(sentence: Sentence) -> SPO | None:
    """Extrait le triplet principal d'une phrase, ou None si aucun prédicat n'est identifiable."""
    if sentence.parser == "rules":
        return _extract_with_rules(sentence)
    return _extract_with_tree(sentence)
