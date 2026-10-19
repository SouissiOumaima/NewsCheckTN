"""Tests Lot A2."""

import itertools
import re

import pytest

from common.schemas import Document, Lang
from normalization.annotation import (
    candidates,
    cohen_kappa,
    read_annotations,
    write_annotations,
)
from normalization.langid import (
    _ARABIZI_MODEL_FILE,
    arabizi_score,
    char_ngrams,
    find_dialect_markers,
    load_arabizi_model,
    load_markers,
    load_neutral_words,
    prepare_latin,
)
from normalization.lexicon import folded as lexicon_folded
from normalization.lexicon import words as lexicon_words
from normalization.normalize import (
    detect_language,
    detect_script,
    normalize,
    normalize_arabic,
)

# ---------------------------------------------------------------------------
# Tests d'origine du dépôt (inchangés) : ils doivent toujours passer.
# ---------------------------------------------------------------------------


def test_detect_language_fr():
    assert detect_language("Le gouvernement a annoncé une hausse.") == Lang.FR


def test_detect_language_ar():
    assert detect_language("أعلنت الحكومة عن زيادة") == Lang.AR


def test_detect_language_arabizi():
    assert detect_language("3lech el 7koma ma 9alet chay") == Lang.TN


def test_normalize_arabic_removes_diacritics():
    assert normalize_arabic("مَدْرَسَة") == "مدرسه"


def test_normalize_whitespace():
    assert normalize("  Bonjour   Tunis  ").text == "Bonjour Tunis"


# ---------------------------------------------------------------------------
# Jeu de textes réalistes, réutilisé par plusieurs tests ci-dessous.
# ---------------------------------------------------------------------------

SAMPLES = [
    "Le chômage en Tunisie est de 16,4 % en 2023.",
    "Le vol A320 a décollé à 9h30 pour le sommet du G20.",
    "La note AAA de la France, sous Louis XIII, 10² = 100.",
    "C\u2019est graaaaave !!! 1000000 dinars",
    "3lech el 7koma ma 9alet chay",
    "Sa7a, el 7ala s3iba برشا برشا",
    "بـــرشـــا مَبْرُوك لتونس ههههههه",
    "إنّ الأسعار ارتفعت بنسبة ٩٫٣٪ في ٢٠٢٣",
    "Voir https://www.ins.tn/a3bc ou écrire à ali@gmail.com @ali",
    "😂😂😂 12345",
    "",
]


# ---------------------------------------------------------------------------
# 1. Le contrat : ce que les autres lots attendent de nous.
# ---------------------------------------------------------------------------

# parametrize lance le même test une fois par élément de SAMPLES.
@pytest.mark.parametrize("raw", SAMPLES)
def test_normalize_respects_contract(raw):
    doc = normalize(raw)
    assert isinstance(doc, Document)
    assert doc.raw_text == raw  # l'original n'est jamais modifié
    assert isinstance(doc.lang, Lang)
    assert doc.script in {"arabic", "latin", "arabizi", "mixed"}


@pytest.mark.parametrize("raw", SAMPLES)
def test_normalize_is_idempotent(raw):
    # Convention du README : normaliser deux fois = normaliser une fois.
    once = normalize(raw).text
    assert normalize(once).text == once


# ---------------------------------------------------------------------------
# 2. La règle d'or : nombres, sigles et liens ne changent jamais.
# ---------------------------------------------------------------------------

def _digits(text: str) -> str:
    """Tous les chiffres du texte, dans l'ordre, convertis en chiffres 0-9."""
    # int() comprend aussi les chiffres arabes-indiens : int("٩") == 9.
    return "".join(str(int(char)) for char in text if char.isdecimal())


@pytest.mark.parametrize("raw", SAMPLES)
def test_normalize_never_changes_digits(raw):
    assert _digits(normalize(raw).text) == _digits(raw)


@pytest.mark.parametrize(
    "fragment",
    ["AAA", "XIII", "10²", "1000000", "16,4 %", "A320", "G20"],
)
def test_normalize_keeps_numbers_and_acronyms(fragment):
    assert fragment in normalize(f"Selon le rapport {fragment} publié hier").text


