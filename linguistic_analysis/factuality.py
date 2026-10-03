"""Lot B — Distinction affirmation factuelle / opinion.

Combine des lexiques (verbes d'opinion, évaluatifs, marqueurs dialectaux) stockés
dans `resources/` et des patrons syntaxiques (verbe d'opinion à la 1re personne
gouvernant une complétive, adjectif évaluatif en racine, question, souhait).
"""

from __future__ import annotations


def classify_factuality(sentence: str) -> tuple[bool, float, list[str]]:
    """Retourne (is_opinion, confiance, indices déclencheurs)."""
    # TODO(Lot B): lexiques FR/AR/TN + patrons de dépendances.
    return False, 0.0, []
