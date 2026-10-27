"""Tests du protocole de métriques Bronze."""

from bronze.evaluate import evaluate
from common.schemas import Evidence
from models.nli.stance import set_classifier


def test_bronze_evaluation_reports_end_to_end_and_retrieval_metrics(monkeypatch):
    monkeypatch.setenv("NLI_BACKEND", "bronze")
    set_classifier(None)
    corpus = [
        Evidence("capitale", "Tunis est la capitale de la Tunisie.", "Tunisie"),
        Evidence("hors-sujet-1", "Le ministère publie un nouveau calendrier scolaire.", "MEN"),
        Evidence("hors-sujet-2", "Les prix agricoles sont suivis chaque semaine.", "ONAGRI"),
    ]
    records = [{
        "id": "fr-001", "text": "Tunis est la capitale de la Tunisie.",
        "gold_label": "vrai", "relevant_doc_ids": ["capitale"],
    }]
    report = evaluate(records, corpus)
    assert report["n"] == 1
    assert report["macro_f1"] == 1.0
    assert report["recall_at_k"] == 1.0
    assert report["items"][0]["correct"]
