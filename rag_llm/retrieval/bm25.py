"""Lot D — Recherche lexicale BM25 (Okapi), sans dépendance externe.

Implémentation en Python pur pour que la CI (qui n'installe que `requirements-dev.txt`)
puisse tester le retrieval. IDF au format Lucene, toujours positif :
    idf(t) = ln(1 + (N - df + 0.5) / (df + 0.5))
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Callable
from dataclasses import replace

from common.schemas import Evidence
from rag_llm.retrieval.text import tokenize


class BM25Index:
    """Index BM25 construit une fois sur le corpus de preuves."""

    def __init__(
        self,
        corpus: list[Evidence],
        k1: float = 1.5,
        b: float = 0.75,
        tokenizer: Callable[[str], list[str]] = tokenize,
    ) -> None:
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.tokenizer = tokenizer
        docs = [tokenizer(ev.text) for ev in corpus]
        self._tf = [Counter(d) for d in docs]
        self._len = [len(d) for d in docs]
        self._avgdl = sum(self._len) / len(docs) if docs else 0.0
        df = Counter(term for tf in self._tf for term in tf)
        n = len(docs)
        self._idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: str) -> list[float]:
        """Score BM25 de chaque passage du corpus pour la requête."""
        terms = [t for t in self.tokenizer(query) if t in self._idf]
        out = [0.0] * len(self.corpus)
        if not terms or not self._avgdl:
            return out
        for i, tf in enumerate(self._tf):
            norm = self.k1 * (1 - self.b + self.b * self._len[i] / self._avgdl)
            for t in terms:
                f = tf.get(t)
                if f:
                    out[i] += self._idf[t] * f * (self.k1 + 1) / (f + norm)
        return out

    def search(self, query: str, k: int = 5) -> list[Evidence]:
        """Top-k passages (score > 0), triés par score décroissant, champ `score` rempli.

        Les passages sans aucun terme commun sont exclus : les garder donnerait un ordre
        arbitraire et gonflerait artificiellement le Recall sur un petit corpus.
        """
        scores = self.scores(query)
        ranked = sorted((i for i, s in enumerate(scores) if s > 0), key=lambda i: -scores[i])
        return [replace(self.corpus[i], score=scores[i]) for i in ranked[:k]]
