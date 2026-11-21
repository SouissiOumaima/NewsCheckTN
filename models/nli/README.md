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
`powershell -File models/nli/run_final.ps1` (ou `python -m models.nli.train --version v3
--seed 42 --lr 1e-5 --epochs 6 --keep-epoch 1`). S'il est absent, la réponse est « neutre »
avec une confiance 0, comme pour les autres moteurs.

Sans torch / transformers, ou si le modèle ne se charge pas, la réponse est « neutre » avec une
confiance 0 : l'API ne tombe jamais. Les tests forcent `NLI_BACKEND=stub` (`tests/conftest.py`) et
ne téléchargent rien.

## État du Gold

Aucune de ces analyses ne relance de mesure sur le test : celles qui sont « mesurées » relisent
les prédictions de la mesure unique d'EXP-C-011, ou n'utilisent que la val.

| Expérience | Objet | État | Résultat ou blocage |
|---|---|---|---|
| EXP-C-014 | biais par langue, source et sujet | **mesuré** (prédictions Silver relues) | aucun écart établi ; sujet confondu avec l'article (catégories du Lot A1 tirées des titres) |
| EXP-C-015 | seuil d'abstention | **mesuré** (val seulement) | aucun seuil retenu (τ = 0) |
| EXP-C-016 | inversions de polarité (supports ↔ refutes) | **mesuré** (prédictions Silver relues) | 1 inversion sur 10 erreurs (affiné), 1 sur 11 (zero-shot), 16 sur 30 (Bronze) ; descriptif seulement |
| EXP-C-012 | transfert vers le tunisien | **protocole seulement**, non mesuré | réécritures générées par IA ; en attente de l'accord de l'équipe sur la transmission externe et de la relecture humaine (Mouhib) ; fichier non figé |
| EXP-C-013 | robustesse aux paraphrases | **protocole seulement**, non mesuré | paraphrases générées par IA ; en attente de l'accord de l'équipe sur la transmission externe et d'une relecture humaine ; fichier non figé |

La mesure unique d'EXP-C-012 et d'EXP-C-013 est préparée, mais pas lancée :
`python -X utf8 -m models.nli.gold_measure --exp tn|paraphrases --dry-run`. Le script refuse
tant que le fichier n'est pas figé (SHA-256 reporté dans le code) et que le vérificateur est vide
(sauf `--exploratoire`), et il refuse une seconde exécution.

## Limites (chiffrées)

Chiffres tirés d'`experiments.md` (EXP-C-011, EXP-C-014, EXP-C-015, EXP-C-016) :

- **Petit test** : 56 paires (25 fr, 31 ar, **0 tunisien**) ; IC 95 % de la macro-F1 du modèle
  affiné [0.689 ; 0.905], soit une largeur d'environ 0.22.
- **Petite val** : 33 paires (une paire ≈ 3 points) ; 3 labels douteux (9 % de la val), corrigés
  par le Lot A1 pour la v4 seulement.
- **Peu d'entraînement** : 174 paires ; l'affinage n'apporte pas de gain établi sur le zero-shot
  (+0.011, IC 95 % [−0.052 ; +0.071], p = 0.40 ; 3 paires différentes sur 56).
- **Variance non mesurée** : les 3 graines donnent les mêmes prédictions (val et test).
- **Ablation inachevée** : sans pré-entraînement NLI, le modèle apprenait encore à 6 époques
  (0.427 ± 0.044).
- **Test concentré** : 10 articles, dont 2 font 25 des 56 paires (45 %) ; 2 sites, dont un à
  8 paires ; aucun écart de langue ou de source n'est établi, faute d'effectifs (EXP-C-014).
- **Sujet** : catégories proposées par le Lot A1 à partir des titres (pas de second annotateur) ;
  dans le test, 6 catégories, chacune de 1 ou 2 articles : un écart de sujet ne peut pas être
  séparé d'un effet d'article (EXP-C-014).
- **Abstention** : aucun seuil de confiance retenu (τ = 0, choisi sur 33 paires de val, EXP-C-015).
- **Analyse d'erreurs** : les catégories d'erreurs ont été **proposées par l'assistant (Claude)
  et ne sont validées par aucun humain** (`categorie_validee` vide) ; 28 des 50 erreurs
  analysées viennent de l'ablation.
- **Tunisien et paraphrases** (EXP-C-012, EXP-C-013) : jeux générés par IA, non encore mesurés ;
  sans relecture humaine, leurs résultats seront exploratoires.
- **Corpus v3**, pas v4 (règle du 2026-11-10).

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
