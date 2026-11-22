"""Tests des scripts du palier Gold du Lot A2 (docs/lot-a2_protocole_gold.md).

Uniquement des textes FACTICES écrits ici : aucun texte du corpus, aucune lecture de data/.
"""

from __future__ import annotations

import json
import random

import pytest

from normalization import baseline_fasttext as ft
from normalization import gold_agreement as ga
from normalization import gold_final as fin
from normalization import gold_kaggle_inputs as ki
from normalization import gold_leakage as lk
from normalization import gold_predict_local as pl
from normalization import gold_presse as pr
from normalization import gold_robustness as inv
from normalization.evaluate import REPO
from normalization.gold_common import (
    RefusGold,
    check_file,
    check_out_dir,
    decision_inv,
    paired_bootstrap,
    safe_main,
    sha256_texts,
    wilson,
)

LATIN = "Bonjour tout le monde"
ARABE = "لا أعرف هذا الكتاب"
SANS_LA = "ذهب الولد إلى المدرسة"


def rng() -> random.Random:
    return random.Random(1)


def factices() -> list[dict]:
    """Petit jeu factice au format de load_examples."""
    return [{"id": "l1", "lang": "fr", "text": "Il fait beau aujourd'hui"},
            {"id": "l2", "lang": "tn", "text": "3lech ya5i barcha"},
            {"id": "l3", "lang": "ar", "text": ARABE},
            {"id": "l4", "lang": "ar", "text": SANS_LA}]


# ---------------------------------------------------------------------------
# Perturbations P1 à P10
# ---------------------------------------------------------------------------

def test_p1_minuscules():
    assert inv.p1_lower(LATIN, rng()) == "bonjour tout le monde"


def test_p2_majuscules():
    assert inv.p2_upper(LATIN, rng()) == "BONJOUR TOUT LE MONDE"


def test_p3_une_lettre_triplee():
    out = inv.p3_elongation(LATIN, rng())
    assert len(out) == len(LATIN) + 2
    assert any(c * 3 in out for c in set(LATIN) if c.isalpha())


def test_p3_sans_lettre_inchange():
    assert inv.p3_elongation("123 !!", rng()) == "123 !!"


def test_p4_tatweel_dans_un_mot():
    out = inv.p4_tatweel(SANS_LA, rng())
    assert out.count(inv.TATWEEL) == 1
    assert out.replace(inv.TATWEEL, "") == SANS_LA
    i = out.index(inv.TATWEEL)
    assert out[i - 1] not in inv.NON_JOINING and inv.ARABIC_LETTER.match(out[i + 1])


def test_p4_texte_latin_inchange():
    assert inv.p4_tatweel(LATIN, rng()) == LATIN


def test_p5_diacritiques_ajoutes():
    out = inv.p5_diacritics(ARABE, rng())
    added = [c for c in out if c in inv.HARAKAT]
    assert added
    assert "".join(c for c in out if c not in inv.HARAKAT) == ARABE


def test_p6_ligature_lam_alef():
    out = inv.p6_presentation(ARABE, rng())
    assert inv.LAM_ALEF in out and "لا" not in out


def test_p6_sans_la_inchange():
    assert inv.p6_presentation(SANS_LA, rng()) == SANS_LA


def test_p7_emoji_en_fin():
    out = inv.p7_emoji(LATIN, rng())
    assert out.startswith(LATIN + " ") and out[len(LATIN) + 1:] in inv.EMOJIS


def test_p8_url_en_fin():
    assert inv.p8_url(LATIN, rng()) == f"{LATIN} {inv.URL}"


def test_p9_ponctuation_en_fin():
    assert inv.p9_punctuation(LATIN, rng()) == LATIN + "!!!"


def test_p10_espaces():
    out = inv.p10_spaces(LATIN, rng())
    assert " " not in out.replace("  ", "").replace(" ", "")
    assert out.replace(" ", " ").replace("  ", " ") == LATIN


def test_p10_sans_espace_inchange():
    assert inv.p10_spaces("Bonjour", rng()) == "Bonjour"


def test_perturbation_deterministe():
    first = inv.perturb("P5", ARABE, "l7")
    assert first == inv.perturb("P5", ARABE, "l7")


def test_portee_des_perturbations():
    latin_only = {c for c, (_, s) in inv.PERTURBATIONS.items() if s == {"latin"}}
    arabic_only = {c for c, (_, s) in inv.PERTURBATIONS.items() if s == {"arabe"}}
    assert latin_only == {"P1", "P2"} and arabic_only == {"P4", "P5", "P6"}
    assert len(inv.PERTURBATIONS) == 10


# ---------------------------------------------------------------------------
# Wilson et règle de décision du §5
# ---------------------------------------------------------------------------

