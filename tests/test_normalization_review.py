"""Tests de normalization.review (chiffres de la revue Bronze) : sans corpus ni fichier annoté."""

from normalization.review import FAMILIES, alphabet_baseline, majority_baseline


def test_majority_baseline_repeats_most_frequent_label():
    # 2 « tn » contre 1 « ar » : la baseline répond « tn » partout.
    assert majority_baseline(["tn", "ar", "tn"]) == ["tn", "tn", "tn"]


def test_alphabet_baseline_ignores_language():
    # Lettres arabes -> « ar », même pour du tunisien ;
    # lettres latines -> « fr », même pour l'arabizi.
    assert alphabet_baseline(["برشا ناس", "ssbh lkhir", "Le sommet du G20"]) == ["ar", "fr", "fr"]


def test_ten_categories_grouped_in_five_families():
    # La revue demande 4 à 6 catégories : les 10 d'EXP-A2-009 tombent dans 5 familles.
    assert len(FAMILIES) == 10
    assert len(set(FAMILIES.values())) == 5
