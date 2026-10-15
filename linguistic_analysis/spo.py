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

Discours rapporté (`reported = True`) : verbe de parole + complétive, ou incise placée après une
virgule (« Les prix vont baisser, a déclaré le ministre »). Source (`source`) : « selon X » → X ;
incise → son groupe nominal (retiré de l'objet) ; verbe de parole + complétive → le sujet du verbe.

Compléments circonstanciels (`resources/adjuncts.json`) : la source (« selon X », « حسب X »),
le temps (« en 2024 », « depuis janvier », « يوم الجمعة ») et le lieu (« à Sfax », « fi Gafsa »)
ne font pas partie de l'objet. Ils sont rangés dans `source`, `time` et `location`. Avec arbre,
un complément de ce type n'est jamais choisi comme objet ; dans les deux modes, un complément
placé en fin d'objet en est retiré. La complétive d'un verbe de parole reste entière.
Une source en tête de phrase suivie d'une virgule est retirée du sujet (mode règles).

Sans arbre (tunisien, ou parseur absent) : patron `[groupe nominal] [verbe du lexique] [reste]`
(lexique : `resources/verbs.json` et formes générées, voir `preprocessing.verb_lexicon` ; un mot
précédé d'un déterminant n'est pas pris pour un verbe ; modal + infinitif forment le prédicat).
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

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from linguistic_analysis.preprocessing import (
    Sentence,
    Token,
    fold,
    is_intransitive_verb,
    verb_lexicon,
)

RESOURCES = Path(__file__).resolve().parent / "resources"

CONFIDENCE_CAP = {"spacy-fr": 0.9, "stanza-ar": 0.8, "rules": 0.5}
COMPLETENESS = {3: 1.0, 2: 0.8, 1: 0.6}
IMPLICIT_PREDICATE = "est"

_PUNCT = ("PUNCT", "SYM")
_NOMINAL = ("NOUN", "PROPN", "ADJ", "NUM", "PRON")
_NEGATION = {"ne", "n'", "pas", "plus", "jamais", "لا", "لم", "لن", "ما", "ليس", "ma"}
# Auxiliaires français (mode règles) et terminaisons de participe passé.
_FR_AUX = {
    "a", "ont", "avait", "avaient", "aura", "auront", "aurait", "auraient",
    "est", "sont", "était", "étaient", "été", "sera", "seront", "serait", "seraient",
}
_INFINITIVE = re.compile(r"(er|ir|re|oir)$")
_PARTICIPLE = re.compile(r"(é|ée|és|ées|i|is|ie|ies|it|its|u|us|ue|ues|t|ts)$")
_COMPLEMENTIZERS = {"que", "qu'", "elli", "illi", "eli", "اللي", "الي", "ان", "انه", "بان"}
# Prépositions de l'arabe standard (limites du sujet quand le verbe est en tête).
_AR_PREPOSITIONS = {
    "عن", "حتي", "بين", "ضد", "نحو", "منذ", "خلال", "حول", "عبر", "لدي", "عند", "بعد", "قبل",
    "امام", "دون", "ضمن", "الي", "علي", "في", "من", "مع", "مقابل", "بسبب", "حسب", "وفق",
}
# Préposition collée suivie d'une quantité (« بنسبه 10 », « بقيمه 5 مليون »).
_AR_ATTACHED_PREPOSITIONS = {"بنسبه", "بقيمه", "بحوالي", "بنحو", "بمعدل", "بمبلغ", "بعدد"}
_SUBJECT_MAX = 6


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
    source: str | None = None  # « selon X », incise ou sujet du verbe de parole
    time: str | None = None  # complément de temps, préposition comprise
    location: str | None = None  # complément de lieu, préposition comprise


@lru_cache(maxsize=1)
def speech_verbs() -> frozenset[str]:
    lines = (RESOURCES / "speech_verbs.txt").read_text(encoding="utf-8").splitlines()
    entries = (line.split("#", 1)[0].strip() for line in lines)
    return frozenset(fold(entry) for entry in entries if entry)


# ---------------------------------------------------------------------------
# Compléments circonstanciels : source, temps, lieu
# ---------------------------------------------------------------------------

_YEAR = re.compile(r"^(1[89]|20)\d\d$")


def _key(word: str) -> str:
    """Forme repliée, article arabe « ال » retiré (« الشهر » → « شهر »)."""
    return re.sub(r"^ال(?=..)", "", fold(word))


def _words(tokens: list[Token]) -> list[str]:
    """Mots repliés hors ponctuation (« % » gardé). Les mots d'un même token d'origine
    (Stanza `mwt`, ex. « الجمعه » découpé en الجمع + ه) sont recollés."""
    words: list[str] = []
    previous = None
    for t in sorted(tokens, key=lambda t: (t.start, t.i)):
        if t.upos == "PUNCT":
            continue
        if previous is not None and (t.start, t.end) == previous and t.end > t.start:
            words[-1] = _key(words[-1] + t.text)
        else:
            words.append(_key(t.text))
        previous = (t.start, t.end)
    return words


@lru_cache(maxsize=1)
def adjunct_lexicon() -> dict[str, frozenset[tuple[str, ...]]]:
    """Listes de `resources/adjuncts.json`, chaque entrée découpée en mots repliés."""
    data = json.loads((RESOURCES / "adjuncts.json").read_text(encoding="utf-8"))
    return {
        name: frozenset(tuple(_key(w) for w in entry.split()) for entry in entries)
        for name, entries in data.items()
        if not name.startswith("_")
    }


def _prefix_len(words: list[str], entries: frozenset[tuple[str, ...]]) -> int:
    """Nombre de mots de la plus longue entrée qui commence `words` (0 si aucune)."""
    return max((len(e) for e in entries if tuple(words[: len(e)]) == e), default=0)


def adjunct_kind(tokens: list[Token]) -> str | None:
    """« source », « time » ou « location » si `tokens` forment en entier un tel complément.

    Source : marqueur en tête (selon, حسب…). Temps : préposition de durée (depuis, منذ…) suivie
    d'au moins un mot, ou, après d'éventuels mots-outils (en, la, في, el…), un nom de temps en tête
    (janvier, semaine, يوم…) suivi uniquement de mots de temps, de nombres ou de mots-outils, ou une
    année précédée d'une préposition (« en 2024 »). Lieu : préposition de lieu puis un lieu connu.
    Un nombre en tête (« 100 jours ») n'est pas un complément de temps : c'est souvent l'objet.
    """
    words = _words(tokens)
    if not words:
        return None
    lex = adjunct_lexicon()
    if _prefix_len(words, lex["source_markers"]):
        return "source"
    time_prep = _prefix_len(words, lex["time_preps"])
    if time_prep and len(words) > time_prep:
        return "time"
    k = 0
    while k < len(words) and (n := _prefix_len(words[k:], lex["lead_words"])):
        k += n
    lead, content = words[:k], words[k:]
    if not content or len(content) > 3:
        return None
    if _prefix_len(content, lex["time_nouns"]):
        allowed = lex["time_nouns"] | lex["time_modifiers"] | lex["lead_words"] | lex["time_links"]
        k = 0
        while k < len(content) and (n := _prefix_len(content[k:], allowed) or content[k].isdigit()):
            k += n
        if k == len(content):
            return "time"
    year_prep = any((w,) in lex["year_preps"] for w in lead)
    if content == [content[0]] and _YEAR.match(content[0]) and year_prep:
        return "time"
    place = _prefix_len(content, lex["places"])
    if place == len(content) and any((w,) in lex["location_preps"] for w in lead):
        return "location"
    return None


def split_trailing_adjuncts(tokens: list[Token]) -> tuple[list[Token], dict[str, list[Token]]]:
    """Retire de la fin de `tokens` les compléments de source, de temps ou de lieu.

    Retourne (tokens restants, {type: tokens du complément}). Pour chaque complément, on cherche
    le plus court suffixe reconnu, puis on l'étend vers la gauche tant qu'il reste du même type
    (« semaine dernière » → « la semaine dernière »). Un suffixe précédé d'un nombre n'est pas
    coupé (« 100 jours » reste entier). Deux compléments du même type sont réunis. Si l'objet
    entier est un complément, la liste restante est vide.
    """
    kept = sorted(tokens, key=lambda t: (t.start, t.i))
    found: dict[str, list[Token]] = {}
    while kept:
        end = len(kept)
        while end and kept[end - 1].upos == "PUNCT":
            end -= 1
        cut = next(
            ((k, kind) for k in range(end - 1, -1, -1) if (kind := adjunct_kind(kept[k:end]))),
            None,
        )
        if cut is None:
            break
        k, kind = cut
        while k > 0 and adjunct_kind(kept[k - 1 : end]) == kind:
            k -= 1
        if k > 0 and (kept[k - 1].upos == "NUM" or kept[k - 1].text.isdigit()):
            break
        found[kind] = kept[k:end] + found.get(kind, [])
        kept = kept[:k]
    return kept, found


def decompose_adjuncts(tokens: list[Token]) -> dict[str, list[Token]] | None:
    """Découpe `tokens` en compléments successifs (« à Sousse en 2023 » → lieu + temps).

    Retourne None si une partie n'est pas un complément de source, de temps ou de lieu.
    """
    kept, found = split_trailing_adjuncts(tokens)
    if _words(kept):
        kind = adjunct_kind(kept)
        if kind is None:
            return None
        found[kind] = kept + found.get(kind, [])
    return found


def _leading_source(tokens: list[Token]) -> tuple[list[Token], int]:
    """Source en tête suivie d'une virgule (« Selon l'INS, … ») : (tokens, indice après virgule)."""
    comma = next((k for k, t in enumerate(tokens) if t.text in (",", "،")), None)
    if comma is None or adjunct_kind(tokens[:comma]) != "source":
        return [], 0
    return tokens[:comma], comma + 1


_RESUMPTIVE = {"به", "بها", "عنه", "عنها", "فيه", "فيها"}


def _adjunct_text(sentence: Sentence, kind: str, tokens: list[Token]) -> str | None:
    """Texte du complément. Pour une source, le marqueur (selon, حسب…) est retiré, ainsi qu'un
    verbe de parole et son pronom de rappel (« حسب ما افاد به المعهد » → « المعهد »)."""
    tokens = [t for t in sorted(tokens, key=lambda t: (t.start, t.i)) if t.upos not in _PUNCT]
    if kind == "source":
        words = [_key(t.text) for t in tokens]
        tokens = tokens[_prefix_len(words, adjunct_lexicon()["source_markers"]) :]
        if len(tokens) > 1 and (tokens[0].upos == "VERB" or _is_speech_form(tokens[0].text)):
            tokens = tokens[1:]
            # Mot graphique d'origine : Stanza découpe « به » en ب + ه.
            while len(tokens) > 1 and fold(_surface(sentence, tokens[0])) in _RESUMPTIVE:
                tokens = [t for t in tokens if (t.start, t.end) != (tokens[0].start, tokens[0].end)]
    return _text(sentence, _span(tokens)) if tokens else None


def _surface(sentence: Sentence, tok: Token) -> str:
    """Texte du token graphique d'origine (identique à `tok.text` hors mots multi-tokens)."""
    return sentence.text[tok.start - sentence.start : tok.end - sentence.start]


def _is_speech_form(word: str) -> bool:
    """Verbe de parole : forme ou lemme de la liste, ou présent en -e (« affirme », « déclare »)."""
    key = fold(word)
    return key in speech_verbs() or key + "r" in speech_verbs()


def _split_incise(tokens: list[Token]) -> tuple[list[Token], list[Token]]:
    """Incise finale après une virgule (« …, a déclaré le ministre », « …, affirme l'INS ») :
    (tokens avant la virgule, groupe nominal de l'incise), ou (tokens, []) s'il n'y en a pas.
    L'incise = auxiliaire facultatif + verbe de parole + groupe nominal sans verbe ni complémenteur.
    """
    ordered = sorted(tokens, key=lambda t: (t.start, t.i))
    end = len(ordered)
    while end and ordered[end - 1].upos == "PUNCT":
        end -= 1
    comma = max((k for k in range(end) if ordered[k].text in (",", "،")), default=None)
    if comma is None:
        return tokens, []
    k = comma + 1
    if k < end and fold(ordered[k].text) in _FR_AUX:
        k += 1
    if not (k < end and _is_speech_form(ordered[k].text)):
        return tokens, []
    phrase = ordered[k + 1 : end]
    if not phrase or any(
        t.upos in ("VERB", "SCONJ") or fold(t.text) in _COMPLEMENTIZERS for t in phrase
    ):
        return tokens, []
    return ordered[:comma], phrase


def _adjunct_fields(sentence: Sentence, found: dict[str, list[Token]]) -> dict[str, str | None]:
    return {kind: _adjunct_text(sentence, kind, found[kind]) for kind in found}


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


def _is_adjunct(sentence: Sentence, tok: Token) -> bool:
    """Complément de source / temps / lieu, ou déterminant isolé (« هذا » de « الشهر هذا »)."""
    tokens = _subtree(sentence, tok)
    return decompose_adjuncts(tokens) is not None or all(t.upos in ("DET", *_PUNCT) for t in tokens)


def _root_adjuncts(sentence: Sentence, root: Token) -> dict[str, list[Token]]:
    """Compléments de source / temps / lieu rattachés directement au prédicat."""
    found: dict[str, list[Token]] = {}
    for child in _children(sentence, root):
        if child.deprel.startswith(("nsubj", "ccomp", "punct", "aux", "cop", "mark")):
            continue
        for kind, tokens in (decompose_adjuncts(_subtree(sentence, child)) or {}).items():
            found.setdefault(kind, tokens)
    return found


def _trim_object(tokens: list[Token], found: dict[str, list[Token]]) -> list[Token]:
    """Retire les compléments en fin d'objet et les ajoute à `found` (sans écraser)."""
    kept, tails = split_trailing_adjuncts(tokens)
    for kind, adjunct in tails.items():
        found.setdefault(kind, adjunct)
    return kept


def _tree_incise(sentence: Sentence, root: Token) -> list[Token]:
    """Incise rattachée au prédicat (parataxis, verbe de parole, après une virgule) : son groupe
    nominal (sujet inversé, ou objet quand le parseur analyse mal l'inversion)."""
    for child in _children(sentence, root):
        if not child.deprel.startswith("parataxis") or child.start < root.start:
            continue
        if not (_is_speech_form(child.lemma) or _is_speech_form(child.text)):
            continue
        first = min(_subtree(sentence, child), key=lambda t: (t.start, t.i))
        if first.text not in (",", "،"):  # virgule rattachée à l'incise, ou juste avant elle
            before = [t for t in sentence.tokens if t.end <= first.start]
            if not before or before[-1].text not in (",", "،"):
                continue
        nominal = next(
            (c for c in _children(sentence, child) if c.deprel.startswith(("nsubj", "obj"))), None
        )
        if nominal is not None:
            return _subtree(sentence, nominal)
    return []


def _pick_object(sentence: Sentence, root: Token, passive: bool, reported: bool) -> Token | None:
    children = [
        c for c in _children(sentence, root)
        if c.deprel in ("ccomp", "obl:agent") or not _is_adjunct(sentence, c)
    ]
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
    adjuncts = _root_adjuncts(sentence, root)

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
        elif obj_tokens:  # la complétive rapportée reste entière
            obj_tokens = _trim_object(obj_tokens, adjuncts)
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
        excluded |= {t.i for tokens in adjuncts.values() for t in tokens}
        attribute = [t for t in _subtree(sentence, root) if t.i not in excluded]
        attribute = _trim_object(attribute, adjuncts)
        obj_span = _span(attribute)
        if _overlaps(obj_span, subject_span):  # attribut de part et d'autre du sujet
            after = [t for t in attribute if subject_span and t.start >= subject_span[1]]
            obj_span = _span(after)
    else:
        return None

    incise = _tree_incise(sentence, root)
    if incise:
        adjuncts.setdefault("source", incise)
    elif reported and subject_tokens:  # verbe de parole + complétive : le locuteur est la source
        adjuncts.setdefault("source", subject_tokens)
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
        reported=reported or bool(incise),
        confidence=_confidence(sentence.parser, subject, predicate, obj),
        **_adjunct_fields(sentence, adjuncts),
    )


