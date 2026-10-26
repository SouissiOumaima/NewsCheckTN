"""Lot C — Model 2 (NLI) : position d'une preuve par rapport à une affirmation.

Contrat (utilisé par le Lot D et par l'API `/nli`) :
    predict_stance(claim, evidence) -> StanceResult
    predict_stances(claim, evidences) -> list[StanceResult]

Trois moteurs, choisis par la variable d'environnement NLI_BACKEND :
    bronze    (défaut) règles par lexique (`models/nli/bronze.py`) : composant classique du palier
              Bronze, sans dépendance ni modèle à télécharger ; c'est lui que montre la démo ;
    zero-shot modèle NLI multilingue déjà entraîné sur XNLI (mDeBERTa-v3), utilisé tel quel
              (prémisse = preuve, hypothèse = affirmation ; entailment → supports,
              contradiction → refutes) ; NLI_MODEL = autre modèle ou checkpoint affiné du Lot C ;
    stub      toujours « neutre » (tests).

Si torch / transformers ne sont pas installés, ou si le modèle ne se charge pas (pas d'accès
réseau, par exemple), la fonction répond « neutre » avec une confiance 0 : l'API ne tombe pas et
le Lot D s'abstient. `backend_info()` dit quel moteur répond réellement.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Sequence

from common.schemas import Claim, Evidence, Stance, StanceResult

log = logging.getLogger(__name__)

DEFAULT_MODEL = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
MAX_LENGTH = 512
BATCH_SIZE = 16

# Noms de classes possibles dans la configuration des modèles NLI → nos positions.
LABEL_MAP = {
    "entailment": Stance.SUPPORTS,
    "supports": Stance.SUPPORTS,
    "contradiction": Stance.REFUTES,
    "refutes": Stance.REFUTES,
    "neutral": Stance.NEUTRAL,
}

# Un classifieur prend des paires (prémisse, hypothèse) et rend, pour chacune,
# un dictionnaire {nom de classe: probabilité}.
Classifier = Callable[[Sequence[tuple[str, str]]], list[dict[str, float]]]

_classifier: Classifier | None = None
_info: dict[str, str] = {"backend": "non chargé", "model": "", "status": "pending"}


def _model_name() -> str:
    return os.getenv("NLI_MODEL") or DEFAULT_MODEL


def _load_zero_shot(model_name: str) -> Classifier:
    """Charge le tokenizer et le modèle une seule fois (imports paresseux : CI légère)."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.eval()
    id2label = {i: name.lower() for i, name in model.config.id2label.items()}
    unknown = set(id2label.values()) - set(LABEL_MAP)
    if unknown:
        raise ValueError(f"classes NLI inattendues dans {model_name} : {sorted(unknown)}")

    def classify(pairs: Sequence[tuple[str, str]]) -> list[dict[str, float]]:
        out: list[dict[str, float]] = []
        for start in range(0, len(pairs), BATCH_SIZE):
            batch = pairs[start : start + BATCH_SIZE]
            enc = tokenizer(
                [p for p, _ in batch],
                [h for _, h in batch],
                truncation="only_first",  # on coupe la preuve, jamais l'affirmation
                max_length=MAX_LENGTH,
                padding=True,
                return_tensors="pt",
            )
            with torch.no_grad():
                probs = torch.softmax(model(**enc).logits, dim=-1).tolist()
            out.extend({id2label[i]: p for i, p in enumerate(row)} for row in probs)
        return out

    return classify


def _bronze_classifier(pairs: Sequence[tuple[str, str]]) -> list[dict[str, float]]:
    """Règles par lexique (palier Bronze), au même format que les modèles : {classe: score}."""
    from models.nli.bronze import predict

    out = []
    for premise, hypothesis in pairs:
        label, confidence = predict(hypothesis, premise)
        rest = (1.0 - confidence) / 2
        out.append(
            {
                lab: (confidence if lab == label else rest)
                for lab in ("supports", "refutes", "neutral")
            }
        )
    return out


def _get_classifier() -> Classifier | None:
    global _classifier, _info
    if _classifier is not None:
        return _classifier
    backend = os.getenv("NLI_BACKEND") or "bronze"
    if backend == "stub":
        _info = {"backend": "stub", "model": "", "status": "neutre fixe (NLI_BACKEND=stub)"}
        return None
    if backend == "bronze":
        _classifier = _bronze_classifier
        _info = {"backend": "bronze", "model": "regles-lexique", "status": "loaded"}
        return _classifier
    if _info["status"] == "unavailable":
        return None  # échec déjà constaté : on ne retente pas à chaque appel
    name = _model_name()
    try:
        _classifier = _load_zero_shot(name)
        backend = "zero-shot" if name == DEFAULT_MODEL else "fine-tuned"
        _info = {"backend": backend, "model": name, "status": "loaded"}
    except Exception as exc:  # dépendances absentes, pas de réseau, modèle invalide…
        log.warning("NLI : modèle %s indisponible (%s) ; réponse « neutre » par défaut.", name, exc)
        _info = {"backend": "stub", "model": name, "status": "unavailable"}
    return _classifier


def set_classifier(classifier: Classifier | None, name: str = "test") -> None:
    """Remplace le moteur (tests, ou futur modèle fine-tuné chargé autrement)."""
    global _classifier, _info
    _classifier = classifier
    _info = (
        {"backend": "custom", "model": name, "status": "loaded"}
        if classifier
        else {"backend": "non chargé", "model": "", "status": "pending"}
    )


def backend_info() -> dict[str, str]:
    """Moteur réellement utilisé (à afficher dans /health ou sur la page du Lot C)."""
    _get_classifier()
    return dict(_info)


def _to_result(evidence: Evidence, probs: dict[str, float]) -> StanceResult:
    scores: dict[Stance, float] = {}
    for name, p in probs.items():
        stance = LABEL_MAP[name]
        scores[stance] = scores.get(stance, 0.0) + p
    stance = max(scores, key=scores.get)
    return StanceResult(
        evidence=evidence, stance=stance, confidence=round(min(1.0, scores[stance]), 4)
    )


def predict_stances(claim: Claim, evidences: list[Evidence]) -> list[StanceResult]:
    """Position de chaque preuve vis-à-vis de l'affirmation (un seul passage du modèle)."""
    if not evidences:
        return []
    classify = _get_classifier()
    if classify is None:
        return [StanceResult(evidence=e, stance=Stance.NEUTRAL, confidence=0.0) for e in evidences]
    probs = classify([(e.text, claim.text) for e in evidences])
    return [_to_result(e, p) for e, p in zip(evidences, probs, strict=True)]


def predict_stance(claim: Claim, evidence: Evidence) -> StanceResult:
    """Retourne soutient / contredit / neutre avec un score de confiance."""
    return predict_stances(claim, [evidence])[0]
