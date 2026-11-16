"""Tests d'EXP-D-011 (verdict avec le NLI affiné du Lot C), avec un faux LLM et de faux NLI."""

import pytest

from common.schemas import Stance, StanceResult
from data.loaders import load_evidence_corpus
from models.nli import stance as nli
from rag_llm import silver_verdict as sv
from rag_llm import silver_verdict_nli as snli
from rag_llm.evaluate_retrieval import FIXTURES, load_claims


class FakeLLM:
    name = "fake-llm"

    def generate(self, messages, seed):
        user = messages[1]["content"]
        if "contredit" in user:  # indices NLI montrés : suit la première position
            return '{"label": "faux", "citations": ["P1"], "explication": "x"}'
        if "[P1]" in user:
            return '{"label": "vrai", "citations": ["P1"], "explication": "x"}'
        return '{"label": "preuves_insuffisantes", "citations": []}'


def fixed(stance_value):
    def predict(claim, evidences):
        return [StanceResult(e, stance_value, 0.9) for e in evidences]

    return predict


@pytest.fixture
def dev():
    corpus = load_evidence_corpus(FIXTURES / "evidence_dev.jsonl")
    claims = load_claims(FIXTURES / "claims_dev.jsonl")
    return claims, snli.retrieve_all(corpus, claims, "bm25")


@pytest.fixture
def nli_propre(monkeypatch):
    """Les tests changent NLI_BACKEND : on remet le moteur « stub » des tests ensuite."""
    monkeypatch.setenv("NLI_BACKEND", "stub")
    yield
    nli.set_classifier(None)


def test_evaluation_complete_sur_le_dev(dev, tmp_path):
    claims, retrieved = dev
    stances = {
        "bronze": snli.stances_for(retrieved, fixed(Stance.SUPPORTS)),
        "fine-tuned": snli.stances_for(retrieved, fixed(Stance.REFUTES)),
    }
    gen = sv.CachedGenerator(FakeLLM(), tmp_path / "c.jsonl")
    res = snli.evaluate(claims, retrieved, stances, gen, "bm25")

    assert set(res["systems"]) == {
        "gabarit + NLI Bronze",
        "gabarit + NLI affiné",
        *(name for name, _ in snli.LLM_SYSTEMS),
    }
    assert set(res["comparisons"]) == {f"{c} vs {b}" for c, b in snli.COMPARISONS}
    for s in res["systems"].values():
        assert len(s["per_claim"]) == len(claims)
    # le moteur NLI change bien les verdicts (indices montrés au LLM, et gabarit)
    pred = lambda name: [r["pred"] for r in res["systems"][name]["per_claim"]]  # noqa: E731
    assert pred("LLM + indices NLI affiné") != pred("LLM + indices NLI Bronze")
    assert pred("gabarit + NLI affiné") != pred("gabarit + NLI Bronze")
    ag = res["stance_agreement"]
    assert ag["identical"] == 0.0 and ag["n_passages"] > 0


def test_meme_passages_pour_tous_les_systemes(dev, tmp_path):
    claims, retrieved = dev
    same = snli.stances_for(retrieved, fixed(Stance.NEUTRAL))
    gen = sv.CachedGenerator(FakeLLM(), tmp_path / "c.jsonl")
    res = snli.evaluate(claims, retrieved, {"bronze": same, "fine-tuned": same}, gen, "bm25")
    s = res["systems"]
    assert s["gabarit + NLI Bronze"]["per_claim"] == s["gabarit + NLI affiné"]["per_claim"]
    assert res["stance_agreement"]["identical"] == 1.0
    assert (
        res["comparisons"]["gabarit + NLI affiné vs gabarit + NLI Bronze"]["accuracy"]["diff"] == 0
    )


def test_activation_du_nli_bronze(nli_propre):
    info = snli.activate("bronze")
    assert info["backend"] == "bronze" and info["status"] == "loaded"


def test_arret_si_le_checkpoint_affine_manque(nli_propre, monkeypatch, tmp_path):
    missing = str(tmp_path / "absent")
    monkeypatch.setenv("NLI_FINETUNED_MODEL", missing)
    monkeypatch.setenv("NLI_MODEL", missing)
    with pytest.raises(SystemExit, match="non chargé"):
        snli.activate("fine-tuned")


def test_empreinte_des_poids(tmp_path):
    assert snli._weights_sha256(tmp_path) is None
    (tmp_path / "model.safetensors").write_bytes(b"abc")
    assert snli._weights_sha256(tmp_path).startswith("ba7816bf")
