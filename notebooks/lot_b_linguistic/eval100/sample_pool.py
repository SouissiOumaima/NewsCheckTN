"""Réservoir de phrases candidates pour eval_100 (AraFacts + X-FACT, arabe et français).

Sortie : un fichier JSONL, hors du dépôt, une ligne par phrase, avec SEULEMENT `id`, `text` et
`origin` (`source`, `url`, `date`, `licence`). Aucun label (ni verdict des fact-checkers, ni
annotation), aucune sortie du système. L'annotateur choisit ensuite les phrases, vérifie leur
langue et leur écriture réelles, puis annote selon `docs/lot-b_protocole_eval_100.md`.

Échantillonnage (reproductible) :
- graine fixe (`--seed`, 20261016 par défaut) ; candidats triés par identifiant avant tirage ;
- AraFacts : affirmations textuelles seulement (`claim_type` = 0), versions 2021 et 2024
  fusionnées ;
- textes nettoyés (espaces), sans URL, de 4 à 60 mots ; doublons retirés (texte normalisé,
  AraFacts prioritaire sur X-FACT) ;
- même cible par langue (`--per-lang`), à parts égales entre trois tranches de longueur
  (`LENGTH_BINS`, en mots), tirage alterné entre les tranches ;
- plafond par site source et par langue : `--cap-share` × cible (arrondi au supérieur), jamais
  relâché : un manque est écrit dans le rapport.

Usage :
    python -I sample_pool.py --arafacts-dir <dossier AraFacts> --xfact-file <xfact_ar_fr.tsv> \\
        --out-dir <sortie> [--per-lang 60] [--cap-share 0.4] [--seed 20261016]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import re
import unicodedata
from collections import Counter
from datetime import date, datetime
from pathlib import Path

SEED = 20261016
LENGTH_BINS = ((4, 12), (13, 24), (25, 60))
LICENCES = {
    "arafacts": "CC BY-NC 4.0 (AraFacts, Sheikh Ali et al., WANLP 2021 : citation requise) ; "
                "texte repris du site de vérification d'origine",
    "xfact": "MIT (dépôt X-FACT, Gupta et Srikumar, ACL 2021) ; texte repris du site de "
             "vérification d'origine",
}
ARAFACTS_SITES = {  # noms différents entre les versions 2021 et 2024
    "Misbar": "misbar.com", "Fatabyyano": "fatabyyano.net", "Fatabayyano": "fatabyyano.net",
    "FactuelAFP": "factuel.afp.com/ar", "AFP": "factuel.afp.com/ar", "Verify-sy": "verify-sy.com",
    "Maharat-news": "maharat-news.com", "Maharat_news": "maharat-news.com",
}
ARAFACTS_FILES = ("AraFacts.csv", "AraFacts_2.csv")  # la version 2024 remplace la 2021
_URL = re.compile(r"https?://|www\.", re.IGNORECASE)
_SPACES = re.compile(r"\s+")
_DIACRITICS = re.compile(r"[ً-ْـ]")

csv.field_size_limit(10**9)


def clean(text: str) -> str:
    return _SPACES.sub(" ", (text or "").replace("‏", " ").replace("‎", " ")).strip()


def dedup_key(text: str) -> str:
    text = _DIACRITICS.sub("", unicodedata.normalize("NFKC", text).casefold())
    text = re.sub("[إأآ]", "ا", text).replace("ى", "ي").replace("ة", "ه")
    return re.sub(r"[\W_]+", " ", text).strip()


def iso_date(value: str) -> str | None:
    value = (value or "").strip()
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", value)
    if match:
        return "-".join(match.groups())
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def load_arafacts(folder: Path) -> list[dict]:
    rows: dict[str, dict] = {}
    for name in ARAFACTS_FILES:
        with (folder / name).open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                rows[r["ClaimID"]] = r
    out = []
    for claim_id, r in rows.items():
        if r.get("claim_type", "").strip() != "0":
            continue
        site = ARAFACTS_SITES.get(r["source"].strip(), r["source"].strip())
        out.append({
            "key": f"arafacts:{claim_id}", "lang": "ar", "text": clean(r["claim"]),
            "origin": {"source": f"AraFacts / {site}", "url": r["source_url"].strip() or None,
                       "date": iso_date(r["date"]), "licence": LICENCES["arafacts"]},
            "site": site,
        })
    return out


def load_xfact(path: Path) -> list[dict]:
    out = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\")
        for r in reader:
            site = r["site"].strip()
            text = clean(r["claim"])
            digest = hashlib.sha1(f"{site}|{text}".encode()).hexdigest()[:12]
            out.append({
                "key": f"xfact:{r['language']}:{digest}", "lang": r["language"], "text": text,
                # X-FACT ne fournit pas l'URL de l'article de vérification (seulement des preuves).
                "origin": {"source": f"X-FACT / {site}", "url": None,
                           "date": iso_date(r["reviewDate"]) or iso_date(r["claimDate"]),
                           "licence": LICENCES["xfact"]},
                "site": site,
            })
    return out


def length_bin(text: str) -> int | None:
    words = len(text.split())
    return next((k for k, (lo, hi) in enumerate(LENGTH_BINS) if lo <= words <= hi), None)


def sample_language(kept: list[dict], lang: str, per_lang: int, cap: int, rng: random.Random,
                    report: list[str]) -> list[dict]:
    """Tirage alterné entre les tranches (une phrase par tranche et par tour) : le plafond par
    site est réparti entre les longueurs au lieu d'être épuisé par la première tranche."""
    per_bin = [per_lang // len(LENGTH_BINS)] * len(LENGTH_BINS)
    for k in range(per_lang % len(LENGTH_BINS)):
        per_bin[k] += 1
    buckets = []
    for b in range(len(LENGTH_BINS)):
        bucket = sorted((c for c in kept if c["lang"] == lang and length_bin(c["text"]) == b),
                        key=lambda c: c["key"])
        rng.shuffle(bucket)
        buckets.append(bucket)
    used: Counter = Counter()
    picked: list[list[dict]] = [[] for _ in LENGTH_BINS]
    cursors = [0] * len(LENGTH_BINS)
    progress = True
    while progress:
        progress = False
        for b, bucket in enumerate(buckets):
            if len(picked[b]) == per_bin[b]:
                continue
            while cursors[b] < len(bucket):
                c = bucket[cursors[b]]
                cursors[b] += 1
                if used[c["site"]] < cap:
                    picked[b].append(c)
                    used[c["site"]] += 1
                    progress = True
                    break
    chosen = []
    for b, target in enumerate(per_bin):
        if len(picked[b]) < target:
            report.append(f"MANQUE {lang} tranche {LENGTH_BINS[b]} : {len(picked[b])}/{target} "
                          f"(candidats {len(buckets[b])}, plafond {cap} par site)")
        chosen += picked[b]
    report.append(f"{lang} : {len(chosen)}/{per_lang} ; par site {dict(used)} ; par tranche "
                  f"{dict(Counter(LENGTH_BINS[length_bin(c['text'])] for c in chosen))}")
    return chosen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--arafacts-dir", type=Path, required=True)
    parser.add_argument("--xfact-file", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--per-lang", type=int, default=60)
    parser.add_argument("--cap-share", type=float, default=0.4)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    candidates = load_arafacts(args.arafacts_dir) + load_xfact(args.xfact_file)
    report = [f"Réservoir eval_100 — {date.today().isoformat()} — graine {args.seed}",
              f"Paramètres : {args.per_lang} par langue, plafond {args.cap_share:.0%} par site, "
              f"tranches de longueur {LENGTH_BINS} mots", "",
              f"Candidats bruts : {dict(Counter(c['lang'] for c in candidates))}"]

    kept, seen, dropped = [], set(), Counter()
    for c in sorted(candidates, key=lambda c: (not c["key"].startswith("arafacts"), c["key"])):
        if not c["text"]:
            dropped["vide"] += 1
        elif _URL.search(c["text"]):
            dropped["URL dans le texte"] += 1
        elif length_bin(c["text"]) is None:
            dropped["longueur hors 4-60 mots"] += 1
        elif dedup_key(c["text"]) in seen:
            dropped["doublon"] += 1
        else:
            seen.add(dedup_key(c["text"]))
            kept.append(c)
    report.append(f"Écartés : {dict(dropped)}")
    report.append(f"Candidats retenus : {dict(Counter(c['lang'] for c in kept))}")

    rng = random.Random(args.seed)
    cap = math.ceil(args.cap_share * args.per_lang)
    pool = []
    for lang in sorted({c["lang"] for c in kept}):
        chosen = sample_language(kept, lang, args.per_lang, cap, rng, report)
        for n, c in enumerate(sorted(chosen, key=lambda c: c["key"]), start=1):
            pool.append({"id": f"pool-{lang}-{n:03d}", "text": c["text"], "origin": c["origin"]})

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / "eval100_pool.jsonl"
    with out.open("w", encoding="utf-8", newline="\n") as f:
        for line in pool:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    report += ["", f"Écrit : {out.name} ({len(pool)} phrases) — champs : id, text, origin"]
    (args.out_dir / "eval100_pool_rapport.txt").write_text("\n".join(report) + "\n",
                                                            encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