def test_wilson_0_sur_100():
    assert wilson(0, 100)[1] == pytest.approx(0.037, abs=0.001)


def test_wilson_0_sur_86():
    assert wilson(0, 86)[1] == pytest.approx(0.043, abs=0.001)


def test_wilson_0_sur_5_non_robuste():
    assert wilson(0, 5)[1] > 0.05
    assert decision_inv(0, 5) == "indéterminé"


def test_decision_robuste():
    assert decision_inv(0, 100) == "robuste"


def test_decision_fragile():
    assert decision_inv(20, 100) == "fragile"


def test_decision_indeterminee_entre_les_seuils():
    assert decision_inv(3, 100) == "indéterminé"


def test_decision_indeterminee_sous_30_textes():
    assert decision_inv(0, 29) == "indéterminé"


# ---------------------------------------------------------------------------
# Bootstrap apparié
# ---------------------------------------------------------------------------

def test_bootstrap_apparie_ecart_nul():
    golds = ["tn", "ar", "fr", "tn"]
    result = paired_bootstrap(golds, golds, golds, draws=50)
    assert result["exactitude"]["ecart"] == 0
    assert result["macro_f1"]["ic_bas"] == result["macro_f1"]["ic_haut"] == 0


def test_bootstrap_apparie_deterministe():
    golds, before, after = ["tn", "ar"] * 5, ["tn", "tn"] * 5, ["tn", "ar"] * 5
    assert paired_bootstrap(golds, before, after, draws=50) == \
        paired_bootstrap(golds, before, after, draws=50)


# ---------------------------------------------------------------------------
# Empreintes et dossier de sortie
# ---------------------------------------------------------------------------

def test_refus_empreinte(tmp_path):
    path = tmp_path / "dev.tsv"
    path.write_text("t\ttexte factice\n", encoding="utf-8")
    with pytest.raises(RefusGold, match="empreinte différente"):
        check_file("dev factice", path, "0" * 64)


def test_refus_fichier_absent(tmp_path):
    with pytest.raises(RefusGold, match="absent"):
        check_file("dev factice", tmp_path / "absent.tsv", "0" * 64)


def test_empreinte_liste_ordonnee():
    assert sha256_texts(["a", "b"]) != sha256_texts(["b", "a"])


def test_empreintes_dev_dans_experiments():
    journal = (REPO / "experiments.md").read_text(encoding="utf-8")
    for _, digest in inv.DEV_SETS.values():
        assert digest in journal


def test_refus_out_dir_dans_depot():
    target = REPO / "data" / "interim" / "gold_test_jamais_cree"
    with pytest.raises(RefusGold, match="dans le dépôt"):
        check_out_dir(target)
    assert not target.exists()


def test_out_dir_hors_depot_cree(tmp_path):
    assert check_out_dir(tmp_path / "sortie").is_dir()


def test_run_refuse_out_dir_avant_toute_lecture():
    with pytest.raises(RefusGold, match="dans le dépôt"):
        inv.run(["--out-dir", str(REPO / "gold_sortie"), "--dev-arabe", "absent.tsv"])


# ---------------------------------------------------------------------------
# Erreurs sans texte
# ---------------------------------------------------------------------------

def test_erreur_par_texte_sans_texte():
    def boom(texts):
        raise ValueError(texts[0])  # message qui contient le texte
    errors: list[dict] = []
    result = inv.measure_perturbation(factices(), "latin", "P9", {"boom": boom}, errors, draws=10)
    assert errors and set(errors[0]) == {"jeu", "ligne", "type"}
    assert errors[0]["type"] == "ValueError"
    dumped = json.dumps([result, errors], ensure_ascii=False)
    assert all(ex["text"] not in dumped for ex in factices())


def test_safe_main_masque_le_message(capsys):
    def run():
        raise ValueError("texte secret du corpus")
    with pytest.raises(SystemExit) as stop:
        safe_main(run)
    out = capsys.readouterr()
    assert stop.value.code == 1
    assert "secret" not in out.out + out.err and "ValueError" in out.out


def test_safe_main_affiche_un_refus(capsys):
    def run():
        raise RefusGold("empreinte différente pour dev")
    with pytest.raises(SystemExit) as stop:
        safe_main(run)
    assert stop.value.code == 2 and "REFUS" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Mesure sur un jeu factice
# ---------------------------------------------------------------------------

def test_invariants_sur_factices():
    result = inv.measure_invariants(factices(), "factice", [])
    assert result["idempotence_echecs"]["n"] == 4
    assert result["idempotence_echecs"]["k"] == 0


