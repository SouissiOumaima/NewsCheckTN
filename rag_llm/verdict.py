"""Lot D — Génération du verdict par LLM (prompting contraint, citations, abstention)."""

from __future__ import annotations

from common.schemas import Claim, Label, Stance, StanceResult, Verdict

MIN_CONFIDENCE = 0.6


def generate_verdict(claim: Claim, stances: list[StanceResult]) -> Verdict:
    """Verdict argumenté. S'abstient si les preuves sont insuffisantes."""
    # TODO(Lot D): appel LLM avec prompt contraint (rag_llm/prompts/), vérification
    #              que chaque citation existe, calibration de l'incertitude.
    decisive = [
        s for s in stances if s.stance != Stance.NEUTRAL and s.confidence >= MIN_CONFIDENCE
    ]
    if not decisive:
        return Verdict(
            claim=claim,
            label=Label.NOT_ENOUGH_INFO,
            explanation="Preuves insuffisantes pour statuer.",
            citations=[],
            uncertainty=1.0,
            abstained=True,
        )
    support = sum(s.confidence for s in decisive if s.stance == Stance.SUPPORTS)
    refute = sum(s.confidence for s in decisive if s.stance == Stance.REFUTES)
    return Verdict(
        claim=claim,
        label=Label.TRUE if support >= refute else Label.FALSE,
        explanation="TODO(Lot D): explication générée par le LLM.",
        citations=[s.evidence.doc_id for s in decisive],
        uncertainty=1.0 - abs(support - refute) / (support + refute),
        abstained=False,
    )
