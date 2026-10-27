"""Tests Lot C."""

from common.schemas import Claim, Evidence, Lang, Stance
import models.claim_detector as claim_detector
from models.claim_detector import filter_checkworthy, score_checkworthiness
from models.nli.stance import predict_stance


def test_checkworthiness_in_range():
    score = score_checkworthiness(Claim(text="Le PIB a augmenté de 2 %.", lang=Lang.FR))
    assert 0.0 <= score <= 1.0


def test_filter_checkworthy_sets_scores():
    claims = [Claim(text="Le PIB a augmenté de 2 % en 2023.", lang=Lang.FR, modality="assertif")]
    kept = filter_checkworthy(claims)
    assert kept and kept[0].checkworthiness > 0


def test_filter_checkworthy_can_classify_the_raw_sentence(monkeypatch):
    seen = []

    def fake_predict(text):
        seen.append(text)
        return "AFFIRMATION", 0.9

    monkeypatch.setattr(claim_detector, "predict_label_and_score", fake_predict)
    claim = Claim(text="texte normalise", lang=Lang.AR)
    assert filter_checkworthy([claim], classification_texts=["نصّ خام"] ) == [claim]
    assert seen == ["نصّ خام"]


def test_predict_stance_returns_valid_stance():
    res = predict_stance(
        Claim(text="Tunis est la capitale.", lang=Lang.FR),
        Evidence(doc_id="e1", text="Tunis est la capitale de la Tunisie.", source="t"),
    )
    assert res.stance in Stance and 0.0 <= res.confidence <= 1.0


def test_predict_stance_supports_matching_evidence():
    res = predict_stance(
        Claim(text="Tunis est la capitale de la Tunisie.", lang=Lang.FR),
        Evidence(doc_id="e1", text="Tunis est la capitale de la Tunisie.", source="t"),
    )
    assert res.stance == Stance.SUPPORTS and res.confidence >= 0.6


def test_predict_stance_refutes_conflicting_numbers():
    res = predict_stance(
        Claim(text="Le chômage est de 16,4 % en 2023.", lang=Lang.FR),
        Evidence(doc_id="e1", text="Le chômage est de 12 % en 2023.", source="t"),
    )
    assert res.stance == Stance.REFUTES and res.confidence >= 0.6
