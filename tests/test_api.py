"""Tests Lot E — API et pipeline."""

import json

from fastapi.testclient import TestClient

from api import main as api_main
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


# --- Routes de la plateforme web ------------------------------------------------------


def test_verdict_detail_route():
    r = client.post("/verdict/detail", json={"claim": TEXT, "k": 3})
    assert r.status_code == 200
    data = r.json()
    assert data["corpus_size"] >= 1 and data["nli"] == "lot-c"
    assert set(data["verdict"]) >= {"label", "explanation", "citations", "uncertainty", "abstained"}
    ranks = [e["rank"] for e in data["evidences"]]
    assert ranks == list(range(1, len(ranks) + 1))
    assert all({"doc_id", "text", "stance", "confidence"} <= set(e) for e in data["evidences"])


def test_verdict_detail_refuse_un_nli_inconnu():
    assert client.post("/verdict/detail", json={"claim": TEXT, "nli": "magique"}).status_code == 422


def test_corpus_stats_route():
    data = client.get("/corpus/stats").json()
    assert data["size"] >= 1 and sum(data["by_source"].values()) == data["size"]


def test_results_route_allege_les_fichiers(tmp_path, monkeypatch):
    payload = {"exp_id": "EXP-X-001", "lot": "X", "metrics": {"f1": 0.5}, "items": [1, 2]}
    (tmp_path / "lot-x_tache_20261023.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "casse.json").write_text("{pas du json", encoding="utf-8")
    monkeypatch.setattr(api_main, "RESULTS_DIR", tmp_path)
    results = client.get("/results").json()["results"]
    good = next(r for r in results if r["file"].startswith("lot-x"))
    assert good["metrics"] == {"f1": 0.5} and "items" not in good
    assert any(r.get("error") for r in results if r["file"] == "casse.json")


def test_pages_web_servies_par_l_api():
    r = client.get("/app/")
    assert r.status_code == 200 and "NewsCheck" in r.text
    assert client.get("/app/assets/app.js").status_code == 200
