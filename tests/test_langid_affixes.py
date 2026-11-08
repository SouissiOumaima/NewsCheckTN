"""Lot A2 — Silver : affixes (EXP-A2-012), filtre par l'arabe standard de Leipzig (EXP-A2-013)."""

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


# --- EXP-A2-013 : référence d'arabe standard (Leipzig) --------------------------------


def test_lecture_archive_leipzig_sans_extraction(tmp_path):
    import io
    import tarfile

    from normalization.silver_tuning import read_leipzig_sentences

    content = "1\tجملة أولى\n2\tجملة ثانية\n".encode()
    archive = tmp_path / "ara_news_2022_300K.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo("ara_news_2022_300K/ara_news_2022_300K-sentences.txt")
        info.size = len(content)
        tar.addfile(info, io.BytesIO(content))
    assert read_leipzig_sentences(archive) == ["جملة أولى", "جملة ثانية"]


def test_filtre_leipzig_ecarte_les_mots_de_presse():
    from collections import Counter

    from normalization.langid import load_markers
    from normalization.silver_tuning import lexicon_for

    rare, press = "باهي", "قالت"  # deux mots choisis pour le test
    counts = Counter({rare: 9, press: 9})  # 9 textes TSAC : retenus au seuil 8
    reference = Counter({press: 3})  # présent dans 3 phrases de presse
    strict = lexicon_for(8, counts, reference, 0)
    assert rare in strict and press not in strict
    assert press in lexicon_for(8, counts, reference, 5)  # tolérance de 5 phrases
    assert load_markers() <= strict  # le lexique actuel n'est jamais filtré