def test_mesure_jeu_factice():
    result = inv.measure_dataset(factices(), "arabe", inv.PREDICTORS, draws=10)
    assert set(result["perturbations"]) == {"P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"}
    p8 = result["perturbations"]["P8"]
    assert p8["applicables"] == 4
    assert set(p8["systemes"]) == {"regles", "alphabet"}
    assert p8["systemes"]["regles"]["decision"] == "indéterminé"  # n < 30


def test_systeme_inconnu_refuse():
    with pytest.raises(RefusGold, match="inconnu"):
        inv.build_predictors("regles,inexistant", inv.parse_args(["--out-dir", "x"]))


# ---------------------------------------------------------------------------
# Baseline fastText lid.176 (faux modèle : aucun téléchargement)
# ---------------------------------------------------------------------------

class _FakeF:
    """Imite la fonction C++ `model.f.predict` de fasttext, sur des textes factices."""

    def __init__(self, answers: dict[str, str]):
        self.answers = answers
        self.seen: list[str] = []

    def predict(self, text, k, threshold, on_error):
        self.seen.append(text)
        return [(0.9, "__label__" + self.answers.get(text, "es"))]


class FakeModel:
    def __init__(self, answers: dict[str, str]):
        self.f = _FakeF(answers)


def test_fasttext_correspondance_des_etiquettes():
    assert [ft.map_label(x) for x in ("ar", "arz", "fr", "es", "en")] == \
        ["ar", "ar", "fr", "autre", "autre"]


def test_fasttext_retire_les_retours_a_la_ligne():
    model = FakeModel({"ligne un ligne deux": "fr"})
    assert ft.top_label(model, "ligne un\nligne deux") == "fr"
    assert "\n" not in model.f.seen[0]


def test_fasttext_predicteur_mappe():
    model = FakeModel({"Il fait beau": "fr", ARABE: "arz"})
    assert ft.make_predictor(model)(["Il fait beau", ARABE, "3lech"]) == ["fr", "ar", "autre"]


def test_fasttext_part_des_t_etiquetes_arz():
    examples = [{"id": "l1", "lang": "tn", "text": "a"}, {"id": "l2", "lang": "tn", "text": "b"},
                {"id": "l3", "lang": "ar", "text": "c"}]
    model = FakeModel({"a": "arz", "b": "ar", "c": "arz"})
    result = ft.compare(examples, "arabe", model, lambda texts: ["tn"], draws=10)
    assert result["t_etiquetes_arz"]["k"] == 1 and result["t_etiquetes_arz"]["n"] == 2
    assert result["fasttext"]["par_classe"]["tn"]["recall"] == 0.0
    assert "regles_moins_fasttext" in result


def test_fasttext_refuse_un_modele_d_empreinte_differente(tmp_path):
    fake = tmp_path / "lid.176.bin"
    fake.write_bytes(b"pas un modele")
    with pytest.raises(RefusGold, match="empreinte différente"):
        ft.load_model(fake)


def test_fasttext_branche_dans_inv(monkeypatch):
    model = FakeModel({})
    monkeypatch.setattr(ft, "load_predictor", lambda path: ft.make_predictor(model))
    chosen = inv.build_predictors("regles,fasttext", inv.parse_args(["--out-dir", "x"]))
    assert set(chosen) == {"regles", "fasttext"}
    assert chosen["fasttext"](["texte factice"]) == ["autre"]


def _fuites_factices() -> dict[str, list[str]]:
    return {
        "test": ["Il fait beau", "texte du test seul", "Bonjour  tout le monde", "3lech ya5i"],
        "entrainement": ["Il fait beau", "autre texte"],
        "dev_arabe": ["Il fait beau", SANS_LA],
        "dev_latin": ["Bonjour tout le monde"],
        "eval_30": ["3lech ya5i"],
    }


def test_fuites_empreinte_normalisee_rattrape_les_espaces():
    first = lk.fingerprints(["Bonjour  tout"], "a", [])
    second = lk.fingerprints(["Bonjour tout"], "b", [])
    assert first[0][1] != second[0][1] and first[0][2] == second[0][2]


def test_fuites_doublons_internes():
    prints = lk.fingerprints(["a", "a", "b", " b "], "factice", [])
    assert lk.internal_duplicates(prints) == {"n": 4, "doublons_bruts": 2,
                                              "doublons_normalises": 2}


def test_fuites_retrait_compte_une_seule_fois():
    results, lines = lk.audit(_fuites_factices())
    # « Il fait beau » est dans l'entraînement ET le dev arabe ; « Bonjour  tout » ne recoupe
    # le dev latin qu'après normalisation : 2 textes à retirer, pas 3.
    assert results["decision"]["textes_du_test_a_retirer"] == 2
    assert lines["test_a_retirer"] == [1, 3]


