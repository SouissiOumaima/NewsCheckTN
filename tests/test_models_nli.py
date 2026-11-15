"""Tests Lot C — Model 2 (NLI) : contrat, préparation des données, évaluation."""

import json

import pytest

from common.schemas import Claim, Evidence, Lang, Stance
from models.nli import data, stance
from models.nli.evaluate import metrics


def fake_classifier(pairs):
    """Faux modèle : « faux » dans la preuve → contradiction, mots communs → implication."""
    out = []
    for premise, hypothesis in pairs:
        if "faux" in premise:
            out.append({"entailment": 0.1, "neutral": 0.1, "contradiction": 0.8})
        elif set(premise.lower().split()) & set(hypothesis.lower().split()):
            out.append({"entailment": 0.7, "neutral": 0.2, "contradiction": 0.1})
        else:
            out.append({"entailment": 0.1, "neutral": 0.85, "contradiction": 0.05})
    return out


@pytest.fixture
def fake_model():
    stance.set_classifier(fake_classifier, "faux-modele")
    yield
    stance.set_classifier(None)


CLAIM = Claim(text="Tunis est la capitale.", lang=Lang.FR)


def ev(text, i="e1"):
    return Evidence(doc_id=i, text=text, source="t")


def test_contrat_avec_un_modele(fake_model):
    res = stance.predict_stances(
        CLAIM,
        [ev("Tunis capitale de la Tunisie", "a"), ev("c'est faux", "b"), ev("autre sujet", "c")],
    )
    assert [r.stance for r in res] == [Stance.SUPPORTS, Stance.REFUTES, Stance.NEUTRAL]
    assert [r.evidence.doc_id for r in res] == ["a", "b", "c"]
    assert all(0.0 <= r.confidence <= 1.0 for r in res)
    assert stance.backend_info()["status"] == "loaded"


def test_sans_modele_reponse_neutre():
    stance.set_classifier(None)
    res = stance.predict_stance(CLAIM, ev("Tunis est la capitale de la Tunisie."))
    assert res.stance == Stance.NEUTRAL and res.confidence == 0.0
    assert stance.predict_stances(CLAIM, []) == []


def test_echec_de_chargement_ne_fait_pas_tomber_l_api(monkeypatch):
    stance.set_classifier(None)
    monkeypatch.setenv("NLI_BACKEND", "zero-shot")

    def boom(name):
        raise OSError("pas de réseau")

    monkeypatch.setattr(stance, "_load_zero_shot", boom)
    assert stance.predict_stance(CLAIM, ev("x")).stance == Stance.NEUTRAL
    assert stance.backend_info()["status"] == "unavailable"
    stance.set_classifier(None)


def test_backend_fine_tuned_charge_le_checkpoint_silver(monkeypatch):
    """NLI_BACKEND=fine-tuned : checkpoint Silver (graine 42) par défaut, ou NLI_FINETUNED_MODEL."""
    loaded = []

    def fake_load(name):
        loaded.append(name)
        return fake_classifier

    monkeypatch.setattr(stance, "_load_zero_shot", fake_load)
    monkeypatch.setenv("NLI_BACKEND", "fine-tuned")
    monkeypatch.delenv("NLI_FINETUNED_MODEL", raising=False)
    monkeypatch.delenv("CHECKPOINT_DIR", raising=False)
    monkeypatch.setenv("NLI_MODEL", stance.DEFAULT_MODEL)  # comme .env.example : sans effet ici
    stance.set_classifier(None)
    res = stance.predict_stance(CLAIM, ev("c'est faux"))
    assert res.stance == Stance.REFUTES
    expected = stance.ROOT / "models" / "checkpoints" / "nli_mdeberta-ft_v3_lr1e-05_e6_seed42"
    assert loaded == [str(expected)]
    assert stance.backend_info() == {
        "backend": "fine-tuned",
        "model": str(expected),
        "status": "loaded",
    }

    monkeypatch.setenv("NLI_FINETUNED_MODEL", "autre/checkpoint")
    stance.set_classifier(None)
    stance.predict_stance(CLAIM, ev("x"))
    assert loaded[-1] == "autre/checkpoint"
    stance.set_classifier(None)


