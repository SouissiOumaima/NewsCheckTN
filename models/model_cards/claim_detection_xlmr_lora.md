# Model Card — Model 1 : détection d'affirmations vérifiables

## Résumé

Ce modèle classe une phrase en `AFFIRMATION`, `OPINION` ou `AUTRE`. Dans le
pipeline NewsCheck TN, seule une prédiction `AFFIRMATION` avec une probabilité
d'au moins 0,50 est transmise aux étapes retrieval et NLI. Ce n'est ni un
fact-checker ni un modèle de véracité : une affirmation fausse peut être
`AFFIRMATION`.

## Modèle et entraînement

- Base : `FacebookAI/xlm-roberta-base`.
- Adaptation : PEFT / LoRA, rang 8, alpha 16, dropout 0,1, modules `query` et
  `value`.
- Tâche : classification de séquences à trois classes.
- Longueur maximale : 256 tokens ; 8 époques ; learning rate `2e-4` ; batch 8.
- Checkpoint utilisé par défaut dans l'API : `claim_detection_xlmr_lora_seed42`.
  Ce choix est fixé avant l'évaluation finale : il ne sélectionne pas le seed
  gagnant sur le test gelé.

## Données

`data/processed/claim_detection_600.jsonl` contient 600 phrases d'origine
annotées pour le Model 1 : 316 `AFFIRMATION`, 93 `OPINION`, 191 `AUTRE`.
Le jeu de test est figé à 120 exemples dans
`data/splits/claim_detection_multiclass_600_seed42.json`. Pour chaque seed,
les 480 exemples restants sont séparés en 408 entraînement et 72 validation.

Les langues attendues sont le français (FR), l'arabe standard (AR) et le
tunisien (TN, arabe ou arabizi). Les 60 phrases dont la métadonnée source était
générique `original` ont été ajoutées explicitement dans la table
`MANUAL_LANGUAGE_METADATA` du script de préparation. Cette révision est
traçable, sans modification du texte ou du label original.

## Résultats connus

Évaluation macro-F1 à trois classes sur le même test gelé de 120 phrases :

| Système | Macro-F1 |
| --- | ---: |
| TF-IDF caractères (3–5) + régression logistique | 0,6435 |
| Embeddings MiniLM figés + régression logistique | 0,6350 |
| XLM-R + LoRA — seed 42 | 0,7108 |
| XLM-R + LoRA — seed 123 | 0,7715 |
| XLM-R + LoRA — seed 2026 | 0,7250 |
| XLM-R + LoRA — moyenne ± écart-type | 0,7357 ± 0,0317 |

Résultats XLM-R par langue, moyenne ± écart-type sur trois seeds : FR
0,9148 ± 0,0000 ; AR 0,6882 ± 0,0185 ; TN 0,6863 ± 0,0567. Le bootstrap apparié
seed42 contre TF-IDF donne +0,0673 [−0,0468 ; 0,1860], p = 0,254 : l'amélioration
observée n'est pas statistiquement significative sur 120 exemples.

## Utilisation prévue

- Aider à prioriser les énoncés vérifiables dans NewsCheck TN.
- Français, arabe standard et tunisien, sous réserve de validation par langue.
- L'API charge le checkpoint local indiqué par `CLAIM_DETECTOR_CHECKPOINT` ou,
  par défaut, `models/checkpoints/claim_detection_xlmr_lora_seed42`.

## Limites et risques

- Petit corpus (600 exemples) : les résultats peuvent varier selon la division
  ou la formulation.
- Les performances TN sont particulièrement sensibles au dialecte, à l'arabe
  mélangé et à l'arabizi.
- Une annotation erronée ou ambiguë se propage au modèle; les labels originaux
  doivent être validés par les responsables de l'annotation.
- Ne pas utiliser comme verdict factuel, source journalistique, ou décision à
  enjeu élevé sans vérification humaine et sources.

## Reproductibilité et suivi

Les commandes d'entraînement sont dans
`models/encoders/train_xlmr_claim_detection.py`; l'évaluation détaillée et le
fichier de 30 erreurs sont générés par
`models/encoders/evaluate_claim_detection.py`. Les paramètres et scores sont
aussi consignés dans `experiments.md`.

Le modèle est entraîné sur texte brut. Dans l'API, le texte brut est utilisé
pour l'inférence Model 1 ; le texte normalisé reste réservé aux étapes
linguistiques et de retrieval. Cette séparation garantit que l'inférence
correspond au protocole d'évaluation.
