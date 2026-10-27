"""Tests du protocole de métriques Bronze."""

from bronze.evaluate import evaluate
from common.schemas import Evidence


def test_bronze_evaluation_reports_end_to_end_and_retrieval_metrics():
    corpus = [Evidence("capitale", "Tunis est la capitale de la Tunisie.", "Tunisie")]
    records = [{
        "id": "fr-001", "text": "Tunis est la capitale de la Tunisie.",
        "gold_label": "vrai", "relevant_doc_ids": ["capitale"],
    }]
    report = evaluate(records, corpus)
    assert report["n"] == 1
    assert report["macro_f1"] == 1.0
    assert report["recall_at_k"] == 1.0
    assert report["items"][0]["correct"]
