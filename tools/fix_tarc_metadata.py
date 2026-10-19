
import json
from pathlib import Path

path = Path("data/annotations/normalized/tarc_review_30.jsonl")

rows = [
    json.loads(line)
    for line in path.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

# Corrections certaines
for row in rows:
    if row["id"] in {"tarc-forum-0344", "tarc-forum-0361"}:
        row["lang"] = "fr"
        row["script"] = "latin"
        row["groupe_linguistique"] = "fr-latin"

# Corrections d'écriture du tunisien
for row in rows:
    if row["lang"] == "tn":
        if row["groupe_linguistique"] == "tn-arabizi":
            row["script"] = "arabizi"
        elif row["groupe_linguistique"] == "tn-mixed":
            row["script"] = "mixed"


# Revue manuelle des groupes linguistiques
groupes_corriges = {
    "tarc-forum-0170": "tn-mixed",
    "tarc-forum-0150": "tn-mixed",
    "tarc-forum-0004": "tn-arabizi",
}

for row in rows:
    if row["id"] in groupes_corriges:
        groupe = groupes_corriges[row["id"]]
        row["groupe_linguistique"] = groupe
        row["script"] = (
            "mixed" if groupe == "tn-mixed" else "arabizi"
        )

with path.open("w", encoding="utf-8") as f:
    for row in rows:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print("Phrases :", len(rows))
print("Corrections des métadonnées terminées.")
