"""Lot E — Contrat commun, repli visible et aucune transmission sans accord."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from common import verdict_runtime as runtime
from common.schemas import Claim, Evidence, Label, Lang, Stance, StanceResult


class FakeGenerator:
    name = "local-fictitious-generator"

    def __init__(self, text):
        self.text = text
        self.calls = 0

    def generate(self, messages, seed):
        self.calls += 1
        return self.text


@pytest.fixture
def case(monkeypatch):
    monkeypatch.setenv("VERDICT_BACKEND", "llm")
    monkeypatch.setenv("LLM_PROVIDER", "hf")
    claim = Claim("Tunis est la capitale de la Tunisie.", Lang.FR)
    evidence = Evidence("demo-1", claim.text, "exemple fictif", score=2.0)
    stance = StanceResult(evidence, Stance.SUPPORTS, 0.99)
    return claim, [evidence], [stance]


def test_default_gabarit_never_constructs_a_generator(case, monkeypatch):
    monkeypatch.delenv("VERDICT_BACKEND")
    monkeypatch.setattr(runtime, "_generator", lambda *args: pytest.fail("LLM appelé"))
    verdict, info = runtime.resolve_verdict(*case)
    assert verdict.label == Label.TRUE
    assert info["used"] == "gabarit" and info["fallback_reason"] is None


def test_valid_llm_output_maps_only_supplied_citations(case, monkeypatch):
    generator = FakeGenerator('{"label":"vrai","citations":["P1"],"explication":"Démo"}')
    monkeypatch.setattr(runtime, "_generator", lambda *args: generator)
    verdict, info = runtime.resolve_verdict(*case)
    assert verdict.citations == ["demo-1"]
    assert verdict.label == Label.TRUE and info["used"] == "llm"
    assert "raw" not in info and generator.calls == 1


@pytest.mark.parametrize("text", [
    '{"label":"vrai","citations":["P99"]}',
    '{"label":"vrai","citations":[]}',
    'not JSON',
])
def test_invalid_generation_falls_back_visibly(case, monkeypatch, text):
    monkeypatch.setattr(runtime, "_generator", lambda *args: FakeGenerator(text))
    verdict, info = runtime.resolve_verdict(*case)
    assert info["used"] == "gabarit" and info["fallback_reason"]
    assert verdict.citations == ["demo-1"]


def test_no_evidence_abstains_without_calling_a_model(case, monkeypatch):
    monkeypatch.setattr(runtime, "_generator", lambda *args: pytest.fail("LLM appelé"))
    verdict, info = runtime.resolve_verdict(case[0], [], [])
    assert verdict.abstained and not verdict.citations
    assert info["fallback_reason"] == "no_evidence"


def test_remote_provider_blocked_before_generator_construction(case, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.invalid/v1")
    monkeypatch.delenv("LLM_ALLOW_EXTERNAL", raising=False)
    monkeypatch.setattr(runtime, "_generator", lambda *args: pytest.fail("Transmission tentée"))
    _, info = runtime.resolve_verdict(*case)
    assert info["fallback_reason"] == "external_provider_not_authorized"


def test_failed_generator_does_not_leak_provider_error(case, monkeypatch):
    def unavailable(*args):
        raise RuntimeError("private prompt or API key")

    monkeypatch.setattr(runtime, "_generator", unavailable)
    verdict, info = runtime.resolve_verdict(*case)
    assert verdict.citations == ["demo-1"]
    assert info["fallback_reason"] == "llm_unavailable" and "private" not in str(info)


def test_api_routes_use_same_llm_runtime(case, monkeypatch):
    generator = FakeGenerator('{"label":"vrai","citations":["P1"],"explication":"Démo"}')
    monkeypatch.setattr(runtime, "_generator", lambda *args: generator)
    client = TestClient(app)
    text = "Le taux de chômage en Tunisie est de 16,4 % en 2023."
    payload = {"claim": text}
    assert client.post("/verdict", json=payload).json()["label"] == "vrai"
    detail = client.post("/verdict/detail", json=payload)
    assert detail.status_code == 200
    assert detail.json()["verdict_engine"]["used"] == "llm"
    trace = client.post("/check/detail", json={"text": text})
    assert trace.status_code == 200
    assert trace.json()["claims"][0]["verdict_engine"]["used"] == "llm"
    assert trace.json()["timings_ms"]["total"] >= 0
    assert client.post("/check", json={"text": text}).json()["verdicts"]


@pytest.mark.parametrize("base_url,allow", [
    ("http://127.0.0.1:11434/v1", "0"),
    ("https://example.invalid/v1", "1"),
])
def test_explicitly_permitted_provider_reaches_only_fake_generator(
    case, monkeypatch, base_url, allow
):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_BASE_URL", base_url)
    monkeypatch.setenv("LLM_ALLOW_EXTERNAL", allow)
    generator = FakeGenerator('{"label":"preuves_insuffisantes","citations":[]}')
    monkeypatch.setattr(runtime, "_generator", lambda *args: generator)
    verdict, info = runtime.resolve_verdict(*case)
    assert generator.calls == 1 and verdict.abstained and not verdict.citations
    assert info["used"] == "llm"