def test_fuites_eval_30_ne_declenche_pas_de_retrait():
    sets = {"test": ["3lech ya5i"], "entrainement": ["x"], "dev_arabe": ["y"],
            "dev_latin": ["z"], "eval_30": ["3lech ya5i"]}
    results, _ = lk.audit(sets)
    assert results["intersections"]["test|eval_30"]["brut"]["empreintes_communes"] == 1
    assert results["decision"]["retrait_necessaire"] is False


def test_fuites_sorties_sans_texte():
    sets = _fuites_factices()
    results, lines = lk.audit(sets)
    dumped = json.dumps([results, lines], ensure_ascii=False)
    assert all(text not in dumped for texts in sets.values() for text in texts)


def test_fuites_liste_ordonnee_verifiee(tmp_path):
    path = tmp_path / "test.tsv"
    path.write_text("?\tpremier texte\n?\tsecond texte\n", encoding="utf-8")
    good = sha256_texts(["premier texte", "second texte"])
    texts, digest = lk.load_set("test", path, "annotation", "liste", good)
    assert texts == ["premier texte", "second texte"] and digest == good
    with pytest.raises(RefusGold, match="empreinte différente"):
        lk.load_set("test", path, "annotation", "liste", "0" * 64)


def test_fuites_empreintes_dans_les_journaux():
    journal = (REPO / "experiments.md").read_text(encoding="utf-8")
    assert lk.SETS["eval_30"][3] in journal
    for name in ("test", "entrainement"):
        assert len(lk.SETS[name][3]) == 64


def test_fuites_refuse_out_dir_dans_depot():
    with pytest.raises(RefusGold, match="dans le dépôt"):
        lk.run(["--out-dir", str(REPO / "gold_sortie")])


# ---------------------------------------------------------------------------
# Accord entre annotateurs (EXP-A2-019)
# ---------------------------------------------------------------------------

def _rows(labels: str) -> list[tuple[str, str]]:
    return [(label, f"texte factice {i}") for i, label in enumerate(labels, 1)]


def test_accord_refuse_un_mauvais_nombre_de_lignes():
    with pytest.raises(RefusGold, match="lignes au lieu de"):
        ga.check_rows("factice", _rows("tta"), 4)


def test_accord_refuse_une_etiquette_invalide():
    with pytest.raises(RefusGold, match="étiquettes invalides"):
        ga.check_rows("factice", _rows("tzt"), 3)


def test_accord_refuse_des_textes_differents():
    other = [("t", "texte factice 1"), ("a", "autre texte")]
    with pytest.raises(RefusGold, match="textes différents"):
        ga.check_same_texts(_rows("ta"), other)


def test_accord_non_mesure_si_annotation_incomplete():
    result, lines = ga.agreement(_rows("tat"), _rows("t?t"), draws=10)
    assert result["statut"].startswith("accord humain non mesuré")
    assert "kappa" not in result and lines == []


def test_accord_kappa_et_desaccords():
    result, lines = ga.agreement(_rows("ttaaft"), _rows("ttaatt"), draws=50)
    assert result["statut"] == "mesuré" and result["desaccords"] == 1 and lines == [5]
    assert result["matrice"]["f->t"] == 1
    assert result["kappa_ic_bas"] <= result["kappa"] <= result["kappa_ic_haut"]
    assert "texte factice" not in json.dumps([result, lines], ensure_ascii=False)


def test_accord_parfait():
    result, _ = ga.agreement(_rows("tat"), _rows("tat"), draws=10)
    assert result["kappa"] == 1.0


def _write_annotations(path, rows):
    path.write_text("".join(f"{label}\t{text}\n" for label, text in rows), encoding="utf-8")


def test_reference_controlee(tmp_path, monkeypatch):
    rows = _rows("t" * 299 + "a")
    monkeypatch.setattr(ga, "TEST_LIST_SHA", sha256_texts([t for _, t in rows]))
    path = tmp_path / "reference.tsv"
    _write_annotations(path, rows)
    assert ga.check_reference(path)["etiquettes"] == {"t": 299, "a": 1}


def test_reference_refusee_si_incomplete(tmp_path, monkeypatch):
    rows = _rows("t" * 299 + "?")
    monkeypatch.setattr(ga, "TEST_LIST_SHA", sha256_texts([t for _, t in rows]))
    path = tmp_path / "reference.tsv"
    _write_annotations(path, rows)
    with pytest.raises(RefusGold, match="incomplète"):
        ga.check_reference(path)


def test_accord_refuse_out_dir_dans_depot():
    with pytest.raises(RefusGold, match="dans le dépôt"):
        ga.run(["accord", "--jeu", "test", "--out-dir", str(REPO / "gold_sortie")])