@pytest.mark.parametrize(
    "fragment",
    ["https://www.ins.tn/a3bc", "ali@gmail.com", "@ali"],
)
def test_normalize_keeps_links_and_addresses(fragment):
    assert fragment in normalize(f"Voir {fragment} pour le détail").text


# ---------------------------------------------------------------------------
# 3. Les règles de normalisation.
# ---------------------------------------------------------------------------

def test_normalize_converts_arabic_digits_and_signs():
    doc = normalize("ارتفعت بنسبة ٩٫٣٪ في ٢٠٢٣")
    assert "9.3%" in doc.text
    assert "2023" in doc.text


def test_normalize_removes_tatweel_and_unifies_alef():
    assert normalize("بـــرشـــا").text == "برشا"
    assert normalize("أعلنت إنّ آخر").text == "اعلنت ان اخر"


def test_normalize_unifies_apostrophes():
    assert normalize("L\u2019inflation").text == "L'inflation"


def test_normalize_reduces_latin_elongation_to_two():
    assert normalize("graaaaave").text == "graave"
    assert normalize("aller").text == "aller"  # double lettre légitime


def test_normalize_reduces_arabic_elongation_to_three():
    assert normalize("ههههههه").text == "ههه"
    assert normalize("تتتبع").text == "تتتبع"  # vrai mot à 3 lettres identiques


def test_normalize_removes_invisible_characters():
    # \u200f = marque de direction droite-gauche, invisible à l'écran.
    assert normalize("تونس\u200f").text == "تونس"


# ---------------------------------------------------------------------------
# 4. Script et langue.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "Le G20 se réunit à Tunis.",
        "Le vol A320 a décollé à 9h30.",
        "La 5G arrive au 2e trimestre.",
        "La superficie est de 163 610 km2.",
        "Voir https://t.co/a3bc pour le détail",
    ],
)
def test_french_with_digits_is_not_arabizi(text):
    # Ces phrases étaient classées "tunisien" par le stub d'origine.
    assert detect_script(text) == "latin"
    assert detect_language(text) == Lang.FR


@pytest.mark.parametrize(
    "text",
    ["3lech el 7koma ma 9alet chay", "Sa7a", "el dar mta3 baba"],
)
def test_arabizi_is_detected(text):
    assert detect_script(text) == "arabizi"
    assert detect_language(text) == Lang.TN


def test_acronym_does_not_make_arabic_text_mixed():
    assert detect_script("أعلنت الحكومة عن زيادة حسب BCT") == "arabic"


def test_balanced_text_is_mixed():
    assert detect_script("el 7ala s3iba برشا برشا") == "mixed"


@pytest.mark.parametrize(
    "text",
    ["", "   ", "12345", "😂😂😂", "https://t.co/abc"],
)
def test_text_without_letters_has_unknown_language(text):
    assert detect_language(text) == Lang.UNKNOWN


def test_is_arabizi_rule_ignores_one_ambiguous_word_in_long_text():
    # Un seul mot douteux ("ta3") dans 40 mots de français ne suffit pas.
    text = " ".join(["le rapport annuel"] * 13) + " ta3"
    assert len(re.findall(r"\w+", text)) == 40
    assert detect_script(text) == "latin"


# ---------------------------------------------------------------------------
# 5. Limites connues, écrites noir sur blanc.
#    xfail = "échec attendu" : le test décrit ce qu'on VEUT obtenir et que le
#    code ne sait pas encore faire. Il passera au vert avec le classifieur.
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# 6. Tunisien en lettres arabes : règle à lexique de marques (langid.py).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "الحكومة باش تزيد في الشهرية برشا",
        "علاش الأسعار طلعت هكا",
        "الوزير قال اللي الزيادة موش توا",
        "ما فهمتش شنوة صار",  # négation en deux mots : ما ... ش
        "مانحبش نحكي في الموضوع هذا",  # négation collée en un seul mot
        "برشااااا ناس خرجت اليوم",  # lettres étirées
    ],
)
def test_tunisian_in_arabic_script_is_tn(text):
    assert detect_language(text) == Lang.TN
    assert normalize(text).lang == Lang.TN  # même réponse après normalisation


