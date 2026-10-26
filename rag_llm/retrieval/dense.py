"""Lot D — Recherche dense (« par le sens ») avec un encodeur de phrases multilingue.

Principe : chaque texte est transformé en un vecteur (embedding) ; deux textes de même sens
ont des vecteurs proches, même s'ils n'ont aucun mot en commun ou ne sont pas dans la même
langue. La proximité est mesurée par la similarité cosinus (de -1 à 1).

- `SentenceTransformerEncoder` charge le modèle `EMBEDDING_MODEL` (.env) de façon paresseuse :
  `sentence-transformers` et `torch` ne sont importés qu'au premier encodage, pour que l'API et
  la CI restent légères.
- `DenseIndex` encode le corpus une fois, garde les vecteurs en mémoire et peut les mettre en
  cache sur disque (`INDEX_DIR`, non versionné).
- Le calcul de similarité est en Python pur (pas de numpy/FAISS) : suffisant pour quelques
  milliers de passages. TODO(Lot D): FAISS si le corpus dépasse ~20 000 passages.

Modèles comparés dans EXP-D-003 (notebooks/lot_d_rag/01_m5_dense_retrieval.ipynb) :
- paraphrase-multilingual-MiniLM-L12-v2 : moins bon que BM25, échoue sur le tunisien ;
- intfloat/multilingual-e5-small / -base (préfixes « query: » / « passage: ») : -base = défaut ;
- BAAI/bge-m3 : aussi bon que e5-base, scores mieux étalés, mais 2,3 Go (GPU conseillé).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import replace
from pathlib import Path
from typing import Protocol

from common.schemas import Evidence

# Choix d'après EXP-D-003 : meilleur Recall@5 en hybride, exécutable sur CPU.
DEFAULT_MODEL = "intfloat/multilingual-e5-base"
# Préfixes exigés par certains modèles (requête, passage).
_PREFIXES = {"e5": ("query: ", "passage: ")}


class Encoder(Protocol):
    name: str

    def encode_queries(self, texts: list[str]) -> list[list[float]]: ...

    def encode_passages(self, texts: list[str]) -> list[list[float]]: ...


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm else vec


class SentenceTransformerEncoder:
    """Encodeur sentence-transformers, chargé au premier appel."""

    def __init__(self, model_name: str | None = None, batch_size: int = 32) -> None:
        self.name = model_name or os.getenv("EMBEDDING_MODEL") or DEFAULT_MODEL
        self.batch_size = batch_size
        self._model = None
        key = next((k for k in _PREFIXES if k in self.name.lower()), None)
        self._query_prefix, self._passage_prefix = _PREFIXES.get(key, ("", ""))

    def _encode(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # import paresseux

            self._model = SentenceTransformer(self.name)
        vectors = self._model.encode(
            texts, batch_size=self.batch_size, normalize_embeddings=True, show_progress_bar=False
        )
        return [list(map(float, v)) for v in vectors]

    def encode_queries(self, texts: list[str]) -> list[list[float]]:
        return self._encode([self._query_prefix + t for t in texts])

    def encode_passages(self, texts: list[str]) -> list[list[float]]:
        return self._encode([self._passage_prefix + t for t in texts])


def corpus_fingerprint(corpus: list[Evidence]) -> str:
    h = hashlib.sha1()
    for ev in corpus:
        h.update(ev.doc_id.encode())
        h.update(ev.text.encode())
    return h.hexdigest()[:16]


class DenseIndex:
    """Index dense : vecteurs normalisés du corpus + recherche par similarité cosinus."""

    def __init__(
        self, corpus: list[Evidence], encoder: Encoder, cache_dir: Path | None = None
    ) -> None:
        self.corpus = corpus
        self.encoder = encoder
        self._vectors = self._load_or_encode(cache_dir)

    def _load_or_encode(self, cache_dir: Path | None) -> list[list[float]]:
        cache = None
        if cache_dir is not None:
            safe = self.encoder.name.replace("/", "__")
            cache = cache_dir / f"dense_{safe}_{corpus_fingerprint(self.corpus)}.json"
            if cache.exists():
                return json.loads(cache.read_text(encoding="utf-8"))
        texts = [e.text for e in self.corpus]
        vectors = [_normalize(v) for v in self.encoder.encode_passages(texts)]
        if cache is not None:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(vectors), encoding="utf-8")
        return vectors

    def similarities(self, query: str) -> list[float]:
        q = _normalize(self.encoder.encode_queries([query])[0])
        return [sum(a * b for a, b in zip(q, v, strict=True)) for v in self._vectors]

    def search(self, query: str, k: int = 5, min_similarity: float = -1.0) -> list[Evidence]:
        """Top-k passages de similarité ≥ `min_similarity`, champ `score` = cosinus."""
        sims = self.similarities(query)
        ranked = sorted(
            (i for i, s in enumerate(sims) if s >= min_similarity), key=lambda i: -sims[i]
        )
        return [replace(self.corpus[i], score=round(sims[i], 4)) for i in ranked[:k]]
