# Bilan Bronze et Silver — NewsCheck TN

**Mise à jour : 26 octobre 2026**
**Périmètre : pipeline de vérification et Model 1 (Lot C)**

Ce document distingue le travail réellement exécuté des étapes qui demandent
encore un jeu de données annoté. Les scores de démonstration ne sont jamais
présentés comme des scores finaux.

## 1. Palier Bronze

### Objectif

Le Bronze est une chaîne explicable limitée au français : extraction à règles,
recherche BM25, position par lexique, verdict par gabarit, métriques et revue
d'erreurs. Aucun encodeur dense, NLI entraîné ni LLM n'est nécessaire.

### Réalisé

| Étape | Réalisation | Preuve dans le dépôt |
| --- | --- | --- |
| Extraction | Extraction des affirmations et de la modalité par règles | `linguistic_analysis/claim_extraction.py` |
| Retrieval | BM25 Okapi local, déterministe et sans dépendance externe | `rag_llm/retrieval/hybrid.py` |
| Position | Règles de recouvrement lexical, nombres et négation | `models/nli/stance.py` |
| Verdict | Gabarit `vrai` / `faux` / `trompeur` / `preuves_insuffisantes`, avec citations | `rag_llm/verdict.py` |
| Runner Bronze | Point d'entrée sans XLM-R ni LLM | `bronze/pipeline.py` |
| Métriques | Macro-F1 et Recall@k, export JSON | `bronze/evaluate.py` |
| Vérification | BM25, pipeline et évaluation couverts par des tests | `tests/test_bronze_*.py` |

### Démonstration reproductible

```powershell
python -m bronze.pipeline "Tunis est la capitale de la Tunisie."
python -m bronze.evaluate --eval data/annotations/bronze_fr_eval_demo.jsonl --corpus data/processed/evidence_corpus_fr_demo.jsonl --output evaluation/results/bronze_metrics_demo.json
```

La démo retourne `vrai` pour la première commande. La seconde retourne
`n = 2`, `macro_f1 = 1.0` et `recall_at_k = 1.0`. Ces deux cas servent
uniquement à valider le fonctionnement du code.

### Éléments restant pour valider Bronze officiellement

| Élément manquant | État | Action nécessaire |
| --- | --- | --- |
| Corpus français de preuves validées | Non livré | Ajouter des passages avec URL, source et date dans `data/processed/evidence_corpus_fr.jsonl`. |
| Gold labels de véracité | Non livré | Annoter au moins 30 affirmations en `vrai`, `faux`, `trompeur` ou `preuves_insuffisantes`. |
| Métriques officielles | Impossible sans gold labels | Lancer `python -m bronze.evaluate` sur le corpus et le jeu annoté. |
| 30 erreurs de chaîne complète | Non livré | Remplir `docs/bronze_registre_erreurs.csv` avec les erreurs réellement observées. |

Un script prépare les passages français candidats depuis les annotations locales :

```powershell
python -m bronze.prepare_review_set
```

Il crée `data/annotations/bronze_fr_review.jsonl` avec `gold_label: null`.
Ces labels doivent être vérifiés par une personne avant toute publication de
métriques. Cette étape ne peut pas être remplacée par des données inventées.

## 2. Palier Silver — Model 1

### Réalisé

| Élément | Résultat | Référence |
| --- | --- | --- |
| Baseline classique | TF-IDF caractères + régression logistique | `models/baselines/claim_detection_tfidf.py`, EXP-C-001 |
| Baseline encodeur figé | MiniLM multilingue + régression logistique | EXP-C-006 |
| Encodeur fine-tuné | XLM-RoBERTa + LoRA, trois seeds | EXP-C-002 |
| Score XLM-R | 0,7357 ± 0,0317 macro-F1 (seeds 42, 123, 2026) | EXP-C-002 |
| Score seed42 par langue | FR 0,9148 ; AR 0,6989 ; TN 0,6445 | EXP-C-003 |
| Comparaison statistique | TF-IDF 0,6435 ; XLM-R seed42 0,7108 ; p = 0,254 | EXP-C-005 |
| Ablation raw / normalisé | raw 0,7108 ; normalisé 0,6671 ; p = 0,188 | EXP-C-007 |
| Analyse d'erreurs | 30 erreurs cross-seed catégorisées | EXP-C-010 |

### Analyse des 30 erreurs Model 1

| Catégorie | Nombre |
| --- | ---: |
| Hypothèse non reconnue | 8 |
| Opinion prise pour AFFIRMATION | 7 |
| Opinion prise pour AUTRE | 6 |
| Affirmation non reconnue | 3 |
| Autre confusion | 2 |
| Souhait non reconnu | 2 |
| Question non reconnue | 1 |
| Discours rapporté non reconnu | 1 |

Le rapport complet est dans `docs/lot-c_error_analysis_cross_seed.md` ; le
fichier structuré est `evaluation/results/model1_errors_30_cross_seed.jsonl`.

### Ce qui reste à faire en Silver

- Les 30 erreurs sont documentées ; une relecture humaine des catégories est
  recommandée avant l'oral.
- Le résultat XLM-R est meilleur que TF-IDF sur seed42, mais le bootstrap ne
  rend pas ce gain statistiquement concluant sur les 120 exemples de test.
- Il faut un test plus grand et mieux équilibré pour conclure de manière forte,
  surtout sur le tunisien et les modalités non factuelles.

## 3. Conclusion pour la présentation

Le **Bronze est implémenté et démontrable**, mais il n'est pas encore validé
par des métriques officielles, faute de corpus français et de gold labels de
véracité. Le **Silver Model 1 est déjà documenté**, avec baselines, XLM-R,
trois seeds, ablation, bootstrap et 30 erreurs analysées.

Pour ne pas induire le jury en erreur, présenter les scores Bronze actuels
comme une **démo technique**, et les scores Model 1 comme les résultats
expérimentaux Silver.
