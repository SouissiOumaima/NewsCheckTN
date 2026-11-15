# `models/nli/` — Lot C, Model 2 : NLI (position d'une preuve)

Pour une affirmation et un passage de preuve, le Model 2 dit si le passage la **soutient**
(`supports`), la **contredit** (`refutes`) ou n'est pas décisif (`neutral`), avec une confiance.
Le Lot D s'en sert pour rendre le verdict.

| Fichier | Rôle |
|---|---|
| `stance.py` | inférence, contrat `predict_stance` / `predict_stances` → `StanceResult` |
| `bronze.py` | **palier Bronze** : position par lexique et règles (moteur par défaut de la démo) |
| `bronze_eval.py` | réglage des seuils sur train + val, évaluation, ablation TF-IDF, CSV des erreurs |
| `data.py` | préparation du corpus NLI du Lot A1, test gelé, contrôle de fuite |
| `evaluate.py` | macro-F1, par classe, confusion, par langue, IC 95 % (bootstrap) |
| `train.py` | affinage du modèle de la baseline sur `train`, meilleure époque choisie sur `val` |
| `compare.py` | bootstrap apparié : différence de macro-F1 entre deux modèles, moyenne ± écart-type |
| `run_grid.ps1`, `analyse_grid.py` | grille Silver sur la val (EXP-C-011) et choix par la règle fixée |
| `run_final.ps1` | relance finale avec les poids (configurations choisies) |
| `measure_test.py` | mesure unique du test Silver (refuse une seconde exécution) |
| `silver_errors.py` | CSV privé des erreurs Silver à relire |

## Palier Bronze (revue) : position par lexique

Moteur par défaut (`NLI_BACKEND=bronze`) : règles classiques, sans modèle à télécharger, comme
l'exige la démo Bronze. Voir l'en-tête de `bronze.py` pour les 6 règles.

```bash
python -m models.nli.bronze_eval --version v3 --tune                          # seuils (train + val)
python -m models.nli.bronze_eval --version v3 --split test --exp-id EXP-C-009 # une seule fois
```

## Modèle NLI pré-entraîné (après le Bronze)

Modèle NLI multilingue déjà entraîné sur XNLI (arabe et français inclus), utilisé tel quel :
`MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` (environ 1 Go au premier lancement).
Prémisse = la preuve, hypothèse = l'affirmation ; entailment → supports,
contradiction → refutes. Variables : `NLI_BACKEND=zero-shot` et `NLI_MODEL` (autre modèle).
Chargement toujours en float32.

## Palier Silver : modèle affiné (`NLI_BACKEND=fine-tuned`)

Composant Silver (EXP-C-011) : le modèle ci-dessus affiné sur le train du corpus A1 v3
(lr 1e-5, époque 1, choisis sur la val ; checkpoint de la graine 42, les 3 graines donnant les
mêmes prédictions). Test v3 (n = 56) : macro-F1 0.809, contre 0.798 sans affinage (différence
non significative : IC 95 % [−0.052 ; +0.071]), 0.471 pour les règles Bronze.

```bash
NLI_BACKEND=fine-tuned uvicorn api.main:app     # ou python pipeline.py, évaluations du Lot D…
```

Le checkpoint (1,1 Go) n'est pas versionné : par défaut
`models/checkpoints/nli_mdeberta-ft_v3_lr1e-05_e6_seed42/` (`CHECKPOINT_DIR` pour un autre
dossier, `NLI_FINETUNED_MODEL` pour un autre chemin). Pour le recréer :
`powershell -File models
liun_final.ps1` (ou `python -m models.nli.train --version v3
--seed 42 --lr 1e-5 --epochs 6 --keep-epoch 1`). S'il est absent, la réponse est « neutre »
avec une confiance 0, comme pour les autres moteurs.

Sans torch / transformers, ou si le modèle ne se charge pas, la réponse est « neutre » avec une
confiance 0 : l'API ne tombe jamais. Les tests forcent `NLI_BACKEND=stub` (`tests/conftest.py`) et
ne téléchargent rien.

## Lancer

Le corpus du Lot A1 est **privé** : il va dans `data/interim/lot_c/nli/` (non versionné),
jamais sur GitHub.

```bash
pip install torch transformers sentencepiece protobuf
python -m models.nli.data --version v3 \
    --input data/interim/lot_c/nli/nli_corpus_300_consolide_v3_prive.jsonl
python -m models.nli.evaluate --version v3 --split test --exp-id EXP-C-0XX
```

`data.py` écrit les identifiants des parties dans `data/splits/nli_<version>_by_article_seed42.json`
(versionnable, sans texte) et les paires dans `data/interim/lot_c/nli/` (privé).

## Affiner le modèle (Model 2 entraîné)

On part de la baseline et on continue l'entraînement sur `train` (4 époques, lr 1e-5, lot de 8).
La validation choisit la meilleure époque ; l'époque 0 (baseline) est candidate, donc si
l'affinage n'aide pas sur `val`, on garde la baseline. Le test n'est jamais regardé pendant
l'entraînement. Trois graines, comme pour le Model 1 :

```bash
python -m models.nli.train --version v3 --seed 42      # puis 123, puis 2026
NLI_MODEL=models/checkpoints/nli_mdeberta-ft_v3_seed42 \
    python -m models.nli.evaluate --version v3 --split test --exp-id EXP-C-0XX
python -m models.nli.compare \
    --baseline predictions_v3_test_mdeberta-v3-base-xnli-multilingual-nli-2mil7.jsonl \
    --models predictions_v3_test_nli_mdeberta-ft_v3_seed42.jsonl \
             predictions_v3_test_nli_mdeberta-ft_v3_seed123.jsonl \
             predictions_v3_test_nli_mdeberta-ft_v3_seed2026.jsonl
```

Chaque checkpoint pèse environ 1,1 Go (`models/checkpoints/`, non versionné). Sur processeur,
compter environ 8 Go de mémoire ; un GPU (Colab) est beaucoup plus rapide.

## Règles du découpage

- **Par groupe d'articles** : deux articles qui partagent un texte (affirmation ou preuve) sont
  dans la même partie. Un même texte n'est jamais à la fois en entraînement et en test.
- **Test gelé** : toutes les paires des articles du jeu de test du Lot D (Tunifact 613, 698, 797,
  890, 933, 937), complétées au hasard (graine 42) jusqu'à 20 % des paires. Ces articles ne
  servent jamais à l'entraînement : le NLI et le verdict du Lot D sont évalués sur les mêmes.
- **Paires en attente** (« Brouillon non valide » dans la remarque, sans validation confirmée
  ensuite) : mises de côté jusqu'à la confirmation du Lot A1.
- Les chiffres **officiels** se font une seule fois, sur la version validée du corpus (v4) ;
  la v3 sert à mettre au point le code.
