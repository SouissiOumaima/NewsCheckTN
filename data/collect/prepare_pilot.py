
import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1]

INPUT_DIR = DATA_DIR / "interim" / "tunifact"
OUTPUT_FILE = DATA_DIR / "annotations" / "pilot_multilingual_100.jsonl"


def split_sentences(text):
    """Découpe le texte en phrases françaises et arabes."""

    # Enlever les URL isolées sur une ligne
    text = re.sub(r"(?m)^\s*https?://\S+\s*$", "", text)

    # Découper après une ponctuation suivie d'un espace
    sentences = re.split(r"(?<=[.!?؟…])\s+", text)

    return [
        re.sub(r"\s+", " ", sentence).strip()
        for sentence in sentences
        if sentence.strip()
    ]


def detect_script(lang):
    if lang == "ar":
        return "arabic"
    if lang == "fr":
        return "latin"
    return "mixed"


def main():
    records = []

    for input_file in sorted(INPUT_DIR.glob("*.json")):
        with input_file.open("r", encoding="utf-8") as f:
            article = json.load(f)

        sentences = split_sentences(article["text"])

        print(
            f"{article['doc_id']} ({article['lang']}) : "
            f"{len(sentences)} phrases"
        )

        for index, sentence in enumerate(sentences, start=1):
            records.append({
                "id": f"{article['doc_id']}-{index:03d}",
                "doc_id": article["doc_id"],
                "text": sentence,
                "lang": article["lang"],
                "script": detect_script(article["lang"]),
                "source": article["source"],
                "url": article["url"],
                "date": article["date"],
            })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nTOTAL : {len(records)} phrases")
    print(f"Fichier créé : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
