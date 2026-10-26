"""Lot de double annotation (30 phrases) pour le second annotateur, sans annotation ni système.

Entrées (hors dépôt) :
- réservoir `eval100_pool.jsonl` (affirmations candidates ar / fr, voir `sample_pool.py`) ;
- TSV CheckThat! 2021 arabe (`claim` = 0 : tweets qui ne sont pas des affirmations, voir
  `extract_checkthat.py`) ;
- facultatif (`--an`) : phrases des débats de l'Assemblée nationale (voir `an_sentences.py`).
Sorties dans `--out-dir` :
- `lot_annotation_A1.csv` : id ; texte ; contexte ; label ; modalite (UTF-8 avec BOM, `;`),
  les trois dernières colonnes vides ;
- `lot_annotation_A1_correspondance.jsonl` : id -> origine (fichier de travail, à ne pas
  transmettre à l'annotateur) ;
- `lot_annotation_A1_controle.txt` : composition et contrôle de recouvrement.

Tirage (graine `--seed`, 20261016 par défaut) : 18 affirmations candidates (moitié ar, moitié fr)
et 12 tweets arabes non-affirmations (4 à 60 mots, sans @mention ni URL, dédoublonnés). Avec
`--an`, 6 de ces 12 tweets sont remplacés par 6 phrases de débats tirées au hasard : leur label
est inconnu (rien ne garantit une non-affirmation). Ordre des lignes mélangé, identifiants neutres.
Contrôle : aucune phrase du lot ne doit apparaître dans les fichiers ou dossiers `--repo`
(texte entier ou séquence de 5 mots, après normalisation).

Usage :
    python -I build_batch.py --pool <eval100_pool.jsonl> --checkthat-dir <dossier des TSV> \\
        --out-dir <sortie> [--an <an_phrases.jsonl>] --repo <fichier_ou_dossier>...
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import unicodedata
from pathlib import Path

SEED = 20261016
N_CLAIMS = 18  # 60 %
N_NON_CLAIMS = 12  # 40 %
N_AN = 6  # avec --an : phrases françaises de débats remplaçant 6 tweets arabes
AN_LICENCE = ("Licence Ouverte / Open Licence (Etalab) ; mention de la source et de la date de "
              "mise à jour (téléchargé le {date})")
_DIACRITICS = re.compile(r"[ً-ْـ]")
_URL = re.compile(r"https?://|www\.", re.IGNORECASE)

csv.field_size_limit(10**9)


def norm(text: str) -> str:
    text = _DIACRITICS.sub("", unicodedata.normalize("NFKC", text).casefold())
    text = re.sub("[إأآ]", "ا", text).replace("ى", "ي").replace("ة", "ه")
    return re.sub(r"[\W_]+", " ", text).strip()


def shingles(text: str, n: int = 5) -> set[str]:
    words = norm(text).split()
    return {" ".join(words[k:k + n]) for k in range(len(words) - n + 1)}


def load_tweets(ct_dir: Path) -> list[dict]:
    tweets = []
    for tsv in sorted(ct_dir.glob("*.tsv")):
        with tsv.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
                text = re.sub(r"\s+", " ", r["tweet_text"]).strip()
                if r["claim"] != "0" or "@" in text or _URL.search(text):
                    continue
                if not 4 <= len(text.split()) <= 60:
                    continue
                tweets.append({"tweet_id": r["tweet_id"], "text": text, "file": tsv.name})
    seen, unique = set(), []
    for t in sorted(tweets, key=lambda t: t["tweet_id"]):
        if norm(t["text"]) not in seen:
            seen.add(norm(t["text"]))
            unique.append(t)
    return unique


def overlaps_with_repo(rows: list[dict], repo_paths: list[Path]) -> tuple[int, list]:
    repo_files = []
    for p in repo_paths:
        repo_files += [q for q in p.rglob("*") if q.is_file()] if p.is_dir() else [p]
    repo_text = " ".join(norm(q.read_text(encoding="utf-8", errors="ignore")) for q in repo_files)
    repo_shingles = shingles(repo_text) if repo_text else set()
    found = []
    for row in rows:
        full = norm(row["text"]) in repo_text
        common = shingles(row["text"]) & repo_shingles
        if full or common:
            found.append((row["id"], "texte entier" if full
                          else f"{len(common)} séquence(s) de 5 mots"))
    return len(repo_files), found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--checkthat-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--an", type=Path, help="phrases de débats AN (an_phrases.jsonl)")
    parser.add_argument("--an-download-date", default="2026-10-16")
    parser.add_argument("--repo", type=Path, nargs="+", required=True,
                        help="fichiers ou dossiers du dépôt pour le contrôle de recouvrement")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    pool = [json.loads(line) for line in args.pool.open(encoding="utf-8") if line.strip()]
    claims = []
    for lang in ("ar", "fr"):
        candidates = sorted((p for p in pool if p["id"].startswith(f"pool-{lang}-")),
                            key=lambda p: p["id"])
        claims += rng.sample(candidates, N_CLAIMS // 2)
    unique = load_tweets(args.checkthat_dir)
    non_claims = rng.sample(unique, N_NON_CLAIMS)

    rows = [{"text": c["text"], "origin": c["origin"], "kind": "affirmation_candidate",
             "lang_source": c["id"].split("-")[1], "pool_id": c["id"]} for c in claims]
    tweet_rows = [{"text": t["text"], "kind": "non_affirmation_candidate", "lang_source": "ar",
                   "origin": {"source": "CheckThat! 2021 (CLEF), tâche 1A arabe, claim = 0",
                              "url": None, "tweet_id": t["tweet_id"], "file": t["file"],
                              "licence": "« free for general research use » ; conditions "
                                         "X/Twitter non vérifiées"}}
                  for t in non_claims]
    if args.an is None:
        rows += tweet_rows
    else:
        rng_replace = random.Random(args.seed)
        rows += rng_replace.sample(tweet_rows, N_NON_CLAIMS - N_AN)
        an_rows = sorted((json.loads(line) for line in args.an.open(encoding="utf-8")
                          if line.strip()), key=lambda r: r["key"])
        for r in rng_replace.sample(an_rows, N_AN):
            rows.append({
                "text": r["text"], "kind": "phrase_de_debat_label_inconnu", "lang_source": "fr",
                "origin": {
                    "source": "Assemblée nationale, compte rendu intégral (DILA, jeu « Comptes "
                              "rendus des Débats de l'Assemblée nationale », data.gouv.fr)",
                    "url": f"https://echanges.dila.gouv.fr/OPENDATA/Debats/AN/2025/{r['archive']}",
                    "date": r["date"], "file": r["file"], "key": r["key"],
                    "licence": AN_LICENCE.format(date=args.an_download_date)}})
    rng.shuffle(rows)
    for k, row in enumerate(rows, start=1):
        row["id"] = f"L{k:02d}"

    n_files, overlaps = overlaps_with_repo(rows, args.repo)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows.sort(key=lambda r: r["id"])
    with (args.out_dir / "lot_annotation_A1.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL)
        writer.writerow(["id", "texte", "contexte", "label", "modalite"])
        for row in rows:
            writer.writerow([row["id"], row["text"], "", "", ""])
    with (args.out_dir / "lot_annotation_A1_correspondance.jsonl").open(
        "w", encoding="utf-8", newline="\n"
    ) as f:
        for row in rows:
            entry = {k: row[k] for k in ("id", "kind", "lang_source", "origin")}
            if "pool_id" in row:
                entry["pool_id"] = row["pool_id"]
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def count(kind: str, lang: str | None = None) -> int:
        return sum(r["kind"] == kind and (lang is None or r["lang_source"] == lang) for r in rows)

    report = [
        f"Lot de double annotation — graine {args.seed}",
        f"{len(rows)} phrases : {count('affirmation_candidate')} affirmations candidates "
        f"(ar {count('affirmation_candidate', 'ar')}, fr {count('affirmation_candidate', 'fr')}), "
        f"{count('non_affirmation_candidate')} non-affirmations candidates (ar), "
        f"{count('phrase_de_debat_label_inconnu')} phrases de débat AN (fr, label inconnu)",
        f"Tweets claim = 0 utilisables après filtres : {len(unique)}",
        f"Fichiers du dépôt contrôlés : {n_files}",
        "Recouvrement avec le dépôt : " + ("aucun" if not overlaps else str(overlaps)),
    ]
    (args.out_dir / "lot_annotation_A1_controle.txt").write_text("\n".join(report) + "\n",
                                                                 encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
