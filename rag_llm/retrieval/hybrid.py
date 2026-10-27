"""Lot D — Retrieval : BM25, dense, ou hybride (fusion RRF). Re-ranking en S5.

Méthode choisie par `RETRIEVAL_METHOD` dans `.env` : `bm25` (défaut) | `dense` | `hybrid`.
Le défaut reste `bm25` pour que l'API et la CI fonctionnent sans télécharger de modèle.

Hybride = Reciprocal Rank Fusion (Cormack et al., 2009) :
    score(d) = Σ_méthodes 1 / (RRF_K + rang_méthode(d))
Elle combine des classements sans avoir à comparer des scores d'échelles différentes
(BM25 non borné, cosinus entre -1 et 1). Un passage retrouvé par les deux méthodes remonte ;
un passage retrouvé par une seule (ex. preuve arabe d'une affirmation française, que seul le
dense trouve) reste dans la liste.

Pertinence minimale (utilisée par le verdict pour la règle d'abstention A2) :
- bm25   : score BM25 ≥ MIN_BM25_SCORE (EXP-D-001) ;
- dense  : cosinus ≥ MIN_DENSE_SIMILARITY ;
- hybrid : le filtrage est fait AVANT la fusion (passages BM25 de score nul et passages denses
  sous MIN_DENSE_SIMILARITY écartés) ; tout passage fusionné est donc jugé pertinent.
TODO(Lot D): calibrer MIN_DENSE_SIMILARITY sur le corpus réel (EXP-D-003).
"""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path

from common.schemas import Claim, Evidence
from rag_llm.retrieval.bm25 import BM25Index
from rag_llm.retrieval.dense import DenseIndex, Encoder, SentenceTransformerEncoder

ROOT = Path(__file__).resolve().parents[2]
METHODS = ("bm25", "dense", "hybrid")
RRF_K = 60
CANDIDATES = 20  # nombre de candidats demandés à chaque méthode avant fusion
MIN_BM25_SCORE = 1.0
MIN_DENSE_SIMILARITY = float(os.getenv("MIN_DENSE_SIMILARITY", "0.4"))

_bm25_cache: dict = {"key": None, "index": None}
_dense_cache: dict = {"key": None, "index": None}
_encoder: Encoder | None = None


def get_method() -> str:
    method = os.getenv("RETRIEVAL_METHOD", "bm25").lower()
    if method not in METHODS:
        raise ValueError(f"RETRIEVAL_METHOD={method!r} inconnu (attendu : {METHODS})")
    return method


def set_encoder(encoder: Encoder | None) -> None:
    """Remplace l'encodeur dense (tests, ou autre modèle). None = modèle de `.env`."""
    global _encoder
    _encoder = encoder
    _dense_cache.update(key=None, index=None)


def _corpus_key(corpus: list[Evidence]) -> tuple:
    return tuple((ev.doc_id, len(ev.text)) for ev in corpus)


def _get_bm25(corpus: list[Evidence]) -> BM25Index:
    key = _corpus_key(corpus)
    if _bm25_cache["key"] != key:
        _bm25_cache.update(key=key, index=BM25Index(corpus))
    return _bm25_cache["index"]


def _get_dense(corpus: list[Evidence]) -> DenseIndex:
    global _encoder
    if _encoder is None:
        _encoder = SentenceTransformerEncoder()
    key = (_encoder.name, _corpus_key(corpus))
    if _dense_cache["key"] != key:
        cache_dir = Path(os.getenv("INDEX_DIR", "rag_llm/index"))
        if not cache_dir.is_absolute():
            cache_dir = ROOT / cache_dir
        _dense_cache.update(key=key, index=DenseIndex(corpus, _encoder, cache_dir=cache_dir))
    return _dense_cache["index"]


def min_relevance_score(method: str | None = None) -> float:
    """Score minimal pour qu'une preuve soit jugée pertinente (règle d'abstention A2)."""
    method = method or get_method()
    return {"bm25": MIN_BM25_SCORE, "dense": MIN_DENSE_SIMILARITY, "hybrid": 0.0}[method]


def rrf_fuse(rankings: list[list[Evidence]], k: int, rrf_k: int = RRF_K) -> list[Evidence]:
    """Fusionne plusieurs classements par Reciprocal Rank Fusion ; `score` = score RRF."""
    scores: dict[str, float] = {}
    by_id: dict[str, Evidence] = {}
    for ranking in rankings:
        for rank, ev in enumerate(ranking, start=1):
            scores[ev.doc_id] = scores.get(ev.doc_id, 0.0) + 1.0 / (rrf_k + rank)
            by_id.setdefault(ev.doc_id, ev)
    ordered = sorted(scores, key=lambda d: -scores[d])[:k]
    return [replace(by_id[d], score=round(scores[d], 5)) for d in ordered]


def retrieve(
    claim: Claim, corpus: list[Evidence], k: int = 5, method: str | None = None
) -> list[Evidence]:
    """Retourne les k passages les plus pertinents, triés par score décroissant.

    `method` (optionnel, pour l'évaluation) remplace `RETRIEVAL_METHOD`.
    """
    if not corpus or k <= 0:
        return []
    method = method or get_method()
    query = claim.text
    if method == "bm25":
        return _get_bm25(corpus).search(query, k=k)
    if method == "dense":
        return _get_dense(corpus).search(query, k=k, min_similarity=MIN_DENSE_SIMILARITY)
    n = max(k, CANDIDATES)
    lexical = _get_bm25(corpus).search(query, k=n)
    semantic = _get_dense(corpus).search(query, k=n, min_similarity=MIN_DENSE_SIMILARITY)
    return rrf_fuse([lexical, semantic], k=k)
