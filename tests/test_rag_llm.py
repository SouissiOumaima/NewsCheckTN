"""Tests Lot D."""

from dataclasses import replace
from pathlib import Path

import pytest

from common.schemas import Claim, Evidence, Label, Lang, Stance, StanceResult
from data.loaders import load_evidence_corpus
from rag_llm import evaluate_verdict
from rag_llm.baseline_stance import (
    _numbers,
    predict_stance_rules,
    predict_stances,
    topic_overlap,
)
from rag_llm.build_tunifact_eval import build_corpus
from rag_llm.evaluate_retrieval import compute_metrics, load_claims, run
from rag_llm.retrieval import hybrid
from rag_llm.retrieval.bm25 import BM25Index
from rag_llm.retrieval.dense import DenseIndex
from rag_llm.retrieval.hybrid import retrieve
from rag_llm.retrieval.text import tokenize
from rag_llm.verdict import (
    CONFLICT,
    LOW_RELEVANCE,
    NO_EVIDENCE,
    NOT_DECISIVE,
    generate_verdict,
    generate_verdict_with_reason,
)

FIXTURES = Path(__file__).parent / "fixtures" / "rag_llm"

CORPUS = [
    Evidence(doc_id="a", text="Tunis est la capitale de la Tunisie.", source="t"),
    Evidence(doc_id="b", text="Le couscous est un plat maghrébin.", source="t"),
]


def test_retrieve_ranks_relevant_first():
    res = retrieve(Claim(text="Quelle est la capitale de la Tunisie ?", lang=Lang.FR), CORPUS, k=2)
    assert res[0].doc_id == "a"


def test_abstention_without_decisive_evidence():
    v = generate_verdict(Claim(text="x", lang=Lang.FR), [])
    assert v.abstained and v.label == Label.NOT_ENOUGH_INFO and v.citations == []


def test_verdict_cites_evidence():
    ev = replace(CORPUS[0], score=5.0)  # score de pertinence venant du retrieval
    stance = StanceResult(evidence=ev, stance=Stance.SUPPORTS, confidence=0.9)
    v = generate_verdict(Claim(text="Tunis est la capitale.", lang=Lang.FR), [stance])
    assert not v.abstained and v.label == Label.TRUE and v.citations == ["a"]


# --- Retrieval BM25 (S1) ---------------------------------------------------------------

def test_tokenize_normalise_arabe():
    # harakat, hamza, ة, article et chiffres arabes unifiés
    assert tokenize("نسبةُ البطالةِ ١٦") == tokenize("نسبه بطاله 16")


def test_tokenize_supprime_accents_et_mots_vides():
    assert tokenize("Le chômage de la Tunisie") == ["chomage", "tunisie"]


def test_bm25_scores_positifs_et_tries():
    res = BM25Index(CORPUS).search("capitale Tunisie", k=5)
    assert [e.doc_id for e in res] == ["a"]
    assert res[0].score > 0


def test_retrieve_sans_terme_commun_renvoie_vide():
    assert retrieve(Claim(text="aéroport Kairouan", lang=Lang.FR), CORPUS, k=5) == []


def test_retrieve_respecte_k_et_contrat():
    corpus = load_evidence_corpus(FIXTURES / "evidence_dev.jsonl")
    res = retrieve(Claim(text="taux de chômage en Tunisie 2025", lang=Lang.FR), corpus, k=2)
    assert len(res) <= 2
    assert all(isinstance(e, Evidence) for e in res)
    assert [e.score for e in res] == sorted((e.score for e in res), reverse=True)


def test_retrieve_ne_modifie_pas_le_corpus():
    retrieve(Claim(text="capitale Tunisie", lang=Lang.FR), CORPUS, k=1)
    assert all(e.score == 0.0 for e in CORPUS)


def test_evaluation_jeu_dev():
    corpus = load_evidence_corpus(FIXTURES / "evidence_dev.jsonl")
    rows = run(corpus, load_claims(FIXTURES / "claims_dev.jsonl"))
    metrics = compute_metrics(rows)
    assert metrics["n"] > 0 and 0.0 <= metrics["mrr"] <= 1.0
    # garde-fou de non-régression sur le français (jeu fictif)
    fr = compute_metrics([r for r in rows if r["group"] == "fr-latin"])
    assert fr["hit@1"] >= 0.8


# --- Baseline NLI par règles (S2) ------------------------------------------------------

