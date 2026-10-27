# Palier Bronze — pipeline française reproductible

Le palier Bronze est volontairement une version explicable, limitée au français
et sans encodeur, recherche dense ni LLM. Il sert de référence avant les
améliorations Silver.

## Chaîne exécutée

1. **Affirmations par règles** — `linguistic_analysis.extract_claims` extrait
   les propositions françaises et leur modalité.
2. **Recherche BM25** — `rag_llm.retrieval.retrieve` applique BM25 Okapi sur le
   corpus de preuves ; aucun passage de score nul n'est utilisé.
3. **Position par lexique** — `models.nli.stance.predict_stance` compare le
   recouvrement lexical, les nombres et la négation (`supports`, `refutes` ou
   `neutral`).
4. **Verdict par gabarit** — `rag_llm.verdict.generate_verdict` produit
   `vrai`, `faux`, `trompeur` ou `preuves_insuffisantes`, avec les identifiants
   des passages cités.

La commande de démonstration est :

```powershell
python -m bronze.pipeline "Tunis est la capitale de la Tunisie."
```

Ce point d'entrée est séparé de `pipeline.py`, qui garde volontairement le
Model 1 XLM-R de l'application complète et relève donc d'un périmètre Silver.

## Vérification

```powershell
pytest tests/test_bronze_bm25.py tests/test_bronze_pipeline.py tests/test_rag_llm.py tests/test_models.py
python -m linguistic_analysis.evaluate --rules --errors
```

Le premier test vérifie le classement BM25, le deuxième l'abstention si aucun
mot pertinent n'est trouvé, et le troisième le respect de `k`.

## Évaluation de bout en bout

Le script `bronze.evaluate` calcule la Macro-F1 des verdicts et Recall@k des
preuves, à partir d'un corpus de preuves et de labels annotés par l'équipe :

```powershell
python -m bronze.evaluate --eval data/annotations/bronze_fr_eval_demo.jsonl --corpus data/processed/evidence_corpus_fr_demo.jsonl --output evaluation/results/bronze_metrics_demo.json
```

Le fichier `data/annotations/bronze_fr_eval_template.jsonl` fournit le schéma
à remplir. Le registre `docs/bronze_registre_erreurs.csv` attribue un identifiant
à chaque erreur et distingue les quatre étapes de la chaîne. Il doit contenir
30 lignes complètement renseignées avant la revue.

### Préparer les exemples à relire

Les annotations de provenance déjà présentes dans le dépôt ne confirment pas
la vérité des affirmations. La commande suivante en extrait les passages FR et
crée un corpus candidat ainsi qu'une feuille de revue avec `gold_label: null` :

```powershell
python -m bronze.prepare_review_set
```

Un membre de l'équipe doit alors remplacer chaque `null` par `vrai`, `faux`,
`trompeur` ou `preuves_insuffisantes`, après vérification de la source. Copier
ensuite cette feuille annotée vers `bronze_fr_eval.jsonl` avant de calculer les
métriques officielles.

## Analyse des 30 erreurs Model 1

Si le fichier d'erreurs Model 1 est disponible, la commande suivante remplit
les catégories et produit un rapport prêt à présenter :

```powershell
python -m bronze.analyze_model1_errors C:\Users\moham\Downloads\errors_30_cross_seed.jsonl --jsonl-output evaluation/results/model1_errors_30_cross_seed.jsonl --report-output docs/lot-c_error_analysis_cross_seed.md
```

## Métriques et erreurs

- Les métriques et l'analyse des erreurs de l'extracteur à règles sont dans
  `docs/lot-b_analyse_erreurs_bronze.md` et l'expérience `EXP-B-001` de
  `experiments.md`.
- Cette analyse porte sur 34 phrases (22 affirmations), avec 25 erreurs du
  mode règles et 16 erreurs du mode parseurs. Elle n'atteint donc pas à elle
  seule l'exigence de **30 erreurs distinctes** de la fiche de revue. Il faut
  annoter au moins cinq erreurs supplémentaires de la chaîne complète
  extraction → BM25 → position → verdict avant de déclarer le Bronze validé.

Cette limite est explicitement consignée pour ne pas présenter un nombre
d'erreurs incomplet comme conforme.
