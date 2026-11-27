"""Lot D — EXP-D-020 (re-ranker) et EXP-D-021 (incertitude par le NLI), sans modèle téléchargé."""

import json

import pytest

from common.schemas import Claim, Evidence, Lang
from rag_llm import gold_reranker as gr
from rag_llm import gold_uncertainty as gu
from rag_llm.bronze_report import NEI
from rag_llm.retrieval import rerank as rr


class FakeScorer:
    name = "fake"

    def __init__(self, scores):
        self.scores = scores

    def score(self, pairs):
        return [self.scores[p[1]] for p in pairs]


def ev(doc_id, text):
    return Evidence(doc_id=doc_id, text=text, source="t")


def test_rerank_reclasse_et_garde_k():
    claim = Claim(text="q", lang=Lang.FR)
    passages = [ev("a", "A"), ev("b", "B"), ev("c", "C")]
    out = rr.rerank(claim, passages, FakeScorer({"A": 0.1, "B": 0.9, "C": 0.5}), k=2)
    assert [e.doc_id for e in out] == ["b", "c"] and out[0].score == 0.9
    same = rr.rerank(claim, passages, FakeScorer({"A": 0.5, "B": 0.5, "C": 0.5}), k=3)
    assert [e.doc_id for e in same] == ["a", "b", "c"]  # égalité : ordre RRF conservé
    assert rr.rerank(claim, [], FakeScorer({}), k=5) == []


def test_regle_de_repli_et_decision():
    assert gr.choose_model(3.0) == rr.PRIMARY_MODEL
    assert gr.choose_model(15.1) == rr.FALLBACK_MODEL
    dev = {"hybride": {"recall@5": 0.9}, "hybride + re-ranker": {"recall@5": 0.9}}
    up = {"bootstrap_recall@5": {"diff": 0.05, "p_one_sided": 0.01}}
    assert gr.decide(up, dev)["adopted"]
    assert not gr.decide({"bootstrap_recall@5": {"diff": 0.05, "p_one_sided": 0.2}}, dev)["adopted"]
    worse = {"hybride": {"recall@5": 0.9}, "hybride + re-ranker": {"recall@5": 0.8}}
    assert not gr.decide(up, worse)["adopted"]


def test_rappel_par_affirmation():
    assert gr.claim_recall(["a", "b"], ["a", "x", "y"]) == 0.5
    assert gr.claim_recall([], ["a"]) == 0.0


def test_mesure_unique_du_test(tmp_path, monkeypatch):
    monkeypatch.setattr(gr, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["x", "--split", "test"])
    with pytest.raises(SystemExit, match="dev"):
        gr.main()
    (tmp_path / "lot-d_reranker_dev.json").write_text(
        json.dumps({"model": rr.PRIMARY_MODEL, "chosen_model": rr.PRIMARY_MODEL})
    )
    (tmp_path / "lot-d_reranker_test.json").write_text("{}")
    with pytest.raises(SystemExit, match="unique"):
        gr.main()


STANCES = {
    "d1": ("supports", 0.9),
    "d2": ("refutes", 0.8),
    "d3": ("neutral", 0.6),
    "d4": ("neutral", 0.4),
    "d5": ("refutes", 0.3),
}


def test_formule_d_incertitude():
    assert gu.uncertainty("vrai", ["d1", "d2"], STANCES) == pytest.approx(0.1)
    assert gu.uncertainty("faux", ["d1", "d2"], STANCES) == pytest.approx(0.2)
    assert gu.uncertainty("faux", ["d1"], STANCES) == 1.0  # aucun passage cité ne contredit
    assert gu.uncertainty("trompeur", ["d5", "d3"], STANCES) == pytest.approx(0.7)
    # preuves insuffisantes : moyenne sur les 5 passages (0.6 + 0.4) / 5 = 0.2
    assert gu.uncertainty(NEI, [], STANCES) == pytest.approx(0.8)
    assert gu.uncertainty("faux", ["inconnu"], STANCES) == 1.0


def test_auroc_brier_ece_et_decision():
    assert gu.auroc([0.9, 0.8, 0.1, 0.2], [1, 1, 0, 0]) == 1.0
    assert gu.auroc([0.1, 0.2, 0.9, 0.8], [1, 1, 0, 0]) == 0.0
    assert gu.auroc([0.5, 0.5], [1, 0]) == 0.5
    assert gu.auroc([0.5, 0.6], [1, 1]) is None
    assert gu.brier([1.0, 0.0], [1, 0]) == 0.0
    assert gu.ece([0.9, 0.9, 0.1, 0.1], [1, 1, 0, 0]) == pytest.approx(0.1)
    m = gu.measure([0.9] * 10 + [0.1] * 10, [1] * 10 + [0] * 10)
    assert m["auroc"] == 1.0 and m["auroc_ci95"][0] > 0.5 and gu.decide(m)["adopted"]
    assert not gu.decide({"auroc_ci95": [0.4, 0.9]})["adopted"]
    assert not gu.decide({"auroc_ci95": None})["adopted"]


def test_lignes_et_controle_des_citations():
    verdicts = [
        {"claim_id": "c1", "pred": "faux", "gold": "faux", "citations": ["d2"]},
        {"claim_id": "c2", "pred": "vrai", "gold": "faux", "citations": ["d1"]},
    ]
    stances = {"c1": STANCES, "c2": STANCES}
    rows = gu.build_rows(verdicts, stances, {"c1": True, "c2": False})
    assert [r["faux"] for r in rows] == [0, 1]
    assert [r["mauvais"] for r in rows] == [1, 1]
    assert rows[0]["u"] == pytest.approx(0.2)
    with pytest.raises(SystemExit, match="non reproduite"):
        gu.build_rows([{**verdicts[0], "citations": ["zz"]}], stances, None)


def test_comparaison_verdict_bonnes_reponses_perdues():
    from rag_llm import gold_reranker_verdict as gv

    base = [
        {"claim_id": "a", "pred": "faux", "gold": "faux"},
        {"claim_id": "b", "pred": "vrai", "gold": "faux"},
        {"claim_id": "c", "pred": "vrai", "gold": "vrai"},
    ]
    new = [
        {"claim_id": "a", "pred": "vrai", "gold": "faux"},
        {"claim_id": "b", "pred": "faux", "gold": "faux"},
        {"claim_id": "c", "pred": "vrai", "gold": "vrai"},
    ]
    cmp_ = gv.compare(base, new)
    assert cmp_["lost"] == ["a"] and cmp_["gained"] == ["b"]
    assert cmp_["correct_base"] == cmp_["correct_rerank"] == 2
    assert cmp_["condition_at_most_one_lost"]
    new2 = [{**r, "pred": "trompeur"} for r in new]
    assert not gv.compare(base, new2)["condition_at_most_one_lost"]
