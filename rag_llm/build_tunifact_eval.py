"""Lot D — Corpus de preuves RÉEL v0, construit à partir des données du Lot A1.

Source : phrases Tunifact (5 articles de fact-checking, FR et AR) et phrases TArC (forum
tunisien) préparées par le Lot A1 (branche `lot-a1-data`, commit 19976a4) :
    data/annotations/tunifact_review_30.jsonl
    data/annotations/tarc_review_30.jsonl

Construction :
- preuves  = phrases Tunifact SAUF la 1re de chaque article (`-001`), qui reformule la rumeur
  elle-même et non une preuve ;
- bruit    = 30 phrases TArC (tunisien, sans rapport avec les 5 articles) : distracteurs réalistes ;
- `doc_id` = identifiant de PHRASE du Lot A1 (ex. `tunifact-698-006`).

Les affirmations à vérifier et leurs preuves attendues sont dans
`tests/fixtures/rag_llm/claims_tunifact_v0.jsonl` (rédigées par le Lot D).

Droits : la redistribution des textes Tunifact n'est pas confirmée (Data Card A1, § 9).
Le corpus construit est donc écrit dans `data/interim/` (non versionné) et n'est pas recopié
dans le dépôt. Une partie des phrases Tunifact (articles 613, 797, 890) sont des reformulations
du Lot A1, pas des citations originales (`text_origin`).

Usage (depuis la racine du dépôt) :
    python -m rag_llm.build_tunifact_eval
Les fichiers sont lus dans `data/annotations/` s'ils existent, sinon directement sur la branche
`origin/lot-a1-data` (`git show`), sans modifier la branche courante.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "origin/lot-a1-data"
TUNIFACT = "data/annotations/tunifact_review_30.jsonl"
TARC = "data/annotations/tarc_review_30.jsonl"
OUT = ROOT / "data" / "interim" / "lot_d" / "evidence_tunifact_v0.jsonl"


def read_jsonl(rel_path: str, branch: str = BRANCH, source_dir: Path = ROOT) -> list[dict]:
    """Lit un JSONL du Lot A1 : fichier local s'il existe, sinon `git show <branche>:<chemin>`."""
    local = source_dir / rel_path
    if local.exists():
        text = local.read_text(encoding="utf-8")
    else:
        result = subprocess.run(
            ["git", "show", f"{branch}:{rel_path}"],
            cwd=ROOT, capture_output=True, check=False,
        )
        if result.returncode != 0:
            raise FileNotFoundError(
                f"{rel_path} introuvable localement et sur {branch}. "
                "Lancer d'abord : git fetch origin"
            )
        text = result.stdout.decode("utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def build_corpus(tunifact: list[dict], tarc: list[dict]) -> list[dict]:
    """Assemble le corpus au format de `data/loaders.py`."""
    corpus = []
    for row in tunifact:
        if row["id"].endswith("-001"):
            continue  # la rumeur elle-même, pas une preuve
        corpus.append({
            "doc_id": row["id"],
            "text": row["text"],
            "source": row.get("source", "Tunifact"),
            "url": row.get("url"),
            "date": row.get("date"),
            "lang": row.get("lang"),
        })
    for row in tarc:
        corpus.append({
            "doc_id": row["id"],
            "text": row["text"],
            "source": row.get("source", "TArC"),
            "url": row.get("url"),
            "date": row.get("date"),
            "lang": row.get("lang"),
        })
    return corpus


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--branch", default=BRANCH)
    p.add_argument("--source-dir", type=Path, default=ROOT)
    p.add_argument("--out", type=Path, default=OUT)
    args = p.parse_args()

    tunifact = read_jsonl(TUNIFACT, args.branch, args.source_dir)
    tarc = read_jsonl(TARC, args.branch, args.source_dir)
    corpus = build_corpus(tunifact, tarc)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for row in corpus:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    n_tf = sum(r["doc_id"].startswith("tunifact") for r in corpus)
    print(f"{len(corpus)} passages ({n_tf} Tunifact, {len(corpus) - n_tf} TArC) → {args.out}")


if __name__ == "__main__":
    main()
