"""Tests Lot C."""

from common.schemas import Claim, Evidence, Lang, Stance
from models.claim_detector import filter_checkworthy, score_checkworthiness
from models.nli.stance import predict_stance


def test_checkworthiness_in_range():
    score = score_checkworthiness(Claim(text="Le PIB a augmenté de 2 %.", lang=Lang.FR))
    assert 0.0 <= score <= 1.0


def test_filter_checkworthy_sets_scores():
    claims = [Claim(text="Le PIB a augmenté de 2 % en 2023.", lang=Lang.FR, modality="assertif")]
    kept = filter_checkworthy(claims)
    assert kept and kept[0].checkworthiness > 0


def test_predict_stance_returns_valid_stance():
    res = predict_stance(
        Claim(text="Tunis est la capitale.", lang=Lang.FR),
        Evidence(doc_id="e1", text="Tunis est la capitale de la Tunisie.", source="t"),
    )
    assert res.stance in Stance and 0.0 <= res.confidence <= 1.0
