"""Lot D : règles NLI provisoires face à l'arabizi (chiffres utilisés comme lettres)."""

from common.schemas import Claim, Evidence, Lang, Stance
from rag_llm.baseline_stance import _numbers, predict_stance_rules


def test_chiffre_lettre_arabizi_n_est_pas_un_nombre():
    assert _numbers("soum 5obez 190 millimes") == {"190"}
    assert _numbers("el 3am hedha") == set()
    assert _numbers("7aja b 2 dinars") == {"2"}


def test_unite_collee_reste_un_nombre():
    assert _numbers("prix 10dt") == {"10"}
    assert _numbers("3kg de tomates") == {"3"}


def test_arabizi_ne_donne_plus_une_fausse_contradiction():
    claim = Claim(text="soum 5obez 190 millimes", lang=Lang.TN)
    ev = Evidence(
        doc_id="x",
        text="Le prix de la baguette subventionnée reste fixé à 190 millimes.",
        source="test",
    )
    assert predict_stance_rules(claim, ev).stance != Stance.REFUTES
