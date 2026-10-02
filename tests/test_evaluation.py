"""Tests Lot E — métriques."""

from evaluation.metrics import macro_f1, precision_recall_f1, recall_at_k


def test_perfect_prediction():
    y = ["vrai", "faux", "vrai"]
    assert precision_recall_f1(y, y, "vrai")["f1"] == 1.0
    assert macro_f1(y, y) == 1.0


def test_recall_at_k():
    assert recall_at_k([{"a", "b"}], [["a", "c", "b"]], k=2) == 0.5
