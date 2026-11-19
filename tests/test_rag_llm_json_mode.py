"""Format JSON imposé à l'API compatible OpenAI (EXP-D-015)."""

import json

from rag_llm import llm_verdict as lv


def capture(monkeypatch, env):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    gen = lv.OpenAICompatibleGenerator()
    sent = []

    def fake_post(body):
        sent.append(json.loads(body))
        return {"choices": [{"message": {"content": '{"label": "vrai"}'}}]}

    monkeypatch.setattr(gen, "_post", fake_post)
    gen.generate([{"role": "user", "content": "x"}], seed=42)
    return sent[0]


def test_sans_option_rien_ne_change(monkeypatch):
    monkeypatch.delenv("LLM_RESPONSE_FORMAT", raising=False)
    payload = capture(monkeypatch, {"LLM_API_KEY": "k", "LLM_MIN_INTERVAL": "0"})
    assert "response_format" not in payload


def test_json_impose(monkeypatch):
    payload = capture(
        monkeypatch, {"LLM_API_KEY": "k", "LLM_MIN_INTERVAL": "0", "LLM_RESPONSE_FORMAT": "JSON"}
    )
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["seed"] == 42 and payload["temperature"] == lv.TEMPERATURE
