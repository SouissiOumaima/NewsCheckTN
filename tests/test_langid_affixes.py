"""Lot A2 — Silver : retrait des affixes avant comparaison au lexique (EXP-A2-012)."""

import pytest

from normalization.langid import affix_variants, find_dialect_markers, is_dialectal_arabic
from normalization.silver_tuning import half, macro_f1

LQIT = "لقيت"  # لقيت : « j'ai trouvé »
WA_LQIT_HA = "و" + LQIT + "ها"  # ولقيتها : « et je l'ai trouvée »
ONLY_LQIT = frozenset({LQIT})


def test_variantes_retirent_prefixe_et_suffixe():
    assert LQIT in affix_variants(WA_LQIT_HA)


def test_variantes_gardent_au_moins_trois_lettres():
    # "وبه" : toutes les formes réduites font moins de 3 lettres -> aucune variante
    assert affix_variants("وبه") == []


def test_sans_option_le_comportement_ne_change_pas():
    assert find_dialect_markers(WA_LQIT_HA, markers=ONLY_LQIT, strip_affixes=False) == []


def test_avec_option_la_marque_est_retrouvee():
    assert find_dialect_markers(WA_LQIT_HA, markers=ONLY_LQIT, strip_affixes=True) == [LQIT]


def test_mot_deja_dans_le_lexique_garde_sa_forme():
    markers = frozenset({WA_LQIT_HA})
    assert find_dialect_markers(WA_LQIT_HA, markers=markers, strip_affixes=True) == [WA_LQIT_HA]


def test_is_dialectal_arabic_transmet_les_options():
    assert is_dialectal_arabic(WA_LQIT_HA, markers=ONLY_LQIT, strip_affixes=True)
    assert not is_dialectal_arabic(WA_LQIT_HA, markers=ONLY_LQIT, strip_affixes=False)


def test_coupe_du_dev_fixe_et_equilibree():
    assert half("abc") == half("abc")  # même réponse à chaque appel
    assert {half(f"texte {i}") for i in range(50)} == {"reglage", "mesure"}


def test_macro_f1():
    assert macro_f1(["tn", "ar"], ["tn", "ar"]) == 1.0
    # tn : F1 = 2/3 ; ar : F1 = 4/5 -> moyenne 11/15
    assert macro_f1(["tn", "tn", "ar", "ar"], ["tn", "ar", "ar", "ar"]) == pytest.approx(11 / 15)
