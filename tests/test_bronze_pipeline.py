"""Le runner Bronze ne doit pas charger le classifieur XLM-R."""

from bronze.pipeline import check_text
from common.schemas import Label


def test_bronze_pipeline_verifies_a_french_fact_with_the_rules_only():
    verdicts = check_text("Tunis est la capitale de la Tunisie.")
    assert len(verdicts) == 1
    assert verdicts[0].label == Label.TRUE
    assert verdicts[0].citations == ["sample-002"]
