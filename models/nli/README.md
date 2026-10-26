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
contradiction → refutes. Variables : `NLI_BACKEND=zero-shot` et
`NLI_MODEL` (autre modèle, ou plus tard le checkpoint fine-tuné du Lot C).

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
