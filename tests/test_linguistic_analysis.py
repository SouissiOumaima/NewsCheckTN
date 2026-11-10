"""Tests Lot B."""

import csv
import hashlib
import json
import os
import random
import subprocess
import sys
import types
from collections import Counter
from dataclasses import asdict, fields
from pathlib import Path

import pytest

from common.schemas import Claim, Document, Lang
from linguistic_analysis import (
    ablation,
    agreement,
    baselines_bronze,
    claim_extraction,
    coreference,
    demo,
    evaluate,
    evaluate_double,
    factuality,
    modality,
    preprocessing,
    spo,
)
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


@pytest.fixture(autouse=True)
def _rules_mode_unless_slow(request, monkeypatch):
    """Hors tests « slow », l'analyse passe par les règles, comme en CI (sans spaCy/Stanza)."""
    if request.node.get_closest_marker("slow") is None:
        monkeypatch.setattr(preprocessing, "get_parser", lambda lang: None)


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
    assert claim.modality == "rapporté" and "rapporté:selon" in claim.triggers


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
        assert preprocessing._load_spacy_fr() is None
        assert preprocessing._load_stanza_ar() is None
    finally:
        preprocessing._load_spacy_fr.cache_clear()
        preprocessing._load_stanza_ar.cache_clear()


# Avant son remplacement par la fixture automatique (mode règles hors tests « slow »).
_GET_PARSER = preprocessing.get_parser


def test_incompatible_spacy_model_falls_back_to_rules(monkeypatch):
    # Modèle installé mais incompatible : `spacy.load` lève une exception.
    def load(name):
        raise OSError(f"{name} : modèle incompatible")

    monkeypatch.setitem(sys.modules, "spacy", types.SimpleNamespace(load=load))
    monkeypatch.setattr(preprocessing, "_is_installed", lambda module: True)
    monkeypatch.setattr(preprocessing, "get_parser", _GET_PARSER)
    preprocessing._load_spacy_fr.cache_clear()
    try:
        (s,) = preprocessing.analyze(normalize("Le ministre a annoncé une hausse des prix."))
    finally:
        preprocessing._load_spacy_fr.cache_clear()
    assert s.parser == "rules" and s.lang == Lang.FR


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


# --- Tâche 3 : fait vs opinion ----------------------------------------------------------


def _sentence(text):
    (sentence,) = preprocessing.analyze(normalize(text))
    return sentence


FACT_OPINION_CASES = [
    # Français
    ("fait", "Le taux de chômage a atteint 16,4 % en 2023."),
    ("fait", "Le ministre de la Santé a visité Sfax hier."),
    ("opinion", "Je pense que cette réforme est une catastrophe pour les jeunes."),
    ("opinion", "C'est scandaleux et totalement inacceptable."),
    # Arabe standard
    ("fait", "ارتفعت نسبة التضخم في تونس إلى 9,3 بالمئة خلال شهر جانفي."),
    ("fait", "حسب المعهد الوطني للإحصاء، بلغ عدد السكان 12 مليون نسمة."),
    ("opinion", "أعتقد أن هذا القرار سيضر بالاقتصاد الوطني."),
    ("opinion", "للأسف، الوضع الاقتصادي كارثي."),
    # Tunisien en lettres arabes
    ("fait", "الحكومة قالت إلي الأسعار باش تنقص 5 بالمئة الشهر الجاي."),
    ("fait", "الوزير زار صفاقس نهار الاثنين."),
    ("opinion", "نحس اللي الوضع خايب برشا."),
    ("opinion", "يا ريت الحكومة تعمل حاجة للشباب."),
    # Tunisien en arabizi
    ("fait", "El 7koma 9alet elli el as3ar bech tan9es 5 fel miya."),
    ("fait", "El ministre zar Sfax nhar el thnin."),
    ("opinion", "Ena n7ess elli el wadh3 khayeb barcha."),
    ("opinion", "Fi ra2yi el qarar hedha ghalet."),
]


@pytest.mark.parametrize(("gold", "text"), FACT_OPINION_CASES)
def test_classify_factuality_rules(gold, text):
    is_opinion, confidence, triggers = factuality.classify_factuality(_sentence(text))
    assert is_opinion == (gold == "opinion"), triggers
    assert 0.5 <= confidence <= 1.0
    assert all(t.split(":", 1)[0] in {"opinion", "question", "souhait", "fait"} for t in triggers)


@pytest.mark.parametrize(
    ("text", "expected_trigger"),
    [
        ("Est-ce que le chômage a baissé en 2024 ?", "question:?"),
        ("هل ارتفعت الأسعار في تونس", "question:هل"),
        ("Inchallah el 7koma tna9es el as3ar.", "souhait:inchallah"),
    ],
)
def test_questions_and_wishes_are_not_factual(text, expected_trigger):
    is_opinion, _, triggers = factuality.classify_factuality(_sentence(text))
    assert is_opinion and expected_trigger in triggers


def test_opinion_verb_third_person_is_not_opinion():
    is_opinion, _, triggers = factuality.classify_factuality(
        _sentence("Le ministre pense que la réforme avance bien.")
    )
    assert not is_opinion
    assert not any(t.startswith("opinion:1re_personne") for t in triggers)


def test_opinion_verb_with_precise_data_stays_factual():
    is_opinion, _, triggers = factuality.classify_factuality(
        _sentence("Je pense que le chômage a atteint 16 % en 2023.")
    )
    assert "opinion:1re_personne:pense" in triggers and not is_opinion


def test_intensifier_ignored_when_number_present():
    _, _, triggers = factuality.classify_factuality(
        _sentence("Le chômage a très fortement augmenté de 5 % en 2024.")
    )
    assert not any(t.startswith("opinion:intensifieur") for t in triggers)


def test_lexicons_load_for_all_languages():
    for code in ("fr", "ar", "tn"):
        factuality.load_lexicon.cache_clear()
        lexicon = factuality.load_lexicon(code)
        assert {"expressions", "evaluatifs", "souhaits"} <= set(lexicon)


def _claim_as(text: str, lang: Lang):
    """Affirmation du texte normalisé, en lettres arabes, avec la langue annoncée forcée."""
    doc = normalize(text)
    (claim,) = extract_claims_detailed(
        Document(raw_text=doc.raw_text, text=doc.text, lang=lang, script="arabic")
    )
    return {
        key: getattr(claim, key)
        for key in ("is_claim", "is_opinion", "modality", "certainty", "triggers")
    }


# Le tunisien en lettres arabes emploie aussi les marqueurs de l'arabe standard, et le Lot A2
# peut l'étiqueter `ar` ou `tn` : en lettres arabes, le résultat ne dépend pas de `lang`.
@pytest.mark.parametrize(
    "item_id, expected",
    [("ar-03", "rapporté"), ("ar-07", "opinion"), ("ar-09", "hypothétique")],
)
def test_arabic_script_lexicons_ignore_announced_lang_eval(item_id, expected):
    (item,) = [it for it in evaluate.load_eval_set() if it["id"] == item_id]
    as_ar, as_tn = _claim_as(item["text"], Lang.AR), _claim_as(item["text"], Lang.TN)
    assert as_ar == as_tn
    assert as_tn["modality"] == expected


@pytest.mark.parametrize(
    "text, expected_modality, expected_trigger",
    [
        ("أعتقد أن الأسعار باش تهبط الشهر الجاي.", "opinion", "opinion:اعتقد"),
        ("حسب وزارة الصحة، برشا حالات جديدة تسجلت.", "rapporté", "rapporté:حسب"),
        ("من المحتمل أن الحكومة باش تزيد في الأجور.", "assertif", "incertitude:من المحتمل"),
    ],
    ids=["opinion", "rapporté", "incertitude"],
)
def test_arabic_script_lexicons_ignore_announced_lang_tunisian(
    text, expected_modality, expected_trigger
):
    as_ar, as_tn = _claim_as(text, Lang.AR), _claim_as(text, Lang.TN)
    assert as_ar == as_tn
    assert as_tn["modality"] == expected_modality
    assert expected_trigger in as_tn["triggers"]


def test_detailed_claims_carry_factuality():
    doc = normalize(
        "Le chômage a atteint 16 % en 2023. Je pense que cette réforme est une catastrophe."
    )
    fact, opinion = extract_claims_detailed(doc)
    assert not fact.is_opinion and "fait:nombre" in fact.triggers
    assert opinion.is_opinion and opinion.parser == "rules"
    assert len(extract_claims(doc)) == 2  # opinions transmises (point L5 non tranché)


@pytest.mark.slow
def test_factuality_tree_patterns_spacy():
    pytest.importorskip("spacy")
    if preprocessing.get_parser(Lang.FR) is None:
        pytest.skip("modèle fr_core_news_md absent")
    s = _sentence("Je pense que cette réforme est une catastrophe pour les jeunes.")
    assert s.parser == "spacy-fr"
    is_opinion, _, triggers = factuality.classify_factuality(s)
    assert is_opinion
    assert "opinion:complétive" in triggers
    assert "opinion:évaluatif:attribut:catastrophe" in triggers
    _, _, triggers = factuality.classify_factuality(_sentence("Le taux de chômage a atteint 16 %."))
    assert "fait:passé" in triggers


@pytest.mark.slow
@pytest.mark.parametrize(("gold", "text"), FACT_OPINION_CASES)
def test_classify_factuality_with_parsers(gold, text):
    is_opinion, _, triggers = factuality.classify_factuality(_sentence(text))
    assert is_opinion == (gold == "opinion"), triggers


# --- Tâche 4 : triplets sujet-prédicat-objet ---------------------------------------------


def _check_exact_extraction(sentence, triple):
    """Chaque élément (sauf prédicat implicite) est un extrait exact du texte du document."""
    for value, span in (
        (triple.subject, triple.subject_span),
        (triple.predicate, triple.predicate_span),
        (triple.obj, triple.obj_span),
    ):
        if span is not None:
            assert sentence.text[span[0] - sentence.start : span[1] - sentence.start] == value


SPO_RULES_CASES = [
    # (texte, sujet, prédicat, objet, discours rapporté) ; les compléments de temps sont hors objet
    # Français (sans parseur)
    ("Le taux de chômage a atteint 16,4 % en 2023.", "Le taux de chômage", "a atteint",
     "16,4 %", False),
    ("Le ministre a visité Sfax hier.", "Le ministre", "a visité", "Sfax", False),
    ("Le gouvernement a signé un accord avec le FMI.", "Le gouvernement", "a signé",
     "un accord avec le FMI", False),
    # Tunisien en lettres arabes (valeurs attendues = texte normalisé par le Lot A2)
    ("الحكومة قالت إلي الأسعار باش تنقص.", "الحكومه", "قالت", "الاسعار باش تنقص", True),
    ("الوزير زار صفاقس نهار الاثنين.", "الوزير", "زار", "صفاقس", False),
    ("الشركة عملت 200 خدمة جديدة.", "الشركه", "عملت", "200 خدمه جديده", False),
    # Tunisien en arabizi
    ("El 7koma 9alet elli el as3ar bech tan9es.", "El 7koma", "9alet",
     "el as3ar bech tan9es", True),
    ("El ministre zar Sfax nhar el thnin.", "El ministre", "zar", "Sfax", False),
    ("El cherka 3mlet 200 khedma jdida.", "El cherka", "3mlet", "200 khedma jdida", False),
]


