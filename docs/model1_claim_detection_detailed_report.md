# Model 1 — Détection d'affirmations vérifiables

## 1. Rôle dans NewsCheck TN

Model 1 est le premier filtre du pipeline. Il décide si une phrase contient une
affirmation factuelle qui mérite d'être vérifiée par les étapes suivantes.

Il ne dit jamais si une phrase est vraie ou fausse. Par exemple, « Le chômage
est de 16 % » est une affirmation, même si le chiffre est faux. La recherche de
preuves, le NLI et le verdict final sont des tâches distinctes.

Le modèle prédit trois classes :

| Classe | Définition | Exemple |
| --- | --- | --- |
| `AFFIRMATION` | Fait concret vérifiable dans des sources | « Le prix du pain a augmenté en 2024. » |
| `OPINION` | Jugement, appréciation ou point de vue | « Cette décision est injuste. » |
| `AUTRE` | Question, souhait, hypothèse, salutation, fragment ou contenu non check-worthy | « Inchallah la saison sera bonne. » |

Les modalités complètent les labels : `assertif`, `rapporté`, `conditionnel`,
`hypothétique`, `souhait`, `interrogatif` et `opinion`. Une phrase rapportée
reste une affirmation. Une question, un souhait ou une hypothèse est `AUTRE`.

## 2. Données

Le script [`data/prepare_claim_detection_dataset.py`](../data/prepare_claim_detection_dataset.py)
convertit le fichier Excel annoté en
[`data/processed/claim_detection_600.jsonl`](../data/processed/claim_detection_600.jsonl).

Chaque ligne conserve la traçabilité :

```json
{
  "id": "P001",
  "text": "Le prix du pain a augmenté.",
  "label": "AFFIRMATION",
  "modalite": "assertif",
  "source": "original (fr)",
  "lang": "fr",
  "script": "latin"
}
```

Le modèle apprend sur `text` et `label`. Les autres champs servent à la
traçabilité, aux résultats par langue et à l'analyse d'erreurs.

### Taille et répartition

Le corpus contient 600 phrases originales :

| Label | Nombre | Part |
| --- | ---: | ---: |
| `AFFIRMATION` | 316 | 52,7 % |
| `AUTRE` | 191 | 31,8 % |
| `OPINION` | 93 | 15,5 % |

`OPINION` est minoritaire : le modèle voit moins d'exemples et cette classe est
donc logiquement plus difficile.

### Langues

| Langue | Nombre total |
| --- | ---: |
| Tunisien (`tn`) | 290 |
| Français (`fr`) | 160 |
| Arabe standard (`ar`) | 150 |

Le tunisien comprend l'arabizi (`n7eb`, `5ayeb`, `ken`), l'écriture arabe et le
mélange français/tunisien. Soixante lignes avaient initialement `source =
original`, sans langue explicite. Elles ont été relues et la correction de
métadonnée est conservée dans `MANUAL_LANGUAGE_METADATA` ; ni les textes ni les
labels originaux n'ont été modifiés. Il n'y a désormais aucune ligne `unk`.

## 3. Protocole de test

Le fichier
[`data/splits/claim_detection_multiclass_600_seed42.json`](../data/splits/claim_detection_multiclass_600_seed42.json)
fige 120 IDs de test. Ces phrases ne sont jamais utilisées pour entraîner ou
régler le modèle.

```text
600 phrases
├── 120 test gelé (20 %) : résultat final
└── 480 restantes
    ├── 408 entraînement
    └── 72 validation
```

La validation choisit la meilleure époque durant l'entraînement. Le split est
stratifié afin de conserver autant que possible la proportion des trois labels.
Garder un même test pour tous les essais rend la comparaison fiable.

## 4. Baseline : TF-IDF + Logistic Regression

Le fichier
[`models/baselines/claim_detection_multiclass_tfidf.py`](../models/baselines/claim_detection_multiclass_tfidf.py)
est la baseline. Elle est nécessaire pour savoir si le modèle profond apporte
vraiment une amélioration.

