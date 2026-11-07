
"""Collecte multiple d'articles Tunifact — NewsCheck TN, Lot A1."""


from data.collect.tunifact_scraper import (
    INTERIM_DIR,
    RAW_DIR,
    extract_doc_id,
    fetch_page,
    parse_article,
    save_interim_json,
    save_raw_html,
)

# Ajouter ici les URL publiques des articles à collecter.
# Chaque URL doit correspondre à un article Tunifact.
ARTICLE_URLS = [
    "https://tunifact.org/articles/933/",
]


def collect_article(url: str) -> None:
    """Collecte un article sans écraser les fichiers existants."""

    doc_id = extract_doc_id(url)

    if doc_id == "tunifact-unknown":
        print(f"[IGNORE] URL non reconnue : {url}")
        return

    article_number = doc_id.split("-")[-1]

    html_filename = f"tunifact_{article_number}.html"
    json_filename = f"tunifact_{article_number}.json"

    html_path = RAW_DIR / html_filename
    json_path = INTERIM_DIR / json_filename

    # Ne pas écraser les articles déjà collectés
    if html_path.exists() or json_path.exists():
        print(f"[EXISTANT] {doc_id} — ignoré")
        return

    print(f"\n[COLLECTE] {doc_id}")

    try:
        html = fetch_page(url)
        article = parse_article(html, url)

        if not article["text"].strip():
            print(f"[ERREUR] Aucun texte extrait : {doc_id}")
            return

        # Langue provisoire : vérification humaine nécessaire
        article["lang"] = None

        save_raw_html(html, html_filename)
        save_interim_json(article, json_filename)

        print(f"[OK] {doc_id}")
        print(f"  Titre   : {article['title']}")
        print(f"  Date    : {article['date']}")
        print(f"  Verdict : {article['verdict']}")
        print(f"  HTML    : {html_path}")
        print(f"  JSON    : {json_path}")

    except Exception as exc:
        print(f"[ERREUR] {doc_id} : {exc}")


def main() -> None:
    if not ARTICLE_URLS:
        print("Aucune URL configurée dans ARTICLE_URLS.")
        return

    for url in ARTICLE_URLS:
        collect_article(url)


if __name__ == "__main__":
    main()
