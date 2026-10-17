
import json
from pathlib import Path
from collections import Counter

FILES = [
    Path("data/annotations/tarc_review_30.jsonl"),
    Path("data/annotations/tunifact_review_30.jsonl"),
]

LABELS = {"AFFIRMATION", "OPINION", "AUTRE"}
GROUPS = {
    "fr-latin",
    "ar-arabic",
    "tn-arabic",
    "tn-arabizi",
    "tn-mixed",
}

all_rows = []
errors = []

for path in FILES:
    print(f"\n--- {path.name} ---")

    if not path.exists():
        errors.append(f"Fichier introuvable : {path}")
        continue

    rows = []

    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(
                    f"{path}:{line_number} JSON invalide : {e}"
                )
                continue

            if not isinstance(row, dict):
                errors.append(
                    f"{path}:{line_number} : objet JSON attendu"
                )
                continue

            row_id = row.get("id")

            if not isinstance(row_id, str) or not row_id.strip():
                errors.append(f"{path}:{line_number} : ID manquant")

            if not isinstance(row.get("text"), str) or not row["text"].strip():
                errors.append(f"{path}:{line_number} : texte manquant")

            if row.get("annotation") not in LABELS:
                errors.append(
                    f"{path}:{line_number} : annotation invalide"
                )

            if row.get("groupe_linguistique") not in GROUPS:
                errors.append(
                    f"{path}:{line_number} : groupe linguistique invalide"
                )

            if row.get("decision") != "CONSERVER":
                errors.append(
                    f"{path}:{line_number} : décision inattendue"
                )

            if not row.get("source"):
                errors.append(f"{path}:{line_number} : source manquante")

            rows.append(row)
            all_rows.append(row)

    print("Total :", len(rows))
    print("Annotations :", dict(Counter(
        r.get("annotation") for r in rows
    )))
    print("Groupes :", dict(Counter(
        r.get("groupe_linguistique") for r in rows
    )))

ids = [r.get("id") for r in all_rows if r.get("id")]

duplicates = [
    item for item, count in Counter(ids).items()
    if count > 1
]

for item in duplicates:
    errors.append(f"ID dupliqué : {item}")

print("\n=== BILAN GLOBAL ===")
print("Phrases :", len(all_rows))
print("Doublons :", len(duplicates))
print("Annotations :", dict(Counter(
    r.get("annotation") for r in all_rows
)))

print("\n=== VALIDATION ===")

if errors:
    for error in errors:
        print("ERREUR :", error)
    print(f"\n{len(errors)} erreur(s) détectée(s)")
else:
    print("VALIDATION RÉUSSIE")
