"""Lot B — Extraction de triplets Sujet–Prédicat–Objet.

Avec arbre UD (FR, AR) : prédicat = racine verbale (ou copule), sujet = nsubj,
objet = obj / obl / attribut. Sans arbre (TN) : patrons positionnels et lexique
de verbes fréquents, avec une confiance plafonnée.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SPO:
    subject: str | None = None
    predicate: str | None = None
    obj: str | None = None
    subject_span: tuple[int, int] | None = None
    obj_span: tuple[int, int] | None = None
    confidence: float = 0.0


def extract_spo(sentence: str) -> SPO | None:
    """Extrait le triplet principal d'une phrase, ou None si aucun n'est identifiable."""
    # TODO(Lot B): règles sur l'arbre de dépendances + repli positionnel pour le tunisien.
    return None
