"""Tests Lot C — Model 2 (NLI) : contrat, préparation des données, évaluation."""

import json
import os

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


def test_gold_bias_sujets_lien_par_article(tmp_path):
    from models.nli.gold_bias import load_subjects, norm_article

    assert norm_article(" https://nawaat.org/2022/11/15/Article/ ") == (
        "https://nawaat.org/2022/11/15/article"
    )
    assert load_subjects(tmp_path / "absent.csv") == {}
    f = tmp_path / "sujets.csv"
    f.write_text(
        "\ufeffarticle_id,categorie_thematique\nhttps://nawaat.org/a/,Sport\ntunifact-938,Santé\n",
        encoding="utf-8",
    )
    assert load_subjects(f) == {"https://nawaat.org/a": "Sport", "tunifact-938": "Santé"}


# --- Palier Gold : tests sans modèle (abstention, biais, gabarits) ---


def _rows(*items):
    """(label, pred, confiance) → lignes au format de gold_abstention.predict."""
    return [
        {"pair_id": f"P{i}", "label": g, "pred": p, "confidence": c}
        for i, (g, p, c) in enumerate(items)
    ]


def test_gold_abstention_apply_ne_change_que_les_decisions_peu_sures():
    from models.nli.gold_abstention import apply

    rows = _rows(
        ("supports", "supports", 0.90),
        ("refutes", "refutes", 0.50),
        ("neutral", "neutral", 0.30),  # déjà neutre : jamais touché, même sous le seuil
        ("supports", "refutes", 0.70),
    )
    assert apply(rows, 0.0) == ["supports", "refutes", "neutral", "refutes"]
    assert apply(rows, 0.60) == ["supports", "neutral", "neutral", "refutes"]
    assert apply(rows, 0.70) == ["supports", "neutral", "neutral", "refutes"]  # < strict
    assert apply(rows, 0.95) == ["neutral"] * 4


def test_gold_abstention_sweep_couverture_et_changements(monkeypatch):
    from models.nli import gold_abstention as ga

    monkeypatch.setattr(ga, "GRID", [0.0, 0.6])
    rows = _rows(
        ("supports", "supports", 0.90),
        ("refutes", "refutes", 0.50),  # juste, mais passe à neutral à τ = 0.6
        ("neutral", "supports", 0.55),  # fausse, corrigée par le seuil
        ("neutral", "neutral", 0.80),
    )
    r0, r6 = ga.sweep(rows)
    assert (r0["tau"], r0["coverage"], r0["changed_to_neutral"]) == (0.0, 0.75, 0)
    assert r0["accuracy"] == 0.75 and r0["decisive_precision"] == round(2 / 3, 4)
    assert (r6["coverage"], r6["changed_to_neutral"], r6["changed_were_correct"]) == (0.25, 2, 1)
    assert r6["accuracy"] == 0.75 and r6["decisive_precision"] == 1.0


def test_gold_abstention_choose_plus_petit_tau_dans_la_marge():
    from models.nli.gold_abstention import choose

    res = [
        {"tau": 0.0, "macro_f1": 0.722},
        {"tau": 0.6, "macro_f1": 0.730},
        {"tau": 0.8, "macro_f1": 0.738},
    ]
    c = choose(res, 0.03)
    assert c["best_tau"] == [0.8] and c["chosen_tau"] == 0.0 and c["no_abstention_in_margin"]
    c = choose(res, 0.01)
    assert c["equivalent_tau"] == [0.6, 0.8] and c["chosen_tau"] == 0.6
    assert not c["no_abstention_in_margin"]
    # marge exacte (0.738 − 0.03 = 0.708) : incluse malgré les arrondis flottants
    assert (
        choose([{"tau": 0.0, "macro_f1": 0.708}, {"tau": 0.5, "macro_f1": 0.738}], 0.03)[
            "chosen_tau"
        ]
        == 0.0
    )


def test_gold_bias_site():
    from models.nli.gold_bias import site

    assert site("tunifact-938") == "tunifact.org"
    assert site("https://www.nawaat.org/2022/11/15/article") == "nawaat.org"
    assert site("https://nawaat.org/x") == "nawaat.org"
    assert site("inconnu:E12") == "inconnu:E12"  # pas d'URL : identifiant gardé tel quel