# ---------------------------------------------------------------------------
# Mesure finale (EXP-A2-020), sans aucune donnée réelle
# ---------------------------------------------------------------------------

def _predictions(path, labels):
    path.write_text("".join(f"{i}\t{label}\n" for i, label in enumerate(labels, 1)),
                    encoding="utf-8")
    return {"chemin": str(path), "sha256": fin.sha256_file(path)}


def test_final_predictions_lues(tmp_path):
    entry = _predictions(tmp_path / "p.tsv", ["tn", "ar", "tn"])
    assert fin.load_predictions("p", entry, 3, {"tn", "ar"}) == ["tn", "ar", "tn"]


def test_final_refuse_une_prediction_manquante(tmp_path):
    entry = _predictions(tmp_path / "p.tsv", ["tn", "ar"])
    with pytest.raises(RefusGold, match="numéros"):
        fin.load_predictions("p", entry, 3, {"tn", "ar"})


def test_final_refuse_une_etiquette_non_autorisee(tmp_path):
    entry = _predictions(tmp_path / "p.tsv", ["tn", "fr", "ar"])
    with pytest.raises(RefusGold, match="non autorisées"):
        fin.load_predictions("p", entry, 3, {"tn", "ar"})


def test_final_refuse_une_empreinte_de_predictions(tmp_path):
    entry = _predictions(tmp_path / "p.tsv", ["tn"])
    entry["sha256"] = "0" * 64
    with pytest.raises(RefusGold, match="empreinte différente"):
        fin.load_predictions("p", entry, 1, {"tn", "ar"})


def test_final_refuse_une_reference_d_empreinte_differente(tmp_path):
    path = tmp_path / "ref.tsv"
    _write_annotations(path, _rows("ta"))
    with pytest.raises(RefusGold, match="empreinte différente"):
        fin.load_reference(path, "0" * 64, n=2)


def test_final_refuse_une_reference_avec_point_d_interrogation(tmp_path):
    rows = _rows("t?")
    path = tmp_path / "ref.tsv"
    _write_annotations(path, rows)
    with pytest.raises(RefusGold, match="invalides ou"):
        fin.load_reference(path, fin.sha256_file(path), sha256_texts([t for _, t in rows]), n=2)


def test_final_f_et_x_exclus():
    kept, golds = fin.reference_view(_rows("tafx"))
    assert kept == [0, 1] and golds == ["tn", "ar"]


def test_final_rappel_et_precision():
    s = fin.binary_scores(["tn", "tn", "ar", "ar"], ["tn", "ar", "tn", "ar"])
    assert s["rappel_tn"] == 0.5 and s["precision_tn"] == 0.5


def _criteria(press: bool) -> dict:
    rows = _rows("ttttaa")
    preds = {s: ["tn", "tn", "tn", "tn", "ar", "ar"] for s in fin.SEEDS}
    eval_examples = [{"lang": "fr", "text": "Il fait beau aujourd'hui"},
                     {"lang": "ar", "text": SANS_LA}]
    eval_preds = {s: ["fr", "ar"] for s in fin.SEEDS}
    press_texts = [SANS_LA] * 100 if press else None
    press_preds = {s: ["ar"] * 100 for s in fin.SEEDS} if press else None
    return fin.criteria(rows, preds, eval_examples, eval_preds, press_texts, press_preds,
                        draws=20)


def test_final_criteres_atteints_si_reference_adjugee():
    result = _criteria(press=True)
    assert result["rappel_tn"]["moyenne"] == 1.0 and result["rappel_tn"]["ecart_type"] == 0.0
    assert fin.verdict(result, "adjugee")["conclusion"] == "critères atteints"


def test_final_indicatif_si_annotateur_unique():
    result = _criteria(press=True)
    assert fin.verdict(result, "annotateur1_seul")["conclusion"].startswith("indicatif")


def test_final_presse_non_mesuree():
    result = _criteria(press=False)
    decision = fin.verdict(result, "adjugee")
    assert decision["criteres"]["3_fausses_alertes"] is None
    assert decision["conclusion"].startswith("non conclu")


def test_final_criteres_non_atteints():
    result = _criteria(press=True)
    result["precision_tn"]["moyenne"] = 0.80
    assert fin.verdict(result, "adjugee")["conclusion"] == "critères non atteints"


def test_final_passage_unique(tmp_path):
    lock = tmp_path / "verrou" / "verrou_gold_final.json"
    assert fin.acquire_passage(lock, False, "a" * 64) == 1
    with pytest.raises(RefusGold, match="déjà faite"):
        fin.acquire_passage(lock, False, "a" * 64)
    assert fin.acquire_passage(lock, True, "a" * 64) == 2
    with pytest.raises(RefusGold, match="deux passages"):
        fin.acquire_passage(lock, True, "a" * 64)


