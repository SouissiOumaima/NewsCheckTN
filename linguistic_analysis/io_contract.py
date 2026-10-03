"""Lot B — Contrat d'entrée/sortie JSON, pour travailler sans dépendre des autres lots.

Entrée : `asdict(Document)` tel que produit par `normalization.normalize.normalize`.
Sortie : `asdict(Claim)` (contrat du dépôt) ou `asdict(ExtractedClaim)` (sortie détaillée).
Les champs supplémentaires de `ExtractedClaim` restent internes au Lot B en attendant
la validation de l'équipe.
"""

from __future__ import annotations

from dataclasses import asdict

from common.schemas import Claim, Document, Lang

DOCUMENT_KEYS = ("raw_text", "text", "lang", "script")


def document_from_json(data: dict) -> Document:
    """Construit un `Document` à partir d'un dict JSON, en validant les clés."""
    missing = [k for k in DOCUMENT_KEYS if k not in data]
    if missing:
        raise ValueError(f"Document invalide, clés manquantes : {missing}")
    return Document(
        raw_text=data["raw_text"], text=data["text"], lang=Lang(data["lang"]), script=data["script"]
    )


def claims_to_json(claims: list[Claim]) -> list[dict]:
    return [asdict(c) for c in claims]


# TODO(Lot B): detailed_to_json + CLI
#              `python -m linguistic_analysis.io_contract entree.jsonl sortie.jsonl`.
