import json

from models.baselines.claim_detection_tfidf import load_examples, run


def test_tfidf_baseline_trains_and_reports_metrics(tmp_path):
    rows = []
    for index in range(12):
        rows.append({"id": f"a{index}", "text": f"Le taux officiel est {index} pour cent.", "lang": "fr", "annotation": "AFFIRMATION"})
        rows.append({"id": f"o{index}", "text": f"Je trouve cette mesure injuste {index}.", "lang": "fr", "annotation": "OPINION"})
    path = tmp_path / "annotated.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report, test = run(load_examples([path]), seed=42, test_size=0.25, split_file=None)

    assert report["n_train"] + report["n_test"] == 24
    assert 0.0 <= report["macro_f1"] <= 1.0
    assert len(report["test_ids"]) == len(test)
