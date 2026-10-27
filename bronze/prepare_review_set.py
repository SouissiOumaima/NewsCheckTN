"""Prépare un lot français à relire depuis les annotations de provenance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = (
    ROOT / "data" / "annotations" / "normalized" / "tunifact_review_30.jsonl",
    ROOT / "data" / "annotations" / "normalized" / "tarc_review_30.jsonl",
)


def load_rows(paths: tuple[Path, ...]) -> list[dict]:
    rows: list[dict] = []
    for path in paths:
        if not path.is_file():
            continue
        with path.open(encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle if line.strip())
    return rows


def build_review_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Retourne corpus candidat et feuille de décision, uniquement pour le FR."""
    french_rows = [row for row in rows if row.get("lang") == "fr"]
    corpus, review = [], []
    for row in french_rows:
        evidence_id = f"bronze-{row['id']}"
        corpus.append({
            "doc_id": evidence_id, "text": row["text"], "source": row.get("source", ""),
            "url": row.get("url"), "date": row.get("date"),
        })
        review.append({
            "id": row["id"], "text": row["text"], "relevant_doc_ids": [evidence_id],
            "gold_label": None, "review_status": "à_annoter",
            "note": "Le label doit être décidé après lecture de la source primaire ou du fact-check.",
        })
    return corpus, review


def write_jsonl(path: Path, rows: list[dict], force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} existe déjà ; utilisez --force seulement pour le régénérer.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Prépare le jeu Bronze FR à annoter.")
    parser.add_argument("--corpus", type=Path, default=ROOT / "data/processed/evidence_corpus_fr_candidates.jsonl")
    parser.add_argument("--review", type=Path, default=ROOT / "data/annotations/bronze_fr_review.jsonl")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    corpus, review = build_review_rows(load_rows(DEFAULT_INPUTS))
    if not review:
        raise RuntimeError("Aucune annotation française de provenance n'a été trouvée.")
    write_jsonl(args.corpus, corpus, args.force)
    write_jsonl(args.review, review, args.force)
    print(json.dumps({"french_candidates": len(review), "corpus": str(args.corpus), "review": str(args.review)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
