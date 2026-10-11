"""Lot D — Baseline NLI par règles (tâche S2 du plan), en attendant le modèle du Lot C.

Même signature que `models.nli.stance.predict_stances` : le Lot E peut l'utiliser comme
solution de repli pour la démo Bronze si le modèle NLI n'est pas prêt. Le vrai NLI reste
la responsabilité du Lot C ; ce module sert surtout à tester le verdict de bout en bout.

Règles, appliquées seulement si la preuve parle du même sujet que l'affirmation
(recouvrement de mots ≥ MIN_OVERLAP) :
1. l'affirmation et la preuve contiennent des nombres (hors années) :
   même nombre → soutient ; nombres différents → contredit ;
2. sinon, la preuve contient un marqueur de démenti (« aucune », « en réalité », « نفت »…)
   → contredit ;
3. sinon → neutre.

Limites connues : pas de compréhension du sens, unités ignorées (16 % = 16 millions),
démenti détecté par mots isolés. À remplacer par le NLI du Lot C dès qu'il est disponible.
"""

from __future__ import annotations

import re

from common.schemas import Claim, Evidence, Stance, StanceResult
from rag_llm.retrieval.text import normalize_for_retrieval, tokenize

MIN_OVERLAP = 0.5
STEM_LEN = 5  # comparaison sur les 5 premières lettres : « remplis » ≈ « remplissage »

_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_YEAR = re.compile(r"^(19|20)\d\d$")

# Marqueurs de démenti, sous forme normalisée (voir `normalize_for_retrieval`).
REFUTE_CUES_FR = (
    "aucun", "aucune", "contrairement", "loin du", "en realite", "dement", "infonde",
    "n'a pas", "n'ont pas", "n'est pas", "pas de", "faux", "rumeur",
)
REFUTE_CUES_AR = (
    "نفت", "نفي", "لا توجد", "لا يوجد", "لم", "غير صحيح", "اشاعه", "عار من الصحه", "مضلل",
)


def _numbers(text: str) -> set[str]:
    nums = {n.replace(",", ".") for n in _NUMBER.findall(normalize_for_retrieval(text))}
    return {n for n in nums if not _YEAR.match(n)}


def _stems(text: str) -> set[str]:
    return {t[:STEM_LEN] for t in tokenize(text) if not any(c.isdigit() for c in t)}


def topic_overlap(claim_text: str, evidence_text: str) -> float:
    """Part des mots (hors nombres) de l'affirmation présents dans la preuve."""
    claim_stems = _stems(claim_text)
    if not claim_stems:
        return 0.0
    return len(claim_stems & _stems(evidence_text)) / len(claim_stems)


def has_refute_cue(text: str) -> bool:
    norm = normalize_for_retrieval(text).replace("’", "'")
    words = set(re.findall(r"\w+", norm))
    for cue in REFUTE_CUES_FR + REFUTE_CUES_AR:
        if (" " in cue or "'" in cue) and cue in norm:
            return True
        if cue in words:
            return True
    return False


def predict_stance_rules(claim: Claim, evidence: Evidence) -> StanceResult:
    overlap = topic_overlap(claim.text, evidence.text)
    if overlap < MIN_OVERLAP:
        return StanceResult(evidence=evidence, stance=Stance.NEUTRAL, confidence=0.0)
    confidence = round(0.5 + 0.5 * overlap, 3)
    claim_nums, ev_nums = _numbers(claim.text), _numbers(evidence.text)
    if claim_nums and ev_nums:
        stance = Stance.SUPPORTS if claim_nums <= ev_nums else Stance.REFUTES
        return StanceResult(evidence=evidence, stance=stance, confidence=confidence)
    if has_refute_cue(evidence.text):
        return StanceResult(evidence=evidence, stance=Stance.REFUTES, confidence=confidence)
    return StanceResult(evidence=evidence, stance=Stance.NEUTRAL, confidence=confidence)


def predict_stances(claim: Claim, evidences: list[Evidence]) -> list[StanceResult]:
    return [predict_stance_rules(claim, e) for e in evidences]
