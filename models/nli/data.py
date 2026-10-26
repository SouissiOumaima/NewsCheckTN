"""Lot C — Model 2 : préparation du corpus NLI du Lot A1 et test gelé.

Étapes :
  1. lecture des paires (affirmation, preuve, label) ;
  2. paires en attente de validation mises de côté (« Brouillon non valide » dans la remarque,
     ou statut explicite autre que validé) ;
  3. `article_id` : champ fourni, sinon déduit de l'identifiant de preuve ou de l'URL ;
  4. regroupement : deux articles qui partagent un même texte (affirmation ou preuve) forment un
     seul groupe, pour qu'aucun texte ne soit à la fois en entraînement et en test ;
  5. test gelé : TOUS les groupes qui touchent les articles du jeu de test du Lot D (voir
     LOT_D_TEST_ARTICLES), complétés au hasard (graine fixe) jusqu'à TEST_SHARE des paires ;
     validation : VAL_SHARE du reste ; entraînement : le reste ;
  6. contrôle de fuite, puis écriture des identifiants (versionnables) et des fichiers de
     paires (privés, dans data/interim/, non versionné).

    python -m models.nli.data --version v3 \
        --input data/interim/lot_c/nli/nli_corpus_300_consolide_v3_prive.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "interim" / "lot_c" / "nli"
SPLITS_DIR = ROOT / "data" / "splits"

LABELS = ("supports", "refutes", "neutral")
# Articles Tunifact du jeu de test du Lot D (EXP-D-006) : jamais en entraînement.
LOT_D_TEST_ARTICLES = frozenset(f"tunifact-{n}" for n in (613, 698, 797, 890, 933, 937))
TEST_SHARE = 0.20
VAL_SHARE = 0.15
SEED = 42

_DRAFT = re.compile(r"brouillon|non[ _-]?valid", re.IGNORECASE)
# La remarque garde l'historique : « …non_validee… ; validation_humaine_A1_confirmee » = validée.
_CONFIRMED = re.compile(r"valid\w*_confirm|confirm\w*_valid", re.IGNORECASE)
_TUNIFACT_ID = re.compile(r"tunifact-(\d+)", re.IGNORECASE)
_TUNIFACT_URL = re.compile(r"tunifact\.org/articles/(\d+)")
_URL = re.compile(r"https?://[^\s|;]+")


def load_pairs(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def is_draft(pair: dict) -> bool:
    """Vrai si la paire n'est pas (encore) validée par un humain."""
    status = str(pair.get("statut") or pair.get("status") or "").lower()
    if status:
        return not status.startswith("valid")
    remark = pair.get("remarque") or ""
    return bool(_DRAFT.search(remark)) and not _CONFIRMED.search(remark)


def article_id(pair: dict) -> str:
    """Article d'origine de la preuve : champ `article_id`, sinon déduit."""
    if pair.get("article_id"):
        return str(pair["article_id"]).lower()
    m = _TUNIFACT_ID.search(pair.get("evidence_id", "")) or _TUNIFACT_URL.search(
        pair.get("remarque") or ""
    )
    if m:
        return f"tunifact-{int(m.group(1))}"
    url = _URL.search(pair.get("remarque") or "")
    if url:
        return url.group(0).rstrip("/").lower()
    return f"inconnu:{pair.get('evidence_id', pair.get('pair_id'))}"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def groups(pairs: list[dict]) -> dict[str, str]:
    """Article → groupe : union des articles reliés par un texte commun."""
    parent: dict[str, str] = {}

    def find(a: str) -> str:
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    seen: dict[str, str] = {}
    for p in pairs:
        art = p["article_id"]
        find(art)
        for key in ("c:" + _norm(p["claim"]), "e:" + _norm(p["evidence"])):
            if key in seen:
                parent[find(art)] = find(seen[key])
            else:
                seen[key] = art
    return {a: find(a) for a in parent}


