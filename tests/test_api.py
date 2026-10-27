"""Tests Lot E — API et pipeline."""

from fastapi.testclient import TestClient

from api import main
from api.main import app
from pipeline import check_text

client = TestClient(app)
TEXT = "Le taux de chômage en Tunisie est de 16,4 % en 2023."


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_root_redirects_to_the_frontend():
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == "/app/"


def test_results_are_normalized_for_the_web_dashboard(tmp_path, monkeypatch):
    (tmp_path / "claim_detection_demo.json").write_text(
        '{"task":"claim_detection","macro_f1":0.7,"n":10,"macro_f1_by_lang":{"fr":0.8}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "RESULTS_DIR", tmp_path)
    result = client.get("/results").json()["results"][0]
    assert result["lot"] == "C"
    assert result["metrics"] == {"macro_f1": 0.7, "n": 10, "by_lang": {"fr": {"macro_f1": 0.8}}}


def test_stage_routes():
    assert client.post("/normalize", json={"text": TEXT}).status_code == 200
    assert client.post("/extract", json={"text": TEXT}).json()["claims"]
    bronze = client.post("/extract/bronze", json={"text": "Tunis est la capitale de la Tunisie."})
    assert bronze.status_code == 200 and bronze.json()["claims"]
    assert client.post("/retrieve", json={"claim": TEXT}).status_code == 200
    assert client.post("/nli", json={"claim": TEXT, "evidence": TEXT}).status_code == 200
    assert client.post("/verdict", json={"claim": TEXT}).status_code == 200


def test_bronze_trace_is_complete_and_timed():
    response = client.post("/bronze/check", json={"text": TEXT, "k": 5})
    assert response.status_code == 200
    payload = response.json()
    assert payload["document"]["lang"] == "fr"
    assert payload["claims"]
    trace = payload["claims"][0]
    assert trace["verdict"]["label"]
    evidence_ids = {citation["doc_id"] for citation in trace["evidence"]}
    assert set(trace["verdict"]["citations"]) <= evidence_ids
    assert trace["timings_ms"].keys() == {"retrieval", "nli", "verdict"}
    assert payload["timings_ms"]["total"] >= 0


def test_bronze_trace_filters_an_opinion_safely():
    response = client.post("/bronze/check", json={"text": "Je pense que Tunis est magnifique."})
    assert response.status_code == 200
    assert response.json()["claims"] == []


def test_bronze_trace_supports_the_arabic_bread_demo_case(monkeypatch):
    monkeypatch.setenv("NLI_BACKEND", "bronze")
    from models.nli.stance import set_classifier

    set_classifier(None)
    response = client.post("/bronze/check", json={"text": "سعر الخبز المدعم 190 مليما"})
    assert response.status_code == 200
    trace = response.json()["claims"][0]
    assert trace["verdict"]["label"] == "vrai"
    assert trace["verdict"]["citations"] == ["sample-003"]


def test_check_route():
    r = client.post("/check", json={"text": TEXT})
    assert r.status_code == 200 and len(r.json()["verdicts"]) == 1


def test_pipeline_end_to_end():
    verdicts = check_text(TEXT)
    assert len(verdicts) == 1 and verdicts[0].claim.text == TEXT
