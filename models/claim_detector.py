"""Lot C — Détection d'affirmations vérifiables (check-worthiness)."""

from __future__ import annotations

import re

from common.schemas import Claim

THRESHOLD = 0.5


def score_checkworthiness(claim: Claim) -> float:
    """Probabilité que l'affirmation soit vérifiable."""
    # TODO(Lot C): baseline TF-IDF/FastText puis XLM-R / AraBERT fine-tuné (+ LoRA).
    score = 0.3
    if re.search(r"\d", claim.text):
        score += 0.4
    if claim.modality == "assertif":
        score += 0.1
    return min(score, 1.0)


def filter_checkworthy(claims: list[Claim], threshold: float = THRESHOLD) -> list[Claim]:
    for c in claims:
        c.checkworthiness = score_checkworthiness(c)
    return [c for c in claims if c.checkworthiness >= threshold]
