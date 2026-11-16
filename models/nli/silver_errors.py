"""Lot C — Model 2, palier Silver (EXP-C-011) : CSV privé des erreurs à relire.

Toutes les erreurs du modèle principal (graine 42) et du zero-shot float32 sur le test v3 (mesure
unique déjà faite : prédictions lues dans data/interim/lot_c/nli/silver_test/), complétées par
celles de la val (prédictions du journal du principal ; zero-shot float32 recalculé sur la val),
car le test seul n'en compte que 12. Section séparée (colonne `modele`) : les erreurs de
l'ablation (graine 42) sur le test, pour dépasser 30 erreurs. Catégorie proposée par relecture
(mêmes catégories que le Bronze quand c'est possible) ; `categorie_validee` reste vide pour la
relecture humaine.

    python -m models.nli.silver_errors
Écrit data/interim/lot_c/nli/erreurs_silver_v3.csv (privé, non versionné).
"""

from __future__ import annotations

import csv
import json
import os

from models.nli import evaluate as ev
from models.nli import stance
from models.nli.data import OUT_DIR, ROOT, load_pairs

PRINCIPAL = ROOT / "models" / "checkpoints" / "nli_mdeberta-ft_v3_lr1e-05_e6_seed42"
OUT = OUT_DIR / "erreurs_silver_v3.csv"
NOTES = OUT_DIR / "notes_erreurs_silver.json"  # privé : {"principal": {...}, "ablation": {...}}

# Catégories du Bronze (EXP-C-009) reprises telles quelles
PARAPHRASE = "paraphrase non reconnue (recouvrement faible)"
DEMENTI = "démenti implicite non détecté"
NEGATION = "négation mal interprétée"
NOMBRES = "nombres mal comparés"
MARQUEUR = "marqueur de démenti trompeur"
RECOUVREMENT = "recouvrement trompeur (même sujet, autre fait)"
# Catégories ajoutées pour les modèles neuronaux
CONFIRMATION = "confirmation implicite non détectée"
META = "méta-affirmation (« selon X », « X a vérifié »)"
LANGUE = "preuve dans l'autre langue (fr / ar)"
ANNOTATION = "annotation à vérifier"

# pair_id → catégorie proposée (2026-11-14, à valider) ; les notes, qui citent le corpus, sont
# dans le fichier privé NOTES (non versionné)
PROPOSED = {
    "NLI-P004": NOMBRES,
    "NLI-P006": DEMENTI,
    "NLI-P007": DEMENTI,
    "NLI-P008": DEMENTI,
    "NLI-P010": RECOUVREMENT,
    "NLI-P012": NOMBRES,
    "NLI-P057": CONFIRMATION,
    "P188": META,
    "P207": PARAPHRASE,
    "P255": NOMBRES,
    "P276": PARAPHRASE,
    "P277": NEGATION,
    "NLI-P035": ANNOTATION,
    "NLI-P037": ANNOTATION,
    "NLI-P053": RECOUVREMENT,
    "P140": DEMENTI,
    "P145": RECOUVREMENT,
    "P274": NOMBRES,
    "P279": META,
    "P297": ANNOTATION,
    "P299": LANGUE,
    "P300": NEGATION,
}


# Ablation (graine 42), test : prédit « supports » pour 48 paires sur 56 (modèle qui n'a pas fini
# d'apprendre) ; pair_id → catégorie proposée (2026-11-14, à valider)
PROPOSED_ABLATION = {
    "NLI-P001": DEMENTI,
    "NLI-P004": NOMBRES,
    "NLI-P005": MARQUEUR,
    "NLI-P006": DEMENTI,
    "NLI-P010": RECOUVREMENT,
    "NLI-P011": RECOUVREMENT,
    "NLI-P012": NOMBRES,
    "NLI-P059": RECOUVREMENT,
    "NLI-P073": NEGATION,
    "NLI-P074": NEGATION,
    "NLI-P076": NEGATION,
    "P189": META,
    "P206": RECOUVREMENT,
    "P209": NEGATION,
    "P231": RECOUVREMENT,
    "P232": NEGATION,
    "P233": RECOUVREMENT,
    "P234": DEMENTI,
    "P235": RECOUVREMENT,
    "P236": NOMBRES,
    "P252": META,
    "P253": RECOUVREMENT,
    "P255": NOMBRES,
    "P256": RECOUVREMENT,
    "P277": NEGATION,
    "P278": RECOUVREMENT,
    "P290": DEMENTI,
    "P293": RECOUVREMENT,
}


