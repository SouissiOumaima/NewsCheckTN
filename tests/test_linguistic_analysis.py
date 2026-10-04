"""Tests Lot B."""

import json
from dataclasses import asdict, fields
from pathlib import Path

import pytest

from common.schemas import Claim, Document, Lang
from linguistic_analysis import claim_extraction, preprocessing
from linguistic_analysis.claim_extraction import (
    detect_modality,
    extract_claims,
    extract_claims_detailed,
    split_sentences,
)
from linguistic_analysis.io_contract import (
    claims_to_json,
    detailed_to_json,
    document_from_json,
    document_to_json,
    read_documents,
    run,
)
from linguistic_analysis.types import MODALITY_LABELS, ExtractedClaim
from normalization.normalize import normalize
from pipeline import check_text

FIXTURES = Path(__file__).parent / "fixtures" / "linguistic_analysis"


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


VALID_DOC = {"raw_text": "a", "text": "a", "lang": "fr", "script": "latin"}


@pytest.mark.parametrize(
    "bad",
    [
        [],
        {**VALID_DOC, "lang": "en"},
        {**VALID_DOC, "script": "cyrillic"},
        {**VALID_DOC, "text": None},
    ],
)
def test_document_from_json_rejects_invalid(bad):
    with pytest.raises(ValueError, match="Document invalide"):
        document_from_json(bad)


def _mock_documents():
    return read_documents(FIXTURES / "mock_documents.jsonl")


def test_mock_documents_cover_languages_and_scripts():
    docs = _mock_documents()
    assert len(docs) >= 10
    assert {d.lang for d in docs} >= {Lang.FR, Lang.AR, Lang.TN}
    assert {d.script for d in docs} >= {"latin", "arabic", "arabizi"}


def test_mock_documents_match_normalization_output():
    # La fixture doit rester identique à ce que produit le Lot A2.
    for doc in _mock_documents():
        assert normalize(doc.raw_text) == doc


def test_json_round_trip():
    for doc in _mock_documents():
        payload = json.loads(json.dumps(document_to_json(doc), ensure_ascii=False))
        assert document_from_json(payload) == doc
        for row in claims_to_json(extract_claims(doc)):
            assert set(json.loads(json.dumps(row))) == {f.name for f in fields(Claim)}


def test_detailed_output_and_projection():
    for doc in _mock_documents():
        detailed = extract_claims_detailed(doc)
        public = extract_claims(doc)
        assert public == [c.to_claim() for c in detailed]
        for c in detailed:
            assert doc.text[c.span[0] : c.span[1]].strip() == c.text
            assert c.resolved_text
            assert c.modality in MODALITY_LABELS
            assert 0.0 <= c.certainty <= 1.0
        rows = detailed_to_json(detailed)
        assert all({"resolved_text", "certainty", "triggers"} <= set(r) for r in rows)


def test_opinions_are_not_filtered(monkeypatch):
    # Le filtrage des opinions n'est pas décidé : extract_claims les transmet.
    monkeypatch.setattr(
        claim_extraction.factuality, "classify_factuality", lambda s: (True, 0.9, ["pense"])
    )
    doc = normalize("Je pense que cette réforme est une catastrophe pour les jeunes.")
    (detailed,) = claim_extraction.extract_claims_detailed(doc)
    assert detailed.is_opinion
    assert extract_claims(doc) == [detailed.to_claim()]


def test_reported_modality_triggers():
    (claim,) = extract_claims_detailed(normalize("Selon le ministère, les prix ont baissé."))
    assert claim.modality == "rapporté" and claim.triggers == ["Selon"]


def test_unknown_modality_rejected():
    with pytest.raises(ValueError):
        ExtractedClaim(text="x", lang=Lang.FR, modality="certain")


def test_cli(tmp_path):
    out = tmp_path / "claims.jsonl"
    n = run(FIXTURES / "mock_documents.jsonl", out, detailed=True)
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert n == len(rows) == len(_mock_documents())
    assert all("claims" in r for r in rows)


def test_pipeline_still_works():
    verdicts = check_text("Le taux de chômage en Tunisie est de 16,4 % en 2023.")
    assert len(verdicts) == 1


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


# --- Tâche 2 : prétraitement (tokenisation, POS, dépendances) ----------------------------


@pytest.fixture
def rules_only(monkeypatch):
    """Force le repli sur règles, quels que soient les modèles installés."""
    monkeypatch.setattr(preprocessing, "get_parser", lambda lang: None)


def _check_offsets(doc, sentences):
    for s in sentences:
        assert doc.text[s.start : s.end] == s.text
        assert s.tokens, s.text
        assert [t.i for t in s.tokens] == list(range(len(s.tokens)))
        for t in s.tokens:
            assert s.start <= t.start < t.end <= s.end


