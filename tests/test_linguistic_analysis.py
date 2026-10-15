"""Tests Lot B."""

import json
from dataclasses import asdict, fields
from pathlib import Path

import pytest

from common.schemas import Claim, Document, Lang
from linguistic_analysis import (
    claim_extraction,
    coreference,
    demo,
    evaluate,
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
