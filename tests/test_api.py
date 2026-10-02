"""Tests Lot E — API et pipeline."""

from fastapi.testclient import TestClient

from api.main import app
from pipeline import check_text

client = TestClient(app)
TEXT = "Le taux de chômage en Tunisie est de 16,4 % en 2023."


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_stage_routes():
    assert client.post("/normalize", json={"text": TEXT}).status_code == 200
    assert client.post("/extract", json={"text": TEXT}).json()["claims"]
    assert client.post("/retrieve", json={"claim": TEXT}).status_code == 200
    assert client.post("/nli", json={"claim": TEXT, "evidence": TEXT}).status_code == 200
    assert client.post("/verdict", json={"claim": TEXT}).status_code == 200


def test_check_route():
    r = client.post("/check", json={"text": TEXT})
    assert r.status_code == 200 and len(r.json()["verdicts"]) == 1


def test_pipeline_end_to_end():
    verdicts = check_text(TEXT)
    assert len(verdicts) == 1 and verdicts[0].claim.text == TEXT
