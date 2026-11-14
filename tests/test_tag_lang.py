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