def test_final_deuxieme_passage_refuse_sans_premier(tmp_path):
    with pytest.raises(RefusGold, match="aucun passage"):
        fin.acquire_passage(tmp_path / "verrou.json", True, "a" * 64)


def test_final_baseline_alignee_sur_normalize(monkeypatch):
    from common.schemas import Document, Lang
    monkeypatch.setattr(fin, "normalize", lambda text: Document(text, text, Lang.TN, "arabic"))
    assert fin.rules_binary("texte factice") == "tn"
    monkeypatch.setattr(fin, "normalize", lambda text: Document(text, text, Lang.FR, "latin"))
    assert fin.rules_binary("texte factice") == "ar"


def test_final_verrou_fixe_hors_depot():
    assert fin.LOCK_PATH == REPO.parent / "NewsCheckTN_out" / "verrou_gold_final.json"
    assert not fin.LOCK_PATH.resolve().is_relative_to(REPO.resolve())


def test_final_eval_30_accepte_unk(tmp_path):
    entry = _predictions(tmp_path / "p.tsv", ["fr", "unk", "tn"])
    assert fin.load_predictions("p", entry, 3, fin.EVAL30_LABELS) == ["fr", "unk", "tn"]


def test_final_modele_de_manifeste_valide():
    template = REPO / "docs" / "lot-a2_gold_manifeste_modele.json"
    manifest = json.loads(template.read_text(encoding="utf-8"))
    assert set(manifest) - {"_notes"} == {"reference_test", "statut_reference", "graines",
                                          "presse"}
    assert sorted(manifest["graines"]) == list(fin.SEEDS)
    for files in manifest["graines"].values():
        assert set(files) == {"test", "eval_30", "presse"}


def test_final_modele_de_manifeste_passe_load_manifest(tmp_path):
    template = REPO / "docs" / "lot-a2_gold_manifeste_modele.json"
    manifest = json.loads(template.read_text(encoding="utf-8"))
    manifest["statut_reference"] = "annotateur1_seul"
    path = tmp_path / "manifeste.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert fin.load_manifest(path)["statut_reference"] == "annotateur1_seul"


# ---------------------------------------------------------------------------
# Entrées de l'entraînement final (gold_kaggle_inputs), textes factices
# ---------------------------------------------------------------------------

def test_entrees_train_exclut_f_et_x():
    rows = ki.train_rows([("t", "3lech"), ("a", SANS_LA), ("f", "Il fait beau"), ("x", "ok")])
    assert [r[0] for r in rows] == [1, 0]
    assert all(r[1] in (0, 1) for r in rows)


def test_entrees_consulte_seulement_arabe_standard_en_lettres_arabes():
    rows = ki.prediction_rows("factice", [SANS_LA, "Il fait beau aujourd'hui"])
    assert rows[0][1] == "ar" and rows[0][2] == 1
    assert rows[1][1] == "fr" and rows[1][2] == 0


def test_entrees_refusent_une_tabulation():
    with pytest.raises(RefusGold, match="tabulation"):
        ki.prediction_rows("factice", ["texte\tavec tabulation"])


def test_entrees_test_sans_etiquette(tmp_path, monkeypatch):
    monkeypatch.setattr(ki, "N_TRAIN", 2)
    summary = ki.build([("t", "3lech"), ("a", SANS_LA)], [SANS_LA, "3lech ya5i"],
                       ["Il fait beau"], None, tmp_path)
    header = (tmp_path / "final_test.tsv").read_text(encoding="utf-8").splitlines()[0]
    assert header == "numero\tregles\tconsulte\ttext"
    assert "presse" not in summary and summary["test"]["n"] == 2
    assert "3lech" not in json.dumps(summary, ensure_ascii=False)


def test_entrees_refusent_un_mauvais_effectif(tmp_path):
    with pytest.raises(RefusGold, match="au lieu de 800"):
        ki.build([("t", "3lech")], [], [], None, tmp_path)


def test_entrees_ne_s_ecrasent_pas(tmp_path, monkeypatch):
    monkeypatch.setattr(ki, "N_TRAIN", 1)
    ki.build([("t", "3lech")], [SANS_LA], ["Il fait beau"], None, tmp_path)
    with pytest.raises(RefusGold, match="existe déjà"):
        ki.build([("t", "3lech")], [SANS_LA], ["Il fait beau"], None, tmp_path)


def test_entrees_refusent_out_dir_dans_depot():
    with pytest.raises(RefusGold, match="dans le dépôt"):
        ki.run(["--out-dir", str(REPO / "gold_sortie")])


