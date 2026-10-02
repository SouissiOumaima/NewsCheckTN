"""Tests Lot A1."""

import json

from data.loaders import load_evidence_corpus


def test_sample_corpus_when_file_missing(tmp_path):
    corpus = load_evidence_corpus(tmp_path / "absent.jsonl")
    assert corpus and all(e.doc_id and e.text for e in corpus)


def test_load_jsonl(tmp_path):
    path = tmp_path / "corpus.jsonl"
    row = {"doc_id": "d1", "text": "Tunis est la capitale.", "source": "test"}
    path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    corpus = load_evidence_corpus(path)
    assert [e.doc_id for e in corpus] == ["d1"]
