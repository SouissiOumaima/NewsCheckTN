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


def test_nli_et_verdict_avec_le_backend_fine_tuned(monkeypatch):
    """API et verdict du Lot D passent par le composant Silver (faux modèle, rien à charger)."""
    from models.nli import stance

    def fake_load(name):
        def classify(pairs):
            return [{"entailment": 0.9, "neutral": 0.05, "contradiction": 0.05} for _ in pairs]

        return classify

    monkeypatch.setattr(stance, "_load_zero_shot", fake_load)
    monkeypatch.setenv("NLI_BACKEND", "fine-tuned")
    stance.set_classifier(None)
    try:
        r = client.post("/nli", json={"claim": TEXT, "evidence": TEXT})
        assert r.status_code == 200
        assert r.json()["stance"] == "supports" and r.json()["confidence"] == 0.9
        assert stance.backend_info()["backend"] == "fine-tuned"
        assert client.post("/verdict", json={"claim": TEXT}).status_code == 200
        detail = client.post("/verdict/detail", json={"claim": TEXT, "nli": "lot-c"})
        assert detail.status_code == 200
    finally:
        stance.set_classifier(None)


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


def test_corpus_invalide_donne_une_erreur_claire_et_pas_500(tmp_path, monkeypatch):
    monkeypatch.setenv("EVIDENCE_CORPUS", str(tmp_path / "absent.jsonl"))
    for r in (client.get("/corpus/stats"), client.post("/verdict/detail", json={"claim": TEXT})):
        assert r.status_code == 503
        assert "introuvable" in r.json()["detail"]


def test_corpus_stats_indique_l_origine(tmp_path, monkeypatch):
    path = tmp_path / "corpus.jsonl"
    path.write_text('{"doc_id": "x-1", "text": "passage", "source": "s"}\n', encoding="utf-8")
    monkeypatch.setenv("EVIDENCE_CORPUS", str(path))
    data = client.get("/corpus/stats").json()
    assert data["size"] == 1 and data["origin"] == "EVIDENCE_CORPUS" and "warning" not in data


def test_model_c_summary_distinguishes_silver_results_from_deployment():
    response = client.get("/model-c/model1")
    assert response.status_code == 200
    nli = response.json()["nli"]
    assert nli["status"] == "silver_evaluated"
    evaluation = nli["evaluation"]
    assert evaluation["macro_f1"] == 0.809
    assert sum(row["n"] for row in evaluation["by_lang"].values()) == 56
    assert evaluation["zero_shot_comparison"]["significant"] is False
    assert "tunisienne" in evaluation["limitations"]
    assert "checkpoint" in nli["deployment"]
