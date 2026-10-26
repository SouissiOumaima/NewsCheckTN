"""Lot A1 — Chargement du corpus de preuves.

Format attendu (une ligne JSON par passage) :
{"doc_id": "...", "text": "...", "source": "...", "url": "...",
 "date": "YYYY-MM-DD", "lang": "fr|ar|tn"}
Champs obligatoires : `doc_id` (unique) et `text` (non vide).

Quel fichier est lu :
1. le chemin passé en argument, sinon
2. le chemin de la variable d'environnement EVIDENCE_CORPUS, sinon
3. `data/processed/evidence_corpus.jsonl` (chemin par défaut).
Un chemin **demandé** (1 ou 2) qui n'existe pas, un dossier, un JSON invalide, un `doc_id` absent ou
en double lèvent `CorpusError` avec un message clair (numéro de ligne compris). Seul le chemin par
défaut absent retombe sur un échantillon de 2 passages, avec un avertissement.

La variable EVIDENCE_CORPUS permet de faire tourner l'API sur un corpus non versionné
(ex. `data/interim/lot_d/evidence_tunifact_v1.jsonl`, droits de redistribution non confirmés)
sans le copier dans `data/processed/`.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from common.schemas import Evidence

log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent
DEFAULT_CORPUS = DATA_DIR / "processed" / "evidence_corpus.jsonl"
ENV_VAR = "EVIDENCE_CORPUS"

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


class CorpusError(ValueError):
    """Corpus de preuves demandé mais introuvable ou invalide."""


def _shown(path: Path) -> str:
    try:
        return path.relative_to(DATA_DIR.parent).as_posix()
    except ValueError:
        return str(path)


def corpus_origin(path: Path | None = None) -> dict:
    """Quel corpus serait lu, et d'où vient ce choix (pour l'API et l'interface)."""
    if path is not None:
        return {"path": str(path), "origin": "argument"}
    env = os.getenv(ENV_VAR)
    if env:
        return {"path": env, "origin": ENV_VAR}
    if DEFAULT_CORPUS.exists():
        return {"path": str(DEFAULT_CORPUS), "origin": "défaut"}
    return {
        "path": None,
        "origin": "échantillon",
        "warning": (
            f"Aucun corpus de preuves : {_shown(DEFAULT_CORPUS)} "
            f"est absent et {ENV_VAR} n'est pas définie. Échantillon de {len(_SAMPLE)} passages."
        ),
    }


def _parse(path: Path) -> list[Evidence]:
    corpus, seen = [], set()
    with path.open(encoding="utf-8") as f:
        for n, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CorpusError(f"{path}, ligne {n} : JSON invalide ({exc.msg})") from None
            if not isinstance(row, dict):
                raise CorpusError(f"{path}, ligne {n} : un objet JSON est attendu")
            doc_id, text = row.get("doc_id"), row.get("text")
            if not doc_id or not isinstance(doc_id, str):
                raise CorpusError(f"{path}, ligne {n} : champ « doc_id » manquant")
            if not text or not isinstance(text, str):
                raise CorpusError(f"{path}, ligne {n} : champ « text » manquant ou vide")
            if doc_id in seen:
                raise CorpusError(f"{path}, ligne {n} : doc_id « {doc_id} » en double")
            seen.add(doc_id)
            corpus.append(
                Evidence(
                    doc_id=doc_id,
                    text=text,
                    source=row.get("source", ""),
                    url=row.get("url"),
                    date=row.get("date"),
                )
            )
    if not corpus:
        raise CorpusError(f"{path} : le corpus est vide")
    return corpus


def load_evidence_corpus(path: Path | None = None) -> list[Evidence]:
    """Charge le corpus de preuves (voir l'ordre de choix en tête du module)."""
    info = corpus_origin(path)
    if info["origin"] == "échantillon":
        log.warning(info["warning"])
        return list(_SAMPLE)
    target = Path(info["path"])
    where = f"(source : {info['origin']})"
    if not target.exists():
        raise CorpusError(f"Corpus de preuves introuvable : {target} {where}")
    if not target.is_file():
        raise CorpusError(f"Le corpus de preuves doit être un fichier .jsonl : {target} {where}")
    return _parse(target)