# ---------------------------------------------------------------------------
# Sans arbre (règles positionnelles)
# ---------------------------------------------------------------------------


def _is_verb(tokens: list[Token], k: int) -> bool:
    """Verbe du lexique, sauf juste après un déterminant (« la baisse », « La visite »)."""
    tok = tokens[k]
    if k > 0 and tokens[k - 1].upos == "DET":
        return False
    return tok.upos == "VERB" or fold(tok.text) in speech_verbs()


def _subject_boundary(tokens: list[Token], k: int) -> bool:
    """Le mot `k` ne peut pas appartenir au sujet : mot-outil, nombre, verbe, ponctuation,
    préposition, ou début de compléments de temps / lieu / source qui vont jusqu'à la fin."""
    tok = tokens[k]
    if tok.upos in (*_PUNCT, "ADP", "SCONJ", "NUM", "VERB", "PART", "CCONJ"):
        return True
    key = fold(tok.text)
    if key in _AR_PREPOSITIONS or key in _COMPLEMENTIZERS or key in _AR_ATTACHED_PREPOSITIONS:
        return True
    return bool(decompose_adjuncts(tokens[k:]))


def _is_nisba(word: str) -> bool:
    """Adjectif de relation défini (« الوطنيه », « المركزي »)."""
    return word.startswith("ال") and word.endswith(("ي", "يه", "يين", "يون", "يات"))


