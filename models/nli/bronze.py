"""Lot C — Model 2, palier Bronze : position d'une preuve par lexique et règles.

Composant classique (aucun réseau de neurones), exigé pour la revue Bronze et utilisé par la démo.
Pour une affirmation (hypothèse) et une preuve (prémisse) :

  1. recouvrement des mots pleins (affirmation → preuve, sur 5 premières lettres)
     trop faible → `neutral` (la preuve ne parle pas du sujet) ;
  2. nombres de l'affirmation absents de la preuve, alors que la preuve en cite → `refutes` ;
  3. marqueur de démenti dans la preuve (« faux », « démenti », « زائف », « مضلل », « mouch s7i7 »…)
     absent de l'affirmation → `refutes` ;
  4. négation présente d'un seul côté (« لم », « ne … pas », « mouch »…) → `refutes` ;
  5. recouvrement élevé → `supports` ; sinon `neutral`.

Les deux seuils de recouvrement sont choisis sur train + val (`tune`), jamais sur le test.
Texte d'abord normalisé par le Lot A2 (`normalization.normalize`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from normalization.normalize import normalize

STEM = 5
# Seuils choisis par `python -m models.nli.bronze_eval --tune` sur train + val (corpus v3).
LOW_OVERLAP = 0.35
HIGH_OVERLAP = 0.4

# Marqueurs de démenti, forme normalisée (Lot A2 : ة → ه, أ/إ/آ → ا, ى → ي, minuscules).
REFUTE_CUES = (
    # français
    "faux",
    "fausse",
    "infonde",
    "infondee",
    "trompeur",
    "trompeuse",
    "dementi",
    "dement",
    "rumeur",
    "rumeurs",
    "inexact",
    "inexacte",
    "errone",
    "erronee",
    "fake",
    "intox",
    "n'a jamais",
    "aucune",
    "aucun",
    "contrairement",
    # arabe standard
    "زائف",
    "زائفه",
    "مضلل",
    "مضلله",
    "كاذب",
    "كاذبه",
    "خاطئ",
    "خاطئه",
    "مفبرك",
    "مفبركه",
    "غير صحيح",
    "غير صحيحه",
    "لا اساس",
    "عار من الصحه",
    "نفت",
    "نفي",
    "ينفي",
    "تنفي",
    "اشاعه",
    "شائعه",
    "شائعات",
    "اشاعات",
    # tunisien (lettres arabes et arabizi)
    "مش صحيح",
    "موش صحيح",
    "كذب",
    "mouch s7i7",
    "mech s7i7",
    "kdheb",
    "kedheb",
    "ghalet",
)
NEGATIONS = frozenset(
    (
        "ne",
        "n'",
        "pas",
        "jamais",
        "ni",
        "sans",
        "non",
        "لا",
        "لم",
        "لن",
        "ليس",
        "ليست",
        "ما",
        "غير",
        "مش",
        "موش",
        "ماهوش",
        "ماهيش",
        "mouch",
        "mech",
        "mich",
        "moch",
    )
)
# Mots outils exclus du recouvrement (les négations sont traitées à part).
STOPWORDS = frozenset(
    (
        "le",
        "la",
        "les",
        "l'",
        "un",
        "une",
        "des",
        "de",
        "du",
        "d'",
        "et",
        "en",
        "a",
        "au",
        "aux",
        "que",
        "qui",
        "ce",
        "cette",
        "ces",
        "est",
        "sont",
        "dans",
        "par",
        "pour",
        "sur",
        "avec",
        "il",
        "elle",
        "ils",
        "se",
        "s'",
        "son",
        "sa",
        "ses",
        "qu'",
        "y",
        "ont",
        "été",
        "ete",
        "في",
        "من",
        "الي",
        "علي",
        "عن",
        "ان",
        "او",
        "و",
        "ثم",
        "هذا",
        "هذه",
        "ذلك",
        "تلك",
        "التي",
        "الذي",
        "مع",
        "كان",
        "كانت",
        "قد",
        "بعد",
        "قبل",
        "كل",
        "بين",
        "عند",
        "هو",
        "هي",
    )
)
_WORD = re.compile(r"[\w']+", re.UNICODE)
_NUMBER = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)?(?![\w])")


@dataclass(frozen=True)
class Signals:
    """Indices lexicaux d'une paire : ce que la règle a vu (affiché dans l'analyse d'erreurs)."""

    overlap: float
    number_conflict: bool
    numbers_match: bool
    refute_cue: bool
    negation_mismatch: bool


def _clean(text: str) -> str:
    return normalize(text).text.lower().replace("’", "'")


def _words(text: str) -> list[str]:
    return _WORD.findall(text)


def _content_stems(words: list[str]) -> set[str]:
    return {
        w[:STEM]
        for w in words
        if w not in STOPWORDS and w not in NEGATIONS and not w.isdigit() and len(w) > 1
    }


def _numbers(text: str) -> set[str]:
    return {n.replace(",", ".") for n in _NUMBER.findall(text)}


def _values_to_compare(numbers: set[str]) -> set[str]:
    """Écarte les années : deux passages peuvent partager la date mais diverger sur le fait.

    Exemple : « 25 % en 2023 » contre « 16,4 % en 2023 ». L'année commune
    ne doit pas masquer le conflit entre les deux pourcentages.
    """
    values = set()
    for number in numbers:
        try:
            value = float(number)
        except ValueError:
            values.add(number)
            continue
        if number.isdigit() and 1900 <= value <= 2100:
            continue
        values.add(number)
    return values


def _has_cue(text: str, words: set[str]) -> bool:
    return any(
        (cue in text) if (" " in cue or "'" in cue) else (cue in words) for cue in REFUTE_CUES
    )


def signals(claim: str, evidence: str) -> Signals:
    c, e = _clean(claim), _clean(evidence)
    cw, ew = _words(c), _words(e)
    cs = _content_stems(cw)
    overlap = len(cs & _content_stems(ew)) / len(cs) if cs else 0.0
    cn, en = _values_to_compare(_numbers(c)), _values_to_compare(_numbers(e))
    return Signals(
        overlap=round(overlap, 4),
        number_conflict=bool(cn and en and not (cn & en)),
        numbers_match=bool(cn and cn <= en),
        refute_cue=_has_cue(e, set(ew)) and not _has_cue(c, set(cw)),
        negation_mismatch=bool(NEGATIONS & set(cw)) != bool(NEGATIONS & set(ew)),
    )


def decide(
    s: Signals, low: float = LOW_OVERLAP, high: float = HIGH_OVERLAP
) -> tuple[str, float, str]:
    """Position, confiance (fixe par règle, pour le verdict du Lot D) et règle appliquée."""
    if s.overlap < low:
        return "neutral", 0.6, "R1 recouvrement faible"
    if s.number_conflict:
        return "refutes", 0.8, "R2 nombres en conflit"
    if s.refute_cue:
        return "refutes", 0.75, "R3 marqueur de démenti"
    if s.negation_mismatch:
        return "refutes", 0.65, "R4 négation d'un seul côté"
    if s.overlap >= high or s.numbers_match:
        return "supports", round(min(0.9, 0.5 + s.overlap / 2), 4), "R5 recouvrement élevé"
    return "neutral", 0.55, "R6 recouvrement moyen"


def predict(claim: str, evidence: str) -> tuple[str, float]:
    label, confidence, _ = decide(signals(claim, evidence))
    return label, confidence