@pytest.mark.parametrize(("text", "subject", "predicate", "obj", "reported"), SPO_RULES_CASES)
def test_spo_rules(text, subject, predicate, obj, reported):
    sentence = _sentence(text)
    triple = spo.extract_spo(sentence)
    assert (triple.subject, triple.predicate, triple.obj) == (subject, predicate, obj)
    assert triple.reported is reported
    assert triple.confidence <= 0.5
    _check_exact_extraction(sentence, triple)


def test_spo_rules_negation_and_passive():
    neg = spo.extract_spo(_sentence("Le chômage n'a pas baissé en 2024."))
    assert (neg.subject, neg.predicate, neg.obj) == ("Le chômage", "n'a pas baissé", None)
    assert neg.time == "en 2024"
    passive = spo.extract_spo(_sentence("120 nouveaux cas ont été enregistrés par le ministère."))
    assert passive.voice == "passive" and passive.predicate == "ont été enregistrés"
    assert passive.subject == "120 nouveaux cas" and passive.obj == "par le ministère"


def test_spo_rules_arabic_verb_first():
    triple = spo.extract_spo(_sentence("قال الوزير إن الأسعار ستنخفض."))
    assert (triple.subject, triple.predicate, triple.obj) == ("الوزير", "قال", "الاسعار ستنخفض")
    assert triple.reported


def test_spo_rules_speech_verb_without_complementizer_is_not_reported():
    triple = spo.extract_spo(_sentence("أعلن الوزير زيادة الأجور."))
    assert triple.predicate == "اعلن" and not triple.reported


def test_spo_rules_no_known_verb_returns_none():
    assert spo.extract_spo(_sentence("تفاقمت أزمة المياه في الجنوب.")) is None


def test_claims_now_carry_spo():
    (claim,) = extract_claims(normalize("Le taux de chômage a atteint 16,4 % en 2023."))
    assert (claim.subject, claim.predicate, claim.obj) == (
        "Le taux de chômage",
        "a atteint",
        "16,4 %",
    )


SPO_SPACY_CASES = [
    ("Le taux de chômage a atteint 16,4 % en 2023.", "Le taux de chômage", "a atteint", "16,4 %"),
    ("Le chômage est de 16 % en 2023.", "Le chômage", "est", "de 16 %"),
    ("Le chômage n'a pas baissé en 2024.", "Le chômage", "n'a pas baissé", None),
    ("Le ministre a déclaré que les prix allaient baisser.", "Le ministre", "a déclaré",
     "les prix allaient baisser"),
]


@pytest.mark.slow
@pytest.mark.parametrize(("text", "subject", "predicate", "obj"), SPO_SPACY_CASES)
def test_spo_spacy_fr(text, subject, predicate, obj):
    pytest.importorskip("spacy")
    if preprocessing.get_parser(Lang.FR) is None:
        pytest.skip("modèle fr_core_news_md absent")
    sentence = _sentence(text)
    assert sentence.parser == "spacy-fr"
    triple = spo.extract_spo(sentence)
    assert (triple.subject, triple.predicate, triple.obj) == (subject, predicate, obj)
    _check_exact_extraction(sentence, triple)


@pytest.mark.slow
def test_spo_spacy_passive():
    pytest.importorskip("spacy")
    if preprocessing.get_parser(Lang.FR) is None:
        pytest.skip("modèle fr_core_news_md absent")
    triple = spo.extract_spo(_sentence("120 nouveaux cas ont été enregistrés par le ministère."))
    assert triple.voice == "passive"
    assert (triple.subject, triple.predicate, triple.obj) == (
        "120 nouveaux cas",
        "ont été enregistrés",
        "par le ministère",
    )


@pytest.mark.slow
def test_spo_stanza_ar():
    pytest.importorskip("stanza")
    if preprocessing.get_parser(Lang.AR) is None:
        pytest.skip("modèle Stanza ar absent")
    # Ordre verbe-sujet-objet + discours rapporté
    reported = spo.extract_spo(_sentence("قال الوزير إن الأسعار ستنخفض."))
    assert (reported.subject, reported.predicate, reported.obj) == (
        "الوزير",
        "قال",
        "الاسعار ستنخفض",
    )
    assert reported.reported
    # Phrase nominale : prédicat implicite, seul élément non extrait du texte
    sentence = _sentence("البطالة مرتفعة في تونس.")
    nominal = spo.extract_spo(sentence)
    assert nominal.predicate == spo.IMPLICIT_PREDICATE and nominal.predicate_span is None
    assert nominal.subject == "البطاله" and nominal.obj == "مرتفعه"
    assert nominal.location == "في تونس"  # complément de lieu hors attribut
    _check_exact_extraction(sentence, nominal)


# --- Tâche 5 : modalité et incertitude -------------------------------------------------

MODALITY_CASES = [
    # Français
    ("assertif", "Le taux de chômage a atteint 16,4 % en 2023."),
    ("assertif", "Le ministre a visité Sfax hier."),
    ("rapporté", "Selon le ministère, les prix ont baissé de 3 %."),
    ("rapporté", "Le ministre a déclaré que les prix allaient baisser."),
    ("conditionnel", "Le gouvernement aurait signé un accord avec le FMI."),
    ("conditionnel", "Les prix pourraient augmenter de 5 % en 2025."),
    ("hypothétique", "Si les prix augmentaient, la consommation baisserait."),
    ("hypothétique", "Au cas où la réforme échoue, le chômage atteindra 20 %."),
    ("opinion", "Je pense que cette réforme est une catastrophe pour les jeunes."),
    ("opinion", "À mon avis, ce projet est ridicule."),
    ("interrogatif", "Est-ce que le chômage a baissé en 2024 ?"),
    ("interrogatif", "Le gouvernement a-t-il menti sur les chiffres ?"),
    ("souhait", "Pourvu que les prix baissent l'an prochain."),
    ("souhait", "J'espère que le chômage va baisser."),
    # Arabe standard (pas de conditionnel morphologique)
    ("assertif", "ارتفعت نسبة التضخم في تونس إلى 9,3 بالمئة."),
    ("assertif", "بلغ عدد السكان 12 مليون نسمة."),
    ("rapporté", "حسب المعهد الوطني للإحصاء، بلغ عدد السكان 12 مليون نسمة."),
    ("rapporté", "نقلا عن مصادر رسمية، ارتفعت الأسعار بنسبة 5 بالمئة."),
    ("hypothétique", "إذا ارتفعت الأسعار فإن الاستهلاك سينخفض."),
    ("hypothétique", "لو انخفضت الضرائب لارتفع الاستثمار."),
    ("opinion", "أعتقد أن هذا القرار سيضر بالاقتصاد الوطني."),
    ("opinion", "للأسف، الوضع الاقتصادي كارثي."),
    ("interrogatif", "هل ارتفعت الأسعار في تونس؟"),
    ("interrogatif", "لماذا ارتفعت الأسعار في تونس؟"),
    ("souhait", "أتمنى أن تنخفض الأسعار قريبا."),
    ("souhait", "إن شاء الله تنخفض الأسعار السنة القادمة."),
    # Tunisien (lettres arabes et arabizi)
    ("assertif", "El cherka 3mlet 200 khedma jdida."),
    ("assertif", "الشركة عملت 200 خدمة جديدة."),
    ("rapporté", "9alou elli el as3ar bech tzid 10 fel miya."),
    ("rapporté", "قالوا اللي الأسعار باش تزيد."),
    ("rapporté", "El 7koma 9alet elli el as3ar bech tan9es."),
    ("hypothétique", "Ken tzid el as3ar, ennes bech t3ani."),
    ("hypothétique", "Law el 7koma t9os el adha, el as3ar tahbet."),
    ("opinion", "Ena n7ess elli el wadh3 khayeb barcha."),
    ("opinion", "نحس اللي الوضع خايب برشا."),
    ("souhait", "Nchallah el as3ar tahbet."),
    ("souhait", "يا ريت الحكومة تعمل حاجة للشباب."),
    ("interrogatif", "3lech el as3ar tal3et ?"),
    ("interrogatif", "علاش الأسعار طلعت؟"),
]


@pytest.mark.parametrize(("gold", "text"), MODALITY_CASES)
def test_detect_modality_rules(gold, text):
    label, certainty, triggers = modality.detect_modality(_sentence(text))
    assert label == gold, triggers
    assert label in MODALITY_LABELS and 0.0 <= certainty <= 1.0


def test_modality_default_is_assertif():
    assert modality.detect_modality(_sentence("Le taux de chômage a atteint 16,4 % en 2023.")) == (
        "assertif",
        1.0,
        [],
    )


@pytest.mark.parametrize(
    "text",
    [
        "Le chômage a probablement baissé en 2024.",
        "ربما ارتفعت الأسعار بنسبة 5 بالمئة.",
        "قد ترتفع الأسعار في الأشهر القادمة.",
        "Ymken el as3ar tzid el chhar ejjay.",
    ],
)
def test_uncertainty_lowers_certainty_without_changing_label(text):
    label, certainty, triggers = modality.detect_modality(_sentence(text))
    assert label == "assertif" and certainty < 1.0
    assert any(t.startswith("incertitude:") for t in triggers)


def test_negated_certainty_lowers_certainty_further():
    _, plain, _ = modality.detect_modality(_sentence("Le chômage a probablement baissé en 2024."))
    _, negated, triggers = modality.detect_modality(
        _sentence("Il n'est pas certain que le chômage ait probablement baissé en 2024.")
    )
    assert negated < plain
    assert any(t.startswith("certitude_niée:") for t in triggers)


def test_future_lowers_certainty_only():
    label, certainty, triggers = modality.detect_modality(
        _sentence("El 7koma bech tna9es el as3ar fel chhar ejjay.")
    )
    assert label == "assertif" and certainty < 1.0 and "futur:bech" in triggers


def test_self_source_is_not_reported():
    sentence = _sentence("Selon moi, le chômage a baissé de 2 %.")
    label, _, triggers = modality.detect_modality(sentence)
    assert label != "rapporté"
    assert not any(t.startswith("rapporté:") for t in triggers)


def test_modality_priority_question_over_reported():
    label, _, triggers = modality.detect_modality(
        _sentence("Selon le ministère, les prix ont-ils baissé ?")
    )
    assert label == "interrogatif" and "rapporté:selon" in triggers


def test_claims_carry_new_modality_labels():
    doc = normalize("Le gouvernement aurait signé un accord avec le FMI.")
    (claim,) = extract_claims(doc)
    assert claim.modality == "conditionnel"
    (detailed,) = extract_claims_detailed(doc)
    assert detailed.certainty == 0.5


@pytest.mark.slow
def test_modality_conditional_morphology_spacy():
    pytest.importorskip("spacy")
    if preprocessing.get_parser(Lang.FR) is None:
        pytest.skip("modèle fr_core_news_md absent")
    # « baisserait » n'est pas dans le lexique : seul le trait Mood=Cnd le détecte.
    label, _, triggers = modality.detect_modality(_sentence("Le chômage baisserait l'an prochain."))
    assert label == "conditionnel" and "conditionnel:Mood=Cnd" in triggers


