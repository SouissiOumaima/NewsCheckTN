# `evaluation/` — Lot E : Évaluation & tableau de bord (utilisé par tous)

**Responsable : Membre 6 · Branche : `lot-e-integration`** — chaque lot y dépose ses résultats.

## Rôle
- `metrics.py` : métriques **communes** pour que tous les lots se comparent de la même manière
  (précision / rappel / F1, macro-F1, Recall@k ; à venir : fidélité, taux d'abstention, calibration).
- `dashboard/app.py` : tableau de bord Streamlit agrégeant les résultats.
- `results/` : fichiers de résultats produits par les scripts d'évaluation. Les synthèses légères
  présentées à la revue sont versionnées ; les sorties brutes lourdes restent ignorées.
- Audit bout-en-bout du pipeline sur `data/processed/factchecks.jsonl`.

## Format des résultats
Un fichier JSON par évaluation : `results/<lot>_<tâche>_<modèle>_<AAAAMMJJ>.json`
```json
{
  "exp_id": "EXP-C-003",
  "lot": "C",
  "task": "checkworthiness",
  "model": "xlmr-lora-r8",
  "split": "test",
  "metrics": {"macro_f1": 0.0, "by_lang": {"fr": {}, "ar": {}, "tn": {}}}
}
```
L'`exp_id` renvoie à l'entrée correspondante de `experiments.md`.

## Lancer le tableau de bord
```bash
streamlit run evaluation/dashboard/app.py
```

## Audit d'intégration Bronze (Lot E)

```bash
python -m evaluation.integration_audit
```

Il vérifie quatre cas annotés : affirmation confirmée, contradiction numérique,
abstention sans preuve et opinion filtrée. Il publie le taux de succès de chaîne,
macro-F1, Recall@5, abstention, validité des citations et latence mesurée.
