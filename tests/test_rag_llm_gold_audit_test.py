"""Lot D — Gold, EXP-D-016 : préparation de l'audit du test v1 (sur le dev, sans LLM)."""

import json

import pytest

from data.loaders import load_evidence_corpus
from rag_llm import gold_audit_test as ga
from rag_llm.evaluate_retrieval import load_claims
from rag_llm.silver_retrieval import SPLITS
from rag_llm.silver_verdict import prepare


def test_lecture_du_systeme_principal(tmp_path):
    f = tmp_path / "r.json"
    f.write_text(json.dumps({"split": "test", "systems": {"LLM": {"per_claim": [{"x": 1}]}}}))
    payload, rows = ga.load_main_rows(f)
    assert rows == [{"x": 1}] and payload["split"] == "test"
    f.write_text(json.dumps({"systems": {"gabarit + NLI": {"per_claim": []}}}))
    with pytest.raises(SystemExit, match="absent"):
        ga.load_main_rows(f)


def test_controle_des_citations():
    corpus_path, claims_path = SPLITS["dev"]
    claims = load_claims(claims_path)[:2]
    prepared = prepare(load_evidence_corpus(corpus_path), claims, "bm25", ga.no_stances)
    top = prepared[claims[0]["claim_id"]][1][0].doc_id
    ok = [{"claim_id": claims[0]["claim_id"], "citations": [top]}]
    assert ga.check_citations(ok, prepared) == []
    bad = [{"claim_id": claims[0]["claim_id"], "citations": ["inconnu"]}]
    assert ga.check_citations(bad, prepared) == [f"{claims[0]['claim_id']}:inconnu"]