@pytest.mark.parametrize(
    "text",
    [
        "أعلنت الحكومة عن زيادة في الأجور",
        "ذهب الرئيس إلى صفاقس لافتتاح المستشفى",  # "إلى" ne doit pas passer pour "اللي"
        "هذا المشهد مدهش ومنعش",  # mots standard qui finissent par ش
        "ما أجمل هذا اليوم",  # "ما" exclamatif, sans négation
        "ما يناقش اليوم في البرلمان هو قانون المالية",  # verbe standard en ش
        "لم يصدر أي بيان رسمي حتى الآن",
    ],
)
def test_standard_arabic_stays_ar(text):
    assert detect_language(text) == Lang.AR
    assert find_dialect_markers(normalize(text).text) == []


def test_find_dialect_markers_returns_the_words():
    # Renvoyer les mots trouvés permet d'expliquer chaque décision.
    assert find_dialect_markers(normalize("الحكومة باش تزيد برشا").text) == ["باش", "برشا"]


def test_one_dialect_word_does_not_flip_a_long_standard_text():
    # 60 mots standard + 1 mot dialectal cité : sous le seuil de 2 %, le texte reste "ar".
    text = " ".join(["أعلنت الحكومة عن زيادة"] * 15) + " برشا"
    assert len(text.split()) == 61
    assert detect_language(text) == Lang.AR


def test_marker_lexicon_is_well_formed():
    markers = load_markers()
    assert len(markers) >= 50
    for word in markers:
        # Le lexique doit être écrit dans la forme normalisée, sinon le mot ne serait jamais trouvé.
        assert normalize_arabic(word) == word, word
    # Mots volontairement exclus : trop ambigus avec l'arabe standard ou avec un prénom.
    assert not markers & {"الي", "لي", "ياسر", "شنوا"}


@pytest.mark.xfail(reason="tunisien sans mot du lexique : rappel mesuré 0.53, classifieur à venir")
def test_tunisian_without_lexicon_word_is_tn():
    assert detect_language("توحشتك يا صاحبي") == Lang.TN


# ---------------------------------------------------------------------------
# 7. Arabizi sans chiffres : modèle appris (langid.py, entraîné par train_langid.py).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "chnowa el jaw lyoum fi tounes",
        "el hkouma kalet elli el asaar bech tonkos",
        "bsaraha el barnamej hedha masset barcha",
        "ena nheb tounes barcha w nheb ennes el kol",
        "rabi yehdik ya weldi w yostor alik",
    ],
)
def test_arabizi_without_digits_is_tn(text):
    assert detect_script(text) == "arabizi"
    assert detect_language(text) == Lang.TN


@pytest.mark.parametrize(
    "text",
    [
        "Le gouvernement a annoncé une hausse des salaires.",
        "Les prix ont augmenté de 12 % selon l'INS.",
        "Je pense que cette réforme est une catastrophe pour les jeunes.",
        "Kaïs Saïed a reçu Najla Bouden au palais de Carthage.",  # noms tunisiens, phrase française
        "Merci beaucoup pour ce beau spectacle",  # français familier, sans accent ni article
        "Très bon acteur, bravo",
    ],
)
def test_french_is_not_arabizi(text):
    assert detect_script(text) == "latin"
    assert detect_language(text) == Lang.FR


def test_prepare_latin_keeps_letters_and_drops_neutral_words():
    # Chiffres, ponctuation et mots neutres ("bravo", "top") ne sont pas donnés au modèle.
    assert prepare_latin("Bravooo !!! 123 c'est TOP") == "c'est"


def test_char_ngrams_marks_word_boundaries():
    # Le mot est entouré d'espaces : " a" = début de mot, "b " = fin de mot.
    assert char_ngrams("ab", 1, 2) == ["a", "b", " a", "ab", "b "]


@pytest.mark.parametrize("text", ["Bravo", "19h15.", "", "ok merci"])
def test_model_gives_no_opinion_without_enough_words(text):
    # Pas assez d'indices : le modèle ne se prononce pas, et le texte n'est pas déclaré arabizi.
    assert arabizi_score(text) is None
    assert detect_script(text) == "latin"


