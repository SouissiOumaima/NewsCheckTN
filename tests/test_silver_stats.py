"""Lot A2 — Silver : bootstrap apparié, graines et courbe d'apprentissage (EXP-A2-014)."""

import pytest

from normalization.silver_stats import (
    binary_scores,
    choose_threshold,
    choose_threshold_flagged,
    evaluate,
    mean_std,
    paired_bootstrap,
    split,
)

GOLDS = ["tn", "tn", "ar", "ar", "fr", "fr"] * 5


def test_systeme_identique_ecart_nul():
    r = paired_bootstrap(GOLDS, GOLDS, GOLDS, n_boot=200, seed=1)
    assert r["diff"] == 0 and r["low"] == 0 and r["high"] == 0


def test_systeme_parfait_contre_baseline_constante():
    baseline = ["tn"] * len(GOLDS)
    r = paired_bootstrap(GOLDS, GOLDS, baseline, n_boot=200, seed=1)
    assert r["diff"] > 0 and r["low"] > 0  # écart positif, IC entièrement au-dessus de 0
    assert r["p"] == 0


def test_reproductible():
    baseline = ["ar"] * len(GOLDS)
    assert paired_bootstrap(GOLDS, GOLDS, baseline, 100, 7) == paired_bootstrap(
        GOLDS, GOLDS, baseline, 100, 7
    )


# --- Graines, baseline neuronale, courbe (EXP-A2-014) ---------------------------------------


def test_moyenne_ecart_type():
    assert mean_std([0.5]) == (0.5, 0.0)  # une seule graine : écart-type nul
    mean, sd = mean_std([0.8, 0.9, 1.0])
    assert mean == pytest.approx(0.9) and sd == pytest.approx(0.1)


def test_seuil_plus_petit_sans_fausse_alerte():
    french_dev = [-3.0, 0.4, 1.2]  # un texte français monte jusqu'à 1,2
    assert choose_threshold(french_dev, [0.0, 0.5, 1.0, 1.5, 2.0]) == 1.5
    assert choose_threshold([9.0], [0.0, 1.0]) == 1.0  # repli : le plus haut seuil


def test_seuil_sans_repli_signale():
    french_dev = [-3.0, 0.4, 1.2]  # le critère est tenu à 1,5
    assert choose_threshold_flagged(french_dev, [0.0, 0.5, 1.0, 1.5, 2.0]) == (1.5, False)


def test_seuil_de_repli_signale():
    # aucun seuil ne tient le critère : on garde le plus haut, et le repli est signalé
    assert choose_threshold_flagged([9.0], [0.0, 1.0]) == (1.0, True)


def test_choose_threshold_inchange_avec_l_indicateur():
    for scores, grid in (([-3.0, 0.4, 1.2], [0.0, 0.5, 1.0, 1.5, 2.0]), ([9.0], [0.0, 1.0])):
        assert choose_threshold(scores, grid) == choose_threshold_flagged(scores, grid)[0]


def test_evaluate_rapporte_le_repli():
    pool = {"french_dev": ["f1", "f2"], "french_test": ["f3"]}
    data = {"ar_dev": ["a1", "a2"]}
    high = {"f1": 9.0, "f2": 0.0, "f3": 0.0, "a1": 9.0, "a2": 9.0}
    low = {"f1": 0.0, "f2": 0.0, "f3": 0.0, "a1": 9.0, "a2": 9.0}
    with_fallback = evaluate(lambda texts: [high[t] for t in texts], [0.5, 1.0], pool, data)
    normal = evaluate(lambda texts: [low[t] for t in texts], [0.5, 1.0], pool, data)
    assert with_fallback["repli"] is True and with_fallback["seuil"] == 1.0
    assert normal["repli"] is False and normal["seuil"] == 0.5
    # les autres chiffres sont ceux de binary_scores au même seuil, sans changement
    assert {k: v for k, v in normal.items() if k != "repli"} == binary_scores(
        [9.0, 9.0], [0.0], threshold=0.5)


def test_scores_binaires():
    r = binary_scores([2.0, 3.0, -1.0], [-2.0, 0.5], threshold=1.0)
    assert r["rappel"] == pytest.approx(2 / 3)
    assert r["alertes"] == 0 and r["n_fr"] == 2 and r["seuil"] == 1.0


POOL = {
    "arabizi": [f"3aslema ya khouya {i} barcha" for i in range(40)],
    "french_train": ["Le gouvernement a annoncé une nouvelle loi sur le prix du pain."] * 5,
}


def test_meme_mise_de_cote_pour_toutes_les_fractions():
    full = split(POOL, seed=13)
    tenth = split(POOL, seed=13, fraction=0.25)
    assert full["ar_dev"] == tenth["ar_dev"]  # la courbe mesure toujours les mêmes textes
    assert len(tenth["ar_train"]) == len(full["ar_train"]) // 4
    assert not set(full["ar_dev"]) & set(full["ar_train"])  # mis de côté jamais appris


def test_graines_differentes_mises_de_cote_differentes():
    assert split(POOL, seed=13)["ar_dev"] != split(POOL, seed=42)["ar_dev"]
    assert split(POOL, seed=42) == split(POOL, seed=42)  # reproductible
