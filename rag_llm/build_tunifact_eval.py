"""Lot D — Corpus de preuves RÉEL, construit à partir des données du Lot A1.

Deux versions, gardées toutes les deux pour pouvoir refaire chaque expérience :

v0 (EXP-D-004, EXP-D-005) — branche `lot-a1-data`, commit 19976a4 :
    data/annotations/tunifact_review_30.jsonl   5 articles (698, 613, 797, 890, 937)
    data/annotations/tarc_review_30.jsonl       30 phrases de forum (distracteurs)

v1 (EXP-D-006) — branche `lot-a1-data`, commit 77a00b9 :
    data/exports/lot_d/tunifact_sentences_46.jsonl   articles 698, 933, 937 complets, avec
                                                     `verdict_article` et `date`
    + les articles de v0 absents de cet export (613, 797, 890), repris de tunifact_review_30
    + les 30 phrases TArC (distracteurs)

Règles de construction (les mêmes pour toutes les phrases) :
- la 1re phrase de chaque article est écartée : elle présente la rumeur (ou le message
  d'origine), ce n'est pas une preuve ;
- v1 seulement : les fragments de moins de MIN_CHARS caractères sont écartés (le découpage
  automatique du Lot A1 coupe certaines citations, ex. « أبدا !! ») ;
- `doc_id` = identifiant de PHRASE du Lot A1 : `tunifact-698-006` (v0) ou `tunifact-698-s0006`
  (export v1) ; un même article n'est jamais pris dans les deux formats.

Les affirmations à vérifier sont dans `tests/fixtures/rag_llm/claims_tunifact_v<N>.jsonl`.

Droits : la redistribution des textes Tunifact n'est pas confirmée (Data Card A1, § 9). Le corpus
est écrit dans `data/interim/` (non versionné) et n'est pas recopié dans le dépôt. Les articles
613, 797 et 890 sont des reformulations du Lot A1, pas des citations originales.

Chaque version lit les fichiers du Lot A1 à un commit figé (`PINNED` : v0 → 19976a4,
v1 → 77a00b9), même si la branche `lot-a1-data` a avancé depuis.

Usage (depuis la racine du dépôt, après `git fetch origin`) :
    python -m rag_llm.build_tunifact_eval              # v1 (défaut)
    python -m rag_llm.build_tunifact_eval --version v0
Les fichiers sont lus dans le dépôt s'ils existent, sinon directement sur `origin/lot-a1-data`
(`git show`), sans modifier la branche courante.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "origin/lot-a1-data"
# Version du Lot A1 utilisée par chaque jeu : un commit fixe, pour que le corpus de test reste
# identique même si la branche lot-a1-data avance (test gelé, voir rag_llm/freeze_test.py).
PINNED = {"v0": "19976a4", "v1": "77a00b9"}
TUNIFACT_V0 = "data/annotations/tunifact_review_30.jsonl"
TUNIFACT_EXPORT = "data/exports/lot_d/tunifact_sentences_46.jsonl"
TARC = "data/annotations/tarc_review_30.jsonl"
OUT_DIR = ROOT / "data" / "interim" / "lot_d"
MIN_CHARS = 15

_SENTENCE_ID = re.compile(r"^(?P<article>.+)-s?(?P<n>\d+)$")


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


def sentence_id(row: dict) -> str:
    return row.get("sentence_id") or row["id"]


def article_of(sid: str) -> str:
    """`tunifact-698-006` et `tunifact-698-s0006` → `tunifact-698`."""
    match = _SENTENCE_ID.match(sid)
    return match.group("article") if match else sid


def is_first_sentence(sid: str) -> bool:
    match = _SENTENCE_ID.match(sid)
    return bool(match) and int(match.group("n")) == 1


def to_evidence(row: dict, default_source: str) -> dict:
    return {
        "doc_id": sentence_id(row),
        "text": row["text"],
        "source": row.get("source", default_source),
        "url": row.get("url"),
        "date": row.get("date"),
        "lang": row.get("lang"),
    }


def build_corpus(
    tunifact: list[dict], tarc: list[dict], min_chars: int = 0
) -> list[dict]:
    """Assemble le corpus au format de `data/loaders.py`."""
    corpus = []
    for row in tunifact:
        sid = sentence_id(row)
        if is_first_sentence(sid) or len(row["text"].strip()) < min_chars:
            continue
        corpus.append(to_evidence(row, "Tunifact"))
    corpus += [to_evidence(row, "TArC") for row in tarc]
    return corpus


def merge_tunifact(export: list[dict], older: list[dict]) -> list[dict]:
    """Phrases de l'export v1, plus les articles de l'ancien fichier absents de l'export."""
    exported = {article_of(sentence_id(r)) for r in export}
    return export + [r for r in older if article_of(sentence_id(r)) not in exported]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--version", choices=["v0", "v1"], default="v1")
    p.add_argument("--branch", default=None,
                   help="version du Lot A1 à lire (défaut : le commit figé du jeu, voir PINNED)")
    p.add_argument("--source-dir", type=Path, default=ROOT)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()
    args.branch = args.branch or PINNED[args.version]

    read = lambda path: read_jsonl(path, args.branch, args.source_dir)  # noqa: E731
    older, tarc = read(TUNIFACT_V0), read(TARC)
    if args.version == "v0":
        corpus = build_corpus(older, tarc)
    else:
        corpus = build_corpus(merge_tunifact(read(TUNIFACT_EXPORT), older), tarc, MIN_CHARS)

    out = args.out or OUT_DIR / f"evidence_tunifact_{args.version}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in corpus:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    tunifact_rows = [r for r in corpus if r["doc_id"].startswith("tunifact")]
    articles = sorted({article_of(r["doc_id"]) for r in tunifact_rows})
    print(f"{args.version} : {len(corpus)} passages ({len(tunifact_rows)} Tunifact de "
          f"{len(articles)} articles, {len(corpus) - len(tunifact_rows)} TArC) → {out}")


if __name__ == "__main__":
    main()
