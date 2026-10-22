"""Scraper Tunifact — Lot A1 NewsCheck TN.

Cette première version teste la collecte sur un seul article.
"""

from __future__ import annotations
import json
import time
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


# Attente entre les requêtes pour éviter
# d'envoyer trop de requêtes rapidement.
REQUEST_DELAY = 3.0

# Identification de notre programme.
HEADERS = {
    "User-Agent": "NewsCheckTN-AcademicProject/1.0"
}

# Dossier data/
DATA_DIR = Path(__file__).resolve().parents[1]

# Dossier dans lequel les pages HTML brutes seront conservées.
RAW_DIR = DATA_DIR / "raw" / "tunifact"
# Dossier contenant les données extraites et structurées.
INTERIM_DIR = DATA_DIR / "interim" / "tunifact"

def fetch_page(url: str) -> str:
    """Télécharge le HTML d'une page publique."""

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=20,
    )

    # Signale les erreurs HTTP : 404, 500, etc.
    response.raise_for_status()

    # Pause avant une éventuelle nouvelle requête.
    time.sleep(REQUEST_DELAY)

    return response.text
def extract_doc_id(url: str) -> str:
    """Construit un identifiant unique à partir de l'URL Tunifact."""

    # Exemple :
    # https://tunifact.org/articles/698/...
    #
    # devient :
    # tunifact-698

    path_parts = urlparse(url).path.strip("/").split("/")

    if len(path_parts) >= 2 and path_parts[0] == "articles":
        return f"tunifact-{path_parts[1]}"

    return "tunifact-unknown"


import re


def extract_verdict(soup: BeautifulSoup) -> str | None:
    """Extrait le verdict officiel de l'article Tunifact."""

    # Chercher uniquement dans l'en-tête de l'article principal
    header = soup.select_one("div.entry-header")

    if header is None:
        return None

    verdict_classes = {
        "ar-true": "vrai",
        "ar-false": "faux",
        "ar-warning": "trompeur",
    }

    for css_class, verdict in verdict_classes.items():
        badge = header.select_one(f"span.{css_class}")

        if badge is not None:
            return verdict

    # Verdict non reconnu : vérification manuelle nécessaire
    return None


def extract_date(soup: BeautifulSoup) -> str | None:
    """Extrait la date de publication d'un article Tunifact."""

    # Format de l'article français (698)
    date_element = soup.select_one("span.post-on")

    # Format de l'article arabe (937)
    if date_element is None:
        date_container = soup.select_one("div.entry-meta")

        if date_container:
            date_element = date_container.find("span")

    if date_element is None:
        return None

    date_text = date_element.get_text(" ", strip=True)

    match = re.search(
        r"\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?",
        date_text,
    )

    return match.group(0) if match else None


def parse_article(html: str, url: str) -> dict:
    """Extrait le titre, le texte et la date d'un article Tunifact."""

    soup = BeautifulSoup(html, "html.parser")

    # Récupérer le titre
    title_element = soup.find("h1")

    if title_element:
        title = title_element.get_text(" ", strip=True)
    else:
        title = ""

    # Trouver la zone principale de l'article
    article_container = soup.find(
        "div",
        class_="articles-height",
    )

    paragraphs = []

    if article_container:

        # Trouver le conteneur du texte
        content_container = article_container.find(
            "p",
            class_="font-large",
        )

        if content_container:

            # Récupérer uniquement les paragraphes directs
            for paragraph in content_container.find_all(
                "p",
                recursive=False,
            ):

                text = paragraph.get_text(
                    " ",
                    strip=True,
                )

                if text:
                    paragraphs.append(text)

    # Réunir les paragraphes
    article_text = "\n".join(paragraphs)

   
    return {
        "doc_id": extract_doc_id(url),
        "source": "Tunifact",
        "url": url,
        "title": title,
        "lang": "fr",
        "text": article_text,
        "date": extract_date(soup),
        "verdict": extract_verdict(soup),
    }




def save_raw_html(html: str, filename: str) -> Path:
    """Sauvegarde le HTML brut dans data/raw/tunifact/."""

    # Crée le dossier s'il n'existe pas.
    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = RAW_DIR / filename

    # UTF-8 est important pour l'arabe.
    path.write_text(
        html,
        encoding="utf-8",
    )

    return path
def save_interim_json(article: dict, filename: str) -> Path:
    """Sauvegarde un article extrait au format JSON."""

    # Créer data/interim/tunifact/ si le dossier n'existe pas.
    INTERIM_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = INTERIM_DIR / filename

    # ensure_ascii=False est important pour conserver correctement
    # les accents français et les caractères arabes.
    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            article,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return path
# ============================================================

# ============================================================
# TEST MANUEL SUR UN ARTICLE ARABE
# ============================================================

if __name__ == "__main__":

    # Deuxième article Tunifact : article en arabe
    url = (
        "https://tunifact.org/articles/937/"
        "%D9%87%D9%84-%D8%AA%D8%B3%D8%A8%D8%A8%D8%AA-"
        "%D9%85%D9%88%D8%AC%D8%A9-%D8%A7%D9%84%D8%AD%D8%B1-"
        "%D9%81%D9%8A-%D8%A7%D9%86%D9%82%D8%B7%D8%A7%D8%B9-"
        "%D8%A7%D9%84%D8%AA%D9%8A%D8%A7%D8%B1-"
        "%D8%A7%D9%84%D9%83%D9%87%D8%B1%D8%A8%D8%A7%D8%A6%D9%8A-"
        "%D8%B9%D9%86-13-%D8%A3%D9%84%D9%81-"
        "%D9%85%D9%86%D8%B2%D9%84-%D9%81%D9%8A-"
        "%D9%81%D8%B1%D9%86%D8%B3%D8%A7%D8%9F-/"
    )

    print("1. Téléchargement...")
    html = fetch_page(url)

    print("2. Extraction...")
    article = parse_article(html, url)

    # Langue de cet article, à vérifier dans le texte extrait
    article["lang"] = "ar"

    print("\nSOURCE :", article["source"])
    print("TITRE  :", article["title"])
    print("DOC ID :", article["doc_id"])
    print("LANG   :", article["lang"])
    print("DATE   :", article["date"])

    print("\n--- TEXTE EXTRAIT ---\n")
    print(article["text"])

    print("\n--- STATISTIQUES ---")
    print("Nombre de caractères :", len(article["text"]))
    print("Nombre de paragraphes :", len(article["text"].splitlines()))

    # Sauvegarde HTML : nom différent de l'article français
    html_path = save_raw_html(
        html,
        "tunifact_0937.html",
    )
    print("HTML sauvegardé :", html_path)

    # Sauvegarde JSON : nom différent de l'article français
    json_path = save_interim_json(
        article,
        "tunifact_937.json",
    )
    print("JSON sauvegardé :", json_path)
