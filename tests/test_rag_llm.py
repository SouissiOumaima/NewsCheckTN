"""Tests Lot D."""

from dataclasses import replace
from pathlib import Path

from common.schemas import Claim, Evidence, Label, Lang, Stance, StanceResult
from data.loaders import load_evidence_corpus
from rag_llm import evaluate_verdict
from rag_llm.baseline_stance import predict_stance_rules, predict_stances, topic_overlap
from rag_llm.evaluate_retrieval import compute_metrics, load_claims, run
from rag_llm.retrieval.bm25 import BM25Index
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
