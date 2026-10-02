"""Structures de données échangées entre les modules du pipeline.

Propriétaire : Lot E. Toute modification de ce fichier impacte les 6 lots :
elle doit passer par une PR relue par au moins un membre de chaque lot concerné.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Lang(str, Enum):
    FR = "fr"
    AR = "ar"  # arabe standard (MSA)
    TN = "tn"  # dialecte tunisien (lettres arabes ou arabizi)
    UNKNOWN = "unk"


class Stance(str, Enum):
    SUPPORTS = "supports"
    REFUTES = "refutes"
    NEUTRAL = "neutral"


class Label(str, Enum):
    TRUE = "vrai"
    FALSE = "faux"
    MISLEADING = "trompeur"
    NOT_ENOUGH_INFO = "preuves_insuffisantes"


@dataclass
class Document:
    """Texte normalisé (sortie Lot A2)."""

    raw_text: str
    text: str
    lang: Lang
    script: str = "arabic"  # arabic | latin | arabizi | mixed


@dataclass
class Claim:
    """Affirmation vérifiable extraite (sortie Lot B + score Lot C)."""

    text: str
    lang: Lang
    span: tuple[int, int] = (0, 0)
    subject: str | None = None
    predicate: str | None = None
    obj: str | None = None
    modality: str | None = None  # assertif | conditionnel | rapporté | ...
    checkworthiness: float = 0.0


@dataclass
class Evidence:
    """Passage de preuve retrouvé (corpus Lot A1, retrieval Lot D)."""

    doc_id: str
    text: str
    source: str
    url: str | None = None
    date: str | None = None
    score: float = 0.0


@dataclass
class StanceResult:
    """Position d'une preuve vis-à-vis d'une affirmation (sortie NLI, Lot C)."""

    evidence: Evidence
    stance: Stance
    confidence: float


@dataclass
class Verdict:
    """Verdict argumenté (sortie Lot D). Citations obligatoires sauf abstention."""

    claim: Claim
    label: Label
    explanation: str
    citations: list[str] = field(default_factory=list)  # doc_id des preuves citées
    uncertainty: float = 1.0  # 0 = certain, 1 = totalement incertain
    abstained: bool = True
