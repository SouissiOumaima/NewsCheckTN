"""Lot A2 — outil d'étiquetage langue / écriture pour les autres lots (support S8)."""

import pytest

from normalization.tag_lang import read_rows, summary, tag_rows, tag_text, write_rows

ROWS = [
    {"id": "1", "claim": "Le prix du pain a augmenté de 20 % en 2024.", "evidence": ""},
    {"id": "2", "claim": "3lech el soum ghla barcha", "evidence": "Le prix est stable."},
]


def test_texte_vide_inconnu():
    assert tag_text("") == ("unk", "unk")
    assert tag_text("   ") == ("unk", "unk")


def test_meme_decision_que_le_pipeline():
    from normalization.normalize import normalize

    text = ROWS[0]["claim"]
    assert tag_text(text)[0] == str(getattr(normalize(text).lang, "value", normalize(text).lang))


def test_champs_ajoutes_sans_toucher_aux_autres():
    tagged = tag_rows(ROWS, ["claim", "evidence"])
    assert tagged[0]["id"] == "1" and tagged[0]["claim"] == ROWS[0]["claim"]
    assert {"claim_lang", "claim_script", "evidence_lang", "evidence_script"} <= set(tagged[0])
    assert tagged[0]["evidence_lang"] == "unk"  # preuve vide
    assert "claim_lang" not in ROWS[0]  # l'entrée n'est pas modifiée


def test_champ_absent_refuse():
    with pytest.raises(KeyError):
        tag_rows(ROWS, ["inexistant"])


@pytest.mark.parametrize("suffix", [".jsonl", ".csv"])
def test_aller_retour_fichier(tmp_path, suffix):
    path = tmp_path / f"jeu{suffix}"
    write_rows(path, ROWS)
    assert read_rows(path) == ROWS


def test_resume_sans_texte():
    lines = summary(tag_rows(ROWS, ["claim"]), ["claim"])
    assert lines[0].startswith("claim (2 lignes)")
    assert "pain" not in lines[0] and "barcha" not in lines[0]  # aucun texte affiché



def test_champ_absent_sur_une_ligne_suivante_refuse():
    with pytest.raises(KeyError, match="Ligne 2"):
        tag_rows([{"claim": "Texte fictif"}, {"id": "2"}], ["claim"])


@pytest.mark.parametrize("column", ["claim_lang", "claim_script"])
def test_annotation_existante_jamais_ecrasee(column):
    row = {"claim": "Texte fictif", column: "annotation humaine"}
    with pytest.raises(ValueError, match="déjà présent"):
        tag_rows([row], ["claim"])
    assert row[column] == "annotation humaine"


@pytest.mark.parametrize("value", [42, ["texte"], {"texte": "fictif"}])
def test_champ_non_textuel_refuse(value):
    with pytest.raises(ValueError, match="texte ou null"):
        tag_rows([{"claim": value}], ["claim"])


def test_null_explicite_reste_inconnu():
    assert tag_rows([{"claim": None}], ["claim"])[0]["claim_lang"] == "unk"


def test_ecriture_refuse_un_fichier_existant(tmp_path):
    path = tmp_path / "jeu.jsonl"
    path.write_text("contenu à préserver", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_rows(path, ROWS)
    assert path.read_text(encoding="utf-8") == "contenu à préserver"


def test_csv_conserve_metadonnee_facultative(tmp_path):
    path = tmp_path / "jeu.csv"
    write_rows(path, [{"claim": "Texte A"}, {"claim": "Texte B", "source": "fictive"}])
    restored = read_rows(path)
    assert restored[1]["source"] == "fictive"
    assert restored[0]["source"] == ""
