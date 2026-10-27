"""Model 1 — détection d'affirmations vérifiables.

Deux moteurs, choisis par la variable d'environnement CLAIM_DETECTOR_BACKEND :

- ``tfidf`` (défaut) : TF-IDF de n-grammes de caractères (3–5) + régression logistique,
  composant classique du palier Bronze, le seul autorisé dans la démo de la revue Bronze.
  Modèle sauvegardé par ``models/baselines/claim_detection_multiclass_tfidf.py --save-model``
  (CLAIM_DETECTOR_TFIDF pour un autre chemin) ;
- ``xlmr`` : XLM-R + LoRA entraîné (CLAIM_DETECTOR_CHECKPOINT pour un autre dossier).

Si le moteur choisi est indisponible (fichier absent, dépendance manquante), la règle
historique sert de repli afin que l'API démarre toujours ; ``model_status()`` le signale.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from common.schemas import Claim

LABELS = ("AFFIRMATION", "OPINION", "AUTRE")
THRESHOLD = 0.5
DEFAULT_CHECKPOINT = (
    Path(__file__).resolve().parent / "checkpoints" / "claim_detection_xlmr_lora_seed42"
)
DEFAULT_TFIDF = (
    Path(__file__).resolve().parent / "checkpoints" / "claim_detection_tfidf_seed42.joblib"
)


def _heuristic_score(claim: Claim) -> float:
    """Repli déterministe, seulement si le modèle entraîné est indisponible."""
    score = 0.3
    if re.search(r"\d", claim.text):
        score += 0.4
    if claim.modality == "assertif":
        score += 0.1
    return min(score, 1.0)


def _backend() -> str:
    return (os.getenv("CLAIM_DETECTOR_BACKEND") or "tfidf").strip().lower()


def _tfidf_path() -> Path:
    configured = os.getenv("CLAIM_DETECTOR_TFIDF")
    return Path(configured) if configured else DEFAULT_TFIDF


@lru_cache(maxsize=1)
def _load_tfidf() -> Any | None:
    """Charge une fois le pipeline TF-IDF + régression logistique, ou ``None`` en repli."""
    path = _tfidf_path()
    if not path.is_file():
        return None
    try:
        import joblib

        model = joblib.load(path)
    except (ImportError, OSError, ValueError, EOFError):
        return None
    return model if hasattr(model, "predict_proba") else None


def _checkpoint_path() -> Path:
    configured = os.getenv("CLAIM_DETECTOR_CHECKPOINT")
    return Path(configured) if configured else DEFAULT_CHECKPOINT


@lru_cache(maxsize=1)
def _load_model() -> tuple[Any, Any] | None:
    """Charge une fois XLM-R + l'adaptateur LoRA, ou retourne ``None`` en repli."""
    checkpoint = _checkpoint_path()
    if not checkpoint.is_dir():
        return None
    try:
        from peft import PeftConfig, PeftModel
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        peft_config = PeftConfig.from_pretrained(str(checkpoint))
        tokenizer = AutoTokenizer.from_pretrained(str(checkpoint))
        base_model = AutoModelForSequenceClassification.from_pretrained(
            peft_config.base_model_name_or_path,
            num_labels=len(LABELS),
            id2label=dict(enumerate(LABELS)),
            label2id={label: index for index, label in enumerate(LABELS)},
        )
        model = PeftModel.from_pretrained(base_model, str(checkpoint))
        model.eval()
        return tokenizer, model
    except (ImportError, OSError, ValueError):
        # Pas de téléchargement implicite ni d'échec de l'API si le modèle est absent.
        return None


def model_status() -> dict[str, str]:
    """État non sensible, utile dans ``/health`` et pour le déploiement."""
    backend = _backend()
    if backend == "xlmr":
        path, loaded, name = _checkpoint_path(), _load_model() is not None, "xlm-r-lora"
    else:
        path, loaded, name = _tfidf_path(), _load_tfidf() is not None, "tfidf-char-logreg"
    return {
        "backend": name if loaded else "heuristic-fallback",
        "requested": backend,
        "checkpoint": str(path),
        "status": "loaded" if loaded else "unavailable",
    }


def predict_label_and_score(text: str) -> tuple[str, float]:
    """Retourne le label Model 1 et ``P(AFFIRMATION)`` pour un texte."""
    if _backend() != "xlmr":
        pipeline = _load_tfidf()
        if pipeline is None:
            return "AFFIRMATION", _heuristic_score(Claim(text=text, lang=None))
        probabilities = pipeline.predict_proba([text])[0]
        classes = list(pipeline.classes_)
        label = classes[max(range(len(classes)), key=lambda i: probabilities[i])]
        return str(label), float(probabilities[classes.index("AFFIRMATION")])

    loaded = _load_model()
    if loaded is None:
        return "AFFIRMATION", _heuristic_score(Claim(text=text, lang=None))

    tokenizer, model = loaded
    import torch

    batch = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
    with torch.no_grad():
        probabilities = torch.softmax(model(**batch).logits, dim=-1)[0].tolist()
    label_index = max(range(len(probabilities)), key=probabilities.__getitem__)
    return LABELS[label_index], float(probabilities[LABELS.index("AFFIRMATION")])


def score_checkworthiness(claim: Claim) -> float:
    """Probabilité Model 1 que la phrase soit une affirmation vérifiable."""
    return predict_label_and_score(claim.text)[1]


def filter_checkworthy(
    claims: list[Claim],
    threshold: float | None = None,
    classification_texts: list[str] | None = None,
) -> list[Claim]:
    """Conserve les ``AFFIRMATION`` assez confiantes.

    Sans ``threshold`` explicite : avec le TF-IDF chargé, on garde la classe la
    plus probable (argmax), comme dans l'évaluation EXP-C-010 ; à trois classes,
    ``P(AFFIRMATION)`` peut gagner sous 0,5. Sinon on applique ``THRESHOLD``.

    ``claims`` reste la sortie normalisée de Lot B, utilisée ensuite par la
    recherche de preuves. Quand elle est fournie, ``classification_texts``
    contient les phrases brutes correspondantes : c'est cette représentation
    qui doit être envoyée à XLM-R, entraîné et évalué en mode ``raw``.
    """
    if classification_texts is not None and len(classification_texts) != len(claims):
        raise ValueError("classification_texts doit avoir un texte par claim")

    if threshold is None:
        tfidf_loaded = _backend() != "xlmr" and _load_tfidf() is not None
        threshold = 0.0 if tfidf_loaded else THRESHOLD

    kept: list[Claim] = []
    for index, claim in enumerate(claims):
        text = classification_texts[index] if classification_texts is not None else claim.text
        label, score = predict_label_and_score(text)
        claim.checkworthiness = score
        if label == "AFFIRMATION" and score >= threshold:
            kept.append(claim)
    return kept
