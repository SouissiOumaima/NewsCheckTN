"""Lot C — Model 2, palier Gold (e) : vue privée des 22 erreurs à valider par Membre 4.

Lit le CSV privé d'EXP-C-011 (`erreurs_silver_v3.csv`) et n'en garde que les 22 erreurs du
modèle principal et du zero-shot float32 (12 test, 10 val) ; les 28 erreurs de l'ablation sont
laissées de côté. Aucun modèle n'est relancé, aucun label n'est relu pour choisir quoi que ce soit.

Les catégories `categorie_proposee` de la vue sont celles de la colonne `categorie_finale`
d'EXP-C-011, proposées par l'assistant (Claude) et non validées. Membre 4 remplit
`categorie_validee` (« ok » si la catégorie proposée lui convient, sinon le nom de sa catégorie)
et, si besoin, `commentaire_validation`.

    python -X utf8 -m models.nli.gold_error_view            # écrit la vue
    python -X utf8 -m models.nli.gold_error_view --merge    # reporte les validations

Écrit data/interim/lot_c/nli/validation_erreurs_22.csv (privé : data/interim/ est ignoré par Git).
`--merge` recopie `categorie_validee` dans `erreurs_silver_v3.csv` (« ok » → catégorie proposée) et
affiche l'accord brut entre l'assistant et Membre 4. Le terminal n'affiche que des comptes.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter

from models.nli.data import OUT_DIR

SOURCE = OUT_DIR / "erreurs_silver_v3.csv"
VIEW = OUT_DIR / "validation_erreurs_22.csv"
KEPT = "principal / zero-shot"
ANNOTATION = "annotation à vérifier"

# Décisions du Lot A1 pour la v4 (mail du 2026-11-15) : rappel utile pour valider ces 3 lignes
A1_DECISIONS = {
    "NLI-P035": "Lot A1 (15/11) : label v4 refutes (v3 : neutral)",
    "NLI-P037": "Lot A1 (15/11) : neutral conservé",
    "P297": "Lot A1 (15/11) : affirmation reformulée en v4, label supports (v3 : refutes)",
}

COLUMNS = [
    "ordre",
    "pair_id",
    "partie",
    "langue",
    "erreur_de",
    "affirmation",
    "preuve",
    "reference",
    "sortie_principal",
    "sortie_zero_shot",
    "categorie_proposee",
    "note_assistant",
    "decision_lot_a1",
    "categorie_validee",
    "commentaire_validation",
]


def read(path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write(path, rows: list[dict], fields: list[str]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def build_view() -> None:
    if VIEW.exists() and any(r["categorie_validee"].strip() for r in read(VIEW)):
        raise SystemExit(f"{VIEW} contient déjà des validations : refus de l'écraser.")
    rows = [r for r in read(SOURCE) if r["modele"] == KEPT]
    if len(rows) != 22:
        raise SystemExit(f"{len(rows)} erreurs principal / zero-shot au lieu de 22 : à vérifier.")
    # d'abord les 3 « annotation à vérifier » (déjà tranchées par le Lot A1), puis test, puis val
    rows.sort(key=lambda r: (r["categorie_finale"] != ANNOTATION, r["partie"] != "test"))
    view = [
        {
            "ordre": i,
            "pair_id": r["pair_id"],
            "partie": r["partie"],
            "langue": r["langue"],
            "erreur_de": r["erreur_de"],
            "affirmation": r["affirmation"],
            "preuve": r["preuve"],
            "reference": r["reference"],
            "sortie_principal": r["sortie_principal"],
            "sortie_zero_shot": r["sortie_zero_shot"],
            "categorie_proposee": r["categorie_finale"],
            "note_assistant": r["note"],
            "decision_lot_a1": A1_DECISIONS.get(r["pair_id"], ""),
            "categorie_validee": "",
            "commentaire_validation": "",
        }
        for i, r in enumerate(rows, 1)
    ]
    write(VIEW, view, COLUMNS)
    print(f"{len(view)} lignes -> {VIEW}")
    print("partie :", dict(Counter(r["partie"] for r in view)))
    print("erreur de :", dict(Counter(r["erreur_de"] for r in view)))
    print("catégories proposées (assistant) :")
    for cat, n in Counter(r["categorie_proposee"] for r in view).most_common():
        print(f"  {n:2d}  {cat}")


def merge() -> None:
    view = {r["pair_id"]: r for r in read(VIEW)}
    done = {k: r for k, r in view.items() if r["categorie_validee"].strip()}
    source = read(SOURCE)
    fields = list(source[0].keys())
    agree = 0
    for r in source:
        v = done.get(r["pair_id"]) if r["modele"] == KEPT else None
        if v is None:
            continue
        val = v["categorie_validee"].strip()
        final = v["categorie_proposee"] if val.lower() == "ok" else val
        agree += final == v["categorie_proposee"]
        r["categorie_validee"] = final
    write(SOURCE, source, fields)
    print(
        f"validées : {len(done)} / {len(view)} ; accord brut assistant / Membre 4 : "
        f"{agree} / {len(done)}" + (f" ({agree / len(done):.0%})" if done else "")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--merge", action="store_true", help="reporter les validations")
    args = parser.parse_args()
    merge() if args.merge else build_view()


if __name__ == "__main__":
    main()
