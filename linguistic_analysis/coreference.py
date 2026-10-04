"""Lot B — Résolution de coréférence par règles.

Objectif : rendre chaque phrase autonome (« Il a annoncé… » → « Le ministre a annoncé… »).
Seul le pronom sujet de la proposition principale est remplacé ; le texte d'origine et les
spans ne changent pas (`resolved_text` est une version supplémentaire).

Mentions candidates (fenêtre des 2 phrases précédentes) :
- le sujet de chaque phrase, tel qu'extrait par `spo` : groupe nominal défini (« le ministre »,
  « الوزير ») ou nom propre ; si ce sujet était lui-même un pronom résolu, c'est son antécédent
  qui sert de mention (chaînes) ;
- les noms propres (PROPN avec parseur ; sans parseur, mot inconnu du lexique à majuscule).

Pronoms résolus : FR il / elle / ils / elles (sauf « il » impersonnel), AR هو / هي / هم,
TN howa / hiya / houma / هوما. Accord genre / nombre quand l'information existe (traits du
parseur, ou déterminant le / la / les sans parseur) ; une information absente est compatible.

Règle : antécédent = sujet compatible le plus récent ; noms propres seulement si la fenêtre ne
contient aucun sujet nominal, même indéfini. Sans candidat compatible, la phrase est laissée
inchangée (mieux vaut ne pas résoudre que mal résoudre).

TODO(Lot B): pronoms affixes arabes / tunisiens (ـه، ـها، ـهم) et pronoms objets (Silver).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from linguistic_analysis import spo
from linguistic_analysis.preprocessing import Sentence, Token, fold

WINDOW = 2

# pronom replié -> (genre, nombre) ; None = non spécifié
PRONOUNS: dict[str, tuple[str | None, str | None]] = {
    "il": ("Masc", "Sing"),
    "elle": ("Fem", "Sing"),
    "ils": ("Masc", "Plur"),
    "elles": ("Fem", "Plur"),
    "هو": ("Masc", "Sing"),
    "هي": ("Fem", "Sing"),
    "هم": ("Masc", "Plur"),
    "هوما": (None, "Plur"),
    "howa": ("Masc", "Sing"),
    "houwa": ("Masc", "Sing"),
    "hiya": ("Fem", "Sing"),
    "hia": ("Fem", "Sing"),
    "houma": (None, "Plur"),
    "homa": (None, "Plur"),
}
# « il » impersonnel : il y a, il faut, il est clair que, il semble…
_IMPERSONAL = re.compile(
    r"^il\s+(?:y\s+a|faut|fallait|faudra|s'agit|semble|paraît|reste|suffit|"
    r"est\s+(?:clair|évident|possible|probable|nécessaire|important|difficile|temps))\b"
)
# Déterminants (mode règles) -> (genre, nombre)
_DETERMINERS: dict[str, tuple[str | None, str | None]] = {
    "le": ("Masc", "Sing"),
    "la": ("Fem", "Sing"),
    "l'": (None, "Sing"),
    "les": (None, "Plur"),
    "el": (None, None),
    "al": (None, None),
}
_FR_DETERMINER_START = re.compile(r"^(?:Le|La|Les|L')(?=[\s'A-Za-zÀ-ÿ])")


@dataclass
class Mention:
    text: str
    gender: str | None = None
    number: str | None = None
    is_subject: bool = True


@dataclass
class Resolution:
    resolved_text: str
    log: list[str] = field(default_factory=list)
    subject: Mention | None = None  # mention sujet de la phrase (après résolution)
    entities: list[Mention] = field(default_factory=list)
    has_nominal_subject: bool = False  # sujet non pronominal, défini ou non


def _compatible(pronoun: tuple[str | None, str | None], mention: Mention) -> bool:
    gender, number = pronoun
    return (gender is None or mention.gender is None or gender == mention.gender) and (
        number is None or mention.number is None or number == mention.number
    )


def _features(sentence: Sentence, head: Token | None, first: Token | None) -> tuple:
    """(genre, nombre) d'une mention.

    Le déterminant initial (le / la / les) est prioritaire : il est plus fiable que les traits
    du parseur pour les noms épicènes (spaCy donne « ministre » masculin même après « la »).
    """
    det = _DETERMINERS.get(fold(first.text), (None, None)) if first else (None, None)
    det_gender, det_number = det
    feats = head.feats if (head is not None and sentence.parser != "rules") else {}
    return det_gender or feats.get("Gender"), det_number or feats.get("Number")


def _is_definite_or_name(sentence: Sentence, tokens: list[Token]) -> bool:
    if not tokens:
        return False
    first = tokens[0]
    head = next((t for t in tokens if t.deprel.startswith("nsubj")), first)
    if head.upos == "PROPN":  # tête nom propre (pas un groupe indéfini qui contient un nom)
        return True
    if fold(first.text) in _DETERMINERS or fold(first.text).startswith("ال"):
        return True
    if sentence.parser != "rules":
        return any(t.feats.get("Definite") == "Def" for t in tokens)
    return first.upos == "X" and first.text[:1].isupper()


def _tokens_in(sentence: Sentence, span: tuple[int, int] | None) -> list[Token]:
    if span is None:
        return []
    return [t for t in sentence.tokens if span[0] <= t.start and t.end <= span[1]]


def _pronoun_key(tok: Token) -> str | None:
    """Pronom replié (sans préfixe arabe و / ف éventuel), ou None."""
    key = fold(tok.text)
    if key in PRONOUNS:
        return key
    if len(key) > 1 and key[0] in "وف" and key[1:] in PRONOUNS:
        return key[1:]
    return None


def _subject_pronoun(sentence: Sentence, triple: spo.SPO | None) -> Token | None:
    """Pronom sujet de la proposition principale, ou None."""
    candidates: list[Token] = []
    if triple is not None and triple.subject_span is not None:
        candidates = _tokens_in(sentence, triple.subject_span)
        if len({(t.start, t.end) for t in candidates}) == 1:
            # Un seul token graphique, éventuellement découpé en mots (Stanza : وهو → و + هو).
            candidates = [t for t in candidates if _pronoun_key(t) is not None][:1]
        else:
            candidates = []
    if not candidates and sentence.tokens:  # sans sujet reconnu : pronom en tête de phrase
        first = sentence.tokens[0]
        same_token = [t for t in sentence.tokens if (t.start, t.end) == (first.start, first.end)]
        candidates = [t for t in same_token if _pronoun_key(t) is not None][:1] or [first]
    tok = candidates[0] if candidates else None
    if tok is None or _pronoun_key(tok) is None:
        return None
    if sentence.parser != "rules" and tok.deprel.startswith("expl"):
        return None
    rest = fold(sentence.text[tok.start - sentence.start :])
    if _IMPERSONAL.match(rest):
        return None
    return tok


def _subject_mention(sentence: Sentence, triple: spo.SPO | None) -> Mention | None:
    if triple is None or triple.subject is None:
        return None
    tokens = _tokens_in(sentence, triple.subject_span)
    if not _is_definite_or_name(sentence, tokens):
        return None
    head = next((t for t in tokens if t.deprel.startswith("nsubj")), None)
    gender, number = _features(sentence, head, tokens[0])
    return Mention(triple.subject, gender, number, is_subject=True)


def _entity_mentions(sentence: Sentence, exclude: tuple[int, int] | None) -> list[Mention]:
    """Noms propres (suites de tokens), hors span du sujet."""
    mentions, run = [], []

    def is_name(t: Token) -> bool:
        if exclude and exclude[0] <= t.start < exclude[1]:
            return False
        if sentence.parser != "rules":
            return t.upos == "PROPN"
        return t.i > 0 and t.upos == "X" and t.text[:1].isupper()

    for tok in [*sentence.tokens, None]:
        if tok is not None and is_name(tok):
            run.append(tok)
            continue
        if run:
            span = (run[0].start, run[-1].end)
            text = sentence.text[span[0] - sentence.start : span[1] - sentence.start]
            gender, number = _features(sentence, run[0], None)
            mentions.append(Mention(text, gender, number, is_subject=False))
            run = []
    return mentions


def _replace(sentence: Sentence, pronoun: Token, mention: Mention) -> str:
    text = mention.text
    at_start = pronoun.start == sentence.start
    if at_start:
        text = text[:1].upper() + text[1:]
    elif _FR_DETERMINER_START.match(text):
        text = text[:1].lower() + text[1:]
    a, b = pronoun.start - sentence.start, pronoun.end - sentence.start
    # Préfixe collé (« وهو ») : seul le pronom est remplacé, la conjonction est conservée.
    surface, key = sentence.text[a:b], _pronoun_key(pronoun) or ""
    if fold(surface) != key and fold(surface).endswith(key):
        a = b - len(key)
    return sentence.text[:a] + text + sentence.text[b:]


def resolve_with_log(sentences: list[Sentence]) -> list[Resolution]:
    """Version autonome de chaque phrase et journal des résolutions (« il → Le ministre »)."""
    results: list[Resolution] = []
    for index, sentence in enumerate(sentences):
        triple = spo.extract_spo(sentence)
        pronoun = _subject_pronoun(sentence, triple)
        result = Resolution(resolved_text=sentence.text)

        if pronoun is not None:
            features = PRONOUNS[_pronoun_key(pronoun) or ""]
            window = results[max(0, index - WINDOW) : index][::-1]  # plus récente d'abord
            subjects = [r.subject for r in window if r.subject is not None]
            # Noms propres seulement si la fenêtre n'a aucun sujet nominal (même indéfini) :
            # dans « Une délégation de Sfax est arrivée. Elle… », « Elle » n'est pas « Sfax ».
            if subjects or any(r.has_nominal_subject for r in window):
                pool = subjects
            else:
                pool = [m for r in window for m in reversed(r.entities)]
            antecedent = next((m for m in pool if _compatible(features, m)), None)
            if antecedent is not None:
                result.resolved_text = _replace(sentence, pronoun, antecedent)
                result.log.append(f"{pronoun.text} → {antecedent.text}")
                result.subject = Mention(
                    antecedent.text, antecedent.gender, antecedent.number, is_subject=True
                )
        else:
            result.subject = _subject_mention(sentence, triple)
            result.has_nominal_subject = triple is not None and triple.subject is not None

        exclude = triple.subject_span if triple is not None else None
        result.entities = _entity_mentions(sentence, exclude)
        results.append(result)
    return results


def resolve(sentences: list[Sentence]) -> list[str]:
    """Retourne une version autonome de chaque phrase (même ordre, même longueur)."""
    return [r.resolved_text for r in resolve_with_log(sentences)]