@pytest.mark.slow
@pytest.mark.parametrize(("gold", "text"), MODALITY_CASES)
def test_detect_modality_with_parsers(gold, text):
    label, _, triggers = modality.detect_modality(_sentence(text))
    assert label == gold, triggers


# --- Tâche 6 : coréférence basique -----------------------------------------------------


def _resolve_last(text):
    """(phrase résolue, journal) pour la dernière phrase du texte."""
    result = coreference.resolve_with_log(preprocessing.analyze(normalize(text)))[-1]
    return result.resolved_text, result.log


COREF_RESOLVED_CASES = [
    # (texte, dernière phrase attendue après résolution)
    ("Le ministre a visité Sfax. Il a annoncé 200 emplois.", "Le ministre a annoncé 200 emplois."),
    ("La ministre a visité Sfax. Elle a annoncé 200 emplois.",
     "La ministre a annoncé 200 emplois."),
    ("Les syndicats ont rencontré le ministre. Ils ont obtenu une hausse de 5 %.",
     "Les syndicats ont obtenu une hausse de 5 %."),
    # Arabe et tunisien (valeurs attendues = texte normalisé par le Lot A2)
    ("الوزير زار صفاقس. هو أعلن عن 200 موطن شغل.", "الوزير اعلن عن 200 موطن شغل."),
    ("زار الوزير صفاقس. وهو أعلن عن 200 موطن شغل.", "والوزير اعلن عن 200 موطن شغل."),
    ("الوزيرة زارت صفاقس. هي أعلنت عن مشروع جديد.", "الوزيره اعلنت عن مشروع جديد."),
    ("El ministre zar Sfax. Howa a3len 200 khedma.", "El ministre a3len 200 khedma."),
]


@pytest.mark.parametrize(("text", "expected"), COREF_RESOLVED_CASES)
def test_coreference_resolves_subject_pronoun(text, expected):
    resolved, log = _resolve_last(text)
    assert resolved == expected
    assert len(log) == 1 and "→" in log[0]


@pytest.mark.parametrize(
    "text",
    [
        "Il a annoncé 200 emplois dans la région.",  # aucun antécédent
        "Le ministre a visité Sfax. Il y a 200 chômeurs dans la région.",  # « il » impersonnel
        "La ministre a visité Sfax. Il a annoncé 200 emplois.",  # genre incompatible
        "Une délégation de Sfax est arrivée. Elle a rencontré le gouverneur.",  # sujet indéfini
        # antécédent hors de la fenêtre de 2 phrases
        "Le ministre a visité Sfax. La visite a duré deux heures. "
        "Les habitants étaient nombreux. Il a annoncé 200 emplois.",
    ],
)
def test_coreference_abstains_without_safe_antecedent(text):
    doc = normalize(text)
    resolved, log = _resolve_last(text)
    assert resolved == preprocessing.analyze(doc)[-1].text and log == []


def test_coreference_follows_chains():
    resolved, log = _resolve_last(
        "Le ministre a visité Sfax. Il a annoncé 200 emplois. Il a promis une nouvelle usine."
    )
    assert resolved == "Le ministre a promis une nouvelle usine."
    assert log == ["Il → Le ministre"]


def test_resolve_keeps_order_length_and_original_text():
    doc = normalize("Le ministre a visité Sfax. Il a annoncé 200 emplois.")
    sentences = preprocessing.analyze(doc)
    resolved = coreference.resolve(sentences)
    assert len(resolved) == len(sentences)
    assert resolved[0] == sentences[0].text
    assert doc.text[sentences[1].start : sentences[1].end] == "Il a annoncé 200 emplois."


def test_detailed_claims_carry_resolution():
    doc = normalize("Le ministre a visité Sfax hier. Il a annoncé 200 emplois.")
    first, second = extract_claims_detailed(doc)
    assert first.resolved_text == first.text and first.resolution_log == []
    assert second.text == "Il a annoncé 200 emplois."
    assert second.resolved_text == "Le ministre a annoncé 200 emplois."
    assert second.resolution_log == ["Il → Le ministre"]
    assert extract_claims(doc)[1].text == "Il a annoncé 200 emplois."  # contrat : phrase d'origine


def test_short_sentence_still_provides_antecedent():
    # « الوزير زار صفاقس. » (3 mots) est écartée des affirmations mais sert d'antécédent.
    (claim,) = extract_claims_detailed(normalize("الوزير زار صفاقس. هو أعلن عن 200 موطن شغل."))
    assert claim.text == "هو اعلن عن 200 موطن شغل."
    assert claim.resolved_text == "الوزير اعلن عن 200 موطن شغل."


@pytest.mark.slow
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Le ministre a visité Sfax. Il a annoncé 200 emplois.",
         "Le ministre a annoncé 200 emplois."),
        ("La ministre a visité Sfax. Elle a annoncé 200 emplois.",
         "La ministre a annoncé 200 emplois."),
        ("Kaïs Saïed a reçu le ministre. Il a demandé des chiffres précis.",
         "Kaïs Saïed a demandé des chiffres précis."),
        ("الوزير زار صفاقس. هو أعلن عن 200 موطن شغل.", "الوزير اعلن عن 200 موطن شغل."),
    ],
)
def test_coreference_with_parsers(text, expected):
    resolved, _ = _resolve_last(text)
    assert resolved == expected


@pytest.mark.slow
def test_coreference_with_parsers_abstains_on_gender_mismatch():
    resolved, log = _resolve_last("La ministre a visité Sfax. Il a annoncé 200 emplois.")
    assert resolved == "Il a annoncé 200 emplois." and log == []


# --- Tâche 8 : jeu d'évaluation annoté (eval_30) ------------------------------------------

EVAL_ITEMS = evaluate.load_eval_set()
REQUIRED_PHENOMENA = {
    "fait_chiffré", "opinion", "question", "rapporté", "conditionnel_journalistique", "copule",
    "phrase_nominale", "passif", "négation", "coréférence", "code_switching",
}


def _eval_params(items, field):
    """Paramètres pytest ; `xfail(strict=False)` si le cas est marqué difficile pour `field`."""
    params = []
    for item in items:
        reason = item.get("known_hard", {}).get(field)
        marks = [pytest.mark.xfail(strict=False, reason=reason)] if reason else []
        params.append(pytest.param(item, id=item["id"], marks=marks))
    return params


def test_eval_set_structure_and_coverage():
    assert len(EVAL_ITEMS) >= 30
    assert len({it["id"] for it in EVAL_ITEMS}) == len(EVAL_ITEMS)
    groups = [evaluate.group_of(it) for it in EVAL_ITEMS]
    minimum = {"fr-latin": 10, "ar-arabic": 10, "tn-arabic": 5, "tn-arabizi": 5, "tn-mixed": 3}
    for group, n in minimum.items():
        assert groups.count(group) >= n, group
    assert REQUIRED_PHENOMENA <= {p for it in EVAL_ITEMS for p in it["phenomena"]}
    for it in EVAL_ITEMS:
        gold = it["gold"]
        assert {"is_claim", "subject", "predicate", "obj", "modality"} <= set(gold), it["id"]
        assert gold["modality"] in MODALITY_LABELS, it["id"]
        if "coréférence" in it["phenomena"]:
            assert it.get("context") and gold.get("resolved_text"), it["id"]


@pytest.mark.parametrize("item", _eval_params(EVAL_ITEMS, "is_claim"))
def test_eval_is_claim(item):
    assert evaluate.predict(item)["is_claim"] is item["gold"]["is_claim"]


@pytest.mark.parametrize("item", _eval_params(EVAL_ITEMS, "modality"))
def test_eval_modality(item):
    assert evaluate.predict(item)["modality"] == item["gold"]["modality"]


@pytest.mark.parametrize(
    "item", _eval_params([it for it in EVAL_ITEMS if it["gold"]["is_claim"]], "spo")
)
def test_eval_spo_exact(item):
    pred = evaluate.predict(item)
    for role in evaluate.ROLES:
        assert evaluate.exact_match(item["gold"][role], pred[role]), (role, pred[role])


@pytest.mark.parametrize(
    "item", _eval_params([it for it in EVAL_ITEMS if it["gold"].get("resolved_text")], "coref")
)
def test_eval_coreference(item):
    pred = evaluate.predict(item)
    assert evaluate.exact_match(item["gold"]["resolved_text"], pred["resolved_text"])


def test_eval_matching_helpers():
    assert evaluate.exact_match("La Banque", "la banque.")
    assert evaluate.exact_match("صابة الحبوب", "صابه الحبوب")  # forme repliée (ة→ه)
    assert evaluate.exact_match(None, None) and not evaluate.exact_match("x", None)
    assert evaluate.token_f1("de 12 %", "de 12 % en 2024") == pytest.approx(0.75)
    assert evaluate.token_f1(None, None) == 1.0 and evaluate.token_f1("x", None) == 0.0


