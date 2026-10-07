"""Lot D — Retrieval hybride BM25 + dense, puis re-ranking.

État actuel (S1) : BM25 seul. Le point d'entrée `retrieve` garde la signature du contrat.
"""

from __future__ import annotations

from common.schemas import Claim, Evidence
from rag_llm.retrieval.bm25 import BM25Index

# Cache d'un seul index : le pipeline appelle `retrieve` une fois par affirmation avec le
# même corpus ; on évite de reconstruire l'index BM25 à chaque appel.
_cache: dict[str, object] = {"key": None, "index": None}


def _get_index(corpus: list[Evidence]) -> BM25Index:
    key = tuple((ev.doc_id, len(ev.text)) for ev in corpus)
    if _cache["key"] != key:
        _cache["key"] = key
        _cache["index"] = BM25Index(corpus)
    return _cache["index"]  # type: ignore[return-value]


def retrieve(claim: Claim, corpus: list[Evidence], k: int = 5) -> list[Evidence]:
    """Retourne les k passages les plus pertinents, triés par score décroissant."""
    # TODO(Lot D): S4 dense (sentence-transformers/FAISS), S5 fusion RRF + re-ranking.
    if not corpus or k <= 0:
        return []
    return _get_index(corpus).search(claim.text, k=k)