def test_backend_fine_tuned_sans_checkpoint_reponse_neutre(monkeypatch):
    def boom(name):
        raise OSError(f"{name} introuvable")

    monkeypatch.setattr(stance, "_load_zero_shot", boom)
    monkeypatch.setenv("NLI_BACKEND", "fine-tuned")
    stance.set_classifier(None)
    res = stance.predict_stance(CLAIM, ev("Tunis capitale"))
    assert res.stance == Stance.NEUTRAL and res.confidence == 0.0
    assert stance.backend_info()["status"] == "unavailable"
    stance.set_classifier(None)


def test_chargement_du_modele_en_float32(monkeypatch):
    """Même chargement que train.py (float32), sans torch ni transformers réels (CI légère)."""
    import sys
    import types

    seen = {}
    fake_torch = types.SimpleNamespace(float32="float32")

    class FakeModel:
        config = types.SimpleNamespace(id2label={0: "entailment", 1: "neutral", 2: "contradiction"})

        def eval(self):
            return self

    def load_model(name, **kwargs):
        seen.update(kwargs)
        return FakeModel()

    fake_tf = types.SimpleNamespace(
        AutoTokenizer=types.SimpleNamespace(from_pretrained=lambda name, **k: object()),
        AutoModelForSequenceClassification=types.SimpleNamespace(from_pretrained=load_model),
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "transformers", fake_tf)
    stance._load_zero_shot("faux-modele")
    assert seen.get("dtype") == "float32"


def pair(pid, art, claim, evidence, label="supports", remarque="ok", lang="ar"):
    return {
        "pair_id": pid,
        "claim": claim,
        "evidence": evidence,
        "label": label,
        "claim_lang": lang,
        "evidence_id": f"{art}-E1",
        "remarque": remarque,
    }


def test_brouillons_et_validations_confirmees():
    assert data.is_draft({"remarque": "Brouillon non valide; source_file=x"})
    assert not data.is_draft(
        {"remarque": "proposition_humaine_non_validee; validation_humaine_A1_confirmee_etape_614"}
    )
    assert not data.is_draft({"remarque": "La preuve conclut que c'est trompeur."})
    assert data.is_draft({"statut": "brouillon"}) and not data.is_draft({"statut": "validé"})


def test_article_id():
    assert data.article_id({"evidence_id": "EVID-TUNIFACT-613-P253"}) == "tunifact-613"
    assert (
        data.article_id(
            {"evidence_id": "E263", "remarque": "x | https://tunifact.org/articles/907/titre"}
        )
        == "tunifact-907"
    )
    assert data.article_id(
        {"evidence_id": "E1", "remarque": "src https://nawaat.org/2023/03/08/a/ ok"}
    ).startswith("https://nawaat.org")
    assert data.article_id({"article_id": "Tunifact-9", "evidence_id": "x"}) == "tunifact-9"


def test_decoupage_sans_fuite_et_articles_du_lot_d_en_test(tmp_path):
    rows = [
        pair("P1", "tunifact-933", "c1", "e1"),
        pair("P2", "tunifact-933", "c2", "e2", "refutes"),
        pair("P3", "tunifact-100", "c3", "e3"),
        pair("P4", "tunifact-101", "c3", "e4", "neutral"),
        pair("P5", "tunifact-102", "c5", "e5"),
        pair("P6", "tunifact-103", "c6", "e6", "refutes"),
        pair("P7", "tunifact-104", "c7", "e7", remarque="Brouillon non valide"),
    ]
    rows += [pair(f"Q{i}", f"tunifact-{200 + i}", f"q{i}", f"f{i}", "neutral") for i in range(20)]
    src = tmp_path / "in.jsonl"
    src.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    m = data.prepare(src, "vt", out_dir=tmp_path, splits_dir=tmp_path)
    assert m["excluded_drafts"] == ["P7"]
    assert {"P1", "P2"} <= set(m["test"])
    # P3 et P4 partagent l'affirmation « c3 » : toujours dans la même partie
    assert sum({"P3", "P4"} <= set(m[s]) for s in ("train", "val", "test")) == 1
    assert sorted(m["train"] + m["val"] + m["test"]) == sorted(
        r["pair_id"] for r in rows if r["pair_id"] != "P7"
    )
    assert (tmp_path / "nli_vt_test.jsonl").exists() and (
        tmp_path / "nli_vt_by_article_seed42.json"
    ).exists()


