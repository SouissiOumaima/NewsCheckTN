"""Lot E — Métriques d'évaluation communes (utilisées par tous les lots)."""

from __future__ import annotations


def precision_recall_f1(y_true: list[str], y_pred: list[str], positive: str) -> dict[str, float]:
    tp = sum(t == positive and p == positive for t, p in zip(y_true, y_pred, strict=True))
    fp = sum(t != positive and p == positive for t, p in zip(y_true, y_pred, strict=True))
    fn = sum(t == positive and p != positive for t, p in zip(y_true, y_pred, strict=True))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def macro_f1(y_true: list[str], y_pred: list[str]) -> float:
    labels = sorted(set(y_true) | set(y_pred))
    if not labels:
        return 0.0
    return sum(precision_recall_f1(y_true, y_pred, lab)["f1"] for lab in labels) / len(labels)


def recall_at_k(relevant: list[set[str]], retrieved: list[list[str]], k: int) -> float:
    """Recall@k pour le retrieval (Lot D)."""
    if not relevant:
        return 0.0
    pairs = zip(relevant, retrieved, strict=True)
    hits = [len(rel & set(ret[:k])) / len(rel) for rel, ret in pairs if rel]
    return sum(hits) / len(hits) if hits else 0.0


# TODO(Lot E + Lot D): grille de fidélité (citations valides, absence d'hallucination),
#                      taux d'abstention, calibration (ECE).
