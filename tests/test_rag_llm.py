"""Tests Lot D."""

from pathlib import Path

from common.schemas import Claim, Evidence, Label, Lang, Stance, StanceResult
from data.loaders import load_evidence_corpus
from rag_llm.evaluate_retrieval import compute_metrics, load_claims, run
from rag_llm.retrieval.bm25 import BM25Index
from rag_llm.retrieval.hybrid import retrieve
from rag_llm.retrieval.text import tokenize
from rag_llm.verdict import generate_verdict

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
    stance = StanceResult(evidence=CORPUS[0], stance=Stance.SUPPORTS, confidence=0.9)
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