def test_controle_de_fuite():
    a = dict(pair("P1", "tunifact-1", "même affirmation", "e1"), article_id="tunifact-1")
    b = dict(pair("P2", "tunifact-2", "même affirmation", "e2"), article_id="tunifact-2")
    with pytest.raises(ValueError, match="fuite"):
        data.check_no_leak({"train": [a], "val": [], "test": [b]})


def test_metriques():
    m = metrics(
        ["supports", "refutes", "neutral", "supports"],
        ["supports", "neutral", "neutral", "refutes"],
    )
    assert m["accuracy"] == 0.5
    assert m["confusion"]["supports"]["refutes"] == 1
    assert abs(m["macro_f1"] - (0.6667 + 0 + 0.6667) / 3) < 1e-3


def test_correspondance_des_labels_et_choix_de_l_epoque():
    from models.nli.train import best_epoch, label_ids

    ids = label_ids({"entailment": 0, "neutral": 1, "contradiction": 2})
    assert ids == {"supports": 0, "neutral": 1, "refutes": 2}
    hist = [
        {"epoch": 0, "val_macro_f1": 0.70},
        {"epoch": 1, "val_macro_f1": 0.75},
        {"epoch": 2, "val_macro_f1": 0.75},
    ]
    assert best_epoch(hist)["epoch"] == 1  # égalité : la plus ancienne
    assert (
        best_epoch([{"epoch": 0, "val_macro_f1": 0.8}, {"epoch": 1, "val_macro_f1": 0.6}])["epoch"]
        == 0
    )


def test_tete_neuve_noms_d_execution_et_classes_manquantes():
    from models.nli.train import ABLATION_MODEL, label_ids, needs_new_head, run_name

    assert needs_new_head({"LABEL_0": 0, "LABEL_1": 1, "LABEL_2": 2})
    assert not needs_new_head({"entailment": 0, "neutral": 1, "contradiction": 2})
    assert (
        run_name(stance.DEFAULT_MODEL, "v3", 2e-5, 6, 42) == "nli_mdeberta-ft_v3_lr2e-05_e6_seed42"
    )
    assert run_name(ABLATION_MODEL, "v3", 3e-5, 6, 123).startswith("nli_mdeberta-v3-base-ft_v3_")
    with pytest.raises(ValueError, match="absentes"):
        label_ids({"LABEL_0": 0, "LABEL_1": 1, "LABEL_2": 2})


def test_bootstrap_apparie():
    from models.nli.compare import paired_bootstrap

    gold = ["supports", "refutes", "neutral"] * 10
    same = paired_bootstrap(gold, gold, gold, n=200)
    assert same["diff"] == 0 and same["p_value"] == 1.0
    worse = ["neutral"] * 30
    better = paired_bootstrap(gold, worse, gold, n=200)
    assert better["diff"] > 0 and better["ci95"][0] > 0 and better["p_value"] == 0.0


def test_bronze_indices_lexicaux():
    from models.nli import bronze

    s = bronze.signals(
        "Le chômage a atteint 25 % en 2025.", "Le chômage a atteint 15 % en 2025, selon l'INS."
    )
    assert s.number_conflict is False and s.numbers_match is False  # 2025 commun, 25 absent
    s = bronze.signals("Le taux de chômage est de 25 %.", "Le taux de chômage est de 15 %.")
    assert s.number_conflict
    s = bronze.signals("الصورة مفبركة", "الصورة غير مفبركه")
    assert s.negation_mismatch
    # limite connue (non corrigée après la mesure du test) : « و » collé cache la négation
    assert not bronze.signals("الصورة مفبركة", "الصورة اصليه وغير مفبركه").negation_mismatch
    s = bronze.signals("Le ministère a confirmé la hausse.", "Le ministère a démenti cette rumeur.")
    assert s.refute_cue
    assert (
        bronze.predict("Le couscous est un plat.", "La bourse de Tunis a progressé.")[0]
        == "neutral"
    )


def test_bronze_par_le_contrat(monkeypatch):
    monkeypatch.setenv("NLI_BACKEND", "bronze")
    stance.set_classifier(None)
    claim = Claim(text="Le taux de chômage est de 25 %.", lang=Lang.FR)
    res = stance.predict_stances(
        claim,
        [ev("Le taux de chômage est de 15 %.", "a"), ev("Le taux de chômage est de 25 %.", "b")],
    )
    assert [r.stance for r in res] == [Stance.REFUTES, Stance.SUPPORTS]
    assert stance.backend_info()["backend"] == "bronze"
    stance.set_classifier(None)
