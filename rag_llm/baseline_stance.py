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

Lecture des nombres (v2, EXP-D-005) :
- séparateurs de milliers reconnus : « 39 000 », « 39.000 », « 39 000 » (espace insécable)
  → 39000 ; « 16,4 » et « 9.3 » restent des décimaux (le groupe après le séparateur n'a pas
  exactement 3 chiffres) ;
- « 13 ألف », « 3 آلاف », « 2 mille » → ×1 000 ; « 2 millions », « 2 مليون » → ×1 000 000 ;
- un nombre collé à un nom n'est pas une quantité : « Covid-19 », « كوفيد-19 », « G20 »,
  « A320 » sont ignorés. Un préfixe arabe collé (« و3 », « ب2025 ») reste accepté.

Limites connues : pas de compréhension du sens, unités ignorées (16 % = 16 millions),
démenti détecté par mots isolés, et une phrase qui reprend l'affirmation pour la réfuter
(« X a classé comme fausse l'information selon laquelle … 67 % ») est lue comme un soutien
(mêmes nombres). À remplacer par le NLI du Lot C dès qu'il est disponible.
"""

from __future__ import annotations

import re

from common.schemas import Claim, Evidence, Stance, StanceResult
from rag_llm.retrieval.text import normalize_for_retrieval, tokenize

MIN_OVERLAP = 0.5
STEM_LEN = 5  # comparaison sur les 5 premières lettres : « remplis » ≈ « remplissage »

_YEAR = re.compile(r"^(19|20)\d\d$")
# Milliers : 1 à 3 chiffres puis des groupes de 3 chiffres séparés par un espace ou un point.
# (Après `normalize_for_retrieval`, les espaces insécables sont déjà des espaces.)
_THOUSANDS = re.compile(r"(?<![\d.,])(\d{1,3})((?:[ .]\d{3})+)(?![\d]|[.,]\d)")
# Multiplicateurs écrits en lettres (formes normalisées : ألف → الف, آلاف → الاف).
_MULTIPLIERS = {
    "mille": 1_000, "الف": 1_000, "الاف": 1_000, "million": 1_000_000, "millions": 1_000_000,
    "مليون": 1_000_000, "ملايين": 1_000_000,
}
_NUMBER_WORD = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(" + "|".join(sorted(_MULTIPLIERS, key=len, reverse=True)) + r")\b"
)
# Un nombre précédé d'une lettre latine (G20, A320, Covid19), ou d'une lettre puis d'un
# tiret (Covid-19, كوفيد-19), fait partie d'un nom : ce n'est pas une quantité.
_NUMBER = re.compile(r"(?<![a-z\d.,])(?<![a-z\u0600-\u06ff]-)\d+(?:[.,]\d+)?")
# Arabizi : un chiffre seul collé à des lettres sert de lettre (5obez = خبز, 3am = عام, 7aja),
# ce n'est pas une quantité. Les nombres suivis d'une unité collée restent des nombres (10dt, 3kg).
_UNITS = ("dt", "d", "tnd", "kg", "g", "km", "m", "l", "ml", "h", "min", "mn", "md", "mds", "ans")

# Marqueurs de démenti, sous forme normalisée (voir `normalize_for_retrieval`).
REFUTE_CUES_FR = (
    "aucun", "aucune", "contrairement", "loin du", "en realite", "dement", "infonde",
    "n'a pas", "n'ont pas", "n'est pas", "pas de", "faux", "rumeur",
)
REFUTE_CUES_AR = (
    "نفت", "نفي", "لا توجد", "لا يوجد", "لم", "غير صحيح", "اشاعه", "عار من الصحه", "مضلل",
)


def _format(value: float) -> str:
    return str(int(value)) if value == int(value) else str(value)


def _numbers(text: str) -> set[str]:
    """Quantités citées dans le texte (hors années), sous une forme comparable."""
    norm = normalize_for_retrieval(text)
    norm = _THOUSANDS.sub(lambda m: m.group(1) + re.sub(r"\D", "", m.group(2)), norm)
    norm = _NUMBER_WORD.sub(
        lambda m: _format(float(m.group(1).replace(",", ".")) * _MULTIPLIERS[m.group(2)]), norm
    )
    nums = set()
    for m in _NUMBER.finditer(norm):
        rest = re.match(r"[a-z]+", norm[m.end():])
        if len(m.group()) == 1 and rest and rest.group() not in _UNITS:
            continue  # chiffre-lettre de l'arabizi (5obez, 3am), pas une quantité
        nums.add(_format(float(m.group().replace(",", "."))))
    return {n for n in nums if not _YEAR.match(n)}


def _stems(text: str) -> set[str]:
    # Mots seulement (les nombres sont comparés à part) ; un mot arabizi comme « 5obez »
    # contient un chiffre mais reste un mot.
    return {t[:STEM_LEN] for t in tokenize(text) if any(c.isalpha() for c in t)}


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
