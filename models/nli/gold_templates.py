"""Lot C — Model 2, palier Gold : gabarits privés des réécritures (EXP-C-012, EXP-C-013).

Copie les 56 paires du test v3 (identifiant, langues, label, affirmation, preuve) dans deux
fichiers à remplir par des humains ; aucune prédiction n'est lue, rien n'est mesuré.

  - reecritures_tn_v1.csv : affirmation réécrite en tunisien en lettres arabes (obligatoire) et en
    arabizi (bonus), même preuve, même label (EXP-C-012) ;
  - paraphrases_v1.csv : une paraphrase dans la langue d'origine (obligatoire), une seconde en
    bonus, même preuve, même label (EXP-C-013).

    python -X utf8 -m models.nli.gold_templates

Écrit dans data/interim/lot_c/nli/gold/ (privé : data/interim/ est ignoré par Git). Refuse
d'écraser un fichier existant, pour ne jamais perdre un travail commencé.
"""

from __future__ import annotations

import csv

from models.nli.data import OUT_DIR, load_pairs

TEST_FILE = OUT_DIR / "nli_v3_test.jsonl"
GOLD_DIR = OUT_DIR / "gold"

BASE = [
    "pair_id",
    "article_id",
    "claim_lang",
    "evidence_lang",
    "label",
    "claim_original",
    "evidence",
]
CHECK = [
    "verificateur",
    "verif_sens_identique",  # oui / non : même fait, mêmes nombres, dates et noms
    "verif_label_tient",  # oui / non : la preuve donne toujours le même label
    "ia_utilisee",  # « non », ou outil + rôle (ex. « proposition par X, relue et corrigée par Y »)
    "statut",  # garde / ecarte (écartée si une vérification est « non »)
    "commentaire",
]
TEMPLATES = {
    "reecritures_tn_v1.csv": BASE
    + ["claim_tn_arabe", "auteur_tn_arabe", "claim_arabizi", "auteur_arabizi"]
    + CHECK,
    "paraphrases_v1.csv": BASE
    + ["claim_paraphrase_1", "auteur_paraphrase_1", "claim_paraphrase_2", "auteur_paraphrase_2"]
    + CHECK,
}


def main() -> None:
    pairs = load_pairs(TEST_FILE)
    if len(pairs) != 56:
        raise SystemExit(f"{len(pairs)} paires de test au lieu de 56")
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    for name, fields in TEMPLATES.items():
        path = GOLD_DIR / name
        if path.exists():
            print(f"{path} existe déjà : laissé tel quel")
            continue
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for p in pairs:
                row = dict.fromkeys(fields, "")
                row.update(
                    pair_id=p["pair_id"],
                    article_id=p["article_id"],
                    claim_lang=p["claim_lang"],
                    evidence_lang=p["evidence_lang"],
                    label=p["label"],
                    claim_original=p["claim"],
                    evidence=p["evidence"],
                )
                w.writerow(row)
        print(f"{len(pairs)} lignes -> {path}")


if __name__ == "__main__":
    main()
