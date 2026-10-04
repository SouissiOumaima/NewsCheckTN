"""Lot B — Contrat d'entrée/sortie JSON, pour travailler sans dépendre des autres lots.

Entrée : `asdict(Document)` tel que produit par `normalization.normalize.normalize`.
Sortie : `asdict(Claim)` (contrat du dépôt) ou `asdict(ExtractedClaim)` (sortie détaillée).

Les champs supplémentaires de `ExtractedClaim` (resolved_text, certainty, is_opinion,
confidence, parser, triggers) sont internes au Lot B, en attendant la validation de
l'équipe ; seule la sortie au format `Claim` fait partie du contrat partagé.

Usage en ligne de commande (depuis la racine du dépôt) :
    python -m linguistic_analysis.io_contract entree.jsonl sortie.jsonl [--detailed]
Chaque ligne de sortie correspond à une ligne d'entrée : {"claims": [...]}.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from common.schemas import Claim, Document, Lang
from linguistic_analysis.types import ExtractedClaim

DOCUMENT_KEYS = ("raw_text", "text", "lang", "script")
SCRIPTS = ("arabic", "latin", "arabizi", "mixed")


def document_from_json(data: dict) -> Document:
    """Construit un `Document` à partir d'un dict JSON, en validant clés, types et valeurs."""
    if not isinstance(data, dict):
        raise ValueError(f"Document invalide : objet JSON attendu, reçu {type(data).__name__}")
    missing = [k for k in DOCUMENT_KEYS if k not in data]
    if missing:
        raise ValueError(f"Document invalide, clés manquantes : {missing}")
    not_str = [k for k in DOCUMENT_KEYS if not isinstance(data[k], str)]
    if not_str:
        raise ValueError(f"Document invalide, valeurs non textuelles : {not_str}")
    try:
        lang = Lang(data["lang"])
    except ValueError:
        allowed = [lang.value for lang in Lang]
        raise ValueError(
            f"Document invalide, langue {data['lang']!r} inconnue (attendu : {allowed})"
        ) from None
    if data["script"] not in SCRIPTS:
        raise ValueError(
            f"Document invalide, script {data['script']!r} inconnu (attendu : {list(SCRIPTS)})"
        )
    return Document(raw_text=data["raw_text"], text=data["text"], lang=lang, script=data["script"])


def _to_json(obj) -> dict:
    """asdict + conversion des enums et tuples en types JSON simples."""
    out = asdict(obj)
    for key, value in out.items():
        if isinstance(value, Lang):
            out[key] = value.value
        elif isinstance(value, tuple):
            out[key] = list(value)
    return out


def document_to_json(doc: Document) -> dict:
    return _to_json(doc)


def claims_to_json(claims: list[Claim]) -> list[dict]:
    return [_to_json(c) for c in claims]


def detailed_to_json(claims: list[ExtractedClaim]) -> list[dict]:
    return [_to_json(c) for c in claims]


def read_documents(path: Path) -> list[Document]:
    """Lit un fichier JSONL de documents (une ligne = un `Document`)."""
    docs = []
    with Path(path).open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                docs.append(document_from_json(json.loads(line)))
            except (ValueError, json.JSONDecodeError) as e:
                raise ValueError(f"{path}, ligne {lineno} : {e}") from None
    return docs


def write_jsonl(rows: list[dict], path: Path) -> None:
    with Path(path).open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run(input_path: Path, output_path: Path, detailed: bool = False) -> int:
    """Traite un fichier de documents et écrit les affirmations. Retourne le nombre de documents."""
    from linguistic_analysis.claim_extraction import extract_claims, extract_claims_detailed

    rows = []
    for doc in read_documents(input_path):
        if detailed:
            rows.append({"claims": detailed_to_json(extract_claims_detailed(doc))})
        else:
            rows.append({"claims": claims_to_json(extract_claims(doc))})
    write_jsonl(rows, output_path)
    return len(rows)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Extraction d'affirmations (Lot B) sur un JSONL.")
    parser.add_argument("input", type=Path, help="JSONL de documents (format Document)")
    parser.add_argument("output", type=Path, help="JSONL de sortie")
    parser.add_argument("--detailed", action="store_true", help="sortie détaillée (interne Lot B)")
    args = parser.parse_args(argv)
    n = run(args.input, args.output, detailed=args.detailed)
    print(f"{n} document(s) traité(s) -> {args.output}")


if __name__ == "__main__":
    main()