Fonctionnement :

1. **TF-IDF de caractères**, n-grammes 3 à 5 : chaque phrase devient un vecteur
   de fragments de caractères pondérés. Les caractères conviennent mieux que
   les seuls mots aux fautes, arabizi, chiffres et mélanges d'écritures.
2. **Régression logistique** : classifieur linéaire à trois classes, avec
   `class_weight="balanced"` pour ne pas ignorer `OPINION`.

Avantages : rapide, léger, reproductible et facile à expliquer. Limite : il ne
comprend pas réellement le contexte ni la syntaxe de la phrase.

Résultat sur le test gelé :

```text
Macro-F1 TF-IDF + Logistic Regression = 0,6435
```

La macro-F1 est la moyenne des F1 de chaque classe. Elle est plus informative
que l'accuracy seule lorsque les classes sont déséquilibrées.

## 5. Modèle avancé : XLM-R + PEFT / LoRA

### Pourquoi XLM-R ?

Le modèle de base est
[`FacebookAI/xlm-roberta-base`](https://huggingface.co/FacebookAI/xlm-roberta-base).
XLM-RoBERTa est un Transformer multilingue pré-entraîné. Il peut apprendre le
contexte autour de marqueurs tels que `si`, `إذا`, `ken`, `inchallah` ou des
expressions d'opinion, ce que TF-IDF fait beaucoup moins bien.

Il est choisi car NewsCheck TN traite français, arabe standard et tunisien.

### Pourquoi LoRA ?

PEFT signifie *Parameter-Efficient Fine-Tuning*. LoRA signifie *Low-Rank
Adaptation*. Au lieu de modifier tous les poids du gros modèle XLM-R, on gèle le
modèle de base et on entraîne de petites matrices d'adaptation dans l'attention.

Cela réduit la mémoire GPU, la taille du checkpoint, le temps d'entraînement et
le risque de surapprentissage sur seulement 600 phrases. Les connaissances
multilingues pré-entraînées de XLM-R sont conservées.

### Hyperparamètres retenus

| Paramètre | Valeur | Utilité |
| --- | ---: | --- |
| Base | `FacebookAI/xlm-roberta-base` | encodeur multilingue |
| Labels | 3 | AFFIRMATION / OPINION / AUTRE |
| LoRA rank `r` | 8 | taille faible des adapters |
| `lora_alpha` | 16 | échelle LoRA |
| `lora_dropout` | 0,1 | régularisation |
| Modules LoRA | `query`, `value` | projections d'attention adaptées |
| Longueur max | 256 tokens | limite les phrases longues |
| Learning rate | `2e-4` | apprentissage des adapters |
| Batch size | 8 | compatible Colab GPU |
| Époques max | 8 | passages maximum sur train |

Le code est dans
[`models/encoders/train_xlmr_claim_detection.py`](../models/encoders/train_xlmr_claim_detection.py).

Il charge les données, crée train/validation/test, tokenise avec XLM-R, ajoute
LoRA aux modules `query` et `value`, entraîne avec Hugging Face `Trainer`,
sélectionne la meilleure époque sur la macro-F1 validation, puis écrit le
checkpoint et `test_metrics.json`.

`DataCollatorWithPadding` complète chaque batch seulement à la longueur utile.
Il évite les erreurs de dimensions variables observées lorsque les phrases ont
des longueurs différentes.

### Baseline neuronale : embeddings figés + régression logistique

Une seconde baseline utilise `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
comme encodeur multilingue figé, suivi d'une régression logistique. Elle sépare
le gain d'un espace sémantique pré-entraîné du gain du fine-tuning XLM-R. Sur le
même test gelé, elle obtient **0,6350 ± 0,0000** de macro-F1, légèrement sous
TF-IDF (0,6435). Son code est dans
[`models/baselines/claim_detection_embedding_logreg.py`](../models/baselines/claim_detection_embedding_logreg.py).

## 6. Trois entraînements avec trois seeds

Une seed fixe les aléas : initialisation, ordre des données et séparation
train/validation. Avec peu de données, un seul entraînement pourrait donner un
score par chance trop bon ou trop mauvais. Trois seeds ont été entraînées :

| Configuration | Macro-F1 test |
| --- | ---: |
| XLM-R + LoRA, seed 42 | 0,7108 |
| XLM-R + LoRA, seed 123 | 0,7715 |
| XLM-R + LoRA, seed 2026 | 0,7250 |
| Moyenne ± écart-type | **0,7357 ± 0,0317** |

XLM-R améliore donc la baseline de **0,0922** point de macro-F1 en moyenne.
L'écart-type montre toutefois une variance non négligeable : il faut rapporter
les trois scores, pas seulement le meilleur.

Le checkpoint utilisé par l'application est `seed42`. Ce choix a été fixé comme
checkpoint de référence avant la lecture des scores finaux. Prendre seed123
seulement parce qu'il est le meilleur sur le test créerait un biais de sélection
sur le test gelé.

## 7. Résultats détaillés de seed42

Le script
[`models/encoders/evaluate_claim_detection.py`](../models/encoders/evaluate_claim_detection.py)
produit `metrics.json`, `predictions.jsonl` et un fichier d'erreurs.

### Résultats globaux

| Mesure | Valeur |
| --- | ---: |
| Test | 120 phrases |
| Accuracy | 0,7917 |
| Macro-F1 | **0,7108** |
| Weighted F1 | 0,7799 |

### Résultats par classe

| Classe | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| AFFIRMATION | 0,8219 | 0,9524 | **0,8824** | 63 |
| OPINION | 0,6154 | 0,4211 | **0,5000** | 19 |
| AUTRE | 0,7941 | 0,7105 | **0,7500** | 38 |

Le modèle détecte très bien les affirmations. Il rate davantage les opinions,
notamment quand elles sont informelles ou exprimées en tunisien.

### Résultats par langue

| Langue | Taille test | Macro-F1 |
| --- | ---: | ---: |
| Français | 26 | **0,9148** |
| Arabe standard | 30 | **0,6989** |
| Tunisien | 64 | **0,6445** |

Le français est le meilleur sous-groupe. Le tunisien est le plus difficile et
aussi le plus représenté. Les sous-groupes restent petits : ces chiffres doivent
être interprétés avec prudence.

### Tableau final : trois seeds et baselines

Les baselines sont déterministes sur le test gelé ; XLM-R est résumé sur les
trois entraînements. Les chiffres sont des macro-F1 moyenne ± écart-type.

| Modèle | Global | FR (n=26) | AR (n=30) | TN (n=64) |
| --- | ---: | ---: | ---: | ---: |
| TF-IDF caractères + LR | 0,6435 ± 0,0000 | 0,5760 ± 0,0000 | 0,4778 ± 0,0000 | 0,6846 ± 0,0000 |
| MiniLM figé + LR | 0,6350 ± 0,0000 | 0,8228 ± 0,0000 | 0,8002 ± 0,0000 | 0,4886 ± 0,0000 |
| XLM-R + LoRA | **0,7357 ± 0,0317** | **0,9148 ± 0,0000** | **0,6882 ± 0,0185** | **0,6863 ± 0,0567** |

### Bootstrap apparié contre TF-IDF

Sur 1 000 réplications appariées, XLM-R seed42 gagne **+0,0673** de macro-F1
sur TF-IDF (0,7108 contre 0,6435), avec IC 95 % `[-0,0468 ; 0,1860]` et p-value
bilatérale **0,254**. L'intervalle contient zéro : sur 120 phrases, cette
amélioration observée n'est pas statistiquement significative.

### Ablation : texte brut ou normalisé

Avec seed42, le texte brut atteint 0,7108 contre **0,6671** après normalisation
A2. La différence normalisé − brut vaut −0,0436 ; bootstrap : IC 95 %
`[-0,1184 ; 0,0202]`, p = **0,188**. La baisse est plus forte en tunisien
(0,6445 → 0,5791) et arabe (0,6989 → 0,6527), tandis que le français reste à
0,9148. Le modèle retenu est donc entraîné sur texte brut.

## 8. Analyse de 30 erreurs

Le détail ligne par ligne est dans
[`docs/lot-c_error_analysis_results.md`](lot-c_error_analysis_results.md).

Seed42 possède 25 erreurs. Pour atteindre 30 exemples sans inventer de cas,
cinq erreurs d'IDs différents de seed2026 ont été ajoutées, avec le seed indiqué
pour chaque exemple. Sur les trois seeds, 32 IDs sont erronés au moins une fois,
dont **18 erreurs stables** (ratées par les trois modèles). Ces erreurs stables
sont les faiblesses les plus solides à cibler dans un futur jeu d'entraînement.

| Cause | Nombre | Exemples et interprétation |
| --- | ---: | --- |
| Hypothétique / conditionnel | 8 | `si`, `إذا`, `كان`, `ken` sont parfois traités comme faits. |
| Opinion, surtout TN arabizi/mixte | 13 | `5ayeb`, `nul`, `3ib`, `ظلم` et les recommandations TN sont mal reconnus. |
| Question, souhait, rapporté | 4 | `؟`, `ليت`, `inchallah`, `sma3t elli` sont sous-appris. |
| Assertion / frontière check-worthy | 5 | Négation, dialecte et événements personnels sont ambigus. |

Ces erreurs appartiennent au test gelé. Elles ne doivent pas être utilisées pour
réentraîner directement le modèle. Elles indiquent quelles nouvelles phrases il
faut annoter pour une version suivante, dans un jeu train/dev séparé du test.

## 9. Intégration dans l'application

Le fichier [`models/claim_detector.py`](../models/claim_detector.py) remplace
l'ancienne règle simple par le checkpoint XLM-R + LoRA.

À la première requête :

1. `_checkpoint_path()` lit `CLAIM_DETECTOR_CHECKPOINT`; sans variable, il
   utilise `models/checkpoints/claim_detection_xlmr_lora_seed42`.
2. `_load_model()` charge une seule fois le tokenizer, `PeftConfig`, le XLM-R
   de base et l'adapter LoRA.
3. `model.eval()` active le mode inférence.
4. `predict_label_and_score()` tokenise à 256 tokens, calcule les logits, puis
   applique `softmax`. Il retourne le label le plus probable et
   `P(AFFIRMATION)`.
5. `filter_checkworthy()` écrit cette probabilité dans
   `Claim.checkworthiness` et garde seulement les prédictions `AFFIRMATION`
   avec score au moins égal à `0,50`.

Le seuil est explicite : `THRESHOLD = 0.5`. Il pourra être réévalué sur un vrai
jeu de validation futur, mais ne doit pas être optimisé sur le test gelé.

Si le checkpoint ou les dépendances sont absents, le code utilise une petite
heuristique de secours afin que l'API ne tombe pas. `/health` le signale alors :

```json
{"backend": "heuristic-fallback", "status": "unavailable"}
```

Ce fallback sert seulement aux tests légers. Le résultat du projet est le
backend `xlm-r-lora`.

## 10. API et validation réelle

Les routes concernées dans [`api/main.py`](../api/main.py) sont :

- `POST /extract` : normalisation, extraction de candidats, puis Model 1 ;
- `POST /check` : pipeline complet, donc même filtre Model 1 ;
- `GET /health` : état du modèle chargé.

Les dépendances locales ont été installées avec :

```bash
python -m pip install torch transformers peft accelerate
```

L'API a été démarrée par :

```bash
python -m uvicorn api.main:app --reload
```

La réponse réelle de `GET http://127.0.0.1:8000/health` a confirmé :

```json
{
  "status": "ok",
  "version": "0.1.0",
  "claim_detector": {
    "backend": "xlm-r-lora",
    "checkpoint": ".../models/checkpoints/claim_detection_xlmr_lora_seed42",
    "status": "loaded"
  }
}
```

Au premier lancement, XLM-R de base est téléchargé depuis Hugging Face
(environ 1,12 Go). Les avertissements `UNEXPECTED` et `MISSING` au chargement
du modèle de base sont normaux : l'adapter LoRA entraîné fournit ensuite les
poids de classification. L'absence de `HF_TOKEN` peut ralentir le téléchargement
mais ne bloque pas l'inférence.

### Cohérence entraînement / inférence

Le modèle retenu est entraîné sur texte brut. L'API conserve le texte normalisé
pour Lot B, retrieval et NLI, mais produit en parallèle les phrases brutes pour
Model 1. Ainsi XLM-R reçoit la même représentation (`raw`) qu'à l'entraînement
et au test. Si les segmentations brut/normalisé ne coïncident pas, l'API revient
explicitement au texte normalisé plutôt que d'associer deux phrases différentes.

Les tests Swagger ont validé une affirmation arabe (`checkworthiness = 0,9996`),
une affirmation tunisienne arabizi (`0,9939`) et le pipeline complet avec
`POST /check` (HTTP 200). Un verdict `preuves_insuffisantes` est une abstention
normale lorsqu'aucune preuve suffisante n'est retrouvée.

### Environnement reproductible

Les résultats ont été produits sur Google Colab avec une **Tesla T4**, Python
3.13.16, torch 2.11.0+cu130, transformers 5.20.2, peft 0.21.2, accelerate
1.15.0, datasets 4.8.5, sentence-transformers 5.7.0, scikit-learn 1.6.1 et
numpy 2.1.3. La capture est disponible dans
[`evaluation/results/model1_environment.json`](../evaluation/results/model1_environment.json)
et les dépendances Model 1 sont figées dans `requirements.txt`.

Les checkpoints historiques conservent les temps de test (0,2379 s ; 0,2543 s ;
0,2442 s pour 120 phrases), mais pas leur temps d'entraînement. Le script
d'entraînement actuel écrit `training_seconds` dans tout nouveau checkpoint ;
un temps de training ne doit pas être reconstitué après coup.

## 11. Fichiers importants

```text
data/prepare_claim_detection_dataset.py                 préparation Excel -> JSONL
data/processed/claim_detection_600.jsonl                corpus Model 1
data/splits/claim_detection_multiclass_600_seed42.json  test gelé
models/baselines/claim_detection_multiclass_tfidf.py    baseline
models/encoders/train_xlmr_claim_detection.py           entraînement XLM-R + LoRA
models/encoders/evaluate_claim_detection.py             évaluation et erreurs
models/checkpoints/claim_detection_xlmr_lora_seed42/    adapter de l'API
models/claim_detector.py                                chargement et inférence
models/model_cards/claim_detection_xlmr_lora.md         Model Card courte
docs/lot-c_error_analysis_results.md                    analyse de 30 erreurs
experiments.md                                          journal des expériences
```

## 12. Limites et prochaine étape

Les limites principales sont le petit nombre de phrases, le déséquilibre de la
classe `OPINION`, et la difficulté du tunisien arabizi/mixte. La prochaine
version devra ajouter des annotations TN, des opinions, des questions, souhaits
et hypothèses, sans toucher au test actuel.

Model 1 est terminé pour cette itération : deux baselines, XLM-R + LoRA sur
trois seeds, bootstrap, ablation, analyse d'erreurs et intégration API réelle
sont disponibles. Les versions exactes du runtime et le GPU doivent être
capturés à chaque exécution dans le fichier de reproductibilité.

La prochaine tâche du Lot C est Model 2, le NLI : il attend des paires
annotées `claim`, `evidence`, `supports|refutes|neutral` livrées par Lot A1.
