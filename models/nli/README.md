# `models/nli/` — Lot C, Model 2 : NLI (position d'une preuve)

Pour une affirmation et un passage de preuve, le Model 2 dit si le passage la **soutient**
(`supports`), la **contredit** (`refutes`) ou n'est pas décisif (`neutral`), avec une confiance.
Le Lot D s'en sert pour rendre le verdict.

| Fichier | Rôle |
|---|---|
| `stance.py` | inférence, contrat `predict_stance` / `predict_stances` → `StanceResult` |
| `data.py` | préparation du corpus NLI du Lot A1, test gelé, contrôle de fuite |
| `evaluate.py` | macro-F1, par classe, confusion, par langue, IC 95 % (bootstrap) |

## Version actuelle : baseline sans entraînement

Modèle NLI multilingue déjà entraîné sur XNLI (arabe et français inclus), utilisé tel quel :
`MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` (environ 1 Go au premier lancement).
Prémisse = la preuve, hypothèse = l'affirmation ; entailment → supports,
contradiction → refutes. Variables : `NLI_BACKEND` (`zero-shot` par défaut, ou `stub`) et
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
