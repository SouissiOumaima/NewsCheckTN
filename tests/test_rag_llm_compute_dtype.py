"""Type de calcul du LLM local (EXP-D-013)."""

import pytest

from rag_llm import llm_verdict as lv


def test_float16_par_defaut(monkeypatch):
    monkeypatch.delenv("LLM_COMPUTE_DTYPE", raising=False)
    assert lv.compute_dtype_name() == "float16"


def test_float32(monkeypatch):
    monkeypatch.setenv("LLM_COMPUTE_DTYPE", " Float32 ")
    assert lv.compute_dtype_name() == "float32"


def test_valeur_refusee(monkeypatch):
    monkeypatch.setenv("LLM_COMPUTE_DTYPE", "int8")
    with pytest.raises(ValueError, match="LLM_COMPUTE_DTYPE"):
        lv.compute_dtype_name()
