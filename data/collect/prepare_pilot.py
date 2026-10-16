
import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = DATA_DIR / "interim" / "tunifact" / "tunifact_698.json"
OUTPUT_FILE = DATA_DIR / "annotations" / "pilot_multilingual_100.jsonl"


def split_sentences(text):
    """Découpage simple des phrases françaises pour le premier test."""
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?؟])\s+", text)
        if sentence.strip()
    ]


def main():
    with INPUT_FILE.open("r", encoding="utf-8") as f:
        article = json.load(f)

    sentences = split_sentences(article["text"])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for index, sentence in enumerate(sentences, start=1):
            record = {
                "id": f"{article['doc_id']}-{index:03d}",
                "doc_id": article["doc_id"],
                "text": sentence,
                "lang": article["lang"],
                "script": "latin",
                "source": article["source"],
                "url": article["url"],
                "date": article["date"],
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"{len(sentences)} phrases extraites.")
    print(f"Fichier créé : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