def test_evaluate_writes_results(tmp_path):
    results = evaluate.evaluate(EVAL_ITEMS, rules=True)
    path = evaluate.write_results(results, tmp_path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert path.name.startswith("lot-b_extraction_regles_")
    assert saved["lot"] == "B" and saved["exp_id"] == evaluate.EXP_ID
    metrics = saved["metrics"]
    groups = {"fr-latin", "ar-arabic", "tn-arabic", "tn-arabizi", "tn-mixed"}
    assert set(metrics["by_lang"]) == groups
    assert metrics["n"] == len(EVAL_ITEMS) and len(saved["items"]) == len(EVAL_ITEMS)
    for key in ("is_claim_accuracy", "is_claim_macro_f1", "modality_accuracy", "coref_accuracy"):
        assert 0.0 <= metrics[key] <= 1.0


def test_hypothesis_is_not_a_claim():
    (claim,) = extract_claims_detailed(normalize("إذا استمر الجفاف فإن الإنتاج الفلاحي سينخفض."))
    assert claim.modality == "hypothétique" and not claim.is_opinion and not claim.is_claim


def test_percent_kept_at_span_edge():
    triple = spo.extract_spo(_sentence("Selon l'INS, l'inflation a reculé à 7 %."))
    assert triple.obj == "à 7 %"


def test_vso_reported_subject_up_to_complementizer():
    triple = spo.extract_spo(_sentence("قال وزير الفلاحة إن صابة الحبوب بلغت 2 مليون طن."))
    assert triple.subject == "وزير الفلاحه" and triple.reported
    assert triple.obj == "صابه الحبوب بلغت 2 مليون طن"


# --- Tâche 9 : analyse d'erreurs ---------------------------------------------------------

ERROR_CATEGORIES = json.loads((FIXTURES / "error_categories.json").read_text(encoding="utf-8"))
VALID_CATEGORIES = {f"E{k}" for k in range(1, 9)}


def _error_keys(results):
    return {f"{e['id']}:{e['field']}" for e in evaluate.find_errors(results)}


def test_error_categories_are_valid():
    for mode in ("regles", "parseurs"):
        for key, entry in ERROR_CATEGORIES[mode].items():
            assert entry["cat"] in VALID_CATEGORIES and entry["cause"], (mode, key)


def test_error_categories_match_rules_errors():
    # Si le système change, l'analyse d'erreurs (docs/lot-b_analyse_erreurs_bronze.md)
    # est à refaire.
    results = evaluate.evaluate(EVAL_ITEMS, rules=True)
    assert _error_keys(results) == set(ERROR_CATEGORIES["regles"])


def test_find_errors_fields():
    results = evaluate.evaluate(EVAL_ITEMS, rules=True)
    expected = {"id", "group", "field", "gold", "pred", "parser", "triggers", "resolution_log"}
    for error in evaluate.find_errors(results):
        assert expected <= set(error)
        assert error["field"] in {"is_claim", "modality", "resolved_text", *evaluate.ROLES}


def test_cli_errors_export(tmp_path, capsys):
    evaluate.main(["--rules", "--errors", "--out-dir", str(tmp_path)])
    names = sorted(path.name for path in tmp_path.iterdir())
    assert any(n.startswith("lot-b_erreurs_regles_") for n in names)
    assert any(n.startswith("lot-b_extraction_regles_") for n in names)
    assert "erreur(s)" in capsys.readouterr().out


def _cli_outputs(tmp_path) -> tuple[dict, dict]:
    """Résultats et erreurs écrits par la ligne de commande dans `tmp_path`."""
    def load(prefix):
        (path,) = [p for p in tmp_path.iterdir() if p.name.startswith(prefix)]
        return json.loads(path.read_text(encoding="utf-8"))

    return load("lot-b_extraction_regles_"), load("lot-b_erreurs_regles_")


def test_cli_exp_id_default_is_unchanged(tmp_path, capsys):
    evaluate.main(["--rules", "--errors", "--bootstrap", "0", "--out-dir", str(tmp_path)])
    results, errors = _cli_outputs(tmp_path)
    assert results["exp_id"] == errors["exp_id"] == evaluate.EXP_ID
    assert capsys.readouterr().out.startswith(f"{evaluate.EXP_ID} — mode regles")


def test_cli_exp_id_option_replaces_default(tmp_path, capsys):
    evaluate.main(["--rules", "--errors", "--bootstrap", "0", "--exp-id", "EXP-B-099",
                   "--out-dir", str(tmp_path)])
    results, errors = _cli_outputs(tmp_path)
    assert results["exp_id"] == errors["exp_id"] == "EXP-B-099"
    out = capsys.readouterr().out
    assert out.startswith("EXP-B-099 — mode regles") and evaluate.EXP_ID not in out
    # Le nom des fichiers ne dépend pas de l'identifiant.
    assert all("EXP" not in p.name for p in tmp_path.iterdir())


def test_cli_exp_id_reaches_comparison(tmp_path):
    evaluate.main(["--compare", "--bootstrap", "0", "--exp-id", "EXP-B-099",
                   "--out-dir", str(tmp_path)])
    (path,) = list(tmp_path.glob("lot-b_comparaison_*.json"))
    assert json.loads(path.read_text(encoding="utf-8"))["exp_id"] == "EXP-B-099"
    for result in tmp_path.glob("lot-b_extraction_*.json"):
        assert json.loads(result.read_text(encoding="utf-8"))["exp_id"] == "EXP-B-099"


@pytest.mark.parametrize(
    "value",
    ["EXP-B-12", "EXP-B-1234", "EXP-C-001", "exp-b-001", "EXP-B-01a", " EXP-B-001", "",
     "EXP-B-\u0661\u0662\u0663"],
)
def test_cli_exp_id_invalid_format_is_refused(tmp_path, capsys, value):
    with pytest.raises(SystemExit) as exc:
        evaluate.main(["--rules", "--exp-id", value, "--out-dir", str(tmp_path)])
    assert exc.value.code == 2
    assert "EXP-B-NNN" in capsys.readouterr().err
    assert not any(tmp_path.iterdir())


def test_cli_output_survives_cp1252_console(tmp_path):
    # Console Windows ou sortie redirigée : encodage cp1252, sans `-X utf8`. Les erreurs listées
    # contiennent de l'arabe (ar-02), que cp1252 ne sait pas encoder.
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
    env |= {"PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    command = [sys.executable, "-m", "linguistic_analysis.evaluate", "--rules", "--errors",
               "--bootstrap", "0", "--out-dir", str(tmp_path)]
    done = subprocess.run(command, cwd=Path(__file__).resolve().parents[1], env=env,
                          capture_output=True, timeout=300)
    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")[-500:]
    assert "ar-02" in done.stdout.decode("utf-8")


@pytest.mark.slow
def test_error_categories_match_parser_errors():
    pytest.importorskip("spacy")
    pytest.importorskip("stanza")
    if preprocessing.get_parser(Lang.FR) is None or preprocessing.get_parser(Lang.AR) is None:
        pytest.skip("modèles spaCy / Stanza absents")
    results = evaluate.evaluate(EVAL_ITEMS)
    assert _error_keys(results) == set(ERROR_CATEGORIES["parseurs"])


# --- Silver : compléments de source / temps / lieu hors objet --------------------------------

ADJUNCT_RULES_CASES = [
    # (texte, objet, source, temps, lieu) — mode règles, phrases hors du jeu d'évaluation
    ("Le chômage a atteint 16 % au premier trimestre, selon l'INS.", "16 %", "l'INS",
     "au premier trimestre", None),
    ("La société a recruté 300 ingénieurs à Sousse en 2023.", "300 ingénieurs", None,
     "en 2023", "à Sousse"),
    ("Les pluies ont endommagé les routes la semaine dernière à Kasserine.", "les routes", None,
     "la semaine dernière", "à Kasserine"),
    ("Les prix ont baissé de 5 % depuis le mois de mars.", "de 5 %", None,
     "depuis le mois de mars", None),
    ("Le taux de chômage était de 15 % en 2022.", "de 15 %", None, "en 2022", None),
    ("El cherka 3mlet 200 khedma jdida fi Sfax.", "200 khedma jdida", None, None, "fi Sfax"),
    # Restent dans l'objet : nombre + nom de temps, nombre seul, lieu non répertorié, personne
    ("Le ministre est resté 100 jours en poste.", "100 jours en poste", None, None, None),
    ("L'usine a produit 2024 voitures.", "2024 voitures", None, None, None),
    ("Le tribunal a condamné l'ancien ministre à dix ans de prison.",
     "l'ancien ministre à dix ans de prison", None, None, None),
    ("Le gouvernement a écrit au Président de la République.",
     "au Président de la République", None, None, None),
]


@pytest.mark.parametrize(("text", "obj", "source", "time", "location"), ADJUNCT_RULES_CASES)
def test_spo_rules_adjuncts_out_of_object(text, obj, source, time, location):
    triple = spo.extract_spo(_sentence(text))
    assert (triple.obj, triple.source, triple.time, triple.location) == (
        obj, source, time, location
    )


def test_spo_rules_leading_source_removed_from_subject():
    triple = spo.extract_spo(_sentence("D'après la Banque mondiale, la croissance a atteint 2 %."))
    assert (triple.subject, triple.obj) == ("la croissance", "2 %")
    assert triple.source == "la Banque mondiale"


def test_spo_rules_reported_clause_kept_whole():
    triple = spo.extract_spo(_sentence("El wali 9al elli el mashrou3 bech yabda fi Sfax."))
    assert triple.reported and triple.obj == "el mashrou3 bech yabda fi Sfax"
    assert triple.location is None


def test_adjunct_kind_lexicon():
    def kind(text):
        return spo.adjunct_kind(_sentence(text).tokens)

    assert kind("en 2024.") == "time" and kind("2024.") is None  # année : préposition requise
    assert kind("يوم الجمعة.") == "time" and kind("منذ شهر جانفي.") == "time"
    assert kind("في صفاقس.") == "location" and kind("صفاقس.") is None
    assert kind("حسب البنك المركزي.") == "source"
    assert kind("100 jours.") is None and kind("à 7 %.") is None


def test_detailed_claim_carries_adjuncts():
    (claim,) = extract_claims_detailed(normalize("Selon l'INS, le chômage a atteint 16 % en 2023."))
    assert (claim.obj, claim.source, claim.time) == ("16 %", "l'INS", "en 2023")
    assert {"source", "time", "location"} <= set(asdict(claim))
    assert "source" not in {f.name for f in fields(Claim)}  # contrat partagé inchangé


@pytest.mark.slow
def test_spo_parsers_adjuncts():
    if preprocessing.get_parser(Lang.FR) is None or preprocessing.get_parser(Lang.AR) is None:
        pytest.skip("modèles spaCy / Stanza absents")
    fr = spo.extract_spo(_sentence("La société a recruté 300 ingénieurs à Sousse en 2023."))
    assert (fr.obj, fr.time, fr.location) == ("300 ingénieurs", "en 2023", "à Sousse")
    ar = spo.extract_spo(_sentence("افتتحت الوزارة مستشفى جديدا في صفاقس يوم الاثنين."))
    assert (ar.subject, ar.obj) == ("الوزاره", "مستشفي جديدا")
    assert (ar.time, ar.location) == ("يوم الاثنين", "في صفاقس")
    duration = spo.extract_spo(_sentence("Le ministre est resté 100 jours en poste."))
    assert duration.obj == "100 jours" and duration.time is None


# --- Silver : lexique verbal du mode règles et sujet verbe-sujet-objet ----------------------

VERB_RULES_CASES = [
    # (texte, sujet, prédicat, objet) — mode règles, phrases hors du jeu d'évaluation
    # Français : formes conjuguées générées, auxiliaire au conditionnel, modal + infinitif
    ("La production de phosphate progresse depuis mars.", "La production de phosphate",
     "progresse", None),
    ("Les autorités auraient arrêté trois suspects.", "Les autorités", "auraient arrêté",
     "trois suspects"),
    ("Le déficit commercial pourrait dépasser 20 milliards de dinars.", "Le déficit commercial",
     "pourrait dépasser", "20 milliards de dinars"),
    ("Le gouvernement va construire un nouvel hôpital.", "Le gouvernement", "va construire",
     "un nouvel hôpital"),
    # Arabe standard, verbe en tête : intransitif (jusqu'à la limite) ou chaîne d'annexion
    ("انخفض سعر صرف الدينار مقابل الأورو.", "سعر صرف الدينار", "انخفض", "مقابل الاورو"),
    ("تراجعت صادرات زيت الزيتون بنسبة 10 بالمئة.", "صادرات زيت الزيتون", "تراجعت",
     "بنسبه 10 بالمئه"),
    ("سجلت الشركة الوطنية أرباحا قياسية.", "الشركه الوطنيه", "سجلت", "ارباحا قياسيه"),
    ("افتتحت الوزارة مستشفى جديدا.", "الوزاره", "افتتحت", "مستشفي جديدا"),
    ("قرر البنك المركزي رفع نسبة الفائدة.", "البنك المركزي", "قرر", "رفع نسبه الفائده"),
    # Tunisien : flexions et négation ما…ش
    ("الحكومة ما زادتش في الشهرية.", "الحكومه", "ما زادتش", "في الشهريه"),
    ("El as3ar ma hbatetch.", "El as3ar", "ma hbatetch", None),
    ("Les loyers tal3ou barcha.", "Les loyers", "tal3ou", "barcha"),
]


@pytest.mark.parametrize(("text", "subject", "predicate", "obj"), VERB_RULES_CASES)
def test_spo_rules_verb_lexicon(text, subject, predicate, obj):
    triple = spo.extract_spo(_sentence(text))
    assert (triple.subject, triple.predicate, triple.obj) == (subject, predicate, obj)


def test_rules_verb_forms_generated():
    def upos(word):
        return _sentence(f"{word} x y z.").tokens[0].upos

    for word in ("progresse", "baissaient", "lança", "يرتفع", "سترتفع", "وارتفعت", "هبطتش"):
        assert upos(word) == "VERB", word
    assert upos("tunis") == "X" and upos("بين") != "VERB"


def test_spo_rules_noun_after_determiner_is_not_a_verb():
    triple = spo.extract_spo(_sentence("La visite du ministre a duré deux heures."))
    assert (triple.subject, triple.predicate) == ("La visite du ministre", "a duré")


def test_coreference_rules_arabic_annexation_antecedent():
    text = "استقبل وزير الصحة وفدا أجنبيا. وهو أكد أهمية التعاون."
    claims = extract_claims_detailed(normalize(text))
    assert claims[-1].resolution_log == ["وهو → وزير الصحه"]


# --- Silver : source du discours rapporté --------------------------------------------------

SOURCE_RULES_CASES = [
    # (texte, objet, source, discours rapporté) — mode règles, phrases hors du jeu d'évaluation
    ("Le porte-parole du gouvernement a annoncé que les salaires seront augmentés.",
     "les salaires seront augmentés", "Le porte-parole du gouvernement", True),
    ("Les prix vont baisser, a déclaré le ministre du Commerce.", None,
     "le ministre du Commerce", True),
    ("Le chômage a reculé à 15 %, affirme l'Institut national de la statistique.", "à 15 %",
     "l'Institut national de la statistique", True),
    ("صرح وزير التجارة بأن الأسعار ستنخفض.", "الاسعار ستنخفض", "وزير التجاره", True),
    ("ارتفعت الصادرات بنسبة 5 بالمئة حسب ما أفاد به المعهد الوطني للإحصاء.", "بنسبه 5 بالمئه",
     "المعهد الوطني للاحصاء", False),
    ("El wali 9al elli el mashrou3 bech yabda.", "el mashrou3 bech yabda", "El wali", True),
    ("9alou elli el banka bech tzid el faida.", "el banka bech tzid el faida", None, True),
    # Pas de discours rapporté : pas de complétive, ou virgule suivie d'autre chose qu'une incise
    ("Le ministre a annoncé la fermeture de trois usines.", "la fermeture de trois usines",
     None, False),
    ("Le contrat a été signé, annonce publiée hier par la société.",
     "annonce publiée hier par la société", None, False),
    ("Les ventes ont baissé, ce qui inquiète les commerçants.",
     "ce qui inquiète les commerçants", None, False),
]


@pytest.mark.parametrize(("text", "obj", "source", "reported"), SOURCE_RULES_CASES)
def test_spo_rules_reported_source(text, obj, source, reported):
    triple = spo.extract_spo(_sentence(text))
    assert (triple.obj, triple.source, triple.reported) == (obj, source, reported)


def test_incise_gives_reported_modality():
    (claim,) = extract_claims_detailed(normalize("Les prix vont baisser, a déclaré le ministre."))
    assert claim.modality == "rapporté" and claim.source == "le ministre"


def test_pronoun_source_replaced_by_antecedent():
    text = "La ministre de la Santé a visité Sfax. Elle a affirmé que 40 lits seront ajoutés."
    claim = extract_claims_detailed(normalize(text))[-1]
    assert claim.subject == "Elle" and claim.source == "La ministre de la Santé"


@pytest.mark.slow
def test_spo_parsers_reported_source():
    if preprocessing.get_parser(Lang.FR) is None:
        pytest.skip("modèle spaCy absent")
    incise = spo.extract_spo(_sentence("Les prix vont baisser, a déclaré le ministre du Commerce."))
    assert incise.reported and incise.source == "le ministre du Commerce"
    inverted = spo.extract_spo(_sentence("Le chômage a reculé à 15 %, affirme l'INS."))
    assert (inverted.obj, inverted.source) == ("à 15 %", "l'INS")
    speech = spo.extract_spo(_sentence("Le ministre a affirmé que le déficit avait baissé."))
    assert speech.source == "Le ministre"


# --- Silver : complément du participe dans le sujet (verbe arabe en tête) ------------------

PARTICIPLE_RULES_CASES = [
    # (texte, sujet, objet) — mode règles, verbe intransitif en tête, phrases hors du jeu
    ("ارتفع عدد التونسيين المقيمين في فرنسا.", "عدد التونسيين المقيمين في فرنسا", None),
    ("تراجع عدد العاملين في القطاع الفلاحي بنسبة 3 بالمئة.", "عدد العاملين في القطاع الفلاحي",
     "بنسبه 3 بالمئه"),
    ("انخفضت أسعار المواد المستوردة من الخارج.", "اسعار المواد المستورده من الخارج", None),
    # Restent hors du sujet : nombre après la préposition, nom qui n'est pas un participe
    ("وصل عدد الوافدين إلى 2 مليون.", "عدد الوافدين", "الي 2 مليون"),
    ("ارتفع عدد المشاريع في الجهة.", "عدد المشاريع", "في الجهه"),
]


@pytest.mark.parametrize(("text", "subject", "obj"), PARTICIPLE_RULES_CASES)
def test_spo_rules_participle_complement_in_subject(text, subject, obj):
    triple = spo.extract_spo(_sentence(text))
    assert (triple.subject, triple.obj) == (subject, obj)


def test_french_participle_endings_unaffected():
    # Garde-fou : le motif des participes arabes ne doit pas remplacer celui du français.
    triple = spo.extract_spo(_sentence("Les exportations ont progressé de 5 %."))
    assert (triple.predicate, triple.obj) == ("ont progressé", "de 5 %")


# --- Silver : conjonction « و » / « ف » collée au verbe de parole --------------------------

ATTACHED_SPEECH = "وقال وزير الصحة إن عدد الإصابات تراجع بشكل كبير."


def _stanza_like(text, words):
    """Phrase analysée comme par Stanza, sans le modèle. `words` : (mot, token d'origine ou None
    pour un mot du même token multi-mots, upos, tête, relation) ; les mots d'un même token
    partagent son empan, comme dans `preprocessing._analyze_stanza`."""
    tokens, position, span = [], 0, (0, 0)
    for i, (word, surface, upos, head, deprel) in enumerate(words):
        if surface is not None:
            start = text.index(surface, position)
            span, position = (start, start + len(surface)), start + len(surface)
        tokens.append(preprocessing.Token(i=i, text=word, lemma=word, upos=upos, head=head,
                                          deprel=deprel, start=span[0], end=span[1]))
    return preprocessing.Sentence(text=text, start=0, end=len(text), tokens=tokens,
                                  lang=Lang.AR, parser="stanza-ar")


def test_spo_tree_attached_conjunction_root_takes_the_verb():
    # Arbre produit par Stanza : « و » racine, verbe de parole en parataxis.
    text = "وقال وزير الصحه ان عدد الاصابات تراجع بشكل كبير."
    sentence = _stanza_like(text, [
        ("و", "وقال", "CCONJ", -1, "root"), ("قال", None, "VERB", 0, "parataxis"),
        ("وزير", "وزير", "NOUN", 1, "nsubj"), ("الصحه", "الصحه", "NOUN", 2, "nmod"),
        ("ان", "ان", "SCONJ", 7, "mark"), ("عدد", "عدد", "NOUN", 7, "nsubj"),
        ("الاصابات", "الاصابات", "NOUN", 5, "nmod"), ("تراجع", "تراجع", "VERB", 1, "ccomp"),
        ("ب", "بشكل", "ADP", 9, "case"), ("شكل", None, "NOUN", 7, "obl"),
        ("كبير", "كبير", "ADJ", 9, "amod"), (".", ".", "PUNCT", 0, "punct"),
    ])
    triple = spo.extract_spo(sentence)
    assert (triple.subject, triple.obj) == ("وزير الصحه", "عدد الاصابات تراجع بشكل كبير")
    assert triple.predicate.endswith("قال")
    assert triple.reported and triple.source == "وزير الصحه"


@pytest.mark.slow
def test_spo_stanza_attached_conjunction_speech_verb():
    if preprocessing.get_parser(Lang.AR) is None:
        pytest.skip("modèle Stanza ar absent")
    (claim,) = extract_claims_detailed(normalize(ATTACHED_SPEECH))
    assert claim.parser == "stanza-ar"
    assert (claim.subject, claim.obj) == ("وزير الصحه", "عدد الاصابات تراجع بشكل كبير")
    assert (claim.modality, claim.source) == ("rapporté", "وزير الصحه")


def test_spo_rules_speech_verb_with_attached_conjunction():
    (claim,) = extract_claims_detailed(normalize(ATTACHED_SPEECH))
    assert claim.parser == "rules"
    assert (claim.subject, claim.obj) == ("وزير الصحه", "عدد الاصابات تراجع بشكل كبير")
    assert (claim.modality, claim.source) == ("rapporté", "وزير الصحه")


def test_spo_rules_attached_conjunction_stripped_only_for_speech_verbs():
    reported = spo.extract_spo(_sentence("فأكد وزير التجارة أن الأسعار ستنخفض."))
    assert reported.reported and reported.source == "وزير التجاره"
    assert reported.obj == "الاسعار ستنخفض"
    # Piège : « و » + verbe qui n'est pas un verbe de parole, suivi de « أن » : pas rapporté.
    trap = spo.extract_spo(_sentence("وتبين أن الأسعار ارتفعت في الشهر الماضي."))
    assert not trap.reported and trap.source is None


# --- Outillage eval_100 : validation, verrou, ventilation, bootstrap, accord ---------------

TEMPLATE = FIXTURES / "eval_100_template.jsonl"


def _item(item_id="fr-001", **changes):
    """Ligne valide minimale (phrase synthétique), modifiable champ par champ."""
    item = {
        "id": item_id, "lang": "fr", "script": "latin", "text": "Le prix a baissé de 5 %.",
        "phenomena": ["fait_chiffré"], "origin": {"type": "rédigée"},
        "gold": {"is_claim": True, "subject": "Le prix", "predicate": "a baissé",
                 "obj": "de 5 %", "modality": "assertif"},
    }
    item.update(changes)
    return item


def test_validate_accepts_eval_30_and_a_valid_line():
    assert evaluate.validate_eval_set(EVAL_ITEMS) == []
    assert evaluate.validate_eval_set([_item()]) == []


def test_validate_rejects_template_lines():
    problems = evaluate.validate_eval_set(evaluate.load_eval_set(TEMPLATE))
    assert any("_commentaire" in p for p in problems)
    assert any("valeurs de gabarit" in p for p in problems)


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"lang": "en"}, "langue"),
        ({"script": "cyrillic"}, "écriture"),
        ({"lang": "fr", "script": "arabic"}, "groupe"),
        ({"phenomena": ["fait_chifre"]}, "phénomènes inconnus"),
        ({"phenomena": []}, "phenomena"),
        ({"gold": {"is_claim": True, "subject": None, "predicate": "a"}}, "champs manquants"),
        ({"gold": {"is_claim": "oui", "subject": None, "predicate": None, "obj": None,
                   "modality": "assertif"}}, "is_claim"),
        ({"gold": {"is_claim": True, "subject": None, "predicate": None, "obj": None,
                   "modality": "certain"}}, "modality"),
        ({"phenomena": ["coréférence"]}, "coréférence"),
        ({"origin": {"type": "blog"}}, "origin.type"),
        ({"text": "<phrase à écrire>"}, "gabarit"),
    ],
)
def test_validate_rejects_invalid_lines(changes, expected):
    problems = evaluate.validate_eval_set([_item(**changes)])
    assert any(expected in p for p in problems), problems


