"""Lot D — Re-ranking des passages par un cross-encoder (EXP-D-020).

Protocole : `docs/lot-d_protocole_reranker_incertitude.md`, section 3.

La recherche hybride (BM25 + e5, fusion RRF) fournit 20 candidats ; un cross-encoder lit chaque
paire (affirmation, passage), donne un score de pertinence, et l'on garde les 5 meilleurs.
Le modèle n'est chargé qu'à la demande (rien n'est téléchargé à l'import, ni dans la CI).
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Protocol

from common.schemas import Claim, Evidence
from rag_llm.retrieval import hybrid

PRIMARY_MODEL = "BAAI/bge-reranker-v2-m3"
FALLBACK_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
CANDIDATES = 20
MAX_LENGTH = 512


class Scorer(Protocol):
    name: str

    def score(self, pairs: list[tuple[str, str]]) -> list[float]: ...


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


class CrossEncoderScorer:
    """Cross-encoder de sentence-transformers, sur le CPU ; scores ramenés entre 0 et 1."""

    def __init__(self, model_name: str = PRIMARY_MODEL, device: str = "cpu"):
        from sentence_transformers import CrossEncoder  # import à la demande

        self.name = model_name
        self._model = CrossEncoder(model_name, max_length=MAX_LENGTH, device=device)

    def score(self, pairs: list[tuple[str, str]]) -> list[float]:
        if not pairs:
            return []
        raw = [float(x) for x in self._model.predict([list(p) for p in pairs])]
        if any(x < 0.0 or x > 1.0 for x in raw):  # logits bruts : sigmoïde (ordre inchangé)
            return [_sigmoid(x) for x in raw]
        return raw


def candidates(claim: Claim, corpus: list[Evidence], n: int = CANDIDATES) -> list[Evidence]:
    """Les n premiers passages de la recherche hybride (même fusion RRF qu'EXP-D-008)."""
    return hybrid.retrieve(claim, corpus, k=n, method="hybrid")


def rerank(claim: Claim, passages: list[Evidence], scorer: Scorer, k: int = 5) -> list[Evidence]:
    """Reclasse les passages par le score du cross-encoder ; `score` = score du re-ranker.

    À score égal, l'ordre de départ (RRF) est conservé.
    """
    if not passages or k <= 0:
        return []
    scores = scorer.score([(claim.text, p.text) for p in passages])
    order = sorted(range(len(passages)), key=lambda i: (-scores[i], i))[:k]
    return [replace(passages[i], score=round(scores[i], 5)) for i in order]