def test_gold_bias_gap_signe_ic_et_regle_des_10_paires():
    from models.nli.gold_bias import gap

    labs = ["supports", "refutes", "neutral"] * 4  # 12 paires
    parfait = (labs, list(labs))
    nul = (labs, ["supports"] * 12)
    g = gap(parfait, nul)
    assert g["accuracy"] > 0 and g["accuracy_ci95"][0] > 0 and g["interpretable"]
    assert g["macro_f1"] > 0 and g["macro_f1_ci95"][0] > 0
    assert gap(parfait, parfait)["accuracy"] == 0 and gap(parfait, parfait)["accuracy_ci95"] == [
        0,
        0,
    ]
    petit = (labs[:9], labs[:9])  # 9 paires < 10 : écart non interprétable
    assert not gap(parfait, petit)["interpretable"]
    assert gap(nul, parfait)["accuracy"] == -g["accuracy"]


def test_gold_templates_refuse_d_ecraser(tmp_path, monkeypatch):
    from models.nli import gold_templates as gt

    test_file = tmp_path / "test.jsonl"
    rows = [
        {
            "pair_id": f"P{i}",
            "article_id": "tunifact-1",
            "claim_lang": "fr",
            "evidence_lang": "fr",
            "label": "supports",
            "claim": f"affirmation {i}",
            "evidence": f"preuve {i}",
        }
        for i in range(56)
    ]
    test_file.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    gold = tmp_path / "gold"
    gold.mkdir()
    deja = gold / "paraphrases_v1.csv"
    deja.write_text("travail commencé, à ne pas perdre", encoding="utf-8")
    monkeypatch.setattr(gt, "TEST_FILE", test_file)
    monkeypatch.setattr(gt, "GOLD_DIR", gold)

    gt.main()
    assert deja.read_text(encoding="utf-8") == "travail commencé, à ne pas perdre"
    cree = (gold / "reecritures_tn_v1.csv").read_text(encoding="utf-8-sig").splitlines()
    assert len(cree) == 57 and cree[0].startswith("pair_id,article_id")
    avant = (gold / "reecritures_tn_v1.csv").read_bytes()
    gt.main()  # seconde exécution : rien n'est réécrit
    assert (gold / "reecritures_tn_v1.csv").read_bytes() == avant

    test_file.write_text("\n".join(json.dumps(r) for r in rows[:55]), encoding="utf-8")
    with pytest.raises(SystemExit, match="55 paires"):
        gt.main()


# --- Palier Gold : polarité (EXP-C-016) et mesure unique préparée (EXP-C-012 / 013) ---


def test_gold_polarity_types_d_erreur_et_wilson():
    from models.nli.gold_polarity import error_type, polarity, wilson

    assert error_type("supports", "supports") is None
    assert error_type("supports", "refutes") == error_type("refutes", "supports") == "inversion"
    assert error_type("refutes", "neutral") == "vers neutral"
    assert error_type("neutral", "supports") == "depuis neutral"
    gold = ["supports", "refutes", "refutes", "neutral", "supports"]
    pred = ["refutes", "supports", "neutral", "neutral", "supports"]
    r = polarity(gold, pred, ["a", "b", "c", "d", "e"])
    assert r["errors"] == 3 and r["by_type"]["inversion"] == 2
    assert r["inversions_by_direction"] == {"supports->refutes": 1, "refutes->supports": 1}
    assert r["inversion_share"] == round(2 / 3, 4) and r["descriptive_only"]
    assert r["confusion"]["refutes"]["neutral"] == 1
    lo, hi = wilson(1, 10)
    assert 0 < lo < 0.1 < hi < 0.5 and wilson(0, 0) is None


GM_LABELS = ["supports", "refutes", "neutral"]
GM_FIELDS = [
    "pair_id",
    "label",
    "evidence",
    "claim_paraphrase_1",
    "claim_paraphrase_2",
    "verificateur",
    "verif_sens_identique",
    "verif_label_tient",
    "statut",
]