def test_validate_rejects_duplicate_ids():
    problems = evaluate.validate_eval_set([_item("fr-001"), _item("fr-001")])
    assert any("id en double" in p for p in problems)


def _lock_files(tmp_path, recorded):
    data = tmp_path / "eval_100.jsonl"
    data.write_text(json.dumps(_item(), ensure_ascii=False) + "\n", encoding="utf-8")
    protocol = tmp_path / "protocole.md"
    protocol.write_text(
        "# Protocole\n\n## 7. Verrouillage et historique\n\n"
        "| Date | Événement | `id` concernés | SHA-256 |\n|---|---|---|---|\n"
        f"| 2026-11-01 | verrouillage | tous | {recorded} |\n",
        encoding="utf-8",
    )
    return data, protocol


def test_lock_accepts_recorded_hash(tmp_path):
    expected = hashlib.sha256(
        (json.dumps(_item(), ensure_ascii=False) + "\n").encode("utf-8")
    ).hexdigest()
    data, protocol = _lock_files(tmp_path, expected)
    assert evaluate.check_lock(data, protocol) == expected
    # Même empreinte avec des fins de ligne CRLF (copie de travail Windows).
    data.write_bytes(data.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert evaluate.check_lock(data, protocol) == expected


def test_lock_refuses_modified_file_or_missing_hash(tmp_path):
    data, protocol = _lock_files(tmp_path, "0" * 64)
    with pytest.raises(evaluate.LockError, match="a changé"):
        evaluate.check_lock(data, protocol)
    protocol.write_text("# Protocole\n\n## 7. Verrouillage\n\n| — | — |\n", encoding="utf-8")
    with pytest.raises(evaluate.LockError, match="aucune empreinte"):
        evaluate.check_lock(data, protocol)


def test_cli_refuses_to_evaluate_unlocked_set(tmp_path, capsys):
    data, protocol = _lock_files(tmp_path, "0" * 64)
    with pytest.raises(SystemExit) as stop:
        evaluate.main(["--eval-set", str(data), "--protocol", str(protocol), "--check-lock",
                       "--out-dir", str(tmp_path)])
    assert stop.value.code == 2 and "refusée" in capsys.readouterr().err
    assert not list(tmp_path.glob("lot-b_extraction_*"))


def test_cli_sha256_and_invalid_set(tmp_path, capsys):
    data, _ = _lock_files(tmp_path, "0" * 64)
    evaluate.main(["--eval-set", str(data), "--sha256"])
    assert evaluate.sha256_file(data) in capsys.readouterr().out
    with pytest.raises(SystemExit) as stop:
        evaluate.main(["--eval-set", str(TEMPLATE), "--out-dir", str(tmp_path)])
    assert stop.value.code == 2 and "invalide" in capsys.readouterr().err


def test_cli_validate_does_not_run_the_system(tmp_path, capsys, monkeypatch):
    def forbidden(_item):
        raise AssertionError("le système ne doit pas être exécuté pendant la validation")

    monkeypatch.setattr(evaluate, "predict", forbidden)
    data, _ = _lock_files(tmp_path, "0" * 64)
    evaluate.main(["--eval-set", str(data), "--validate", "--out-dir", str(tmp_path)])
    out = capsys.readouterr().out
    assert "Jeu valide : 1 phrases" in out and "fr-latin 1" in out
    assert not list(tmp_path.glob("lot-b_extraction_*"))


def test_breakdown_by_phenomenon_with_counts():
    metrics = evaluate.evaluate(EVAL_ITEMS, rules=True)["metrics"]
    counts = {}
    for it in EVAL_ITEMS:
        for phenomenon in it["phenomena"]:
            counts[phenomenon] = counts.get(phenomenon, 0) + 1
    assert {ph: m["n"] for ph, m in metrics["by_phenomenon"].items()} == counts
    rapporte = metrics["by_phenomenon"]["rapporté"]
    assert rapporte["spo_n"] == sum(
        it["gold"]["is_claim"] for it in EVAL_ITEMS if "rapporté" in it["phenomena"]
    )


def _record(item_id, correct):
    """Phrase synthétique : sortie identique au gold (correct) ou fausse sur tous les champs."""
    gold = {"is_claim": True, "subject": "le prix", "predicate": "a baissé", "obj": "de 5 %",
            "modality": "assertif"}
    wrong = {"is_claim": True, "subject": "x", "predicate": "y", "obj": "z",
             "modality": "opinion"}
    return {"id": item_id, "gold": gold, "pred": dict(gold) if correct else wrong}


def test_bootstrap_interval_contains_true_value():
    rng = random.Random(7)  # population synthétique : 70 % de phrases correctes
    records = [_record(f"s{k:03d}", rng.random() < 0.7) for k in range(200)]
    ci = evaluate.bootstrap_ci(records, resamples=300)["modality_accuracy"]
    assert ci["low"] <= 0.7 <= ci["high"] and ci["high"] - ci["low"] < 0.2
    again = evaluate.bootstrap_ci(records, resamples=300)["modality_accuracy"]
    assert again == ci  # graine fixe : résultat reproductible


def test_paired_bootstrap_detects_obvious_difference():
    good = [_record(f"s{k:02d}", True) for k in range(30)]
    bad = [_record(f"s{k:02d}", False) for k in range(30)]
    result = evaluate.paired_bootstrap(bad, good, resamples=200)["spo_all_exact"]
    assert result["diff"] == 1.0 and result["low"] > 0 and result["contains_zero"] is False


def test_paired_bootstrap_identical_outputs_show_no_difference():
    rng = random.Random(3)
    records = [_record(f"s{k:02d}", rng.random() < 0.6) for k in range(30)]
    result = evaluate.paired_bootstrap(records, records, resamples=200)
    computed = [r for r in result.values() if r["diff"] is not None]
    assert computed and all(r["diff"] == 0 and r["contains_zero"] for r in computed)


def test_paired_bootstrap_requires_same_sentences():
    with pytest.raises(ValueError):
        evaluate.paired_bootstrap([_record("a", True)], [_record("b", True)], resamples=10)


def test_cohen_kappa_known_values():
    labels = ["assertif", "opinion", "rapporté", "assertif", "interrogatif"]
    assert agreement.cohen_kappa(labels, labels) == 1.0
    # Cas d'école : 20 oui/oui, 5 oui/non, 10 non/oui, 15 non/non → po = 0.70, pe = 0.50
    a = [True] * 25 + [False] * 25
    b = [True] * 20 + [False] * 5 + [True] * 10 + [False] * 15
    assert agreement.cohen_kappa(a, b) == pytest.approx(0.4)


def test_agreement_lists_disagreements(tmp_path, capsys):
    a = [_item("fr-001"), _item("fr-002"), _item("fr-003")]
    b = [_item("fr-001"),
         _item("fr-002", gold={"is_claim": False, "subject": None, "predicate": None,
                               "obj": None, "modality": "opinion"}),
         _item("fr-004")]
    report = agreement.agreement(a, b)
    assert report["n"] == 2 and report["only_a"] == ["fr-003"] and report["only_b"] == ["fr-004"]
    assert {(d["id"], d["field"]) for d in report["disagreements"]} == {
        ("fr-002", "is_claim"), ("fr-002", "modality")
    }
    files = []
    for name, items in (("a", a), ("b", b)):
        path = tmp_path / f"{name}.jsonl"
        path.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items),
                        encoding="utf-8")
        files.append(str(path))
    agreement.main(files)
    out = capsys.readouterr().out
    assert "Phrases comparées : 2" in out and "fr-002" in out


