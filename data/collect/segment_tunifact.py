
"""
NewsCheck TN — Lot A1
Segmentation des articles Tunifact en phrases.

Entrée  : data/interim/tunifact/*.json
Sortie  : data/processed/tunifact_sentences.jsonl

Les fichiers JSON originaux ne sont pas modifiés.
"""

import json
import re
from pathlib import Path

INPUT_DIR = Path("data/interim/tunifact")
OUTPUT_FILE = Path("data/processed/tunifact_sentences.jsonl")



def segment_sentences(text: str) -> list[str]:
    """Découpage initial du français et de l'arabe en phrases."""

    # Nettoyer les espaces sans supprimer les paragraphes
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Retirer les URL du texte utilisé pour la segmentation
    text = re.sub(r"https?://[^\s]+", " ", text)

    sentences = []

    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()

        if not paragraph:
            continue


        # Séparer après . ! ? et les ponctuations arabes ؟ ۔
        # Ne pas couper les décimaux ou les points d'URL simples.
        parts = re.split(
            r"(?<=[.!?؟۔])\s+(?=[^\s])",
            paragraph,
        )

        for part in parts:
            sentence = " ".join(part.split()).strip()

            if sentence:
                sentences.append(sentence)

    return sentences


def main():
    if not INPUT_DIR.exists():
        print(f"[ERREUR] Dossier introuvable : {INPUT_DIR}")
        return

    files = sorted(INPUT_DIR.glob("*.json"))

    if not files:
        print("[ERREUR] Aucun article JSON trouvé.")
        return

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    total_sentences = 0
    total_articles = 0

    with OUTPUT_FILE.open("w", encoding="utf-8") as output:
        for file in files:
            try:
                article = json.loads(file.read_text(encoding="utf-8"))

                doc_id = article.get("doc_id", file.stem)
                text = article.get("text", "")
                lang = article.get("lang")
                date = article.get("date")
                verdict = article.get("verdict")

                if not text.strip():
                    print(f"[IGNORE] Texte vide : {file.name}")
                    continue

                sentences = segment_sentences(text)

                for index, sentence in enumerate(sentences, start=1):
                    record = {
                        "sentence_id": f"{doc_id}-s{index:04d}",
                        "doc_id": doc_id,
                        "source": "Tunifact",
                        "lang": lang,
                        "date": date,
                        "verdict_article": verdict,
                        "text": sentence,
                    }

                    output.write(
                        json.dumps(record, ensure_ascii=False) + "\n"
                    )

                total_articles += 1
                total_sentences += len(sentences)

                print(
                    f"[OK] {doc_id} | "
                    f"{lang} | {len(sentences)} phrases"
                )

            except (OSError, ValueError, TypeError) as error:
                print(f"[ERREUR] {file.name} : {error}")

    print("\n=== RÉSULTAT ===")
    print(f"Articles traités : {total_articles}")
    print(f"Phrases extraites : {total_sentences}")
    print(f"Fichier créé : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
