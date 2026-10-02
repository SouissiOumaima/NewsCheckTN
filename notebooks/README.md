# `notebooks/` — Exploration (tous les lots)

Un sous-dossier par lot ; chacun ne travaille que dans le sien :

| Dossier | Lot |
|---------|-----|
| `lot_a1_data/` | A1 — corpus, statistiques, annotation |
| `lot_a2_normalization/` | A2 — normalisation, langue, perplexité |
| `lot_b_linguistic/` | B — analyse linguistique |
| `lot_c_models/` | C — entraînements, analyse d'erreurs |
| `lot_d_rag/` | D — retrieval, prompts |
| `lot_e_integration/` | E — audit bout-en-bout |

## Conventions
- Nom : `NN_<membre>_<sujet>.ipynb` (ex. `03_m5_bm25_vs_dense.ipynb`).
- Les notebooks servent à **explorer** ; le code réutilisable est déplacé dans le module du lot.
- Vider les sorties volumineuses avant commit (recommandé : `pip install nbstripout && nbstripout --install`).
- Pas de chemins absolus : lancer Jupyter depuis la racine du repo et importer les modules du projet.
- Toute expérience notable est reportée dans `experiments.md`.
