"""Tests des scripts du palier Gold du Lot A2 (docs/lot-a2_protocole_gold.md).

Uniquement des textes FACTICES écrits ici : aucun texte du corpus, aucune lecture de data/.
"""

from __future__ import annotations

import json
import random

import pytest

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