# ---------------------------------------------------------------------------
# Prédiction locale (gold_predict_local), faux modèle
# ---------------------------------------------------------------------------

def _summary(train_sha: str) -> dict:
    return {"config": dict(pl.EXPECTED_CONFIG), "entrainement": {"sha256": train_sha},
            "modeles": {s: {"fichiers": {}} for s in pl.SEEDS}}


def test_prediction_cascade():
    assert pl.cascade_label("tn", 0, None, True) == "tn"
    assert pl.cascade_label("ar", 1, 0.30, True) == "tn"
    assert pl.cascade_label("ar", 1, 0.29, True) == "ar"
    assert pl.cascade_label("fr", 0, None, False) == "fr"
    assert pl.cascade_label("fr", 0, None, True) == "ar"
    assert pl.cascade_label("unk", 0, None, False) == "unk"


def test_prediction_refuse_une_probabilite_manquante():
    with pytest.raises(ValueError):
        pl.cascade_label("ar", 1, None, True)


def test_prediction_modele_appele_sur_les_seuls_consultes():
    seen: list[list[str]] = []

    def scorer(texts):
        seen.append(texts)
        return [0.9] * len(texts)
    rows = [(1, "tn", 0, "a"), (2, "ar", 1, "b"), (3, "fr", 0, "c")]
    assert pl.predict_set(rows, scorer, binary=False) == ["tn", "tn", "fr"]
    assert seen == [["b"]]


def test_prediction_resume_configuration_figee():
    pl.check_summary(_summary("s" * 64), "s" * 64)
    changed = _summary("s" * 64)
    changed["config"]["lr"] = 5e-5
    with pytest.raises(RefusGold, match="configuration différente"):
        pl.check_summary(changed, "s" * 64)


def test_prediction_resume_autre_entrainement():
    with pytest.raises(RefusGold, match="autre final_train"):
        pl.check_summary(_summary("s" * 64), "t" * 64)


def test_prediction_empreintes_du_modele(tmp_path):
    folder = tmp_path / "graine1"
    folder.mkdir()
    (folder / "config.json").write_text("{}", encoding="utf-8")
    good = {"config.json": fin.sha256_file(folder / "config.json")}
    pl.check_model_dir("1", folder, good)
    with pytest.raises(RefusGold, match="empreinte différente"):
        pl.check_model_dir("1", folder, {"config.json": "0" * 64})
    with pytest.raises(RefusGold, match="fichiers du modèle"):
        pl.check_model_dir("1", folder, {**good, "model.safetensors": "0" * 64})


def test_prediction_bout_en_bout_faux_modele(tmp_path, monkeypatch):
    monkeypatch.setattr(ki, "N_TRAIN", 1)
    inputs = tmp_path / "entrees"
    inputs.mkdir()
    summary = ki.build([("t", "3lech")], [SANS_LA, "3lech ya5i"], ["Il fait beau", SANS_LA],
                       None, inputs)
    (inputs / "final_inputs.json").write_text(json.dumps({"fichiers": summary}),
                                              encoding="utf-8")
    info, sets = pl.load_inputs(inputs)
    assert set(sets) == {"test", "eval_30"}
    out = tmp_path / "sortie"
    out.mkdir()
    result = pl.predict_all(sets, {s: (lambda texts: [0.9] * len(texts)) for s in pl.SEEDS}, out)
    entry = result["1"]["test"]
    lines = (out / "predictions_test_graine1.tsv").read_text(encoding="utf-8").splitlines()
    assert entry["n"] == len(lines) == 2 and all(line.split("\t")[1] in ("tn", "ar")
                                                 for line in lines)
    assert entry["sha256"] == fin.sha256_file(out / "predictions_test_graine1.tsv")
    with pytest.raises(RefusGold, match="existe déjà"):
        pl.predict_all(sets, {"1": lambda texts: [0.9] * len(texts)}, out)


def test_prediction_entrees_alterees(tmp_path, monkeypatch):
    monkeypatch.setattr(ki, "N_TRAIN", 1)
    summary = ki.build([("t", "3lech")], [SANS_LA], ["Il fait beau"], None, tmp_path)
    (tmp_path / "final_inputs.json").write_text(json.dumps({"fichiers": summary}),
                                                encoding="utf-8")
    with (tmp_path / "final_test.tsv").open("a", encoding="utf-8") as handle:
        handle.write("2\tar\t1\tligne ajoutée\n")
    with pytest.raises(RefusGold, match="empreinte différente"):
        pl.load_inputs(tmp_path)