def _ev(doc_id, text, score=5.0):
    return Evidence(doc_id=doc_id, text=text, source="t", score=score)


def test_stance_nombres_differents_contredit():
    claim = Claim(text="Le chômage en Tunisie a atteint 25 % en 2025.", lang=Lang.FR)
    ev = _ev("x", "Le taux de chômage en Tunisie est de 16 % en 2025.")
    assert predict_stance_rules(claim, ev).stance == Stance.REFUTES


def test_stance_meme_nombre_soutient_et_annees_ignorees():
    claim = Claim(text="Le chômage en Tunisie est de 16 % en 2024.", lang=Lang.FR)
    ev = _ev("x", "Le taux de chômage en Tunisie est de 16 % en 2025.")
    assert predict_stance_rules(claim, ev).stance == Stance.SUPPORTS


def test_stance_dementi_arabe():
    claim = Claim(text="شرب الماء الساخن يعالج الأنفلونزا", lang=Lang.AR)
    ev = _ev("x", "لا توجد أي دراسة تثبت أن شرب الماء الساخن يعالج الأنفلونزا.")
    assert predict_stance_rules(claim, ev).stance == Stance.REFUTES


def test_stance_hors_sujet_neutre():
    claim = Claim(text="Le chômage en Tunisie a atteint 25 %.", lang=Lang.FR)
    ev = _ev("x", "Les barrages sont remplis à 35 %.")
    assert topic_overlap(claim.text, ev.text) < 0.5
    res = predict_stance_rules(claim, ev)
    assert res.stance == Stance.NEUTRAL and res.confidence == 0.0


def test_baseline_stance_meme_signature_que_lot_c():
    claim = Claim(text="x", lang=Lang.FR)
    res = predict_stances(claim, CORPUS)
    assert len(res) == len(CORPUS) and all(isinstance(r, StanceResult) for r in res)


# --- Verdict par gabarit et abstention (S3) -------------------------------------------

CLAIM_FR = Claim(text="Le chômage a atteint 25 %.", lang=Lang.FR)


def test_abstention_a1_aucune_preuve():
    v, reason = generate_verdict_with_reason(CLAIM_FR, [])
    assert v.abstained and reason == NO_EVIDENCE


def test_abstention_a2_preuves_peu_pertinentes():
    s = StanceResult(evidence=_ev("x", "texte", score=0.3), stance=Stance.REFUTES, confidence=0.9)
    v, reason = generate_verdict_with_reason(CLAIM_FR, [s])
    assert v.abstained and reason == LOW_RELEVANCE and v.label == Label.NOT_ENOUGH_INFO


def test_abstention_a3_preuves_non_decisives():
    stances = [
        StanceResult(evidence=_ev("x", "texte"), stance=Stance.NEUTRAL, confidence=0.9),
        StanceResult(evidence=_ev("y", "texte"), stance=Stance.REFUTES, confidence=0.4),
    ]
    v, reason = generate_verdict_with_reason(CLAIM_FR, stances)
    assert v.abstained and reason == NOT_DECISIVE


def test_abstention_a4_preuves_contradictoires_citees():
    stances = [
        StanceResult(evidence=_ev("x", "texte"), stance=Stance.SUPPORTS, confidence=0.8),
        StanceResult(evidence=_ev("y", "texte"), stance=Stance.REFUTES, confidence=0.8),
    ]
    v, reason = generate_verdict_with_reason(CLAIM_FR, stances)
    assert v.abstained and reason == CONFLICT and set(v.citations) == {"x", "y"}


def test_verdict_faux_cite_le_passage_mot_pour_mot():
    text = "Selon l'INS, le chômage est de 16 %."
    s = StanceResult(evidence=_ev("ins-1", text), stance=Stance.REFUTES, confidence=0.9)
    v = generate_verdict(CLAIM_FR, [s])
    assert v.label == Label.FALSE and v.citations == ["ins-1"]
    assert "[ins-1]" in v.explanation and text in v.explanation
    assert 0.1 <= v.uncertainty < 0.5


def test_verdict_gabarit_arabe_pour_tunisien():
    claim = Claim(text="سوم الخبز طلع", lang=Lang.TN)
    s = StanceResult(evidence=_ev("x", "سعر الخبز"), stance=Stance.REFUTES, confidence=0.9)
    assert generate_verdict(claim, [s]).explanation.startswith("خاطئ")