# --- Accord inter-annotateurs : CSV du lot (labels A1), ventilation par langue -------------


def _write_csv(path, rows, delimiter=";"):
    """CSV d'annotation synthétique (id, texte, contexte, label, modalite)."""
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(["id", "texte", "contexte", "label", "modalite"])
        writer.writerows(rows)
    return path


def test_convert_label_from_a1():
    assert agreement.convert_label("AFFIRMATION") is True
    assert agreement.convert_label(" opinion ") is False
    assert agreement.convert_label("Autre") is False
    with pytest.raises(ValueError):
        agreement.convert_label("FAIT")


def test_read_csv_annotation_formats_and_problems(tmp_path):
    rows = [["L01", "phrase un", "", "AFFIRMATION", "rapporte"],  # modalité sans accent
            ["L02", "phrase deux", "", "OPINION", "opinion"]]
    for delimiter in (";", ","):
        items, problems = agreement.read_csv_annotation(
            _write_csv(tmp_path / f"a{delimiter == ','}.csv", rows, delimiter))
        assert problems == []
        assert [(i["id"], i["gold"]["is_claim"], i["gold"]["modality"]) for i in items] == [
            ("L01", True, "rapporté"), ("L02", False, "opinion")]
    bad = _write_csv(tmp_path / "bad.csv", [["L01", "x", "", "FAIT", "assertif"],
                                            ["L02", "y", "", "AUTRE", "certain"],
                                            ["L02", "z", "", "AUTRE", "assertif"]])
    problems = agreement.read_csv_annotation(bad)[1]
    assert any("FAIT" in p for p in problems) and any("certain" in p for p in problems)
    assert any("double" in p for p in problems)


def _textbook_rows(prefix):
    """Cas d'école : 20 oui/oui, 5 oui/non, 10 non/oui, 15 non/non → accord 70 %, kappa 0.4."""
    pairs = [("AFFIRMATION", "AFFIRMATION")] * 20 + [("AFFIRMATION", "OPINION")] * 5
    pairs += [("OPINION", "AFFIRMATION")] * 10 + [("OPINION", "OPINION")] * 15
    a = [[f"{prefix}{k:02d}", "t", "", la, "assertif"] for k, (la, _) in enumerate(pairs)]
    b = [[f"{prefix}{k:02d}", "t", "", lb, "assertif"] for k, (_, lb) in enumerate(pairs)]
    return a, b


def test_agreement_by_language_known_values(tmp_path):
    fr_a, fr_b = _textbook_rows("F")
    ar = [[f"A{k:02d}", "t", "", "AFFIRMATION" if k % 2 else "AUTRE", "assertif"]
          for k in range(10)]
    a = agreement.read_csv_annotation(_write_csv(tmp_path / "a.csv", fr_a + ar))[0]
    b = agreement.read_csv_annotation(_write_csv(tmp_path / "b.csv", fr_b + ar))[0]
    langs = {r[0]: "fr" for r in fr_a} | {r[0]: "ar" for r in ar}
    report = agreement.agreement(a, b, langs)
    fr, ar_stats = report["by_lang"]["fr"]["is_claim"], report["by_lang"]["ar"]["is_claim"]
    assert (fr["n"], fr["agreement_pct"], fr["kappa"]) == (50, 70.0, 0.4)
    assert (ar_stats["n"], ar_stats["agreement_pct"], ar_stats["kappa"]) == (10, 100.0, 1.0)
    assert report["is_claim"]["n"] == 60 and report["fields"] == ["is_claim", "modality", "label"]
    assert fr["class_counts"] == {"A": {"False": 25, "True": 25}, "B": {"False": 20, "True": 30}}
    assert report["by_lang"]["ar"]["label"]["class_counts"]["A"] == {"AFFIRMATION": 5, "AUTRE": 5}


