"""Clé du cache et `--exp-id` de silver_verdict (remarques de relecture de la PR #33)."""

import argparse

import pytest

from rag_llm import silver_verdict as sv


class Fake:
    name = "fake"

    def __init__(self, json_mode=None):
        if json_mode is not None:
            self.json_mode = json_mode
        self.calls = 0

    def generate(self, messages, seed):
        self.calls += 1
        return '{"label": "vrai"}'


MSG = [{"role": "user", "content": "x"}]


def test_cle_inchangee_sans_format_json():
    old = sv.CachedGenerator(Fake(), None)._key(MSG, 42)
    assert sv.CachedGenerator(Fake(json_mode=False), None)._key(MSG, 42) == old


def test_format_json_dans_la_cle(tmp_path):
    path = tmp_path / "cache.jsonl"
    sans_json = sv.CachedGenerator(Fake(), path)
    sans_json.generate(MSG, 42)
    inner = Fake(json_mode=True)
    avec_json = sv.CachedGenerator(inner, path)  # même fichier de cache
    avec_json.generate(MSG, 42)
    assert avec_json._key(MSG, 42) != sans_json._key(MSG, 42)
    assert (avec_json.hits, avec_json.misses, inner.calls) == (0, 1, 1)


def test_exp_id():
    assert sv.exp_id_arg("EXP-D-015") == "EXP-D-015"
    assert sv.DEFAULT_EXP_ID == "EXP-D-009"
    for bad in ("EXP-B-001", "exp-d-015", "EXP-D-15"):
        with pytest.raises(argparse.ArgumentTypeError):
            sv.exp_id_arg(bad)
