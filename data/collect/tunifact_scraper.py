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

def parse_article(html: str, url: str) -> dict:
    """Extrait le titre et le texte principal d'un article Tunifact."""

    soup = BeautifulSoup(html, "html.parser")

    # Récupérer le titre.
    title_element = soup.find("h1")

    if title_element:
        title = title_element.get_text(" ", strip=True)
    else:
        title = ""

    # Trouver la zone principale de l'article.
    article_container = soup.find(
        "div",
        class_="articles-height",
    )

    paragraphs = []

    if article_container:

        # Trouver le conteneur du texte.
        content_container = article_container.find(
            "p",
            class_="font-large",
        )

        if content_container:

            # Récupérer uniquement les paragraphes directs
            # pour éviter les répétitions.
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

    # Réunir les paragraphes.
    article_text = "\n".join(paragraphs)

    return {
      "doc_id": extract_doc_id(url),
    "source": "Tunifact",
    "url": url,
    "title": title,
    "lang": "fr",
    "text": article_text,
    "date": None,
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
# TEST MANUEL SUR UN ARTICLE
# ============================================================
if __name__ == "__main__":

    # URL de l'article Tunifact utilisé pour notre premier test.
    url = (
        "https://tunifact.org/articles/698/"
        "Est-il-vrai-que-39000-ing%C3%A9nieurs-et-3000-m%C3%A9decins-"
        "ont-quitt%C3%A9-la-Tunisie-entre-2015-et-2020---/"
    )

    print("1. Téléchargement...")

    html = fetch_page(url)

    print("2. Extraction...")

    article = parse_article(html, url)

    print("\nSOURCE :", article["source"])
    print("TITRE  :", article["title"])
    print("URL    :", article["url"])
    print("DOC ID :", article["doc_id"])
    print("LANG   :", article["lang"])
    print("DATE   :", article["date"])
    # Afficher le début du texte.
    print("\n--- DÉBUT DU TEXTE ---\n")
    print(article["text"][:1500])

    # Afficher la fin du texte.
    # Cela permet de vérifier s'il y a du contenu parasite.
    print("\n--- FIN DU TEXTE ---\n")
    print(article["text"][-1000:])

    # Afficher quelques statistiques sur l'extraction.
    print("\n--- STATISTIQUES ---")
    print("Nombre de caractères :", len(article["text"]))
    print("Nombre de paragraphes :", len(article["text"].splitlines()))

    # Sauvegarder la page HTML brute.
    print("\n3. Sauvegarde du HTML brut...")

    saved_path = save_raw_html(
        html,
        "tunifact_0001.html",
    )

    print("Fichier sauvegardé :", saved_path)
    
    print("\n4. Sauvegarde des données extraites...")

json_path = save_interim_json(
    article,
    "tunifact_698.json",
)

print("JSON sauvegardé :", json_path)