"""Tests d'EXP-D-012 : comparaison de deux fichiers de verdict LLM (faux LLM, dev fictif)."""

import json

import pytest

from common.schemas import StanceResult
from data.loaders import load_evidence_corpus
from rag_llm import compare_llm_runs as cr
from rag_llm import silver_verdict as sv
from rag_llm.evaluate_retrieval import FIXTURES, load_claims


class FakeLLM:
    def __init__(self, name, label):
        self.name, self.label = name, label

    def generate(self, messages, seed):
        if self.label == "preuves_insuffisantes":
            return '{"label": "preuves_insuffisantes", "citations": []}'
        return '{"label": "%s", "citations": ["P1"], "explication": "x"}' % self.label


def neutral(claim, evidences):
    from common.schemas import Stance

    return [StanceResult(e, Stance.NEUTRAL, 0.5) for e in evidences]


def run(name, label, tmp_path):
    corpus = load_evidence_corpus(FIXTURES / "evidence_dev.jsonl")
    claims = load_claims(FIXTURES / "claims_dev.jsonl")
    gen = sv.CachedGenerator(FakeLLM(name, label), tmp_path / f"{name}.jsonl")
    res = sv.evaluate_split(corpus, claims, gen, neutral, "bm25", main_only=True)
    return {"llm": name, "prompt_sha": "abc", "temperature": 0.3, "seeds": [13, 42, 2026], **res}


@pytest.fixture
def two_runs(tmp_path):
    return run("ref-8b", "vrai", tmp_path), run("tiny", "faux", tmp_path)


def test_rapport_complet(two_runs):
    ref, cand = two_runs
    r = cr.compare_runs(ref, cand)
    assert r["protocol_differences"] == []
    assert r["cand_minus_ref"]["accuracy"]["diff"] == pytest.approx(
        r["cand"]["metrics"]["accuracy"] - r["ref"]["metrics"]["accuracy"], abs=1e-3
    )
    assert len(r["changed"]) > 0
    assert set(r["decision"]) >= {"valid_ok", "gap_ok", "demo_locale_autorisee"}


def test_memes_sorties_aucun_ecart(two_runs):
    ref, _ = two_runs
    r = cr.compare_runs(ref, ref)
    assert r["changed"] == [] and r["cand_minus_ref"]["accuracy"]["diff"] == 0
    assert r["decision"]["gap_ok"] is True


def test_regle_de_decision():
    assert cr.decide({"valid_outputs": 0.95}, 0.30)["demo_locale_autorisee"] is True
    assert cr.decide({"valid_outputs": 0.80}, 0.30)["demo_locale_autorisee"] is False
    assert cr.decide({"valid_outputs": 0.95}, 0.01)["demo_locale_autorisee"] is False
    assert cr.decide({}, 0.30)["demo_locale_autorisee"] is False


def test_protocole_different_signale(two_runs):
    ref, cand = two_runs
    cand = {**cand, "temperature": 0.1}
    assert cr.compare_runs(ref, cand)["protocol_differences"] == ["temperature"]


def test_affirmations_differentes_refusees(two_runs):
    ref, cand = two_runs
    rows = cand["systems"]["LLM"]["per_claim"][:-1]
    cand = {**cand, "systems": {"LLM": {**cand["systems"]["LLM"], "per_claim": rows}}}
    with pytest.raises(SystemExit, match="mêmes affirmations"):
        cr.compare_runs(ref, cand)


def test_cli(two_runs, tmp_path, monkeypatch, capsys):
    ref, cand = two_runs
    a, b = tmp_path / "ref.json", tmp_path / "tiny.json"
    a.write_text(json.dumps(ref), encoding="utf-8")
    b.write_text(json.dumps(cand), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["x", "--ref", str(a), "--cand", str(b)])
    cr.main()
    assert "démo locale autorisée" in capsys.readouterr().out
    assert (tmp_path / "tiny_vs_ref.json").exists()
