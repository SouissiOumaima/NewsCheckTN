"""Model 1 — détection d'affirmations vérifiables.

Le service utilise XLM-R + LoRA entraîné dès que l'adaptateur est présent. La
règle historique reste uniquement un repli afin que l'API démarre aussi sans
PyTorch/Transformers.
"""

from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
import re
from typing import Any

from common.schemas import Claim

LABELS = ("AFFIRMATION", "OPINION", "AUTRE")
THRESHOLD = 0.5
DEFAULT_CHECKPOINT = Path(__file__).resolve().parent / "checkpoints" / "claim_detection_xlmr_lora_seed42"


def _heuristic_score(claim: Claim) -> float:
    """Repli déterministe, seulement si le modèle entraîné est indisponible."""
    score = 0.3
    if re.search(r"\d", claim.text):
        score += 0.4
    if claim.modality == "assertif":
        score += 0.1
    return min(score, 1.0)


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
    checkpoint = _checkpoint_path()
    loaded = _load_model() is not None
    return {
        "backend": "xlm-r-lora" if loaded else "heuristic-fallback",
        "checkpoint": str(checkpoint),
        "status": "loaded" if loaded else "unavailable",
    }


def predict_label_and_score(text: str) -> tuple[str, float]:
    """Retourne le label Model 1 et ``P(AFFIRMATION)`` pour un texte."""
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
    threshold: float = THRESHOLD,
    classification_texts: list[str] | None = None,
) -> list[Claim]:
    """Conserve les ``AFFIRMATION`` assez confiantes.

    ``claims`` reste la sortie normalisée de Lot B, utilisée ensuite par la
    recherche de preuves. Quand elle est fournie, ``classification_texts``
    contient les phrases brutes correspondantes : c'est cette représentation
    qui doit être envoyée à XLM-R, entraîné et évalué en mode ``raw``.
    """
    if classification_texts is not None and len(classification_texts) != len(claims):
        raise ValueError("classification_texts doit avoir un texte par claim")

    kept: list[Claim] = []
    for index, claim in enumerate(claims):
        text = classification_texts[index] if classification_texts is not None else claim.text
        label, score = predict_label_and_score(text)
        claim.checkworthiness = score
        if label == "AFFIRMATION" and score >= threshold:
            kept.append(claim)
    return kept