def test_analyze_rules_offsets_all_languages(rules_only):
    for doc in _mock_documents():
        sentences = preprocessing.analyze(doc)
        assert sentences and all(s.parser == "rules" for s in sentences)
        _check_offsets(doc, sentences)
        for s in sentences:
            for t in s.tokens:
                assert doc.text[t.start : t.end] == t.text  # pas de mwt en mode règles
                assert t.head == -1 and t.deprel == "dep"


def test_rules_tokenization_arabizi_and_numbers(rules_only):
    doc = normalize("El ministre 9al que le taux a baissé de 2,5 % en 2024.")
    (s,) = preprocessing.analyze(doc)
    by_text = {t.text: t for t in s.tokens}
    assert "9al" in by_text and by_text["9al"].upos == "VERB"
    assert by_text["2,5"].upos == "NUM" and by_text["2024"].upos == "NUM"
    assert by_text["%"].upos == "SYM" and by_text["."].upos == "PUNCT"
    assert by_text["que"].upos == "SCONJ"


def test_rules_lexicon_arabic_script(rules_only):
    doc = normalize("الحكومة قالت إلي الأسعار باش تنقص برشا.")
    (s,) = preprocessing.analyze(doc)
    upos = {t.text: t.upos for t in s.tokens}
    assert upos["قالت"] == "VERB" and upos["باش"] == "PART" and upos["برشا"] == "ADV"


def test_rules_french_elision(rules_only):
    (s,) = preprocessing.analyze(normalize("D'après l'INS, le chômage a baissé."))
    assert [t.text for t in s.tokens][:4] == ["D'", "après", "l'", "INS"]


def test_mixed_document_redetects_language_per_sentence(rules_only):
    text = "Le chômage a baissé en 2024. ارتفعت الأسعار كثيرا."
    doc = Document(raw_text=text, text=text, lang=Lang.AR, script="mixed")
    langs = [s.lang for s in preprocessing.analyze(doc)]
    assert langs == [Lang.FR, Lang.AR]


@pytest.mark.parametrize(
    ("text", "lang"),
    [
        ("Le taux de chômage a baissé.", Lang.FR),
        ("ارتفعت الأسعار في تونس.", Lang.AR),
        ("El 7koma 9alet elli el as3ar bech tan9es.", Lang.TN),
        ("...", Lang.UNKNOWN),
    ],
)
def test_detect_sentence_lang(text, lang):
    assert preprocessing.detect_sentence_lang(text) == lang


def test_unavailable_parser_falls_back_to_rules(rules_only):
    (s,) = preprocessing.analyze(normalize("Le ministre a annoncé une hausse des prix."))
    assert s.parser == "rules" and s.lang == Lang.FR


def test_lexicon_has_no_conflicting_forms():
    preprocessing._tn_lexicon.cache_clear()
    assert len(preprocessing._tn_lexicon()) > 100


@pytest.mark.slow
def test_analyze_spacy_fr_tree():
    pytest.importorskip("spacy")
    if preprocessing.get_parser(Lang.FR) is None:
        pytest.skip("modèle fr_core_news_md absent")
    doc = normalize("Le ministre a annoncé une hausse des prix. Il a visité Sfax.")
    sentences = preprocessing.analyze(doc)
    assert [s.parser for s in sentences] == ["spacy-fr", "spacy-fr"]
    _check_offsets(doc, sentences)
    for s in sentences:
        roots = [t for t in s.tokens if t.deprel == "root"]
        assert len(roots) == 1 and roots[0].head == -1
        assert all(-1 <= t.head < len(s.tokens) for t in s.tokens)
        assert all(doc.text[t.start : t.end] == t.text for t in s.tokens)
    first = {t.text: t for t in sentences[0].tokens}
    assert first["ministre"].deprel == "nsubj"
    assert sentences[0].tokens[first["ministre"].head].text == "annoncé"


@pytest.mark.slow
def test_analyze_stanza_ar_multiword_tokens():
    pytest.importorskip("stanza")
    if preprocessing.get_parser(Lang.AR) is None:
        pytest.skip("modèle Stanza ar absent")
    doc = normalize("وقال الوزير إن الأسعار ارتفعت.")
    (s,) = preprocessing.analyze(doc)
    assert s.parser == "stanza-ar"
    _check_offsets(doc, [s])
    assert any(t.deprel == "root" and t.head == -1 for t in s.tokens)
    assert all(-1 <= t.head < len(s.tokens) for t in s.tokens)
    # « وقال » = و + قال : deux mots syntaxiques partageant le span du token d'origine.
    spans = [(t.start, t.end) for t in s.tokens]
    first_span = (s.start, s.start + len("وقال"))
    assert spans.count(first_span) >= 2
    assert doc.text[first_span[0] : first_span[1]] == "وقال"
