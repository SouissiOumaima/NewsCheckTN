"""Lot C — Model 1 : choix du moteur de détection (TF-IDF pour la démo Bronze, XLM-R ensuite)."""

import pytest

from common.schemas import Claim
from models import claim_detector as cd


@pytest.fixture
def clean(monkeypatch):
    cd._load_tfidf.cache_clear()
    cd._load_model.cache_clear()
    yield monkeypatch
    cd._load_tfidf.cache_clear()
    cd._load_model.cache_clear()


def test_tfidf_par_defaut_et_repli_sans_fichier(clean, tmp_path):
    clean.delenv("CLAIM_DETECTOR_BACKEND", raising=False)
    clean.setenv("CLAIM_DETECTOR_TFIDF", str(tmp_path / "absent.joblib"))
    status = cd.model_status()
    assert status["requested"] == "tfidf" and status["backend"] == "heuristic-fallback"
    assert cd.predict_label_and_score("Le PIB a augmenté de 2 %.")[0] == "AFFIRMATION"


def test_xlmr_absent_donne_le_repli(clean, tmp_path):
    clean.setenv("CLAIM_DETECTOR_BACKEND", "xlmr")
    clean.setenv("CLAIM_DETECTOR_CHECKPOINT", str(tmp_path / "absent"))
    status = cd.model_status()
    assert status["requested"] == "xlmr" and status["status"] == "unavailable"


def test_moteur_tfidf_charge(clean, tmp_path):
    pytest.importorskip("sklearn")
    import joblib
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    texts = [
        "Le taux a atteint 16 % en 2025.",
        "Le prix a augmenté de 10 %.",
        "Cette décision est injuste.",
        "Ce choix est honteux.",
        "Est-ce vrai ?",
        "Inchallah ça ira mieux.",
    ]
    labels = ["AFFIRMATION", "AFFIRMATION", "OPINION", "OPINION", "AUTRE", "AUTRE"]
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    ).fit(texts, labels)
    path = tmp_path / "tfidf.joblib"
    joblib.dump(model, path)
    clean.delenv("CLAIM_DETECTOR_BACKEND", raising=False)
    clean.setenv("CLAIM_DETECTOR_TFIDF", str(path))
    assert cd.model_status()["backend"] == "tfidf-char-logreg"
    label, score = cd.predict_label_and_score("Le taux a atteint 16 % en 2025.")
    assert label == "AFFIRMATION" and 0.0 <= score <= 1.0
    # Avec le TF-IDF, l'API garde la classe la plus probable (argmax), comme l'évaluation.
    kept = cd.filter_checkworthy([Claim(text="Le taux a atteint 16 % en 2025.", lang="fr")])
    assert len(kept) == 1
