"""Tests Lot D."""

from common.schemas import Claim, Evidence, Label, Lang, Stance, StanceResult
from rag_llm.retrieval.hybrid import retrieve
from rag_llm.verdict import generate_verdict

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
