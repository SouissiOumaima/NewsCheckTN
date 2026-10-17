
import json
from pathlib import Path

base = Path("data/annotations/normalized")
output = Path("data/deliverables/oumaima")
output.mkdir(parents=True, exist_ok=True)

sources = [
    base / "tarc_review_30.jsonl",
    base / "tunifact_review_30.jsonl",
]

rows = []

for path in sources:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))

ids = [row["id"] for row in rows]

if len(rows) != 60 or len(set(ids)) != 60:
    raise ValueError("Il faut 60 phrases avec 60 IDs uniques.")

sans_labels = output / "corpus_a1_pilot_60_sans_labels.jsonl"
labels_prives = output / "corpus_a1_pilot_60_labels_prives.jsonl"

champs_publics = [
    "id", "text", "lang", "script",
    "source", "url", "date",
    "groupe_linguistique", "text_origin"
]

with sans_labels.open("w", encoding="utf-8") as f1, \
     labels_prives.open("w", encoding="utf-8") as f2:

    for row in rows:
        phrase = {
            key: row.get(key)
            for key in champs_publics
        }

        etiquette = {
            "id": row["id"],
            "annotation": row["annotation"]
        }

        f1.write(json.dumps(phrase, ensure_ascii=False) + "\n")
        f2.write(json.dumps(etiquette, ensure_ascii=False) + "\n")

print("Livrable créé !")
print("Phrases :", len(rows))
print("Fichier pour Oumaima :", sans_labels)
print("Étiquettes privées :", labels_prives)