# Catégorie finale (relecture du 2026-11-14 par Claude, pas la validation humaine) : la catégorie
# proposée, sauf ces corrections (modèle, pair_id) → catégorie.
FINAL_OVERRIDES = {
    # chiffre absent de la preuve (comme P278, P293) : pas une comparaison de nombres
    ("ablation", "P236"): RECOUVREMENT,
}


def _final(model: str, pid: str, proposed: str) -> str:
    return FINAL_OVERRIDES.get((model, pid), proposed)


def _preds(path) -> dict[str, str]:
    with open(path, encoding="utf-8") as f:
        return {r["pair_id"]: r["pred"] for r in map(json.loads, f)}


def main() -> None:
    test = load_pairs(OUT_DIR / "nli_v3_test.jsonl")
    notes = (
        json.loads(NOTES.read_text(encoding="utf-8"))
        if NOTES.exists()
        else {"principal": {}, "ablation": {}}
    )
    val = load_pairs(OUT_DIR / "nli_v3_val.jsonl")
    d = OUT_DIR / "silver_test"
    p_test = _preds(d / "predictions_v3_test_principal_seed42.jsonl")
    z_test = _preds(d / "predictions_v3_test_zero-shot-fp32.jsonl")
    a_test = _preds(d / "predictions_v3_test_ablation_seed42.jsonl")
    log = json.loads((PRINCIPAL / "train_log.json").read_text(encoding="utf-8"))
    p_val = log["kept_val_predictions"]
    os.environ["NLI_BACKEND"] = "zero-shot"
    os.environ.pop("NLI_MODEL", None)
    stance.set_classifier(None)
    _, zp = ev.evaluate(val)
    z_val = {p["pair_id"]: s for p, (s, _) in zip(val, zp, strict=True)}

    rows = []
    for part, pairs, P, Z in (("test", test, p_test, z_test), ("val", val, p_val, z_val)):
        for p in pairs:
            pid, gold = p["pair_id"], p["label"]
            wrong_p, wrong_z = P[pid] != gold, Z[pid] != gold
            if not (wrong_p or wrong_z):
                continue
            who = "les deux" if wrong_p and wrong_z else ("principal" if wrong_p else "zero-shot")
            cat = PROPOSED.get(pid, "")
            note = notes["principal"].get(pid, "à classer")
            rows.append(
                [
                    "principal / zero-shot",
                    part,
                    pid,
                    p.get("claim_lang"),
                    p.get("article_id"),
                    p["claim"],
                    p["evidence"],
                    gold,
                    P[pid],
                    Z[pid],
                    a_test.get(pid, "") if part == "test" else "",
                    who,
                    cat,
                    note,
                    _final("principal", pid, cat),
                    "",
                ]
            )
    for p in test:
        pid, gold = p["pair_id"], p["label"]
        if a_test[pid] == gold:
            continue
        cat = PROPOSED_ABLATION.get(pid, "")
        note = notes["ablation"].get(pid, "à classer")
        rows.append(
            [
                "ablation (graine 42)",
                "test",
                pid,
                p.get("claim_lang"),
                p.get("article_id"),
                p["claim"],
                p["evidence"],
                gold,
                p_test[pid],
                z_test[pid],
                a_test[pid],
                "ablation",
                cat,
                note,
                _final("ablation", pid, cat),
                "",
            ]
        )
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "modele",
                "partie",
                "pair_id",
                "langue",
                "article_id",
                "affirmation",
                "preuve",
                "reference",
                "sortie_principal",
                "sortie_zero_shot",
                "sortie_ablation",
                "erreur_de",
                "categorie_proposee",
                "note",
                "categorie_finale",
                "categorie_validee",
            ]
        )
        w.writerows(rows)
    missing = [(r[0], r[2]) for r in rows if not r[12]]
    n_abl = sum(r[0].startswith("ablation") for r in rows)
    print(
        f"{len(rows)} erreurs ({len(rows) - n_abl} principal / zero-shot, {n_abl} ablation) "
        f"-> {OUT}" + (f" ; sans catégorie : {missing}" if missing else "")
    )


if __name__ == "__main__":
    main()
