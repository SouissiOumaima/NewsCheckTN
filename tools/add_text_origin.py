
import json
from pathlib import Path
from collections import Counter

FILES = [
    Path("data/annotations/tarc_review_30.jsonl"),
    Path("data/annotations/tunifact_review_30.jsonl"),
]

OUTPUT = Path("data/annotations/normalized")
OUTPUT.mkdir(parents=True, exist_ok=True)

for path in FILES:
    rows = []
    counts = Counter()

    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            row = json.loads(line)
            source = row.get("source", "")

            if "reformulation" in source.lower():
                origin = "reformulation"
            else:
                origin = "a_verifier"

            row["text_origin"] = origin
            rows.append(row)
            counts[origin] += 1

    output_path = OUTPUT / path.name

    with output_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(
                json.dumps(row, ensure_ascii=False) + "\n"
            )

    print(f"\nFichier : {output_path}")
    print("Phrases :", len(rows))
    print("Origines :", dict(counts))

print("\nTerminé : fichiers originaux conservés.")
