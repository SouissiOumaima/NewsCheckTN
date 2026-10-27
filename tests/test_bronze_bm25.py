"""Critères vérifiables de la recherche BM25 du palier Bronze."""

from common.schemas import Claim, Evidence, Lang
from rag_llm.retrieval.hybrid import retrieve


CORPUS = [
    Evidence("fr-1", "L'INS publie le chômage de la Tunisie en 2023.", "INS"),
    Evidence("fr-2", "Le ministère annonce de nouveaux horaires scolaires.", "MEN"),
    Evidence("fr-3", "Le chômage tunisien atteint 16,4 % au deuxième trimestre 2023.", "INS"),
]


def test_bronze_bm25_ranks_the_most_specific_french_evidence_first():
    claim = Claim("Le chômage tunisien est de 16,4 % en 2023.", Lang.FR)
    results = retrieve(claim, CORPUS, k=2)
    assert [item.doc_id for item in results] == ["fr-3", "fr-1"]
    assert results[0].score > results[1].score > 0


def test_bronze_bm25_returns_no_evidence_without_lexical_match():
    claim = Claim("La récolte d'olives augmente fortement.", Lang.FR)
    assert retrieve(claim, CORPUS) == []


def test_bronze_bm25_honours_an_empty_result_limit():
    claim = Claim("Le chômage tunisien.", Lang.FR)
    assert retrieve(claim, CORPUS, k=0) == []
