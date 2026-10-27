"""Préparation de la feuille d'annotation Bronze."""

from bronze.prepare_review_set import build_review_rows


def test_prepare_review_set_keeps_only_french_sourced_items():
    corpus, review = build_review_rows([
        {"id": "fr-1", "text": "Tunis est une capitale.", "lang": "fr", "source": "source"},
        {"id": "ar-1", "text": "تونس", "lang": "ar", "source": "source"},
    ])
    assert corpus[0]["doc_id"] == "bronze-fr-1"
    assert review == [{
        "id": "fr-1", "text": "Tunis est une capitale.", "relevant_doc_ids": ["bronze-fr-1"],
        "gold_label": None, "review_status": "à_annoter",
        "note": "Le label doit être décidé après lecture de la source primaire ou du fact-check.",
    }]
