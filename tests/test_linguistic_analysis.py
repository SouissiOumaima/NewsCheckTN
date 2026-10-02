"""Tests Lot B."""

from linguistic_analysis.claim_extraction import detect_modality, extract_claims, split_sentences
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