def test_agreement_flags_class_imbalance(tmp_path):
    rows = [[f"L{k:02d}", "t", "", "OPINION" if k < 2 else "AFFIRMATION", "assertif"]
            for k in range(30)]
    items = agreement.read_csv_annotation(_write_csv(tmp_path / "a.csv", rows))[0]
    warnings = agreement.agreement(items, items)["warnings"]
    assert any("global is_claim" in w and "rare" in w for w in warnings)
    single = [[f"L{k:02d}", "t", "", "AFFIRMATION", "assertif"] for k in range(10)]
    items = agreement.read_csv_annotation(_write_csv(tmp_path / "s.csv", single))[0]
    warnings = agreement.agreement(items, items)["warnings"]
    assert any("is_claim" in w and "qu'une classe" in w for w in warnings)
    # Modalité à une seule classe : kappa de 1.0 dégénéré, signalé lui aussi
    assert any("modality" in w and "qu'une classe" in w for w in warnings)


def test_agreement_jsonl_against_csv_takes_language_from_jsonl(tmp_path):
    a = [_item("fr-001"), _item("fr-002", lang="ar", script="arabic")]
    b = agreement.read_csv_annotation(_write_csv(tmp_path / "b.csv", [
        ["fr-001", "x", "", "AFFIRMATION", "assertif"],
        ["fr-002", "y", "", "OPINION", "opinion"],
    ]))[0]
    report = agreement.agreement(a, b)
    assert set(report["by_lang"]) == {"fr", "ar"} and report["fields"] == ["is_claim", "modality"]
    assert report["spo_n"] == 0  # pas de triplet dans le CSV
    assert {(d["id"], d["field"]) for d in report["disagreements"]} == {
        ("fr-002", "is_claim"), ("fr-002", "modality")}


def test_agreement_cli_with_csv_and_langs(tmp_path, capsys):
    fr_a, fr_b = _textbook_rows("F")
    a = _write_csv(tmp_path / "a.csv", fr_a)
    b = _write_csv(tmp_path / "b.csv", fr_b)
    langs = tmp_path / "corr.jsonl"
    langs.write_text("".join(json.dumps({"id": r[0], "lang_source": "fr"}) + "\n" for r in fr_a),
                     encoding="utf-8")
    agreement.main([str(a), str(b), "--langs", str(langs)])
    out = capsys.readouterr().out
    assert "Langue fr (50 phrases)" in out and "accord  70.0 %" in out and "kappa  0.40" in out
    with pytest.raises(SystemExit) as stop:
        agreement.main([str(a), str(_write_csv(tmp_path / "x.csv", [["L1", "t", "", "?", "?"]]))])
    assert stop.value.code == 2


# --- Script de démonstration ---------------------------------------------------------------


def test_demo_describes_opinion(capsys):
    demo.main(["Je pense que le gouvernement devrait agir plus vite."])
    out = capsys.readouterr().out
    assert "affirmation vérifiable : non" in out
    assert "opinion / non factuel  : oui" in out
    assert "opinion:1re_personne:pense" in out


def test_demo_shows_coreference_and_examples(capsys):
    demo.main([])  # exemples par défaut (FR, AR, tunisien)
    out = capsys.readouterr().out
    assert out.count("Texte :") == len(demo.EXAMPLES)
    assert "coréférence            : Il → Le ministre" in out


def test_demo_json(capsys):
    demo.main(["--json", "Le taux de chômage a atteint 16 % en 2023."])
    payload = json.loads(capsys.readouterr().out)
    (claim,) = next(iter(payload.values()))
    assert claim["is_claim"] is True and claim["is_opinion"] is False
    assert {"subject", "predicate", "obj", "triggers", "resolved_text"} <= set(claim)


def test_demo_short_text_has_no_candidate(capsys):
    demo.main(["Bonjour Tunis."])
    assert "Aucune phrase candidate" in capsys.readouterr().out


# --- Bronze : baselines triviales (EXP-B-007) ---------------------------------------------


def test_baselines_gold_modality_distribution():
    counts = Counter(it["gold"]["modality"] for it in EVAL_ITEMS)
    assert counts == {"assertif": 14, "rapporté": 7, "opinion": 5, "interrogatif": 4,
                      "souhait": 2, "conditionnel": 1, "hypothétique": 1}
    assert baselines_bronze.majority_label(EVAL_ITEMS) == "assertif"


def test_baselines_scores_on_eval_30():
    records = baselines_bronze.baseline_records(
        EVAL_ITEMS, baselines_bronze.majority_label(EVAL_ITEMS)
    )
    scores = baselines_bronze.scores(records)
    expected = {
        "claim_accuracy": 0.647,
        "modality_accuracy": 0.412,
        "spo_exact.subject": 0.227,
        "spo_exact.predicate": 0.364,
        "spo_all_exact": 0.0,
    }
    for key, value in expected.items():
        assert scores[key] == pytest.approx(value, abs=0.001), key


def test_baselines_cli_rules_only(tmp_path, capsys):
    out_file = tmp_path / "baselines.md"
    baselines_bronze.main(["--rules-only", "--markdown", str(out_file)])
    report = out_file.read_text(encoding="utf-8")
    assert report == capsys.readouterr().out.rstrip("\n") + "\n"
    assert "Analyseurs utilisés : rules." in report
    assert "| Détection : exactitude | 0.647 | 1.000 | 34 |" in report
    assert "| Modalité : exactitude | 0.412 | 1.000 | 34 |" in report
    assert "| SPO : triplet exact | 0.000 | 0.909 | 22 |" in report


# ---------------------------------------------------------------------------
# Mesure en double annotation (evaluate_double) : textes inventés
# ---------------------------------------------------------------------------

DOUBLE_HEADER = ["id", "texte", "label", "modalite", "sujet", "predicat", "objet", "source"]
DOUBLE_ROWS_A = [
    ["d1", "Le ministère a publié un communiqué en mars 2024.", "AFFIRMATION", "assertif",
     "Le ministère", "a publié", "un communiqué", "test"],
    ["d2", "Je trouve cette décision vraiment injuste.", "OPINION", "opinion", "", "", "", "test"],
    ["d3", "Est-ce que la réunion aura lieu demain ?", "AUTRE", "interrogatif", "", "", "", "test"],
    ["d4", "Selon l'institut, le chômage a reculé à 15 %.", "AFFIRMATION", "rapporté",
     "le chômage", "a reculé", "à 15 %", "test"],
    ["d5", "Bonjour à tous !", "AUTRE", "souhait", "", "", "", "test"],
    ["d6", "La commune compte trois nouvelles écoles depuis 2023.", "AFFIRMATION", "assertif",
     "La commune", "compte", "trois nouvelles écoles", "test"],
]


