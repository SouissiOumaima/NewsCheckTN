"""Lot A2 — tirage des jeux du modèle tunisien : reproductible et sans recouvrement."""

import pytest

from normalization.model_tn_data import fingerprint, split_pool

POOL = [f"texte {i}" for i in range(100)]


def test_tirage_disjoint_et_de_bonne_taille():
    test, train = split_pool(POOL, seed=1, n_test=20, n_train=50)
    assert len(test) == 20 and len(train) == 50
    assert not set(test) & set(train)  # aucun texte dans les deux jeux


def test_tirage_reproductible():
    assert split_pool(POOL, 7, 20, 50) == split_pool(POOL, 7, 20, 50)
    assert split_pool(POOL, 7, 20, 50) != split_pool(POOL, 8, 20, 50)  # autre graine, autre tirage


def test_reserve_intacte():
    before = list(POOL)
    split_pool(POOL, 1, 20, 50)
    assert POOL == before  # le mélange porte sur une copie


def test_reserve_trop_petite():
    with pytest.raises(ValueError):
        split_pool(POOL, 1, 60, 50)


def test_empreinte_depend_de_l_ordre():
    assert fingerprint(["a", "b"]) == fingerprint(["a", "b"])
    assert fingerprint(["a", "b"]) != fingerprint(["b", "a"])