def split(pairs: list[dict], seed: int = SEED) -> dict[str, list[dict]]:
    """Découpe train / val / test par groupe d'articles (voir l'en-tête du module)."""
    grp = groups(pairs)
    by_group: dict[str, list[dict]] = {}
    for p in pairs:
        by_group.setdefault(grp[p["article_id"]], []).append(p)

    forced = sorted({grp[a] for a in grp if a in LOT_D_TEST_ARTICLES})
    others = sorted(g for g in by_group if g not in forced)
    random.Random(seed).shuffle(others)

    test_groups, n_test = list(forced), sum(len(by_group[g]) for g in forced)
    target_test = TEST_SHARE * len(pairs)
    while others and n_test < target_test:
        g = others.pop()
        test_groups.append(g)
        n_test += len(by_group[g])

    val_groups, n_val = [], 0
    target_val = VAL_SHARE * (len(pairs) - n_test)
    while others and n_val < target_val:
        g = others.pop()
        val_groups.append(g)
        n_val += len(by_group[g])

    def gather(gs: list[str]) -> list[dict]:
        return sorted((p for g in gs for p in by_group[g]), key=lambda p: p["pair_id"])

    return {"train": gather(others), "val": gather(val_groups), "test": gather(test_groups)}


def check_no_leak(splits: dict[str, list[dict]]) -> None:
    """Lève une erreur si un texte (affirmation ou preuve) est partagé entre deux parties."""
    owner: dict[str, str] = {}
    for name, rows in splits.items():
        for p in rows:
            for key in ("c:" + _norm(p["claim"]), "e:" + _norm(p["evidence"])):
                if owner.setdefault(key, name) != name:
                    raise ValueError(
                        f"fuite : {p['pair_id']} partage un texte entre {owner[key]} et {name}"
                    )
    train_articles = {p["article_id"] for p in splits["train"] + splits["val"]}
    leaked = train_articles & LOT_D_TEST_ARTICLES
    if leaked:
        raise ValueError(f"articles du test du Lot D hors du test : {sorted(leaked)}")


def stats(rows: list[dict]) -> dict:
    return {
        "n": len(rows),
        "labels": dict(Counter(p["label"] for p in rows)),
        "claim_lang": dict(Counter(p.get("claim_lang", "?") for p in rows)),
        "articles": len({p["article_id"] for p in rows}),
        "lot_d_test_pairs": sum(p["article_id"] in LOT_D_TEST_ARTICLES for p in rows),
    }


def prepare(
    input_path: Path,
    version: str,
    seed: int = SEED,
    out_dir: Path = OUT_DIR,
    splits_dir: Path = SPLITS_DIR,
) -> dict:
    pairs = load_pairs(input_path)
    bad = [p.get("pair_id") for p in pairs if p.get("label") not in LABELS]
    if bad:
        raise ValueError(f"labels inconnus : {bad[:10]}")
    drafts = [p for p in pairs if is_draft(p)]
    kept = [p for p in pairs if not is_draft(p)]
    for p in kept:
        p["article_id"] = article_id(p)

    parts = split(kept, seed)
    check_no_leak(parts)

    out_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in parts.items():
        with open(out_dir / f"nli_{version}_{name}.jsonl", "w", encoding="utf-8") as f:
            for p in rows:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

    manifest = {
        "corpus": input_path.name,
        "version": version,
        "seed": seed,
        "rule": "découpage par groupe d'articles ; test = articles du test du Lot D + tirage",
        "lot_d_test_articles": sorted(LOT_D_TEST_ARTICLES),
        "excluded_drafts": sorted(p["pair_id"] for p in drafts),
        **{name: [p["pair_id"] for p in rows] for name, rows in parts.items()},
        "stats": {name: stats(rows) for name, rows in parts.items()},
    }
    splits_dir.mkdir(parents=True, exist_ok=True)
    with open(splits_dir / f"nli_{version}_by_article_seed{seed}.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--version", required=True, help="ex. v3, v4 (nom des fichiers produits)")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    m = prepare(args.input, args.version, args.seed)
    print(f"{len(m['excluded_drafts'])} paires en attente de validation mises de côté")
    for name in ("train", "val", "test"):
        s = m["stats"][name]
        print(
            f"{name:5} {s['n']:4} paires, {s['articles']:3} articles, labels {s['labels']}, "
            f"langues {s['claim_lang']}, paires des articles du Lot D : {s['lot_d_test_pairs']}"
        )
    print(
        "aucune fuite entre les parties ; identifiants dans data/splits/, paires dans data/interim/"
    )


if __name__ == "__main__":
    main()
