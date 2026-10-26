"""Lot A1 — Chargement du corpus de preuves.

Format attendu de data/processed/evidence_corpus.jsonl (une ligne par passage) :
{"doc_id": "...", "text": "...", "source": "...", "url": "...",
 "date": "YYYY-MM-DD", "lang": "fr|ar|tn"}
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from common.schemas import Evidence

DATA_DIR = Path(__file__).resolve().parent
# Chemin modifiable par la variable d'environnement EVIDENCE_CORPUS : permet de faire
# tourner l'API sur un corpus non versionné (ex. data/interim/lot_d/evidence_tunifact_v1.jsonl,
# droits de redistribution non confirmés) sans le copier dans data/processed/.
EVIDENCE_CORPUS = Path(
    os.getenv("EVIDENCE_CORPUS") or DATA_DIR / "processed" / "evidence_corpus.jsonl"
)

# Petit échantillon de démonstration utilisé tant que le vrai corpus n'existe pas.
_SAMPLE = [
    Evidence(
        doc_id="sample-001",
        text=(
            "Selon l'INS, le taux de chômage en Tunisie était de 16,4 % au deuxième trimestre 2023."
        ),
        source="INS (échantillon)",
    ),
    Evidence(
        doc_id="sample-002",
        text="Tunis est la capitale de la Tunisie.",
        source="échantillon",
    ),
]


def load_evidence_corpus(path: Path = EVIDENCE_CORPUS) -> list[Evidence]:
    """Charge le corpus de preuves. Retourne l'échantillon si le fichier est absent."""
    # TODO(Lot A1): remplacer l'échantillon par le corpus réel collecté.
    if not path.exists():
        return list(_SAMPLE)
    corpus = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                corpus.append(
                    Evidence(
                        doc_id=row["doc_id"],
                        text=row["text"],
                        source=row.get("source", ""),
                        url=row.get("url"),
                        date=row.get("date"),
                    )
                )
    return corpus
