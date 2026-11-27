"""Lot D — Incertitude du verdict calculée à partir du NLI (adoptée dans EXP-D-021).

u = 1 − soutien des passages au verdict, sans aucun paramètre réglé :
- vrai : plus haute confiance « soutient » parmi les passages cités (0 s'il n'y en a pas) ;
- faux : plus haute confiance « contredit » parmi les passages cités ;
- trompeur : plus haute confiance « soutient » ou « contredit » parmi les passages cités ;
- preuves insuffisantes : moyenne, sur les passages proposés, de la confiance « neutre » (0 sinon).

C'est un **indicateur de classement, non calibré** (EXP-D-021 : AUROC 0.96 sur le dev pour
repérer les verdicts faux, 0.82 sur le test ; ECE 0.33 sur le test).
"""

from __future__ import annotations

from common.schemas import StanceResult

NEI = "preuves_insuffisantes"
EXPECTED = {"vrai": {"supports"}, "faux": {"refutes"}, "trompeur": {"supports", "refutes"}}


def stance_table(stances: list[StanceResult]) -> dict[str, tuple[str, float]]:
    """doc_id → (position, confiance) pour les passages proposés au verdict."""
    return {s.evidence.doc_id: (s.stance.value, s.confidence) for s in stances}


def nli_uncertainty(
    pred: str, citations: list[str], stances: dict[str, tuple[str, float]]
) -> float:
    """u = 1 − soutien ; `stances` : doc_id → (position, confiance) des passages proposés."""
    if pred == NEI:
        if not stances:
            return 1.0
        s = sum(conf if st == "neutral" else 0.0 for st, conf in stances.values()) / len(stances)
    else:
        want = EXPECTED.get(pred, set())
        s = max(
            (stances[d][1] for d in citations if d in stances and stances[d][0] in want),
            default=0.0,
        )
    return round(1.0 - s, 4)