def test_evaluation_verdict_jeu_dev():
    corpus = load_evidence_corpus(FIXTURES / "evidence_dev.jsonl")
    rows = evaluate_verdict.run(corpus, load_claims(FIXTURES / "claims_dev.jsonl"))
    m = evaluate_verdict.compute_metrics(rows)
    assert m["invalid_citations"] == 0
    assert m["justified_abstention"] == 1.0  # aucune invention quand le corpus est muet


# --- Retrieval dense et hybride (S4) --------------------------------------------------
# Aucun vrai modèle en CI : un faux encodeur « bilingue » associe des mots FR et AR au même
# concept, ce qui imite ce que fait un encodeur multilingue (même sens → vecteurs proches).

_CONCEPTS = {
    "chomage": 0, "بطاله": 0, "tunisie": 1, "تونس": 1, "huile": 2, "زيت": 2,
    "olive": 3, "زيتون": 3, "prix": 4, "سعر": 4, "pain": 5, "خبز": 5, "baguette": 5,
}


class FakeBilingualEncoder:
    name = "fake-bilingual"

    def __init__(self):
        self.calls = 0

    def _vec(self, text):
        v = [0.0] * len(set(_CONCEPTS.values()))
        for tok in tokenize(text):
            if tok in _CONCEPTS:  # mots inconnus ignorés
                v[_CONCEPTS[tok]] += 1.0
        return v

    def encode_queries(self, texts):
        return [self._vec(t) for t in texts]

    def encode_passages(self, texts):
        self.calls += 1
        return [self._vec(t) for t in texts]


@pytest.fixture
def fake_encoder(tmp_path, monkeypatch):
    monkeypatch.setenv("INDEX_DIR", str(tmp_path))  # ne pas écrire dans rag_llm/index
    enc = FakeBilingualEncoder()
    hybrid.set_encoder(enc)
    yield enc
    hybrid.set_encoder(None)


def test_dense_retrouve_la_preuve_dans_l_autre_langue(fake_encoder):
    corpus = load_evidence_corpus(FIXTURES / "evidence_dev.jsonl")
    claim = Claim(text="Le chômage en Tunisie a atteint 25 %.", lang=Lang.FR)
    ids = [e.doc_id for e in retrieve(claim, corpus, k=2, method="dense")]
    assert set(ids) == {"dev-ev001", "dev-ev002"}  # preuve FR ET preuve AR
    bm25_ids = [e.doc_id for e in retrieve(claim, corpus, k=5, method="bm25")]
    assert "dev-ev002" not in bm25_ids  # BM25 ne relie pas FR → AR


def test_dense_scores_cosinus_tries_et_seuil(fake_encoder):
    corpus = load_evidence_corpus(FIXTURES / "evidence_dev.jsonl")
    res = DenseIndex(corpus, fake_encoder).search("prix huile olive", k=5, min_similarity=0.5)
    scores = [e.score for e in res]
    assert scores == sorted(scores, reverse=True)
    assert all(0.5 <= s <= 1.0 for s in scores)


def test_dense_index_mis_en_cache_sur_disque(tmp_path):
    enc = FakeBilingualEncoder()
    DenseIndex(CORPUS, enc, cache_dir=tmp_path)
    DenseIndex(CORPUS, enc, cache_dir=tmp_path)
    assert enc.calls == 1 and len(list(tmp_path.glob("dense_*.json"))) == 1


def test_rrf_favorise_les_passages_trouves_par_les_deux_methodes():
    a, b, c = (Evidence(doc_id=d, text=d, source="t") for d in "abc")
    fused = hybrid.rrf_fuse([[a, b], [b, c]], k=3)
    assert [e.doc_id for e in fused] == ["b", "a", "c"]
    assert fused[0].score == round(1 / 62 + 1 / 61, 5)


def test_hybride_combine_lexical_et_semantique(fake_encoder):
    corpus = load_evidence_corpus(FIXTURES / "evidence_dev.jsonl")
    claim = Claim(text="Le prix de l'huile d'olive a doublé.", lang=Lang.FR)
    ids = [e.doc_id for e in retrieve(claim, corpus, k=3, method="hybrid")]
    assert ids[0] == "dev-ev003"  # trouvé par les deux méthodes → premier
    assert "dev-ev004" in ids  # preuve arabe, que BM25 seul ne trouve pas
    assert "dev-ev004" not in [e.doc_id for e in retrieve(claim, corpus, k=5, method="bm25")]