@pytest.fixture
def gold_measure_env(tmp_path, monkeypatch):
    """Faux test v3 (56 paires inventées), fausses prédictions d'origine, faux fichier figé."""
    import copy
    import csv

    from models.nli import gold_measure as gm

    test = [
        {
            "pair_id": f"P{i:02d}",
            "label": GM_LABELS[i % 3],
            "claim": f"affirmation {i}",
            "evidence": f"preuve {i}",
            "claim_lang": "fr" if i % 2 else "ar",
            "evidence_lang": "fr" if i % 4 < 2 else "ar",
        }
        for i in range(56)
    ]
    (tmp_path / "test.jsonl").write_text("\n".join(json.dumps(p) for p in test), encoding="utf-8")
    preds = tmp_path / "silver"
    preds.mkdir()
    for _, fname in gm.MODELS.values():  # prédictions d'origine : toutes justes
        rows = [{"pair_id": p["pair_id"], "label": p["label"], "pred": p["label"]} for p in test]
        (preds / fname).write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    gold = tmp_path / "gold"
    gold.mkdir()
    exps = copy.deepcopy(gm.EXPERIMENTS)
    monkeypatch.setattr(gm, "TEST_FILE", tmp_path / "test.jsonl")
    monkeypatch.setattr(gm, "PRED_DIR", preds)
    monkeypatch.setattr(gm, "GOLD_DIR", gold)
    monkeypatch.setattr(gm, "RESULTS", tmp_path / "results")
    monkeypatch.setattr(gm, "EXPERIMENTS", exps)

    def write(verificateur="", verif="", sha=True):
        path = gold / exps["paraphrases"]["file"]
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=GM_FIELDS)
            w.writeheader()
            for k, p in enumerate(test):
                w.writerow(
                    {
                        "pair_id": p["pair_id"],
                        "label": p["label"],
                        "evidence": p["evidence"],
                        "claim_paraphrase_1": f"reformulation {k}",
                        "claim_paraphrase_2": "",
                        "verificateur": verificateur,
                        "verif_sens_identique": "non" if k == 0 else verif,
                        "verif_label_tient": verif,
                        "statut": "",
                    }
                )
        exps["paraphrases"]["sha256"] = gm.sha256(path) if sha else None
        return path

    def fake(pairs):
        """Faux prédicteur, sans modèle : une paire sur 4 bascule vers neutral."""
        assert all(p["claim"].startswith("reformulation") for p in pairs)
        return ["neutral" if k % 4 == 0 else p["label"] for k, p in enumerate(pairs)]

    return gm, write, dict.fromkeys(gm.MODELS, fake), gold


def test_gold_measure_refuse_sans_fichier_fige_ou_sans_sha(gold_measure_env):
    gm, write, fakes, gold = gold_measure_env
    with pytest.raises(SystemExit):
        gm.main(["--exp", "paraphrases"], predictors=fakes)  # fichier pas encore figé
    write(verificateur="X", verif="oui", sha=False)
    assert any("non noté" in e for e in gm.checks("paraphrases", False))
    path = write(verificateur="X", verif="oui")
    path.write_text(path.read_text(encoding="utf-8-sig") + "\n", encoding="utf-8-sig")
    assert any("SHA-256 différent" in e for e in gm.checks("paraphrases", False))
    with pytest.raises(SystemExit):
        gm.main(["--exp", "paraphrases"], predictors=fakes)
    assert not list(gold.glob("MESURE_FAITE_*"))


def test_gold_measure_refuse_un_label_ou_une_preuve_modifies(gold_measure_env):
    gm, write, fakes, gold = gold_measure_env
    path = write(verificateur="X", verif="oui")
    text = path.read_text(encoding="utf-8-sig").replace("preuve 3,", "preuve changée,")
    path.write_text(text, encoding="utf-8-sig")
    gm.EXPERIMENTS["paraphrases"]["sha256"] = gm.sha256(path)
    assert any("preuve ou label" in e for e in gm.checks("paraphrases", False))


