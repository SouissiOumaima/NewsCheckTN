"""Tests du verdict par LLM contraint (Silver, Lot D), avec un faux LLM : aucun modèle chargé."""

import json

import pytest

from common.schemas import Claim, Evidence, Label, Lang, Stance, StanceResult
from data.loaders import load_evidence_corpus
from rag_llm import llm_verdict as lv
from rag_llm import silver_verdict as sv
from rag_llm.baseline_stance import predict_stances
from rag_llm.evaluate_retrieval import FIXTURES, load_claims

CLAIM = Claim(text="Le chômage en Tunisie est de 16,4 %.", lang=Lang.FR)
EVS = [
    Evidence(doc_id="d1", text="Selon l'INS, le chômage est de 16,4 %.", source="INS"),
    Evidence(doc_id="d2", text="Tunis est la capitale.", source="x"),
]


class FakeLLM:
    """Renvoie une réponse fixe, ou une réponse choisie par une fonction du prompt."""

    name = "fake-llm"

    def __init__(self, answer):
        self.answer, self.calls = answer, 0

    def generate(self, messages, seed):
        self.calls += 1
        return self.answer(messages, seed) if callable(self.answer) else self.answer


def test_prompt_numerote_les_passages_et_les_indices_nli():
    stances = [StanceResult(EVS[0], Stance.SUPPORTS, 0.9)]
    msgs = lv.build_messages(CLAIM, EVS, stances)
    user = msgs[1]["content"]
    assert msgs[0]["role"] == "system" and "UNIQUEMENT" in msgs[0]["content"]
    assert "[P1] (INS)" in user and "[P2]" in user and "soutient, confiance 0.90" in user
    assert "indice NLI" not in lv.build_messages(CLAIM, EVS)[1]["content"]


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("pas de json", "json_absent"),
        ('{"label": "vrai", "citations": ["P1"]', "json_absent"),
        ('{"label": "peut-etre", "citations": []}', "label_inconnu"),
        ('{"label": "vrai", "citations": ["P7"]}', "citation_hors_liste"),
        ('{"label": "faux", "citations": []}', "verdict_sans_citation"),
        ('{"label": "vrai", "citations": "P1"}', "citations_mal_formees"),
    ],
)
def test_sorties_rejetees(text, reason):
    with pytest.raises(lv.OutputError) as err:
        lv.parse_output(text, n_passages=2)
    assert err.value.reason == reason


def test_sortie_valide_avec_texte_autour():
    out = lv.parse_output(
        'Voici : {"label": "Vrai", "citations": ["[P1]", "P1"], '
        '"explication": "Confirmé par l\'INS."} fin',
        2,
    )
    assert out == {"label": "vrai", "indices": [1], "explanation": "Confirmé par l'INS."}
    nei = lv.parse_output('{"label": "preuves_insuffisantes", "citations": ["P2"]}', 2)
    assert nei["indices"] == []


def test_verdict_llm_cite_les_vrais_doc_id():
    llm = FakeLLM(json.dumps({"label": "vrai", "citations": ["P1"], "explication": "ok"}))
    res = lv.llm_verdict(CLAIM, EVS, llm, seed=1)
    assert res.valid and res.verdict.label == Label.TRUE and res.verdict.citations == ["d1"]
    assert not res.verdict.abstained and res.fallback is None


def test_sortie_rejetee_repli_gabarit_ou_abstention():
    llm = FakeLLM('{"label": "vrai", "citations": ["P9"]}')
    res = lv.llm_verdict(CLAIM, EVS, llm)
    assert not res.valid and res.fallback == "abstention" and res.verdict.abstained
    stances = [StanceResult(EVS[0], Stance.SUPPORTS, 0.9), StanceResult(EVS[1], Stance.NEUTRAL, 0)]
    res = lv.llm_verdict(CLAIM, EVS, llm, stances=stances, min_score=0.0)
    assert res.fallback == "gabarit" and res.error == "citation_hors_liste"
    assert res.verdict.label == Label.TRUE  # verdict du gabarit Bronze


def test_cache_des_generations(tmp_path):
    llm = FakeLLM('{"label": "preuves_insuffisantes", "citations": []}')
    path = tmp_path / "cache.jsonl"
    cached = sv.CachedGenerator(llm, path)
    msgs = lv.build_messages(CLAIM, EVS)
    cached.generate(msgs, 42)
    cached.generate(msgs, 42)
    cached.generate(msgs, 13)
    assert llm.calls == 2 and cached.hits == 1
    again = sv.CachedGenerator(llm, path)  # relu depuis le disque (reprise après coupure)
    again.generate(msgs, 42)
    assert llm.calls == 2 and again.hits == 1


def test_evaluation_complete_sur_le_dev(tmp_path):
    def answer(messages, seed):
        # « vrai » en citant P1 s'il y a un passage, sinon abstention
        if "[P1]" in messages[1]["content"]:
            return '{"label": "vrai", "citations": ["P1"], "explication": "x"}'
        return '{"label": "preuves_insuffisantes", "citations": []}'

    corpus = load_evidence_corpus(FIXTURES / "evidence_dev.jsonl")
    claims = load_claims(FIXTURES / "claims_dev.jsonl")
    gen = sv.CachedGenerator(FakeLLM(answer), tmp_path / "c.jsonl")
    res = sv.evaluate_split(corpus, claims, gen, predict_stances, method="bm25")
    systems = res["systems"]
    assert set(systems) == {"gabarit + NLI", *(s[0] for s in sv.LLM_SYSTEMS)}
    main = systems["LLM"]
    assert set(main["per_seed"]) == set(sv.SEEDS) and main["seeds"]["accuracy"]["std"] == 0.0
    assert main["metrics"]["valid_outputs"] == 1.0 and main["metrics"]["invalid_citations"] == 0
    assert set(main["bootstrap_vs_gabarit"]) == {"accuracy", "macro_f1"}
    assert len(main["per_claim"]) == len(claims)
    assert any(k.startswith("majorité") for k in res["baselines"])


def test_bootstrap_macro_f1():
    gold = ["vrai", "faux", "faux", "vrai"]
    same = sv.paired_bootstrap_macro_f1(gold, gold, gold, replications=100)
    assert same["diff"] == 0 and same["p_one_sided"] == 1.0
    better = sv.paired_bootstrap_macro_f1(gold, ["faux"] * 4, gold, replications=200)
    assert better["diff"] > 0


def test_api_reessaie_et_retire_la_graine(monkeypatch):
    import io
    import urllib.error

    monkeypatch.setenv("LLM_API_KEY", "cle-de-test")
    monkeypatch.setenv("LLM_MIN_INTERVAL", "0")
    monkeypatch.setattr("time.sleep", lambda s: None)
    gen = lv.OpenAICompatibleGenerator("modele-test", "https://exemple.invalid/v1")
    sent = []

    def fake_post(body):
        payload = json.loads(body)
        sent.append(payload)
        if len(sent) == 1:
            raise urllib.error.HTTPError("u", 429, "quota", {}, io.BytesIO(b""))
        if "seed" in payload:
            raise urllib.error.HTTPError("u", 400, "seed", {}, io.BytesIO(b""))
        return {"choices": [{"message": {"content": '{"label": "faux"}'}}]}

    monkeypatch.setattr(gen, "_post", fake_post)
    assert gen.generate([{"role": "user", "content": "x"}], seed=42) == '{"label": "faux"}'
    assert len(sent) == 3 and "seed" not in sent[-1] and sent[0]["model"] == "modele-test"