def test_hybride_sans_preuve_renvoie_vide(fake_encoder):
    corpus = load_evidence_corpus(FIXTURES / "evidence_dev.jsonl")
    claim = Claim(text="aéroport Kairouan inauguré", lang=Lang.FR)
    assert retrieve(claim, corpus, k=5, method="hybrid") == []


def test_methode_inconnue(monkeypatch):
    monkeypatch.setenv("RETRIEVAL_METHOD", "magique")
    with pytest.raises(ValueError):
        hybrid.get_method()


def test_seuil_abstention_depend_de_la_methode():
    assert hybrid.min_relevance_score("bm25") == hybrid.MIN_BM25_SCORE
    assert hybrid.min_relevance_score("dense") == hybrid.MIN_DENSE_SIMILARITY
    # cosinus 0.9 : pertinent en dense, mais sous le seuil BM25
    s = StanceResult(evidence=_ev("x", "t", score=0.9), stance=Stance.REFUTES, confidence=0.9)
    assert not generate_verdict_with_reason(CLAIM_FR, [s], min_score=0.4)[0].abstained
    assert generate_verdict_with_reason(CLAIM_FR, [s], min_score=1.0)[1] == LOW_RELEVANCE


# --- Jeu réel Tunifact v0 (EXP-D-004) -------------------------------------------------
# Les textes du Lot A1 ne sont pas recopiés dans le dépôt (droits à confirmer) : on teste la
# construction du corpus sur de petites lignes factices et la cohérence du fichier d'affirmations.


def test_corpus_tunifact_exclut_la_rumeur_et_ajoute_les_distracteurs():
    tunifact = [
        {"id": "tunifact-1-001", "text": "rumeur", "lang": "fr", "source": "Tunifact"},
        {"id": "tunifact-1-002", "text": "preuve", "lang": "fr", "source": "Tunifact"},
    ]
    tarc = [{"id": "tarc-forum-0001", "text": "bruit", "lang": "tn", "source": "TArC"}]
    ids = [r["doc_id"] for r in build_corpus(tunifact, tarc)]
    assert ids == ["tunifact-1-002", "tarc-forum-0001"]


def test_affirmations_tunifact_coherentes():
    claims = load_claims(FIXTURES / "claims_tunifact_v0.jsonl")
    labels = {lab.value for lab in Label}
    assert len({c["claim_id"] for c in claims}) == len(claims)
    for c in claims:
        assert c["gold_label"] in labels and Lang(c["lang"])
        assert (c["gold_label"] == "preuves_insuffisantes") == (not c["gold_doc_ids"])
        # preuves attendues : phrases d'un seul article, jamais la rumeur (-001)
        articles = {d.rsplit("-", 1)[0] for d in c["gold_doc_ids"]}
        assert len(articles) <= 1
        assert not any(d.endswith("-001") for d in c["gold_doc_ids"])


# --- Lecture des nombres v2 (EXP-D-005) -----------------------------------------------


@pytest.mark.parametrize(
    "text, expected",
    [
        ("39 000 ingénieurs et 3 000 médecins", {"39000", "3000"}),
        ("39.000 ingénieurs et 3.300 médecins", {"39000", "3300"}),
        ("13\u00a0000 foyers", {"13000"}),  # espace insécable
        ("39 ألف مهندس و3 آلاف طبيب", {"39000", "3000"}),  # « و3 » : préfixe arabe accepté
        ("2 millions de dinars", {"2000000"}),
        ("le chômage est de 16,4 % en 2023", {"16.4"}),  # décimale ; année ignorée
        ("ارتفعت بنسبة ٩٫٣٪ في ٢٠٢٣", {"9.3"}),  # décimale arabe
        ("Covid-19, G20, A320 et Covid19", set()),  # nombres collés à un nom
        ("اللقاحات ضد كوفيد-19", set()),
    ],
)
def test_lecture_des_nombres(text, expected):
    assert _numbers(text) == expected


def test_memes_quantites_ecrites_differemment_sont_egales():
    assert _numbers("13 000 foyers") == _numbers("13 ألف منزل") == _numbers("13.000 maisons")


def test_covid19_ne_fait_plus_soutenir_une_preuve():
    claim = Claim(text="Les vaccins anti Covid-19 provoquent des cancers du sang.", lang=Lang.FR)
    ev = _ev("x", "Selon l'OMS, les vaccins anti Covid-19 ne provoquent pas de cancers du sang.")
    assert predict_stance_rules(claim, ev).stance == Stance.REFUTES  # démenti, plus « 19 = 19 »
