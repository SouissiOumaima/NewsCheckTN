"""Tests Lot B."""

from dataclasses import asdict, fields

import pytest

from common.schemas import Claim, Lang
from linguistic_analysis import preprocessing
from linguistic_analysis.claim_extraction import detect_modality, extract_claims, split_sentences
from linguistic_analysis.io_contract import document_from_json
from linguistic_analysis.types import MODALITY_LABELS, ExtractedClaim
from normalization.normalize import normalize


def test_split_sentences_spans():
    text = "Première phrase ici. Deuxième phrase là."
    sentences = split_sentences(text)
    assert len(sentences) == 2
    for sent, (start, end) in sentences:
        assert text[start:end].strip() == sent


def test_extract_claims():
    claims = extract_claims(normalize("Le chômage atteint 16 % en 2023. Bonjour."))
    assert [c.text for c in claims] == ["Le chômage atteint 16 % en 2023."]


def test_reported_modality():
    assert detect_modality("Selon le ministère, les prix ont baissé.") == "rapporté"


def test_to_claim_matches_shared_contract():
    extracted = ExtractedClaim(text="Le PIB a augmenté.", lang=Lang.FR, certainty=0.4)
    claim = extracted.to_claim()
    assert isinstance(claim, Claim)
    assert set(asdict(claim)) == {f.name for f in fields(Claim)}
    assert claim.checkworthiness == 0.0
    assert claim.modality in MODALITY_LABELS


def test_document_from_json():
    doc = document_from_json({"raw_text": "x y", "text": "x y", "lang": "tn", "script": "arabizi"})
    assert doc.lang == Lang.TN
    with pytest.raises(ValueError):
        document_from_json({"text": "x"})


def test_parser_fallback_without_libraries(monkeypatch):
    monkeypatch.setattr(preprocessing.importlib.util, "find_spec", lambda name: None)
    preprocessing._load_spacy_fr.cache_clear()
    preprocessing._load_stanza_ar.cache_clear()
    try:
        assert preprocessing.get_parser(Lang.FR) is None
        assert preprocessing.get_parser(Lang.AR) is None
        assert preprocessing.parser_name(Lang.FR) == "rules"
    finally:
        preprocessing._load_spacy_fr.cache_clear()
        preprocessing._load_stanza_ar.cache_clear()


def test_tunisian_uses_rules():
    assert preprocessing.get_parser(Lang.TN) is None


@pytest.mark.slow
def test_spacy_fr_parser():
    pytest.importorskip("spacy")
    nlp = preprocessing.get_parser(Lang.FR)
    if nlp is None:
        pytest.skip("modèle fr_core_news_md absent")
    deps = {t.dep_ for t in nlp("Le ministre a annoncé une hausse des prix.")}
    assert "nsubj" in deps


@pytest.mark.slow
def test_stanza_ar_parser():
    pytest.importorskip("stanza")
    nlp = preprocessing.get_parser(Lang.AR)
    if nlp is None:
        pytest.skip("modèle Stanza ar absent")
    words = [w for s in nlp("أعلن الوزير عن زيادة الأسعار.").sentences for w in s.words]
    assert any(w.deprel == "nsubj" for w in words) or any(w.deprel == "root" for w in words)