def _vso_subject_end(tokens: list[Token], k0: int, intransitive: bool) -> int:
    """Fin (exclue) du sujet d'un verbe arabe en tête, sujet qui commence au mot `k0`.

    Verbe intransitif (« ارتفع », « تراجع ») : jusqu'à la première limite (préposition, nombre,
    complément…). Sinon, chaîne d'annexion : un nom sans article est suivi de son complément
    (« وزير الصحه », « نتائج الامتحانات ») ; après un mot défini, seuls les adjectifs de relation
    sont ajoutés (« الامتحانات الوطنيه »), pour ne pas absorber un objet défini.
    """
    end = k0
    while end < len(tokens) and end - k0 < _SUBJECT_MAX and not _subject_boundary(tokens, end):
        if end > k0 and not intransitive:
            previous, current = fold(tokens[end - 1].text), fold(tokens[end].text)
            if previous.startswith("ال") and not _is_nisba(current):
                break
        end += 1
    return end


def _extract_with_rules(sentence: Sentence) -> SPO | None:
    tokens = sentence.tokens
    verb_index = next((k for k in range(len(tokens)) if _is_verb(tokens, k)), None)
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
    # Modal + infinitif (« pourraient augmenter », « va construire ») : prédicat commun.
    modals = verb_lexicon()["modals"]
    if (
        fold(predicate_tokens[-1].text) in modals
        and after < len(tokens)
        and _INFINITIVE.search(fold(tokens[after].text))
    ):
        predicate_tokens.append(tokens[after])
        after += 1
    passive = any(fold(t.text) == "été" for t in predicate_tokens[:-1])

    speech = any(fold(t.text) in speech_verbs() for t in predicate_tokens)
    source_tokens, lead = _leading_source(tokens[:start])
    adjuncts = {"source": source_tokens} if source_tokens else {}
    subject_tokens = tokens[lead:start]
    # Arabe verbe–sujet–objet : verbe en tête (après une éventuelle source) ; sujet = mots
    # jusqu'au complémenteur pour un verbe de parole (« قال وزير الفلاحة إن … »), sinon voir
    # `_vso_subject_end`.
    if start == lead and re.search(r"[؀-ۿ]", tokens[verb_index].text):
        window = range(after, min(after + 4, len(tokens)))
        comp = next((k for k in window if fold(tokens[k].text) in _COMPLEMENTIZERS), None)
        if speech and comp is not None and comp > after:
            subject_tokens = tokens[after:comp]
            after = comp
        else:
            intransitive = is_intransitive_verb(tokens[verb_index].text)
            end = _vso_subject_end(tokens, after, intransitive)
            subject_tokens = tokens[after:end]
            after = end
    # Discours rapporté : verbe de parole suivi d'un complémenteur (exclu de l'objet).
    reported = speech and after < len(tokens) and fold(tokens[after].text) in _COMPLEMENTIZERS
    if reported:
        after += 1

    obj_tokens = tokens[after:]
    incise: list[Token] = []
    if not reported:  # la complétive rapportée reste entière
        obj_tokens, incise = _split_incise(obj_tokens)
        obj_tokens = _trim_object(obj_tokens, adjuncts)
    if incise:
        adjuncts.setdefault("source", incise)
    elif reported and subject_tokens:  # verbe de parole + complétive : le locuteur est la source
        adjuncts.setdefault("source", subject_tokens)
    reported = reported or bool(incise)
    subject_span = _span(subject_tokens)
    predicate_span = _span(predicate_tokens)
    obj_span = _span(obj_tokens)
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
        **_adjunct_fields(sentence, adjuncts),
    )


def extract_spo(sentence: Sentence) -> SPO | None:
    """Extrait le triplet principal d'une phrase, ou None si aucun prédicat n'est identifiable."""
    if sentence.parser == "rules":
        return _extract_with_rules(sentence)
    return _extract_with_tree(sentence)
