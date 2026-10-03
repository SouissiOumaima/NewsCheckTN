"""Lot B — Modalité et incertitude.

Labels possibles : voir `types.MODALITY_LABELS`. Indices : conditionnel morphologique,
verbes de doute, adverbes d'incertitude, discours rapporté (« selon », حسب, 9alou),
hypothétique (« si », إذا / لو, ki). Le score de certitude est dérivé de lexiques
pondérés (`resources/modality_<langue>.json`).
"""

from __future__ import annotations

from linguistic_analysis.types import DEFAULT_MODALITY


def detect_modality(sentence: str) -> tuple[str, float, list[str]]:
    """Retourne (label, certitude dans [0, 1], indices déclencheurs)."""
    # TODO(Lot B): lexiques pondérés FR/AR/TN, ordre de priorité entre labels.
    return DEFAULT_MODALITY, 1.0, []
