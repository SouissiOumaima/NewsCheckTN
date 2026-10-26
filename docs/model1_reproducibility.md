# Model 1 — Reproductibilité

## Environnement d'entraînement

Environnement effectivement utilisé pour les résultats rapportés : **Google
Colab, Tesla T4, Python 3.13.16**, Linux 6.6.122+. Versions : torch
2.11.0+cu130, transformers 5.20.2, peft 0.21.2, accelerate 1.15.0, datasets
4.8.5, sentence-transformers 5.7.0, scikit-learn 1.6.1 et numpy 2.1.3. La
capture machine est archivée dans
[`evaluation/results/model1_environment.json`](../evaluation/results/model1_environment.json).

Les scores de référence sont produits sur Google Colab avec GPU. Avant une
nouvelle exécution, lancer depuis la racine du dépôt :

```bash
python -m models.evaluation.capture_environment \
  --output evaluation/results/model1_environment.json
```

Le fichier généré conserve la version Python, le système, le nom du GPU ainsi
que les versions exactes de `torch`, `transformers`, `peft`, `accelerate`,
`datasets`, `sentence-transformers`, `scikit-learn` et `numpy`. Il doit être
archivé avec les résultats : ne pas le remplacer manuellement par les versions
du poste Windows d'inférence.

## Configurations de référence

| Système | Données | Test | Seeds |
| --- | --- | --- | --- |
| TF-IDF caractères 3–5 + LR | 480 train | 120 IDs gelés | 42, 123, 2026 |
| MiniLM figé + LR | 480 train | 120 IDs gelés | 42, 123, 2026 |
| XLM-R + LoRA | 408 train + 72 validation | 120 IDs gelés | 42, 123, 2026 |

Le test est fixé par
`data/splits/claim_detection_multiclass_600_seed42.json`. Les 120 IDs ne
servent ni au choix d'époque ni au réglage des hyperparamètres. La séparation
train/validation des 480 autres exemples varie avec la seed et cette limite est
déclarée dans le rapport.

## Commandes XLM-R retenues

```bash
python -m models.encoders.train_xlmr_claim_detection \
  --input data/processed/claim_detection_600.jsonl \
  --split-file data/splits/claim_detection_multiclass_600_seed42.json \
  --seed 42 \
  --text-mode raw \
  --output-dir models/checkpoints/claim_detection_xlmr_lora_seed42

python -m models.encoders.evaluate_claim_detection \
  --input data/processed/claim_detection_600.jsonl \
  --split-file data/splits/claim_detection_multiclass_600_seed42.json \
  --checkpoint models/checkpoints/claim_detection_xlmr_lora_seed42 \
  --text-mode raw \
  --output-dir evaluation/results/xlmr_seed42_raw
```

`test_metrics.json` écrit par l'entraînement conserve aussi le temps total et
le device de chaque run. Pour une comparaison honnête, rapporter ce temps avec
le nom du GPU généré ci-dessus, plutôt qu'un temps d'inférence local.

Les anciens checkpoints enregistrent le temps de test, pas le temps total de
training : seed42 **0,2379 s**, seed123 **0,2543 s**, seed2026 **0,2442 s** pour
les 120 phrases. Le script actuel écrit désormais `training_seconds` dans tout
nouveau `test_metrics.json`. Pour déclarer un temps d'entraînement comparable
pour les trois seeds, il faut donc relancer les trois runs ou conserver leurs
logs initiaux ; aucun chiffre n'est rétroactivement inventé.

## Inference

Le checkpoint de référence API est `seed42`, fixé avant lecture des résultats
du test. Model 1 est entraîné en `raw` et l'API lui transmet les phrases brutes
correspondantes. La version normalisée reste utilisée pour les modules A2/B,
retrieval et NLI.
