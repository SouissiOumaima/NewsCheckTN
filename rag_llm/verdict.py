"""Lot D — Verdict par gabarit et politique d'abstention v1 (S2–S3).

Le verdict est construit à partir des positions (NLI) des preuves retrouvées, sans LLM :
l'explication suit un gabarit fixe (FR, ou AR pour les affirmations en arabe / tunisien)
et cite les passages mot pour mot. Le LLM avec prompt contraint arrive en S6.

Politique d'abstention v1 — le système répond `preuves_insuffisantes` si :
  A1. aucune preuve n'a été retrouvée ;
  A2. aucune preuve n'atteint le score de pertinence minimal de la méthode de retrieval
      (`hybrid.min_relevance_score` : BM25 ≥ 1.0, cosinus dense ≥ 0.4…) ;
  A3. aucune preuve pertinente n'est décisive (soutient / contredit avec
      confiance ≥ MIN_CONFIDENCE) ;
  A4. les preuves décisives se contredisent (écart < CONFLICT_MARGIN).

Le label `trompeur` n'est pas produit par le gabarit : il demande une nuance que seul le
LLM (S6) pourra formuler.
"""

from __future__ import annotations

from common.schemas import Claim, Label, Lang, Stance, StanceResult, Verdict
from rag_llm.retrieval.hybrid import min_relevance_score

MIN_CONFIDENCE = 0.6
CONFLICT_MARGIN = 0.25
# Un verdict par règles n'est jamais certain à 100 % : plancher d'incertitude.
MIN_UNCERTAINTY = 0.1
MAX_CITATIONS = 3
QUOTE_LEN = 200

# Raisons d'abstention (codes stables, réutilisables dans l'évaluation et l'interface).
NO_EVIDENCE = "aucune_preuve"
LOW_RELEVANCE = "preuves_peu_pertinentes"
NOT_DECISIVE = "preuves_non_decisives"
CONFLICT = "preuves_contradictoires"

_TEXTS = {
    "fr": {
        Label.TRUE: "Vrai : les preuves retrouvées confirment l'affirmation.",
        Label.FALSE: "Faux : les preuves retrouvées contredisent l'affirmation.",
        NO_EVIDENCE: "Aucune preuve n'a été trouvée dans le corpus.",
        LOW_RELEVANCE: "Les passages retrouvés ne traitent pas assez directement de l'affirmation.",
        NOT_DECISIVE: "Les passages retrouvés ne permettent ni de confirmer ni de contredire "
        "l'affirmation.",
        CONFLICT: "Les preuves retrouvées se contredisent ; impossible de trancher.",
        "intro_abstain": "Preuves insuffisantes pour statuer.",
        "according": "Selon",
    },
    "ar": {
        Label.TRUE: "صحيح: الأدلة المتوفرة تؤكد هذا الادعاء.",
        Label.FALSE: "خاطئ: الأدلة المتوفرة تنفي هذا الادعاء.",
        NO_EVIDENCE: "لم يتم العثور على أي دليل في قاعدة البيانات.",
        LOW_RELEVANCE: "المقاطع المسترجعة لا تتعلق بشكل مباشر بهذا الادعاء.",
        NOT_DECISIVE: "المقاطع المسترجعة لا تسمح بتأكيد الادعاء أو نفيه.",
        CONFLICT: "الأدلة المتوفرة متناقضة، لا يمكن الحسم.",
        "intro_abstain": "الأدلة غير كافية للحكم.",
        "according": "حسب",
    },
}


def _texts(claim: Claim) -> dict:
    return _TEXTS["ar"] if claim.lang in (Lang.AR, Lang.TN) else _TEXTS["fr"]


def _quote(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= QUOTE_LEN else text[:QUOTE_LEN].rsplit(" ", 1)[0] + "…"


def _cite(s: StanceResult, according: str) -> str:
    ev = s.evidence
    meta = ", ".join(x for x in (ev.source, ev.date) if x)
    meta = f" ({meta})" if meta else ""
    return f"{according} [{ev.doc_id}]{meta} : « {_quote(ev.text)} »"


def _abstain(claim: Claim, reason: str, cited: list[StanceResult] | None = None) -> Verdict:
    t = _texts(claim)
    cited = cited or []
    lines = [t["intro_abstain"], t[reason], *(_cite(s, t["according"]) for s in cited)]
    return Verdict(
        claim=claim,
        label=Label.NOT_ENOUGH_INFO,
        explanation="\n".join(lines),
        citations=[s.evidence.doc_id for s in cited],
        uncertainty=1.0,
        abstained=True,
    )


def generate_verdict(claim: Claim, stances: list[StanceResult]) -> Verdict:
    """Point d'entrée du Lot D : verdict argumenté, abstention si preuves insuffisantes.

    `stances` provient de `predict_stances(claim, retrieve(...))` : le champ
    `evidence.score` est le score de pertinence du retrieval.
    """
    return generate_verdict_with_reason(claim, stances)[0]


def generate_verdict_with_reason(
    claim: Claim, stances: list[StanceResult], min_score: float | None = None
) -> tuple[Verdict, str | None]:
    """Comme `generate_verdict`, avec en plus le code de la raison d'abstention (ou None).

    `min_score` : seuil de pertinence (A2) ; par défaut celui de la méthode de retrieval active.

    TODO(Lot D + E): proposer un champ `abstention_reason` dans `Verdict` (common/schemas.py).
    """
    if not stances:
        return _abstain(claim, NO_EVIDENCE), NO_EVIDENCE  # A1

    threshold = min_relevance_score() if min_score is None else min_score
    relevant = [s for s in stances if s.evidence.score >= threshold]
    if not relevant:
        return _abstain(claim, LOW_RELEVANCE), LOW_RELEVANCE  # A2

    decisive = [
        s for s in relevant if s.stance != Stance.NEUTRAL and s.confidence >= MIN_CONFIDENCE
    ]
    if not decisive:
        return _abstain(claim, NOT_DECISIVE), NOT_DECISIVE  # A3

    support = sum(s.confidence for s in decisive if s.stance == Stance.SUPPORTS)
    refute = sum(s.confidence for s in decisive if s.stance == Stance.REFUTES)
    margin = abs(support - refute) / (support + refute)
    if support and refute and margin < CONFLICT_MARGIN:
        return _abstain(claim, CONFLICT, cited=decisive[:MAX_CITATIONS]), CONFLICT  # A4

    winner = Stance.SUPPORTS if support > refute else Stance.REFUTES
    label = Label.TRUE if winner == Stance.SUPPORTS else Label.FALSE
    cited = sorted(
        (s for s in decisive if s.stance == winner), key=lambda s: s.confidence, reverse=True
    )[:MAX_CITATIONS]

    t = _texts(claim)
    lines = [t[label], *(_cite(s, t["according"]) for s in cited)]
    best_conf = cited[0].confidence
    verdict = Verdict(
        claim=claim,
        label=label,
        explanation="\n".join(lines),
        citations=[s.evidence.doc_id for s in cited],
        uncertainty=round(max(MIN_UNCERTAINTY, 1.0 - margin * best_conf), 3),
        abstained=False,
    )
    return verdict, None
