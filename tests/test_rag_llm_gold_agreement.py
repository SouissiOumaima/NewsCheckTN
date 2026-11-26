"""Lot D — Gold : accord entre annotateurs (lecture des fichiers, paires, sorties du juge)."""

import csv
import json

from rag_llm import gold_agreement as ga

COLS = ["claim_id", "citations", "pertinence_P1", "invente", "fidelite"]


def write(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)


def test_accord_par_paire(tmp_path):
    write(
        tmp_path / "lot-d_annotation_hadil_dev_annote.csv",
        [
            {
                "claim_id": "c1",
                "citations": "P1",
                "pertinence_P1": "pertinent",
                "invente": "oui",
                "fidelite": "infidele",
            },
            {
                "claim_id": "c2",
                "citations": "",
                "pertinence_P1": "",
                "invente": "non",
                "fidelite": "fidele",
            },
        ],
    )
    write(
        tmp_path / "lot-d_annotation_wiem_dev_annote.csv",
        [
            {
                "claim_id": "c1",
                "citations": "P1",
                "pertinence_P1": "pertinent",
                "invente": "non",
                "fidelite": "infidele",
            },
        ],
    )
    (tmp_path / "lot-d_annotation_wiem_dev.csv").write_text("ignoré", encoding="utf-8")
    humans = ga.load_humans(tmp_path)
    assert set(humans) == {"hadil", "wiem"}
    for part, cid in (("mise_au_point", "c2"), ("mesure", "c1")):
        (tmp_path / f"lot-d_juge_{part}_juge_v2_20261122.json").write_text(
            json.dumps(
                {
                    "per_item": [
                        {"claim_id": cid, "labels": {"invente": "non", "fidelite": "fidele"}}
                    ]
                }
            )
        )
    (tmp_path / "lot-d_juge_mesure_juge_v2_qwen2.5-7b-instruct_20261122.json").write_text("{}")
    judge = ga.load_judge(tmp_path)
    assert judge == {
        ("c2", "invente"): "non",
        ("c2", "fidelite"): "fidele",
        ("c1", "invente"): "non",
        ("c1", "fidelite"): "fidele",
    }
    res = ga.pairwise({**humans, "juge": judge})
    assert set(res) == {"hadil / wiem", "hadil / juge", "wiem / juge"}
    hw = res["hadil / wiem"]
    assert hw["invente"]["n"] == 1 and hw["invente"]["raw"] == 0.0
    assert hw["fidelite"]["raw"] == 1.0
    assert res["hadil / juge"]["fidelite"]["n"] == 2
