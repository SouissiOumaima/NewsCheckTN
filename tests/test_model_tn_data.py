"""Lot A2 — tirage des jeux du modèle tunisien : reproductible et sans recouvrement."""

import hashlib

import pytest

from normalization import model_tn_data
from normalization import model_tn_kaggle_prep as prep
from normalization.evaluate import REPO
from normalization.model_tn_data import aligned_pairs, fingerprint, split_pool

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


# ---------------------------------------------------------------------------
# Accord entre annotateurs (command_kappa), textes FACTICES
# ---------------------------------------------------------------------------

def _rows(labels: str, prefix: str = "texte factice") -> list[tuple[str, str]]:
    return [(label, f"{prefix} {i}") for i, label in enumerate(labels, 1)]


def test_paires_alignees():
    pairs, misaligned = aligned_pairs(_rows("tat"), _rows("tta"))
    assert pairs == [("t", "t"), ("a", "t"), ("t", "a")] and misaligned == 0


def test_paires_desalignees_comptees():
    second = _rows("tat")
    second[1] = ("a", "autre texte")
    pairs, misaligned = aligned_pairs(_rows("tat"), second)
    assert len(pairs) == 2 and misaligned == 1


def test_lignes_sans_vis_a_vis_non_comptees_comme_desalignees():
    pairs, misaligned = aligned_pairs(_rows("tatat"), _rows("ta"))
    assert len(pairs) == 2 and misaligned == 0


def _files(tmp_path, monkeypatch, rows_1, rows_2):
    for key, rows in (("test_1", rows_1), ("test_2", rows_2), ("train_1", rows_1),
                      ("train_2", rows_2)):
        path = tmp_path / f"{key}.tsv"
        path.write_text("".join(f"{label}\t{text}\n" for label, text in rows), encoding="utf-8")
        monkeypatch.setitem(model_tn_data.FILES, key, path)


def test_command_kappa_aligne(tmp_path, monkeypatch, capsys):
    _files(tmp_path, monkeypatch, _rows("ttaa"), _rows("ttat"))
    model_tn_data.command_kappa()
    out = capsys.readouterr().out
    assert out.count("lignes désalignées écartées : 0") == 2
    assert "4 paires" in out and "texte factice" not in out


def test_command_kappa_lignes_desalignees(tmp_path, monkeypatch, capsys):
    second = _rows("ttaa")
    second[0] = ("t", "autre factice 1")
    second[2] = ("a", "autre factice 3")
    _files(tmp_path, monkeypatch, _rows("ttaa"), second + [("t", "ligne en plus")])
    model_tn_data.command_kappa()
    out = capsys.readouterr().out
    assert out.count("lignes désalignées écartées : 2") == 2
    assert "lignes sans vis-à-vis : 1" in out and "2 paires" in out
    assert "factice" not in out and "ligne en plus" not in out


# ---------------------------------------------------------------------------
# Préparation de kaggle_train.tsv (model_tn_kaggle_prep), textes FACTICES
# ---------------------------------------------------------------------------

FACTICE = [("t", "3lech ya5i"), ("a", "ذهب الولد إلى المدرسة"), ("f", "Il fait beau"),
           ("x", "ok")]


def _source(tmp_path, rows=FACTICE):
    path = tmp_path / "train.tsv"
    path.write_text("".join(f"{label}\t{text}\n" for label, text in rows), encoding="utf-8")
    return path, fingerprint([text for _, text in rows])


def test_kaggle_prep_exclut_f_et_x_et_code_les_etiquettes():
    rows = prep.kaggle_rows(FACTICE)
    assert [r[0] for r in rows] == [1, 0] and all(r[1] in (0, 1) for r in rows)
    assert [r[2] for r in rows] == ["3lech ya5i", "ذهب الولد إلى المدرسة"]


def test_kaggle_prep_format_exact(tmp_path):
    source, digest = _source(tmp_path)
    n, sha = prep.prepare(source, tmp_path / "out.tsv", expected=digest, n_expected=2)
    content = (tmp_path / "out.tsv").read_bytes()
    lex = prep.kaggle_rows(FACTICE)
    expected = (f"label\tlex\ttext\n1\t{lex[0][1]}\t3lech ya5i\n0\t{lex[1][1]}\t"
                "ذهب الولد إلى المدرسة\n").encode("utf-8")
    assert content == expected and n == 2
    assert sha == hashlib.sha256(expected).hexdigest()


def test_kaggle_prep_refuse_une_autre_liste(tmp_path):
    source, _ = _source(tmp_path)
    with pytest.raises(prep.Refus, match="empreinte"):
        prep.prepare(source, tmp_path / "out.tsv", expected="0" * 64, n_expected=2)


def test_kaggle_prep_refuse_un_mauvais_effectif(tmp_path):
    source, digest = _source(tmp_path)
    with pytest.raises(prep.Refus, match="au lieu de 800"):
        prep.prepare(source, tmp_path / "out.tsv", expected=digest)


def test_kaggle_prep_refuse_une_tabulation():
    with pytest.raises(prep.Refus, match="tabulation"):
        prep.kaggle_rows([("t", "texte\tavec tabulation")])


def test_kaggle_prep_refuse_d_ecraser(tmp_path):
    existing = tmp_path / "kaggle_train.tsv"
    existing.write_text("déjà là", encoding="utf-8")
    with pytest.raises(prep.Refus, match="existe déjà"):
        prep.check_output(existing)


def test_kaggle_prep_refuse_un_chemin_versionne():
    with pytest.raises(prep.Refus, match="versionnée"):
        prep.check_output(REPO / "normalization" / "kaggle_train_jamais_cree.tsv")


def test_kaggle_prep_accepte_data_ignore():
    target = REPO / "data" / "interim" / "langid" / "model_tn" / "kaggle_train_jamais_cree.tsv"
    assert prep.check_output(target) == target.resolve()
    assert not target.exists()
