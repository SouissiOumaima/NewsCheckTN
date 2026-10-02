"""Lot C — NLI : position d'une preuve par rapport à une affirmation."""

from __future__ import annotations

from common.schemas import Claim, Evidence, Stance, StanceResult


def predict_stance(claim: Claim, evidence: Evidence) -> StanceResult:
    """Retourne soutient / contredit / neutre avec un score de confiance."""
    # TODO(Lot C): modèle NLI multilingue (ex. mDeBERTa-xnli) fine-tuné sur nos données.
    return StanceResult(evidence=evidence, stance=Stance.NEUTRAL, confidence=0.0)


def predict_stances(claim: Claim, evidences: list[Evidence]) -> list[StanceResult]:
    return [predict_stance(claim, e) for e in evidences]
