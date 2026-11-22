"""Lot A2 — Gold, EXP-A2-020 : tirage de la presse neuve (fausses alertes, critère 3).

Protocole : docs/lot-a2_protocole_gold.md, §9. Règle fixée avant tout téléchargement :
- corpus Leipzig `ara_news` de l'année la plus récente disponible, différente de 2022 (réglage
  Silver), en version 10K (`ara_news_<année>_10K`) ;
- tirage de 300 phrases avec la graine 42 ;
- année, URL, SHA-256 de l'archive et de l'échantillon consignés dans EXP-A2-020 avant la mesure ;
- aucune année autre que 2022 disponible : critère « fausses alertes » non mesuré.

Usage (lancé par le responsable du lot, depuis la racine du dépôt) :
    python -X utf8 -m normalization.gold_presse annee                     # en-têtes HTTP seulement
    python -X utf8 -m normalization.gold_presse tirer --out-dir <hors dépôt>   # télécharge et tire

Aucune option d'année, de taille ni de graine. Aucun texte affiché : effectifs et empreintes.
"""

from __future__ import annotations

import argparse
import random
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import date
from pathlib import Path

from normalization.gold_common import (
    RefusGold,
    check_out_dir,
    git_state,
    safe_main,
    sha256_file,
    sha256_texts,
    write_json,
)
from normalization.silver_tuning import read_leipzig_sentences

URL_PATTERN = "https://downloads.wortschatz-leipzig.de/corpora/ara_news_{year}_10K.tar.gz"
EXCLUDED_YEAR = 2022  # a servi au réglage Silver (EXP-A2-013)
OLDEST_YEAR = 2000  # on ne remonte pas plus loin
SAMPLE_SIZE = 300
SAMPLE_SEED = 42
TIMEOUT = 30  # secondes


def url_for(year: int) -> str:
    return URL_PATTERN.format(year=year)


def http_head(url: str) -> bool:
    """Vrai si le serveur annonce le fichier (en-têtes seulement, rien n'est téléchargé)."""
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def most_recent_year(head: Callable[[str], bool] = http_head,
                     newest: int | None = None) -> int | None:
    """Année la plus récente disponible, 2022 exclue ; None si aucune."""
    newest = newest or date.today().year
    for year in range(newest, OLDEST_YEAR - 1, -1):
        if year != EXCLUDED_YEAR and head(url_for(year)):
            return year
    return None


def download(url: str, target: Path) -> None:
    """Télécharge l'archive (jamais lancé par les tests)."""
    with urllib.request.urlopen(url, timeout=TIMEOUT) as response, target.open("wb") as handle:
        while chunk := response.read(1 << 20):
            handle.write(chunk)


def draw_sample(archive: Path, out_dir: Path, year: int) -> dict:
    """Tire 300 phrases (graine 42) de l'archive ; écrit l'échantillon ; refuse de le retirer."""
    sample_path = out_dir / f"presse_ara_news_{year}_10K_300.txt"
    if sample_path.exists():
        raise RefusGold(f"échantillon déjà tiré ({sample_path}) : un tirage ne se refait pas")
    sentences = read_leipzig_sentences(archive)
    if len(sentences) < SAMPLE_SIZE:
        raise RefusGold(f"archive trop petite : {len(sentences)} phrases pour {SAMPLE_SIZE}")
    sample = random.Random(SAMPLE_SEED).sample(sentences, SAMPLE_SIZE)
    broken = sum(len(s.splitlines()) != 1 for s in sample)  # séparateur de ligne caché
    if broken:
        raise RefusGold(f"{broken} phrases tirées contiennent un séparateur de ligne ou sont vides")
    with sample_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("".join(f"{s}\n" for s in sample))
    return {"annee": year, "url": url_for(year), "archive": archive.name,
            "sha256_archive": sha256_file(archive), "phrases_archive": len(sentences),
            "chemin": str(sample_path), "n": SAMPLE_SIZE, "graine": SAMPLE_SEED,
            "sha256": sha256_file(sample_path), "sha256_liste": sha256_texts(sample)}


def command_year() -> None:
    year = most_recent_year()
    if year is None:
        print("aucune année ≠ 2022 disponible : critère « fausses alertes » non mesuré (§9)")
        return
    print(f"année retenue : {year} ; URL : {url_for(year)}")


def command_draw(out_dir: Path) -> None:
    year = most_recent_year()
    if year is None:
        print("aucune année ≠ 2022 disponible : critère « fausses alertes » non mesuré (§9)")
        write_json(out_dir, "lot-a2_gold_presse", {"experience": "EXP-A2-020",
                                                   "statut": "non mesuré"})
        return
    archive = out_dir / f"ara_news_{year}_10K.tar.gz"
    if not archive.exists():
        download(url_for(year), archive)
    result = draw_sample(archive, out_dir, year)
    print(f"année {result['annee']} ; URL {result['url']}")
    print(f"archive : {result['phrases_archive']} phrases ; SHA-256 {result['sha256_archive']}")
    print(f"échantillon : {result['n']} phrases (graine {result['graine']}) ;"
          f" SHA-256 {result['sha256']}")
    payload = {"experience": "EXP-A2-020", "protocole": "docs/lot-a2_protocole_gold.md §9",
               "code": git_state(), "statut": "tiré", **result}
    print(f"JSON : {write_json(out_dir, 'lot-a2_gold_presse', payload)}")


def run(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="commande", required=True)
    commands.add_parser("annee", help="année retenue (en-têtes HTTP seulement)")
    draw = commands.add_parser("tirer", help="télécharge l'archive et tire 300 phrases")
    draw.add_argument("--out-dir", type=Path, required=True,
                      help="dossier de sortie HORS du dépôt (obligatoire)")
    args = parser.parse_args(argv)
    if args.commande == "annee":
        command_year()
    else:
        command_draw(check_out_dir(args.out_dir))


def main() -> None:
    safe_main(run)


if __name__ == "__main__":
    main()