def test_prediction_refuse_out_dir_dans_depot(tmp_path):
    args = ["--entrees", str(tmp_path), "--resume", str(tmp_path / "r.json"),
            "--modele-graine1", "a", "--modele-graine2", "b", "--modele-graine3", "c",
            "--out-dir", str(REPO / "gold_sortie")]
    with pytest.raises(RefusGold, match="dans le dépôt"):
        pl.run(args)


def test_prediction_sans_torch_a_l_import():
    # import paresseux : torch et transformers ne sont importés que dans load_scorer
    source = (REPO / "normalization" / "gold_predict_local.py").read_text(encoding="utf-8")
    header = source.split("def load_scorer")[0]
    assert "import torch" not in header and "import transformers" not in header


def test_final_manifeste_incomplet(tmp_path):
    path = tmp_path / "manifeste.json"
    path.write_text(json.dumps({"reference_test": {}}), encoding="utf-8")
    with pytest.raises(RefusGold, match="incomplet"):
        fin.load_manifest(path)


def test_final_manifeste_statut_invalide(tmp_path):
    path = tmp_path / "manifeste.json"
    path.write_text(json.dumps({"reference_test": {}, "statut_reference": "autre",
                                "graines": {}, "presse": None}), encoding="utf-8")
    with pytest.raises(RefusGold, match="statut_reference"):
        fin.load_manifest(path)


def test_final_refuse_out_dir_dans_depot(tmp_path):
    with pytest.raises(RefusGold, match="dans le dépôt"):
        fin.run(["--manifeste", str(tmp_path / "m.json"), "--out-dir", str(REPO / "gold_sortie")])


def test_final_criteres_du_protocole_inchanges():
    assert (fin.MIN_RECALL_TN, fin.MIN_PRECISION_TN, fin.MAX_FALSE_ALARMS) == (0.70, 0.90, 0.01)
    assert fin.SEEDS == ("1", "2", "3")


# ---------------------------------------------------------------------------
# Presse neuve (EXP-A2-020, §9) : faux serveur, archive factice, aucun accès réseau
# ---------------------------------------------------------------------------

def _archive(tmp_path, year: int, n: int):
    import io
    import tarfile
    path = tmp_path / f"ara_news_{year}_10K.tar.gz"
    content = "".join(f"{i}\tphrase factice numéro {i}\n" for i in range(1, n + 1)).encode()
    with tarfile.open(path, "w:gz") as archive:
        info = tarfile.TarInfo(f"ara_news_{year}_10K/ara_news_{year}_10K-sentences.txt")
        info.size = len(content)
        archive.addfile(info, io.BytesIO(content))
    return path


def test_presse_annee_la_plus_recente_sans_2022():
    available = {pr.url_for(2022), pr.url_for(2021), pr.url_for(2020)}
    assert pr.most_recent_year(lambda url: url in available, newest=2026) == 2021


def test_presse_aucune_annee_disponible():
    assert pr.most_recent_year(lambda url: url == pr.url_for(2022), newest=2026) is None


def test_presse_url_10k():
    assert pr.url_for(2024).endswith("/ara_news_2024_10K.tar.gz")


def test_presse_tirage_deterministe_de_300(tmp_path):
    archive = _archive(tmp_path, 2024, 1000)
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    first = pr.draw_sample(archive, tmp_path / "a", 2024)
    second = pr.draw_sample(archive, tmp_path / "b", 2024)
    assert first["n"] == 300 and first["phrases_archive"] == 1000
    assert first["sha256"] == second["sha256"] and first["graine"] == 42
    lines = (tmp_path / "a" / "presse_ara_news_2024_10K_300.txt").read_text(encoding="utf-8")
    assert len(lines.splitlines()) == 300


def test_presse_refuse_un_second_tirage(tmp_path):
    archive = _archive(tmp_path, 2024, 400)
    pr.draw_sample(archive, tmp_path, 2024)
    with pytest.raises(RefusGold, match="déjà tiré"):
        pr.draw_sample(archive, tmp_path, 2024)


def test_presse_refuse_une_archive_trop_petite(tmp_path):
    with pytest.raises(RefusGold, match="trop petite"):
        pr.draw_sample(_archive(tmp_path, 2024, 50), tmp_path, 2024)


def test_presse_resultat_sans_texte(tmp_path):
    result = pr.draw_sample(_archive(tmp_path, 2024, 400), tmp_path, 2024)
    assert "phrase factice" not in json.dumps(result, ensure_ascii=False)


def test_presse_refuse_out_dir_dans_depot():
    with pytest.raises(RefusGold, match="dans le dépôt"):
        pr.run(["tirer", "--out-dir", str(REPO / "gold_sortie")])


def test_fasttext_non_charge_par_defaut():
    assert set(inv.build_predictors("regles,alphabet", inv.parse_args(["--out-dir", "x"]))) == \
        {"regles", "alphabet"}
