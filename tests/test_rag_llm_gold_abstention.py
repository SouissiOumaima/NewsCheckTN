"""Lot D — Gold, EXP-D-018 : règle R-abst, règle de décision et fichiers d'annotation."""

import json

import pytest

from common.schemas import Stance, StanceResult
from data.loaders import load_evidence_corpus
from rag_llm import gold_abstention as ga
from rag_llm.bronze_report import NEI
from rag_llm.evaluate_retrieval import load_claims
from rag_llm.silver_retrieval import SPLITS


def row(cid, gold, pred, citations, abstained=None):
    return {
        "claim_id": cid,
        "gold": gold,
        "pred": pred,
        "abstained": pred == NEI if abstained is None else abstained,
        "citations": citations,
        "invalid_citations": [],
        "lang": "fr",
        "group": "fr-latin",
    }


STANCES = {
    "c1": {"d1": "refutes", "d2": "neutral"},
    "c2": {"d3": "neutral", "d4": "neutral"},
    "hs1": {"d5": "neutral"},
    "c3": {"d6": "supports"},
}


def test_rabst_seulement_si_tous_les_passages_cites_sont_neutres():
    rows = [
        row("c1", "faux", "faux", ["d1", "d2"]),  # un passage contredit : inchangé
        row("c2", "faux", "faux", ["d3", "d4"]),  # tous neutres : abstention
        row("hs1", NEI, "faux", ["d5"]),  # tous neutres : abstention
        row("c3", NEI, NEI, []),  # déjà abstenu : inchangé
    ]
    out = ga.apply_rabst(rows, STANCES)
    assert [r["rabst_applied"] for r in out] == [False, True, True, False]
    assert [r["pred"] for r in out] == ["faux", NEI, NEI, NEI]
    assert all(r["abstained"] for r in out[1:])
    assert out[0]["cited_stances"] == ["refutes", "neutral"]
    assert rows[1]["pred"] == "faux"  # l'entrée n'est pas modifiée


def test_regle_de_decision():
    base = [
        row("c1", "faux", "faux", ["d1", "d2"]),
        row("c2", "faux", "faux", ["d3", "d4"]),
        row("hs1", NEI, "faux", ["d5"]),
    ]
    eff = ga.compare_rabst(base, ga.apply_rabst(base, STANCES))
    assert eff["justified_abstentions_gained"] == ["hs1"]
    assert eff["with_evidence_turned_to_abstention"] == ["c2"]
    assert eff["correct_answers_lost"] == ["c2"]
    assert eff["condition_1_justified_abstention_up"]
    assert eff["condition_2_at_most_one_correct_lost"]
    assert eff["adopted"]

    # deux bons verdicts perdus : refusée
    base2 = base + [row("c4", "vrai", "vrai", ["d7"])]
    stances2 = {**STANCES, "c4": {"d7": "neutral"}}
    eff2 = ga.compare_rabst(base2, ga.apply_rabst(base2, stances2))
    assert eff2["correct_answers_lost"] == ["c2", "c4"]
    assert not eff2["condition_2_at_most_one_correct_lost"] and not eff2["adopted"]

    # aucune abstention justifiée gagnée : refusée
    base3 = [row("c1", "faux", "faux", ["d1", "d2"])]
    assert not ga.compare_rabst(base3, ga.apply_rabst(base3, STANCES))["adopted"]


def test_empreinte_des_phrases_hors_sujet(tmp_path, monkeypatch):
    f = tmp_path / "hs.jsonl"
    f.write_text('{"claim_id": "dev-hs01"}\n', encoding="utf-8")
    monkeypatch.setattr(ga, "HORS_SUJET", f)
    with pytest.raises(SystemExit, match="modifiées"):
        ga.load_dev_claims()
    monkeypatch.setattr(ga, "HORS_SUJET", tmp_path / "absent.jsonl")
    with pytest.raises(SystemExit, match="absent"):
        ga.load_dev_claims()


def test_echantillon_seconde_annotatrice_fixe():
    lines = [{"claim_id": f"c{i}"} for i in range(30)]
    a, b = ga.second_annotator_sample(lines), ga.second_annotator_sample(lines)
    assert a == b and len(a) == 10 and len({r["claim_id"] for r in a}) == 10


class FakeLLM:
    name = "fake"

    def generate(self, messages, seed):
        return json.dumps({"label": "faux", "citations": ["P1"], "explication": "Selon P1."})


def neutral_stances(claim, evidences):
    return [StanceResult(evidence=e, stance=Stance.NEUTRAL, confidence=0.5) for e in evidences]


def test_bout_en_bout_dev_avec_faux_llm(tmp_path):
    claims = load_claims(SPLITS["dev"][1])[:4]
    corpus = load_evidence_corpus(SPLITS["dev"][0])
    res = ga.evaluate(claims, corpus, FakeLLM(), neutral_stances, method="bm25")
    r42 = res["per_seed"][ga.MAIN_SEED]
    assert set(res["per_seed"]) == set(ga.SEEDS)
    assert all(r["pred"] == "faux" for r in r42["llm_rows"])  # Falcon tel quel
    assert all(r["pred"] == NEI for r in r42["per_claim"])  # tout est neutre : R-abst partout

    lines = ga.annotation_rows(claims, res["prepared"], r42["llm_rows"])
    assert lines[0]["citations"] == "P1" and lines[0]["P1"]
    assert "gold" not in lines[0] and "gold_label" not in lines[0]  # verdict de référence caché
    out = tmp_path / "a.csv"
    ga.write_csv(out, lines)
    assert out.read_text(encoding="utf-8-sig").splitlines()[0].startswith("claim_id,affirmation")
