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


def test_chemin_du_corpus_modifiable_par_variable_d_environnement(tmp_path, monkeypatch):
    import importlib

    import data.loaders as loaders

    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text('{"doc_id": "x-1", "text": "passage", "source": "test"}\n', encoding="utf-8")
    monkeypatch.setenv("EVIDENCE_CORPUS", str(corpus))
    try:
        reloaded = importlib.reload(loaders)
        assert [e.doc_id for e in reloaded.load_evidence_corpus()] == ["x-1"]
    finally:
        monkeypatch.delenv("EVIDENCE_CORPUS")
        importlib.reload(loaders)
