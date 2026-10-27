"""Analyse catégorielle des erreurs Model 1."""

from bronze.analyze_model1_errors import enrich, markdown


def test_error_analysis_assigns_categories_and_renders_report():
    rows = enrich([
        {"id": "x1", "text": "Si la pluie continue", "label": "AUTRE", "modalite": "hypothétique", "predicted_label": "AFFIRMATION", "model_seed": "seed42", "correct": False},
        {"id": "x2", "text": "C'est injuste", "label": "OPINION", "modalite": "opinion", "predicted_label": "AUTRE", "model_seed": "seed42", "correct": False},
    ])
    assert [row["error_category"] for row in rows] == ["hypothese_non_reconnue", "opinion_pris_pour_autre"]
    report = markdown(rows)
    assert "Nombre d'erreurs : **2**" in report
    assert "hypothese non reconnue" in report
