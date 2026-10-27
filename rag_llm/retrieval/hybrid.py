"""Recherche de preuves : baseline BM25 du palier Bronze.

Le palier Bronze ne dépend d'aucun encodeur dense ni d'un re-ranker : il
retrouve des passages français avec BM25.  Les étapes Silver pourront ajouter
la recherche dense et une fusion, sans modifier :func:`retrieve`.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import replace
from math import log

from common.schemas import Claim, Evidence


_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
_STOPWORDS_FR = frozenset({
    "a", "ai", "as", "au", "aux", "avec", "ce", "ces", "cet", "cette", "dans",
    "de", "des", "du", "elle", "en", "est", "et", "il", "la", "le", "les", "leur",
    "leurs", "on", "ou", "par", "pour", "que", "qui", "sur", "un", "une",
})
_K1 = 1.5
_B = 0.75


def _tokens(text: str) -> list[str]:
    """Tokenisation minimale et explicable de la baseline française."""
    return [
        token for token in _TOKEN_RE.findall(text.casefold())
        if len(token) > 1 and token not in _STOPWORDS_FR
    ]


def _bm25_scores(query: list[str], documents: list[list[str]]) -> list[float]:
    """Calcule BM25 Okapi, en mémoire, pour un petit corpus de preuves.

    Conserver ce calcul local rend la revue Bronze reproductible et évite que
    le classement dépende d'un service ou d'un modèle entraîné.
    """
    if not query or not documents:
        return [0.0] * len(documents)

    document_frequency = Counter(
        token for document in documents for token in set(document)
    )
    average_length = sum(len(document) for document in documents) / len(documents)
    scores: list[float] = []
    for document in documents:
        frequencies = Counter(document)
        length_norm = 1 - _B + _B * len(document) / max(average_length, 1.0)
        score = 0.0
        for token in set(query):
            frequency = frequencies[token]
            if not frequency:
                continue
            # Formule BM25 Okapi avec IDF lissé, toujours positive.
            idf = log(1 + (len(documents) - document_frequency[token] + 0.5) /
                      (document_frequency[token] + 0.5))
            score += idf * (frequency * (_K1 + 1)) / (frequency + _K1 * length_norm)
        scores.append(score)
    return scores


def retrieve(claim: Claim, corpus: list[Evidence], k: int = 5) -> list[Evidence]:
    """Retourne les *k* preuves BM25 pertinentes, par score décroissant.

    Aucun résultat de score nul n'est retourné : en Bronze, l'absence de
    recouvrement lexical doit conduire au verdict ``preuves_insuffisantes``.
    """
    if k <= 0:
        return []
    scores = _bm25_scores(_tokens(claim.text), [_tokens(item.text) for item in corpus])
    ranked = [
        replace(evidence, score=round(score, 6))
        for evidence, score in zip(corpus, scores)
        if score > 0
    ]
    return sorted(ranked, key=lambda evidence: (-evidence.score, evidence.doc_id))[:k]
