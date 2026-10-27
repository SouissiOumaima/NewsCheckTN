"""Lot C — baseline explicable de position d'une preuve.

Cette baseline est volontairement conservative : elle ne conclut que lorsqu'une
preuve recouvre largement l'affirmation et qu'aucun nombre ou signal de
négation ne diverge. Elle est le palier Bronze; elle doit être remplacée par le
modèle NLI entraîné du lot C sans changer l'API publique.
"""

from __future__ import annotations

import re
import unicodedata

from common.schemas import Claim, Evidence, Stance, StanceResult


_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)
_NEGATIONS = frozenset({"ne", "pas", "jamais", "aucun", "sans", "non", "لا", "لم", "لن", "ليس", "ما", "moch", "mouch"})


def _tokens(text: str) -> set[str]:
    """Tokens normalisés, sans mots-outils très fréquents."""
    folded = unicodedata.normalize("NFKD", text.casefold())
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    stopwords = {"le", "la", "les", "de", "des", "du", "un", "une", "et", "en", "est", "a", "au", "aux", "the", "of", "in", "and", "في", "من", "على", "الى", "أن", "ان", "هو", "هي"}
    return {token for token in _TOKEN.findall(folded) if len(token) > 1 and token not in stopwords}


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)?", text))


def predict_stance(claim: Claim, evidence: Evidence) -> StanceResult:
    """Retourne soutient / contredit / neutre avec un score de confiance."""
    claim_tokens, evidence_tokens = _tokens(claim.text), _tokens(evidence.text)
    if not claim_tokens or not evidence_tokens:
        return StanceResult(evidence=evidence, stance=Stance.NEUTRAL, confidence=0.0)

    overlap = len(claim_tokens & evidence_tokens) / len(claim_tokens)
    claim_numbers, evidence_numbers = _numbers(claim.text), _numbers(evidence.text)
    # Une divergence numérique est un indice de contradiction seulement si les
    # deux passages présentent des valeurs. Sinon, mieux vaut s'abstenir.
    numbers_conflict = bool(claim_numbers and evidence_numbers and claim_numbers != evidence_numbers)
    negation_conflict = bool(claim_tokens & _NEGATIONS) != bool(evidence_tokens & _NEGATIONS)

    if overlap >= 0.55 and numbers_conflict:
        return StanceResult(evidence=evidence, stance=Stance.REFUTES, confidence=round(min(0.9, 0.55 + overlap / 3), 3))
    if overlap >= 0.72 and not negation_conflict:
        return StanceResult(evidence=evidence, stance=Stance.SUPPORTS, confidence=round(min(0.95, 0.45 + overlap / 2), 3))
    return StanceResult(evidence=evidence, stance=Stance.NEUTRAL, confidence=round(min(0.49, overlap / 2), 3))


def predict_stances(claim: Claim, evidences: list[Evidence]) -> list[StanceResult]:
    return [predict_stance(claim, e) for e in evidences]
