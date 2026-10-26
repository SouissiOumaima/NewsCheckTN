"""Lot B — Modalité et incertitude.

`detect_modality(sentence)` renvoie `(label, certitude, indices)`, avec un label de
`types.MODALITY_LABELS` et une certitude dans [0, 1].

Ordre de priorité en cas de conflit entre labels :

    interrogatif > souhait > hypothétique > conditionnel > rapporté > opinion > assertif

(`souhait`, absent de l'ordre initial, est placé juste après `interrogatif` : un souhait
n'affirme rien, quel que soit son contenu.)

Sources des labels :
- `interrogatif`, `souhait`, `opinion` : repris de `factuality.classify_factuality`, pour ne pas
  maintenir deux détections divergentes (indices `question:` / `souhait:`, décision `is_opinion`) ;
- `rapporté`, `conditionnel`, `hypothétique` : lexiques `resources/modality_<langue>.json`
  (`{label: {marqueur: poids}}`, choisis comme dans `factuality.lexicon_codes`), le patron
  « si » + imparfait, la morphologie avec arbre (`Mood=Cnd`) et, pour le rapporté, un verbe de
  parole suivi d'une complétive (voir `spo`).

Certitude : `1 - max(poids des marqueurs trouvés)`, tous labels confondus, puis baisse
supplémentaire du poids du groupe `certitude_niée` (« il n'est pas certain que »), bornée à 0.
Les groupes `incertitude` (peut-être, ربما, ymken, « قد » + inaccompli) et `futur` (bech, سوف)
baissent la certitude sans changer le label : « Le chômage a probablement baissé » reste
`assertif`, avec une certitude de 0.6.

Poids des labels repris de `factuality` : interrogatif 1.0, souhait 0.8, opinion 0.5.
Défaut : `("assertif", 1.0, [])`.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from linguistic_analysis import factuality, spo
from linguistic_analysis.factuality import find_marker, match_text
from linguistic_analysis.preprocessing import Sentence
from linguistic_analysis.types import DEFAULT_MODALITY, MODALITY_LABELS

RESOURCES = Path(__file__).resolve().parent / "resources"

PRIORITY = (
    "interrogatif",
    "souhait",
    "hypothétique",
    "conditionnel",
    "rapporté",
    "opinion",
    "assertif",
)
LABEL_WEIGHTS = {"interrogatif": 1.0, "souhait": 0.8, "opinion": 0.5}
LEXICON_LABELS = ("rapporté", "conditionnel", "hypothétique")
CERTAINTY_ONLY = ("incertitude", "futur")
MORPH_WEIGHTS = {"conditionnel": 0.5, "hypothétique": 0.6, "futur": 0.2, "rapporté": 0.2}
QAD_IMPERFECTIVE_WEIGHT = 0.4

if set(PRIORITY) != set(MODALITY_LABELS):
    raise RuntimeError("PRIORITY doit couvrir exactement MODALITY_LABELS")

# « selon moi », « d'après nous » : opinion, pas discours rapporté.
_SELF_SOURCE = re.compile(r"(?:selon|d'après)\s+(?:moi|nous)\b")
# « قد » suivi d'un verbe à l'inaccompli (préfixe ي / ت / ن / ا) : possibilité.
_QAD_IMPERFECTIVE = re.compile(r"(?<!\w)قد\s+[يتنا]\w+")
# « si » + imparfait : « si les prix augmentaient ».
_SI_IMPARFAIT = re.compile(r"(?<![\w'])si\b(?:\s+\S+){0,4}?\s+\w+(?:ait|aient|ais)\b")


@lru_cache(maxsize=None)
def load_lexicon(lang: str) -> dict[str, dict[str, float]]:
    """Charge `modality_<lang>.json` : groupe -> {marqueur replié: poids}."""
    data = json.loads((RESOURCES / f"modality_{lang}.json").read_text(encoding="utf-8"))
    return {
        group: {match_text(marker): float(weight) for marker, weight in markers.items()}
        for group, markers in data.items()
        if not group.startswith("_")
    }


def _markers(sentence: Sentence, group: str) -> dict[str, float]:
    """Marqueurs du groupe dans les lexiques de `factuality.lexicon_codes` (le premier prime)."""
    out: dict[str, float] = {}
    for code in reversed(factuality.lexicon_codes(sentence)):
        out.update(load_lexicon(code).get(group, {}))
    return out


def _lexicon_hits(text: str, markers: dict[str, float]) -> list[tuple[str, float]]:
    """Tous les marqueurs présents (un même marqueur compte une fois)."""
    return [(m, w) for m, w in markers.items() if find_marker(text, [m])]


def _morphology(sentence: Sentence) -> list[tuple[str, str, float]]:
    """Indices morphosyntaxiques (arbre requis) : (groupe, indice, poids)."""
    if sentence.parser == "rules":
        return []
    cues = []
    tokens = sentence.tokens
    if any(t.upos in ("VERB", "AUX") and t.feats.get("Mood") == "Cnd" for t in tokens):
        cues.append(("conditionnel", "conditionnel:Mood=Cnd", MORPH_WEIGHTS["conditionnel"]))
    if any(t.feats.get("Tense") == "Fut" for t in tokens):
        cues.append(("futur", "futur:Tense=Fut", MORPH_WEIGHTS["futur"]))
    return cues


def detect_modality(
    sentence: Sentence,
    *,
    factual: tuple[bool, float, list[str]] | None = None,
    reported: bool | None = None,
) -> tuple[str, float, list[str]]:
    """Retourne (label, certitude dans [0, 1], indices déclencheurs).

    `factual` (sortie de `classify_factuality`) et `reported` (`SPO.reported`) peuvent être
    fournis par l'appelant pour éviter de les recalculer.
    """
    text = match_text(sentence.text)
    labels: set[str] = set()
    weights: list[float] = []
    triggers: list[str] = []

    def add(label: str | None, trigger: str, weight: float) -> None:
        if label:
            labels.add(label)
        weights.append(weight)
        triggers.append(trigger)

    # 1. Labels repris de la factualité (question, souhait, opinion).
    is_opinion, _, fact_triggers = factual or factuality.classify_factuality(sentence)
    if any(t.startswith("question:") for t in fact_triggers):
        add("interrogatif", "interrogatif", LABEL_WEIGHTS["interrogatif"])
    if any(t.startswith("souhait:") for t in fact_triggers):
        add("souhait", "souhait", LABEL_WEIGHTS["souhait"])
    if is_opinion and any(t.startswith("opinion:") for t in fact_triggers):
        add("opinion", "opinion", LABEL_WEIGHTS["opinion"])

    # 2. Lexiques de modalité.
    for label in LEXICON_LABELS:
        for marker, weight in _lexicon_hits(text, _markers(sentence, label)):
            if label == "rapporté" and marker in ("selon", "d'après") and _SELF_SOURCE.search(text):
                continue
            add(label, f"{label}:{marker}", weight)
    for group in CERTAINTY_ONLY:
        for marker, weight in _lexicon_hits(text, _markers(sentence, group)):
            add(None, f"{group}:{marker}", weight)
    if _QAD_IMPERFECTIVE.search(text):
        add(None, "incertitude:قد+inaccompli", QAD_IMPERFECTIVE_WEIGHT)
    # Lexical plutôt que morphologique : le parseur peut mal étiqueter l'imparfait
    # (spaCy tague « augmentaient » ADJ dans « Si les prix augmentaient, … »).
    if _SI_IMPARFAIT.search(text) and "même si" not in text:
        add("hypothétique", "hypothétique:si+imparfait", MORPH_WEIGHTS["hypothétique"])

    # 3. Morphosyntaxe (arbre) et discours rapporté détecté par l'extraction SPO.
    for group, trigger, weight in _morphology(sentence):
        add(group if group in MODALITY_LABELS else None, trigger, weight)
    if reported is None:
        triple = spo.extract_spo(sentence)
        reported = bool(triple and triple.reported)
    if reported:
        add("rapporté", "rapporté:verbe_de_parole", MORPH_WEIGHTS["rapporté"])

    label = next((lab for lab in PRIORITY if lab in labels), DEFAULT_MODALITY)
    certainty = 1.0 - max(weights, default=0.0)
    negated = _lexicon_hits(text, _markers(sentence, "certitude_niée"))
    if negated:
        certainty -= max(w for _, w in negated)
        triggers.extend(f"certitude_niée:{m}" for m, _ in negated)
    return label, round(max(0.0, min(1.0, certainty)), 3), triggers
