"""Tests du rapport Silver du Lot D (recherche dense et hybride), sans télécharger de modèle."""

import pytest

from data.loaders import load_evidence_corpus
from rag_llm import silver_retrieval as silver
from rag_llm.evaluate_retrieval import FIXTURES, load_claims
from rag_llm.retrieval.text import tokenize

_CONCEPTS = {"chomage": 0, "بطاله": 0, "tunisie": 1, "تونس": 1, "prix": 2, "سعر": 2}


class FakeEncoder:
    """Encodeur bilingue minuscule : un mot connu = une dimension partagée fr / ar."""

    def __init__(self, name="fake"):
        self.name = name

    def _vec(self, text):
        v = [0.0] * 3
        for tok in tokenize(text):
            if tok in _CONCEPTS:
                v[_CONCEPTS[tok]] += 1.0
        return v

    def encode_queries(self, texts):
        return [self._vec(t) for t in texts]

    def encode_passages(self, texts):
        return [self._vec(t) for t in texts]


@pytest.fixture
def fake(monkeypatch):
    monkeypatch.setattr(silver, "SentenceTransformerEncoder", FakeEncoder)


def test_metriques_par_affirmation():
    m = silver.claim_metrics(["a", "b"], ["x", "a", "y", "z", "w", "b"])
    assert m["recall@5"] == 0.5 and m["mrr"] == 0.5 and m["rank"] == 2
    assert m["hit@1"] == 0.0 and m["hit@5"] == 1.0
    assert silver.claim_metrics(["a"], [])["mrr"] == 0.0


def test_bootstrap_apparie():
    same = silver.paired_bootstrap([0.5, 1.0, 0.0], [0.5, 1.0, 0.0], replications=200)
    assert same["diff"] == 0 and same["ci95"] == [0, 0] and same["p_one_sided"] == 1.0
    better = silver.paired_bootstrap([0.0] * 10, [1.0] * 10, replications=200)
    assert better["diff"] == 1.0 and better["p_one_sided"] == 0.0
    with pytest.raises(ValueError):
        silver.paired_bootstrap([1.0], [1.0, 0.0])


def test_bootstrap_reproductible():
    a, b = [0.0, 1.0, 0.5, 0.0], [1.0, 1.0, 0.0, 0.5]
    assert silver.paired_bootstrap(a, b, 500) == silver.paired_bootstrap(a, b, 500)


def test_evaluation_complete_sur_le_dev(fake):
    corpus = load_evidence_corpus(FIXTURES / "evidence_dev.jsonl")
    claims = load_claims(FIXTURES / "claims_dev.jsonl")
    results = {
        name: silver.evaluate_config(corpus, claims, method, model, sim, runs=2)
        for name, method, model, sim in silver.CONFIGS
    }
    with_gold = sum(1 for c in claims if c.get("gold_doc_ids"))
    for res in results.values():
        assert res["summary"]["n"] == with_gold
        assert set(res["summary"]["by_lang"]) <= set(silver.LANGS)
        assert res["identical_runs"] is True
    tests = silver.compare(results)
    assert set(tests) == {name for name, *_ in silver.CONFIGS} - {"bm25"}
    assert silver.PRIMARY in tests


def test_le_seuil_dense_est_restaure(fake):
    before = silver.hybrid.MIN_DENSE_SIMILARITY
    with silver.configured(silver.BASE_MODEL, -1.0):
        assert silver.hybrid.MIN_DENSE_SIMILARITY == -1.0
    assert silver.hybrid.MIN_DENSE_SIMILARITY == before
