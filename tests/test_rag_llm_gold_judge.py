"""Lot D — Gold, EXP-D-017 : LLM-juge (lecture des annotations, sortie du juge, kappa)."""

import json

import pytest

from rag_llm import gold_judge as gj

ROW = {
    "claim_id": "dev-c01",
    "affirmation": "Le chômage a atteint 25 %.",
    "verdict": "vrai",
    "explication": "P1 contredit.",
    "citations": "P1, P5",
    "P1": "Chômage 16 %.",
    "P2": "Touristes.",
    "P3": "",
    "P4": "",
    "P5": "البطالة 16",
    "pertinence_P1": "pertinent",
    "pertinence_P5": "non_pertinent",
    "invente": "non",
    "fidelite": "infidele",
}


def test_etiquettes_humaines():
    lab = gj.human_labels(ROW)
    assert lab == {
        ("dev-c01", "pertinence:P1"): "pertinent",
        ("dev-c01", "pertinence:P5"): "non_pertinent",
        ("dev-c01", "invente"): "non",
        ("dev-c01", "fidelite"): "infidele",
    }


def test_messages_marquent_les_passages_cites():
    user = gj.build_messages(ROW, "règles")[1]["content"]
    assert "P1 (CITÉ) : Chômage 16 %." in user and "P2 : Touristes." in user
    assert "P3" not in user.split("Passages :")[1].split("Passages cités")[0]
    assert user.endswith("Passages cités : P1, P5")


def test_lecture_de_la_sortie_du_juge():
    raw = (
        'Voici : {"pertinence": {"P1": "pertinent", "P5": "non pertinent"}, '
        '"invente": "Non", "fidelite": "infidèle"}'
    )
    lab, err = gj.parse_judge(raw, ROW)
    assert err is None and lab[("dev-c01", "pertinence:P5")] == "non_pertinent"
    assert lab[("dev-c01", "fidelite")] == "infidele"
    assert gj.parse_judge("pas de json", ROW) == ({}, "json_absent")
    _, err = gj.parse_judge(json.dumps({"invente": "non", "fidelite": "fidele"}), ROW)
    assert err == "etiquettes_manquantes"


def test_kappa():
    assert gj.cohen_kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == pytest.approx(1.0)
    assert gj.cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"]) == pytest.approx(0.0)
    assert gj.cohen_kappa(["a", "a"], ["a", "a"]) is None  # une seule valeur : non défini


def test_accord_et_validation():
    ref = {("c1", "invente"): "oui", ("c2", "invente"): "non", ("c3", "invente"): "non"}
    same = dict(ref)
    agr = gj.agreement(ref, same, "invente")
    assert agr["n"] == 3 and agr["kappa"] == 1.0 and agr["disagreements"] == []
    flat = {("c1", "pertinence:P1"): "pertinent"}
    assert gj.agreement(flat, flat, "pertinence")["kappa"] is None
    v = gj.validate(
        {
            "invente": agr,
            "pertinence": gj.agreement(flat, flat, "pertinence"),
            "fidelite": {**agr, "kappa": 0.4},
        }
    )
    assert v == {
        "invente": "validée",
        "pertinence": "non validable (kappa non défini)",
        "fidelite": "non validée",
    }


def test_partage_fixe_en_deux_moities():
    ids = [f"c{i:02d}" for i in range(30)]
    h1, h2 = gj.split_halves(ids), gj.split_halves(list(reversed(ids)))
    assert h1 == h2
    assert len(h1["mise_au_point"]) == len(h1["mesure"]) == 15
    assert not set(h1["mise_au_point"]) & set(h1["mesure"])


def test_temperature_zero_pour_le_juge(monkeypatch):
    seen = {}

    def fake_generate(self, messages, seed):
        seen["t"] = gj.lv.TEMPERATURE
        return "{}"

    monkeypatch.setattr(gj.lv.OpenAICompatibleGenerator, "generate", fake_generate)
    monkeypatch.setenv("LLM_API_KEY", "x")
    before = gj.lv.TEMPERATURE
    gj.JudgeGenerator().generate([], 42)
    assert seen["t"] == 0.0 and gj.lv.TEMPERATURE == before


def test_prompt_v2_cles_explicites_et_format_plat():
    system = gj.build_messages(ROW, "Clés :\n{{CLES}}")[0]["content"]
    assert '"pertinence_P1"' in system and '"pertinence_P5"' in system
    assert '"verdict_fidele"' in system and "{{CLES}}" not in system
    v1 = gj.build_messages(ROW, "règles v1")[0]["content"]
    assert v1 == "règles v1"  # le prompt v1 reste identique (cache et résultats inchangés)
    raw = json.dumps(
        {
            "raison": "...",
            "sens_explication": "contredite",
            "pertinence_P1": "oui",
            "pertinence_P5": "Non",
            "fait_invente": "non",
            "verdict_fidele": "non",
        }
    )
    lab, err = gj.parse_judge(raw, ROW)
    assert err is None
    assert lab[("dev-c01", "pertinence:P1")] == "pertinent"
    assert lab[("dev-c01", "pertinence:P5")] == "non_pertinent"
    assert lab[("dev-c01", "invente")] == "non" and lab[("dev-c01", "fidelite")] == "infidele"
    _, err = gj.parse_judge('{"fait_invente": "oui", "verdict_fidele": "invente"}', ROW)
    assert err == "etiquettes_manquantes"


def test_prompt_v3_regle_de_fidelite_appliquee_par_le_code():
    system = gj.build_messages(ROW, 'liste "faits_absents"\n{{CLES}}')[0]["content"]
    assert '"faits_absents": ["..."]' in system and '"verdict_fidele"' not in system

    def judge(sens, absent, verdict="vrai"):
        raw = json.dumps(
            {
                "sens_explication": sens,
                "pertinence_P1": "oui",
                "pertinence_P5": "oui",
                "faits_absents": absent,
            }
        )
        return gj.parse_judge(raw, {**ROW, "verdict": verdict})

    lab, err = judge("contredite", [])  # explication contredit, verdict « vrai »
    assert err is None and lab[("dev-c01", "fidelite")] == "infidele"
    assert lab[("dev-c01", "invente")] == "non"
    lab, _ = judge("contredite", [], verdict="faux")
    assert lab[("dev-c01", "fidelite")] == "fidele"
    lab, _ = judge("contredite", ["troisième trimestre"], verdict="faux")
    assert lab[("dev-c01", "invente")] == "oui" and lab[("dev-c01", "fidelite")] == "infidele"
    lab, _ = judge("insuffisante", ["..."], verdict="preuves_insuffisantes")
    assert lab[("dev-c01", "invente")] == "non" and lab[("dev-c01", "fidelite")] == "fidele"
    _, err = judge("peut-être", [])
    assert err == "etiquettes_manquantes"