def _double_files(tmp_path, rows_b=None, header=DOUBLE_HEADER):
    """Écrit a.tsv (DOUBLE_ROWS_A) et b.tsv (`rows_b`, par défaut identique) avec un BOM."""
    rows_b = [list(r) for r in DOUBLE_ROWS_A] if rows_b is None else rows_b
    paths = []
    for name, rows in (("a.tsv", DOUBLE_ROWS_A), ("b.tsv", rows_b)):
        path = tmp_path / name
        lines = ["\t".join(header)] + ["\t".join(r[: len(header)]) for r in rows]
        path.write_text("﻿" + "\n".join(lines) + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def _rows_b_with_disagreements():
    rows = [list(r) for r in DOUBLE_ROWS_A]
    rows[1][2] = "AUTRE"  # d2 : label différent
    rows[3][3] = "assertif"  # d4 : modalité différente
    return rows


def test_double_reads_tsv_with_bom_and_triplet(tmp_path):
    path, _ = _double_files(tmp_path)
    items, problems = evaluate_double.read_annotation(path)
    assert problems == []
    assert [it["id"] for it in items] == ["d1", "d2", "d3", "d4", "d5", "d6"]
    assert items[0]["has_triplet"] and items[0]["gold"]["subject"] == "Le ministère"
    assert items[1]["gold"]["subject"] is None and items[1]["gold"]["is_claim"] is False
    assert items[3]["gold"]["modality"] == "rapporté"
    only = evaluate_double.read_annotation(path, evaluate_double.id_range("d2,d3"))[0]
    assert [it["id"] for it in only] == ["d2", "d3"]


def test_double_reports_format_problems(tmp_path):
    rows = [list(r) for r in DOUBLE_ROWS_A]
    rows[1][2] = "FAIT"
    rows[2][3] = "certain"
    rows[4][0] = "d1"
    _, path = _double_files(tmp_path, rows)
    _, problems = evaluate_double.read_annotation(path)
    assert len(problems) == 3
    assert any("FAIT" in p for p in problems) and any("certain" in p for p in problems)
    assert any("id en double" in p for p in problems)
    _, path = _double_files(tmp_path, header=["id", "texte", "label"])
    assert "colonnes manquantes" in evaluate_double.read_annotation(path)[1][0]


def test_double_id_range():
    assert evaluate_double.id_range("P01-P03") == {"P01", "P02", "P03"}
    assert evaluate_double.id_range("P098-P101") == {"P098", "P099", "P100", "P101"}
    assert evaluate_double.id_range("a, b") == {"a", "b"}


def test_double_detection_metrics_by_hand():
    gold = [True, True, False, False]
    pred = [True, True, True, False]
    assert evaluate_double.accuracy(gold, pred) == 0.75
    assert evaluate_double.precision(gold, pred) == pytest.approx(2 / 3)
    assert evaluate_double.recall(gold, pred) == 1.0
    # F1 affirmation 0.8, F1 non-affirmation 2/3.
    assert evaluate_double.detection_macro_f1(gold, pred) == pytest.approx((0.8 + 2 / 3) / 2)
    assert evaluate_double.precision(gold, [False] * 4) is None
    assert evaluate_double.recall([False] * 4, pred) is None


def test_double_paired_vs_baseline_is_deterministic():
    gold = [True, False, True, False, True, False]
    pred = [True, False, True, True, True, False]
    runs = [evaluate_double.paired_vs_baseline(42, 200, evaluate_double.detection_macro_f1,
                                               gold, pred, [True] * 6) for _ in range(2)]
    assert runs[0] == runs[1]
    d = runs[0]
    assert d["difference"] == pytest.approx(d["systeme"] - d["baseline"])
    assert d["ci"][0] <= d["difference"] <= d["ci"][1]
    assert (d["seed"], d["resamples"], d["n"]) == (42, 200, 6)


def test_double_measure_structure_and_agreement(tmp_path):
    path_a, path_b = _double_files(tmp_path, _rows_b_with_disagreements())
    a = evaluate_double.read_annotation(path_a)[0]
    b = evaluate_double.read_annotation(path_b)[0]
    out = evaluate_double.measure(a, b, names=("A", "B"), modes=("regles",), resamples=50,
                                  paired_resamples=50, exp_id="EXP-B-099", eval30=False)
    assert out["n_common"] == 6 and out["ids_only_one_file"] == []
    label = out["accord"]["label (3 classes)"]
    assert label["accord"] == 5
    assert label["kappa"] == pytest.approx(agreement.cohen_kappa(
        [r[2] for r in DOUBLE_ROWS_A], [r[2] for r in _rows_b_with_disagreements()]))
    assert out["accord"]["modalité (7)"]["accord"] == 5
    res = out["modes"]["regles"]
    assert res["groupes"] == {"fr": 6}
    det = res["par_groupe"]["tous"]["détection"]
    assert set(det) == {"A", "B", "accord label"} and det["accord label"]["n"] == 5
    assert det["A"]["baseline_exactitude"] == 0.5 and det["A"]["baseline_rappel"] == 1.0
    mod = res["par_groupe"]["tous"]["modalité"]
    assert mod["A"]["baseline_exactitude"] == pytest.approx(2 / 6)
    assert mod["accord modalité"]["n"] == 5
    trip = res["par_groupe"]["tous"]["triplet"]["A"]
    assert trip["n"] == 3 and set(trip) >= {"sujet", "prédicat", "objet", "triplet exact"}
    main_det = res["principal"]["A"]["détection macro-F1"]
    assert main_det["baseline"] == pytest.approx(evaluate_double.detection_macro_f1(
        [r[2] == "AFFIRMATION" for r in DOUBLE_ROWS_A], [True] * 6))
    assert set(res["principal"]) == {"A", "B", "accord"}
    assert set(res["predictions"]) == {f"d{k}" for k in range(1, 7)}


def test_double_measure_flags_missing_ids_and_runs_eval30(tmp_path):
    path_a, path_b = _double_files(tmp_path)
    a = evaluate_double.read_annotation(path_a)[0]
    b = evaluate_double.read_annotation(path_b)[0][:5]
    b[0] = {**b[0], "text": "Le ministère a publié deux communiqués en mars 2024."}
    out = evaluate_double.measure(a, b, modes=("regles",), resamples=0, paired_resamples=10,
                                  exp_id="EXP-B-099")
    assert out["ids_only_one_file"] == ["d6"] and out["n_common"] == 5
    assert out["ids_text_differs"] == ["d1"]
    e30 = out["eval_30"]["regles"]
    assert e30["exp_id"] == "EXP-B-099"
    assert (e30["is_claim_accuracy"], e30["spo_all_exact_count"], e30["spo_n"]) == (1.0, 20, 22)


def test_double_cli_writes_outputs_without_text(tmp_path, capsys):
    path_a, path_b = _double_files(tmp_path, _rows_b_with_disagreements())
    out_dir = tmp_path / "sortie"
    evaluate_double.main(["--a", str(path_a), "--b", str(path_b), "--exp-id", "EXP-B-099",
                          "--modes", "regles", "--resamples", "20", "--paired-resamples", "20",
                          "--no-eval30", "--out-dir", str(out_dir)])
    names = sorted(p.name for p in out_dir.iterdir())
    assert names == ["EXP-B-099_double.json", "EXP-B-099_double.md"]
    saved = (out_dir / "EXP-B-099_double.json").read_text(encoding="utf-8")
    printed = capsys.readouterr().out
    assert json.loads(saved)["exp_id"] == "EXP-B-099" and "EXP-B-099" in printed
    for row in DOUBLE_ROWS_A:  # aucun texte ni élément de triplet dans les sorties
        assert row[1] not in saved and row[1] not in printed
    assert "ministère" not in saved and "ministère" not in printed


@pytest.mark.parametrize("extra", [
    ["--out-dir", str(evaluate.ROOT / "evaluation" / "results")],
    ["--out-dir", "OUT", "--exp-id", "EXP-B-9"],
    ["--out-dir", "OUT", "--modes", "regles,autre"],
])
def test_double_cli_refuses_bad_options(tmp_path, extra):
    path_a, path_b = _double_files(tmp_path)
    extra = [str(tmp_path / "x") if e == "OUT" else e for e in extra]
    before = sorted(p.name for p in (evaluate.ROOT / "evaluation" / "results").iterdir())
    with pytest.raises(SystemExit) as exc:
        evaluate_double.main(["--a", str(path_a), "--b", str(path_b), *extra])
    assert exc.value.code == 2
    after = sorted(p.name for p in (evaluate.ROOT / "evaluation" / "results").iterdir())
    assert after == before and not (tmp_path / "x").exists()


def test_double_cli_refuses_invalid_annotation(tmp_path, capsys):
    rows = [list(r) for r in DOUBLE_ROWS_A]
    rows[0][2] = "VRAI"
    path_a, path_b = _double_files(tmp_path, rows)
    with pytest.raises(SystemExit) as exc:
        evaluate_double.main(["--a", str(path_a), "--b", str(path_b), "--out-dir",
                              str(tmp_path / "x")])
    assert exc.value.code == 2 and "VRAI" in capsys.readouterr().err
    assert not (tmp_path / "x").exists()


# ---------------------------------------------------------------------------
# Ablation (retrait en mémoire des composants)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def ablation_rules_rows():
    return ablation.run(modes=("regles",))


def test_ablation_complete_matches_evaluate(ablation_rules_rows):
    complete = ablation_rules_rows[0]
    assert complete["variante"] == ablation.COMPLETE and complete["reference"]
    m = evaluate.evaluate(evaluate.load_eval_set(), rules=True)["metrics"]
    assert complete["metrics"] == {
        "e30 claim": m["is_claim_accuracy"], "e30 mod.": m["modality_accuracy"],
        "e30 triplet": round(m["spo_all_exact"] * m["spo_n"]),
        "e30 coref": round(m["coref_accuracy"] * m["coref_n"])}
    # Chiffres de main en mode règles : détection et modalité 34/34, triplet 20/22, coréf. 3/3.
    assert complete["metrics"] == {"e30 claim": 1.0, "e30 mod.": 1.0, "e30 triplet": 20,
                                   "e30 coref": 3}


def test_ablation_each_variant_runs_and_changes_eval30(ablation_rules_rows):
    by_name = {r["variante"]: r for r in ablation_rules_rows}
    assert set(by_name) == set(ablation.VARIANTS)
    for name, row in by_name.items():
        assert set(row["metrics"]) == {"e30 claim", "e30 mod.", "e30 triplet", "e30 coref"}
        if name != ablation.COMPLETE:  # le retrait a bien un effet mesurable
            assert any(row["ecarts"].values()), name
    assert by_name["sans coréférence"]["metrics"]["e30 coref"] == 0
    assert by_name["sans règles de factualité"]["metrics"]["e30 claim"] < 1.0


def test_ablation_restores_components():
    originals = (modality.load_lexicon, coreference.resolve_with_log,
                 factuality.classify_factuality, spo.speech_verbs)
    for context in ablation.VARIANTS.values():
        with context():
            pass
    with pytest.raises(RuntimeError), ablation.without_factuality():
        raise RuntimeError("erreur pendant la mesure")
    assert (modality.load_lexicon, coreference.resolve_with_log,
            factuality.classify_factuality, spo.speech_verbs) == originals


def test_ablation_with_double_annotation(tmp_path):
    path_a, path_b = _double_files(tmp_path, _rows_b_with_disagreements())
    pair = ablation.make_pair(evaluate_double.read_annotation(path_a)[0],
                              evaluate_double.read_annotation(path_b)[0], ("A", "B"))
    variants = {k: ablation.VARIANTS[k] for k in (ablation.COMPLETE, "sans règles de factualité")}
    rows = ablation.run(pair=pair, modes=("regles", "parseurs"), variants=variants)
    names = [(r["mode"], r["variante"]) for r in rows]
    assert names[-1] == ("parseurs", ablation.WITHOUT_PARSERS) and len(rows) == 5
    assert {"dét. F1 A", "mod. F1 B", "mod. F1 consensus"} <= set(rows[0]["metrics"])
    assert set(rows[0]["preds"]) == {f"d{k}" for k in range(1, 7)}
    table = ablation.to_markdown(rows)
    assert "textes changés" in table and "ministère" not in table


def test_ablation_cli_refuses_bad_options(tmp_path):
    path_a, _ = _double_files(tmp_path)
    for argv in (["--a", str(path_a)], ["--out-dir", str(evaluate.ROOT / "evaluation")],
                 ["--modes", "autre"]):
        with pytest.raises(SystemExit) as exc:
            ablation.main(argv)
        assert exc.value.code == 2


# --- Détection : formules de requête polie (souhait / injonction) ----------------------------

POLITE_REQUEST_CASES = [
    "Pouvez-vous me conseiller une bonne voiture, merci d'avance.",
    "Envoyez-moi le lien du communiqué s'il vous plaît.",
    "3aychek 9olli win nal9a el formulaire mta3 el inscription.",
    "عيشك قلي وين نلقى الاستمارة متاع التسجيل.",
    "من فضلك أرسل لي رابط البلاغ الرسمي.",
]


@pytest.mark.parametrize("text", POLITE_REQUEST_CASES)
def test_polite_request_is_wish_not_claim(text):
    (claim,) = extract_claims_detailed(normalize(text))
    assert claim.modality == "souhait" and not claim.is_claim, claim.triggers


@pytest.mark.parametrize(
    "text",
    [
        "Le ministre a remercié les médecins de Sfax en 2024.",
        "El 7koma 3mlet 200 khedma jdida fi Gafsa.",
        "عيشة بنت محمد فازت بالجائزة الأولى سنة 2024.",  # prénom proche de la formule tunisienne
    ],
)
def test_request_markers_do_not_fire_on_claims(text):
    claims = extract_claims_detailed(normalize(text))
    assert claims and all(c.is_claim for c in claims), [c.triggers for c in claims]


# --- Détection : formules de salutation (phatiques) ---------------------------------------

SALUTATION_CASES = [
    "Bonjour à tous les membres du groupe !",
    "Aslema 3la el jma3a el kol.",
    "صباح الخير على الجميع يا أصدقاء.",
    "مساء الخير لكل المتابعين الكرام.",
]


@pytest.mark.parametrize("text", SALUTATION_CASES)
def test_salutation_alone_is_not_claim(text):
    (claim,) = extract_claims_detailed(normalize(text))
    assert claim.modality == "souhait" and not claim.is_claim, claim.triggers
    assert any(t.startswith("souhait:salutation:") for t in claim.triggers)


@pytest.mark.parametrize(
    "text",
    [
        "Bonjour, le ministre a annoncé 200 emplois à Gafsa.",  # indice factuel : nombre
        "Bonjour, El Ministre Ben Salah a visité Sfax.",  # indice factuel : entité (règles)
        "Le président a dit bonjour aux enfants de l'école.",  # salutation hors tête de phrase
        "Aslema, el 7koma 3mlet 200 khedma jdida.",
    ],
)
def test_salutation_does_not_hide_claim(text):
    claims = extract_claims_detailed(normalize(text))
    assert claims and all(c.is_claim for c in claims), [c.triggers for c in claims]
    assert not any(t.startswith("souhait:salutation") for c in claims for t in c.triggers)
