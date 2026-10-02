"""Lot D — Retrieval hybride BM25 + dense, puis re-ranking."""

from __future__ import annotations

import re
from dataclasses import replace

from common.schemas import Claim, Evidence


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"\w+", text.lower()) if len(t) > 2}


def retrieve(claim: Claim, corpus: list[Evidence], k: int = 5) -> list[Evidence]:
    """Retourne les k passages les plus pertinents, triés par score décroissant."""
    # TODO(Lot D): BM25 (rank-bm25) + dense (sentence-transformers/FAISS), fusion RRF,
    #              puis re-ranking cross-encoder.
    query = _tokens(claim.text)
    scored = []
    for ev in corpus:
        overlap = len(query & _tokens(ev.text))
        if overlap:
            scored.append(replace(ev, score=overlap / max(len(query), 1)))
    scored.sort(key=lambda e: e.score, reverse=True)
    return scored[:k]