def test_arabizi_model_file_is_well_formed():
    model = load_arabizi_model()
    assert model is not None, "normalization/resources/arabizi_ngrams.json est absent"
    assert model["ngram_range"] == [1, 4]
    assert 1000 <= len(model["weights"]) <= 20000
    assert isinstance(model["intercept"], float)
    assert model["threshold"] >= 0
    # Le fichier est versionné : il doit rester petit (convention du README du lot).
    assert _ARABIZI_MODEL_FILE.stat().st_size < 1_000_000


def test_neutral_words_are_written_without_repeated_letters():
    for word in load_neutral_words():
        assert word == word.lower()
        # pairwise("abc") donne (a, b), (b, c) : deux voisines ne doivent pas être identiques.
        assert not any(a == b for a, b in itertools.pairwise(word)), word


def test_arabic_presentation_forms_are_arabic_script():
    # Lettres arabes "déjà dessinées" (anciens codes) : mêmes mots que "يحشم على روحو".
    drawn = "ﻳﺤﺸﻢ ﻋﻠﻲ ﺭﻭﺣﻮ"
    assert detect_script(drawn) == "arabic"
    assert detect_language(drawn) == Lang.TN  # "روحو" est dans le lexique de marques


@pytest.mark.xfail(reason="phrase française avec un seul mot tunisien : modèle insuffisant")
def test_mostly_french_sentence_with_one_tunisian_word_is_tn():
    assert detect_language("Honnêtement la décision hedhi n'est pas normale") == Lang.TN


# ---------------------------------------------------------------------------
# Échantillons annotés (normalization/annotation.py)
# ---------------------------------------------------------------------------


def test_cohen_kappa_on_a_hand_computed_example():
    # Observé : 3 lignes sur 4 identiques = 0.75.
    # Hasard : a (0.50 x 0.25) + b (0.50 x 0.75) = 0.50.  Kappa = (0.75 - 0.50) / (1 - 0.50) = 0.50.
    observed, expected, kappa = cohen_kappa(["a", "a", "b", "b"], ["a", "b", "b", "b"])
    assert (observed, expected, kappa) == (0.75, 0.5, 0.5)


def test_cohen_kappa_is_one_for_perfect_agreement():
    assert cohen_kappa(["t", "a", "x"], ["t", "a", "x"])[2] == 1.0


def test_cohen_kappa_refuses_lists_of_different_length():
    with pytest.raises(ValueError):
        cohen_kappa(["t"], ["t", "a"])


def test_annotation_files_round_trip_and_are_never_overwritten(tmp_path):
    path = tmp_path / "sample.tsv"
    rows = [("t", "barcha mahlek"), ("?", "texte à annoter\tavec tabulation")]
    write_annotations(path, rows)
    assert read_annotations(path) == rows  # seule la PREMIÈRE tabulation sépare l'étiquette
    with pytest.raises(SystemExit):
        write_annotations(path, rows)  # des annotations seraient perdues : on refuse


def test_sample_candidates_follow_the_rules():
    texts = [
        "برشا ناس جاو اليوم",  # lettres arabes, 4 mots : candidat "arabic"
        "برشا ناس",  # trop court (moins de 3 mots)
        "mahlek ya zina barcha",  # lettres latines sans chiffre : candidat "latin"
        "3lech ya sahbi kifech",  # chiffre d'arabizi : déjà reconnu par les règles, pas "latin"
    ]
    assert candidates(texts, "arabic") == ["برشا ناس جاو اليوم"]
    assert candidates(texts, "latin") == ["mahlek ya zina barcha"]


# ---------------------------------------------------------------------------
# Lexique des marques (normalization/lexicon.py)
# ---------------------------------------------------------------------------


def test_lexicon_words_use_the_folded_form_of_the_rule():
    # Le mot est compté sous la forme que lit la règle : alef, ta marbouta et tatweel repliés.
    assert lexicon_words("برشــــا الإنسانة") == {"برشا", "الانسانه"}


def test_lexicon_markers_are_stored_in_folded_form():
    # Sinon le comptage des candidats ne retrouverait pas les mots du lexique.
    for marker in load_markers():
        assert lexicon_folded(marker) == marker, marker
