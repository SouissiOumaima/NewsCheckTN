# Analyse d'erreurs — Model 1

Ne pas inventer les 30 exemples : ils doivent provenir des prédictions du
checkpoint réellement déployé sur le test gelé.

## Génération

Depuis Colab ou un environnement avec PyTorch, `transformers`, `peft` et
`scikit-learn` :

```bash
python -m models.encoders.evaluate_claim_detection \
  --input data/processed/claim_detection_600.jsonl \
  --split-file data/splits/claim_detection_multiclass_600_seed42.json \
  --checkpoint models/checkpoints/claim_detection_xlmr_lora_seed42 \
  --output-dir evaluation/results/model1_seed42 \
  --max-errors 30
```

Le script produit :

- `metrics.json` : macro-F1 globale et par `fr`, `ar`, `tn`, `unk` ;
- `predictions.jsonl` : toutes les prédictions du test gelé ;
- `errors_to_review_30.jsonl` : les 30 premières erreurs, avec texte, gold,
  prédiction et confiance.

## Revue humaine

Pour chaque ligne de `errors_to_review_30.jsonl`, remplir `error_category` et
`review_note`. Catégories recommandées :

- `ambiguite_guide` — la règle ou la phrase est raisonnablement ambiguë ;
- `modalite` — question, souhait, hypothèse, conditionnel ou discours rapporté ;
- `opinion_vs_affirmation` — jugement avec ou sans contenu vérifiable ;
- `langue_script` — arabe standard, tunisien, arabizi ou mélange ;
- `contexte_implicite` — manque de contexte ;
- `annotation_a_verifier` — label de référence potentiellement discutable ;
- `autre`.

Les 60 lignes initialement `lang=unk` sont maintenant renseignées dans
`MANUAL_LANGUAGE_METADATA` de `data/prepare_claim_detection_dataset.py`.
Après toute modification de cette table, régénérer le JSONL avant de calculer
les résultats FR/AR/TN.