def test_gold_measure_verificateur_vide_refuse_sauf_exploratoire(gold_measure_env):
    gm, write, fakes, gold = gold_measure_env
    write()  # aucune ligne vérifiée
    with pytest.raises(SystemExit):
        gm.main(["--exp", "paraphrases"], predictors=fakes)
    assert not gm.marker("paraphrases").exists()
    gm.main(["--exp", "paraphrases", "--dry-run", "--exploratoire"], predictors=fakes)
    assert not gm.marker("paraphrases").exists()  # --dry-run : rien n'est consommé

    gm.main(["--exp", "paraphrases", "--exploratoire"], predictors=fakes)
    assert json.loads(gm.marker("paraphrases").read_text(encoding="utf-8"))["exploratoire"]
    out = next(gm.RESULTS.glob("lot-c_nli-gold_paraphrases_test_*.json"))
    res = json.loads(out.read_text(encoding="utf-8"))["results"]
    r = res["paraphrase_1"]
    assert r["exploratoire"] and r["n_kept"] == 56 and r["non_verifiees"] == 56
    assert res["paraphrase_2"]["measured"] is False and res["paraphrase_2"]["vides"] == 56
    m = r["models"]["principal_seed42"]
    # 14 paires basculent vers neutral, dont 4 déjà neutral : 10 changements sur 56
    assert m["original"]["accuracy"] == 1.0 and m["change_rate"] == round(10 / 56, 4)
    assert m["variant"]["accuracy"] == round(46 / 56, 4) and m["paired_diff_macro_f1"] < 0
    assert set(m["by_claim_lang"]) == {"fr", "ar"}
    assert (gold / "predictions_paraphrases_paraphrase_1_bronze.jsonl").exists()
    # seconde exécution refusée, même avec --exploratoire
    with pytest.raises(SystemExit):
        gm.main(["--exp", "paraphrases", "--exploratoire"], predictors=fakes)


def test_gold_measure_verifiees_ecartees_et_regle_des_40_paires(gold_measure_env):
    gm, write, fakes, gold = gold_measure_env
    write(verificateur="Relecteur", verif="oui")  # P00 a « non » : écartée
    gm.main(["--exp", "paraphrases"], predictors=fakes)
    out = next(gm.RESULTS.glob("*.json"))
    res = json.loads(out.read_text(encoding="utf-8"))["results"]["paraphrase_1"]
    assert (res["n_kept"], res["ecartees"], res["non_verifiees"]) == (55, 1, 0)
    assert not res["exploratoire"]  # 55 paires ≥ 40, toutes vérifiées

    rows = gm.read_frozen("paraphrases")
    for r in rows[:20]:
        r["statut"] = "ecarte"
    keep, counts = gm.kept(rows, "claim_paraphrase_1")
    # P00 (déjà écartée par son « non ») fait partie des 20 : 36 gardées, 20 écartées
    assert len(keep) == 36 and counts["ecartees"] == 20  # < 40 : serait exploratoire


# --- gold_measure : changement de moteur entre variantes (revue d'Achref, PR #34) ---

FAKE_PROBS = {  # faux moteurs : zero-shot → supports, affiné → refutes, Bronze → neutral
    "zero-shot": {"entailment": 0.9, "neutral": 0.05, "contradiction": 0.05},
    "fine-tuned": {"entailment": 0.05, "neutral": 0.05, "contradiction": 0.9},
    "bronze": {"supports": 0.05, "refutes": 0.05, "neutral": 0.9},
}
EXPECTED_ENGINE_LABEL = {
    "zero-shot-fp32": ("zero-shot", "supports"),
    "principal_seed42": ("fine-tuned", "refutes"),
    "bronze": ("bronze", "neutral"),
}


