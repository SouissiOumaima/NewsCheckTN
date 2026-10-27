"""Tests Lot A1."""

import json

import pytest

from data.loaders import CorpusError, load_evidence_corpus


def test_echantillon_si_aucun_corpus_configure(tmp_path, monkeypatch):
    import data.loaders as loaders

    monkeypatch.delenv("EVIDENCE_CORPUS", raising=False)
    monkeypatch.setattr(loaders, "DEFAULT_CORPUS", tmp_path / "absent.jsonl")
    corpus = loaders.load_evidence_corpus()
    assert corpus and all(e.doc_id and e.text for e in corpus)
    assert loaders.corpus_origin()["origin"] == "échantillon"
    assert "warning" in loaders.corpus_origin()


def test_load_jsonl(tmp_path):
    path = tmp_path / "corpus.jsonl"
    row = {"doc_id": "d1", "text": "Tunis est la capitale.", "source": "test"}
    path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    corpus = load_evidence_corpus(path)
    assert [e.doc_id for e in corpus] == ["d1"]


def test_chemin_du_corpus_modifiable_par_variable_d_environnement(tmp_path, monkeypatch):
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text('{"doc_id": "x-1", "text": "passage", "source": "test"}\n', encoding="utf-8")
    monkeypatch.setenv("EVIDENCE_CORPUS", str(corpus))
    assert [e.doc_id for e in load_evidence_corpus()] == ["x-1"]


def test_corpus_demande_mais_absent_erreur_claire(tmp_path, monkeypatch):
    monkeypatch.setenv("EVIDENCE_CORPUS", str(tmp_path / "absent.jsonl"))
    with pytest.raises(CorpusError, match="introuvable"):
        load_evidence_corpus()
    with pytest.raises(CorpusError, match="introuvable"):
        load_evidence_corpus(tmp_path / "autre.jsonl")


def test_corpus_dossier_au_lieu_d_un_fichier(tmp_path):
    with pytest.raises(CorpusError, match="fichier"):
        load_evidence_corpus(tmp_path)


@pytest.mark.parametrize(
    "contenu, message",
    [
        ('{"doc_id": "a", "text": "ok"}\n{pas du json\n', "ligne 2 : JSON invalide"),
        ('{"text": "sans identifiant"}\n', "ligne 1 : champ « doc_id » manquant"),
        ('{"doc_id": "a", "text": ""}\n', "ligne 1 : champ « text »"),
        (
            '{"doc_id": "a", "text": "x"}\n{"doc_id": "a", "text": "y"}\n',
            "ligne 2 : doc_id « a » en double",
        ),
    ],
)
def test_corpus_invalide_message_avec_numero_de_ligne(tmp_path, contenu, message):
    path = tmp_path / "corpus.jsonl"
    path.write_text(contenu, encoding="utf-8")
    with pytest.raises(CorpusError, match=message):
        load_evidence_corpus(path)