@pytest.fixture
def fake_nli_engines(monkeypatch):
    """Trois faux moteurs branchés dans `stance` (aucun modèle chargé, aucune donnée du corpus).

    Renvoie le journal des appels (moteur, affirmation), le journal des chargements de modèle
    (zero-shot / affiné) et le nombre de changements de moteur (`set_classifier(None)`).
    """
    calls, loads, switches = [], [], []

    def classifier(engine):
        def classify(pairs):
            calls.extend((engine, hypothesis) for _premise, hypothesis in pairs)
            return [dict(FAKE_PROBS[engine]) for _ in pairs]

        return classify

    def fake_load(name):
        engine = "zero-shot" if name == stance.DEFAULT_MODEL else "fine-tuned"
        loads.append(engine)
        return classifier(engine)

    real_set = stance.set_classifier

    def spy_set(clf, name="test"):
        if clf is None:
            switches.append(os.environ.get("NLI_BACKEND"))
        return real_set(clf, name)

    monkeypatch.setattr(stance, "_load_zero_shot", fake_load)
    monkeypatch.setattr(stance, "_bronze_classifier", classifier("bronze"))
    monkeypatch.setattr(stance, "set_classifier", spy_set)
    monkeypatch.setenv("NLI_BACKEND", "stub")  # valeur restaurée après le test
    monkeypatch.delenv("NLI_MODEL", raising=False)
    monkeypatch.setenv("NLI_FINETUNED_MODEL", "faux-checkpoint-affine")
    real_set(None)
    yield calls, loads, switches
    real_set(None)


def _switch_pairs(prefix, n=4):
    return [
        {
            "pair_id": f"Q{i}",
            "claim": f"{prefix} {i}",
            "evidence": f"preuve {i}",
            "claim_lang": "fr",
        }
        for i in range(n)
    ]


def test_gold_measure_changement_de_moteur_dans_n_importe_quel_ordre(fake_nli_engines):
    """Cas de la revue : Bronze appelé en dernier sur la variante 1, puis zero-shot sur la 2."""
    from models.nli import gold_measure as gm

    calls, _loads, switches = fake_nli_engines
    preds = gm.backend_predictors({n: b for n, (b, _) in gm.MODELS.items()})
    # ordre « variante d'abord », celui qui bloquait : zs, affiné, Bronze, puis zs, affiné, Bronze
    for prefix in ("variante1", "variante2"):
        pairs = _switch_pairs(prefix)
        for name in ("zero-shot-fp32", "principal_seed42", "bronze"):
            engine, label = EXPECTED_ENGINE_LABEL[name]
            start = len(calls)
            assert preds[name](pairs) == [label] * len(pairs), (prefix, name)
            assert {e for e, _ in calls[start:]} == {engine}  # le bon moteur a répondu
            assert stance.backend_info()["backend"] == engine
    assert len(switches) == 6  # un changement de moteur à chaque appel dans cet ordre


def test_gold_measure_deux_variantes_trois_moteurs(fake_nli_engines, gold_measure_env):
    """measure() avec deux variantes successives : chaque passage utilise le bon moteur."""
    from models.nli.data import load_pairs

    gm, write, _fakes, _gold = gold_measure_env
    calls, loads, switches = fake_nli_engines
    write(verificateur="Relecteur", verif="oui")  # P00 écartée (« non »), 55 gardées
    rows = gm.read_frozen("paraphrases")
    for r in rows:
        r["claim_paraphrase_2"] = "autre " + r["claim_paraphrase_1"]  # seconde variante remplie
    test = {p["pair_id"]: p for p in load_pairs(gm.TEST_FILE)}
    original = {name: {i: p["label"] for i, p in test.items()} for name in gm.MODELS}

    predictors = gm.backend_predictors({n: b for n, (b, _) in gm.MODELS.items()})
    results, preds = gm.measure("paraphrases", rows, test, original, predictors, False)

    for variant in ("paraphrase_1", "paraphrase_2"):
        assert results[variant]["measured"] and results[variant]["n_kept"] == 55
        for name, (_engine, label) in EXPECTED_ENGINE_LABEL.items():
            assert set(preds[variant][name].values()) == {label}, (variant, name)
    # chaque moteur a vu les deux variantes, et seulement des affirmations réécrites
    for engine in ("zero-shot", "fine-tuned", "bronze"):
        seen = {h.split(" ")[0] for e, h in calls if e == engine}
        assert seen == {"reformulation", "autre"}, (engine, seen)
        assert sum(e == engine for e, _ in calls) == 2 * 55
    # moteur par moteur : chaque moteur n'est chargé qu'une fois
    assert switches == ["zero-shot", "fine-tuned", "bronze"]
    assert loads == ["zero-shot", "fine-tuned"]
    assert results["agreement_paraphrases_1_2"]["bronze"]["agreement"] == 1.0
