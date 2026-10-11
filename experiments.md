# Journal d'expériences — NewsCheck TN

Ce journal est **exigé par le cahier des charges du module**. Chaque expérience (entraînement,
évaluation, essai de prompt, configuration de retrieval, choix de normalisation…) y est consignée,
**y compris les échecs**. Les entrées sont ajoutées **en haut** de la section *Entrées* (plus récente d'abord).

## Format d'une entrée

```markdown
### EXP-<lot>-<NNN> — <titre court>
- **Date** : AAAA-MM-JJ
- **Auteur / Lot** : Membre X / Lot Y
- **Objectif / hypothèse** : ce qu'on cherche à vérifier
- **Données** : jeu(x) utilisé(s), version, split (train/dev/test), taille, langues
- **Méthode / configuration** : modèle, hyperparamètres, prompt, graine aléatoire
- **Code** : commit `abc1234`, fichier / notebook
- **Résultats** : métriques (par langue si possible : FR / AR / TN)
- **Analyse** : interprétation, erreurs typiques
- **Décision / suite** : retenu / abandonné / à creuser
```

Numérotation : `EXP-A1-001`, `EXP-A2-001`, `EXP-B-001`, `EXP-C-001`, `EXP-D-001`, `EXP-E-001`…

## Tableau récapitulatif

| ID | Date | Lot | Tâche | Configuration | Métrique principale | Résultat | Décision |
|----|------|-----|-------|---------------|---------------------|----------|----------|
| EXP-E-001 | 2026-10-02 | E | Squelette pipeline | stubs | — | pipeline + API OK | base de départ |
| EXP-D-002 | 2026-10-07 | D | Verdict par gabarit + abstention v1 | BM25 top-5 + NLI par règles | précision sélective / couverture | 0.92 / 0.65 ; TN 0 verdict émis | retenu pour Bronze ; LLM en S6 |
| EXP-D-001 | 2026-10-07 | D | Retrieval baseline | BM25 (k1=1.5, b=0.75), jeu de dev fictif | Hit@1 / MRR | 0.87 / 0.89 ; arabizi 0.50 | baseline retenue ; dense en S4 |
| EXP-B-001 | 2026-10-04 | B | Extraction d'affirmations (SPO, modalité, coréférence) | règles ; règles + spaCy FR / Stanza AR | modalité ; triplet SPO exact | modalité 1.00 ; SPO 0.46 (règles et parseurs) | Bronze retenu ; Silver : objets, lexique verbal |

## Entrées

### EXP-D-002 — Verdict par gabarit, NLI par règles et abstention v1 (S2–S3)
- **Date** : 2026-10-07
- **Auteur / Lot** : Membre 5 / Lot D
- **Objectif / hypothèse** : obtenir un verdict de bout en bout sans LLM ; vérifier que la politique
  d'abstention empêche tout verdict inventé quand le corpus ne contient pas de preuve.
- **Données** : `tests/fixtures/rag_llm/` v2 — 15 passages **fictifs** ; 20 affirmations avec `gold_label`
  (12 faux, 5 vrai, 1 trompeur, 2 preuves_insuffisantes). Par rapport à v1 : + 3 affirmations vraies
  (`dev-c18` à `dev-c20`). Une seule annotatrice.
- **Méthode / configuration** : BM25 (EXP-D-001), top-5 → NLI par règles `rag_llm/baseline_stance.py`
  (recouvrement de mots ≥ 0.5 sur radicaux de 5 lettres ; nombres hors années : égaux → soutient,
  différents → contredit ; sinon marqueurs de démenti FR/AR → contredit) → verdict par gabarit
  `rag_llm/verdict.py` (MIN_RETRIEVAL_SCORE = 1.0, MIN_CONFIDENCE = 0.6, CONFLICT_MARGIN = 0.25,
  incertitude ≥ 0.1). Déterministe.
- **Code** : `python -m rag_llm.evaluate_verdict` (`--stance rules`).
- **Résultats** :

  | Groupe | n | Exactitude | Couverture | Précision sélective | Abstention justifiée |
  |--------|---|------------|------------|---------------------|----------------------|
  | Global | 20 | 0.70 | 0.65 | 0.92 | 1.00 |
  | fr-latin | 11 | 0.82 | 0.82 | 0.89 | 1.00 |
  | ar-arabic | 4 | 1.00 | 1.00 | 1.00 | — |
  | tn-arabic | 2 | 0.00 | 0.00 | — | — |
  | tn-arabizi | 3 | 0.33 | 0.00 | — | 1.00 |

  Macro-F1 (4 labels) 0.52 ; citations invalides 0 ; abstentions : 4 « preuves non décisives »,
  3 « aucune preuve ». Avec `--stance lot-c` (stub neutre) : couverture 0, exactitude 0.10.
  Retrieval re-mesuré sur v2 : Hit@1 0.89, Recall@5 0.67, MRR 0.91.
- **Analyse** : quand le système tranche, il a presque toujours raison (12/13) ; la seule erreur est
  `dev-c13` (`trompeur` attendu, `faux` prédit), label que le gabarit ne sait pas produire. Les
  abstentions viennent du tunisien et de l'arabizi (vocabulaire différent de la preuve → recouvrement
  < 0.5) et de `dev-c08` (« bac » ≠ « baccalauréat »). Aucune affirmation sans preuve n'a reçu de
  verdict. Les règles ont été écrites en voyant le jeu de dev : résultats **optimistes**, à refaire sur
  des données réelles et un jeu de test gelé.
- **Décision / suite** : retenu comme verdict de la démo Bronze. S4–S5 : retrieval dense/hybride
  (et recalibrer MIN_RETRIEVAL_SCORE) ; S6 : LLM avec prompt contraint, comparé à ce gabarit ;
  remplacer le NLI par règles par le modèle du Lot C dès qu'il est disponible.

### EXP-D-001 — Retrieval BM25, baseline S1
- **Date** : 2026-10-07
- **Auteur / Lot** : Membre 5 / Lot D
- **Objectif / hypothèse** : disposer d'une baseline lexicale mesurée avant le retrieval dense ;
  vérifier où BM25 échoue (croisement FR ↔ AR, tunisien, arabizi).
- **Données** : `tests/fixtures/rag_llm/` — 15 passages **fictifs** (8 FR, 7 AR) et 17 affirmations
  (9 FR dont 1 sans preuve, 3 AR, 2 TN lettres arabes, 3 arabizi dont 1 sans preuve), preuves attendues
  annotées par une seule personne. Jeu de développement, pas un jeu de test.
- **Méthode / configuration** : BM25 Okapi en Python pur, k1 = 1.5, b = 0.75, IDF Lucene ;
  normalisation de recherche (accents, harakat, hamzas, ة → ه, ى → ي, article ال retiré, mots vides
  FR/AR) ; passages de score nul exclus. Déterministe.
- **Code** : `rag_llm/retrieval/{text,bm25,hybrid}.py`, `python -m rag_llm.evaluate_retrieval`.
- **Résultats** (top-10) :

  | Groupe | n | Hit@1 | Hit@5 | Recall@5 | MRR |
  |--------|---|-------|-------|----------|-----|
  | Global | 15 | 0.87 | 0.93 | 0.60 | 0.89 |
  | fr-latin | 8 | 1.00 | 1.00 | 0.63 | 1.00 |
  | ar-arabic | 3 | 1.00 | 1.00 | 0.67 | 1.00 |
  | tn-arabic | 2 | 0.50 | 1.00 | 0.50 | 0.67 |
  | tn-arabizi | 2 | 0.50 | 0.50 | 0.50 | 0.50 |

  Score BM25 du 1er passage : 1.07 à 11.7 quand il est correct ; 0.0 pour les 2 affirmations sans preuve.
- **Analyse** : Recall@5 plafonne vers 0.6 car BM25 ne relie jamais une affirmation française à la
  preuve arabe équivalente (et inversement) : aucun mot commun. L'arabizi n'aboutit que s'il partage un
  chiffre avec la preuve (« 37 »). Le tunisien en lettres arabes passe partiellement grâce aux mots
  communs avec l'arabe standard (« زيت », « الماء »). Jeu minuscule et fictif : chiffres optimistes.
- **Décision / suite** : baseline retenue. S4 : retrieval dense multilingue (attendu : gain sur le
  croisement FR ↔ AR) ; translittération arabizi du Lot A2 ; refaire l'évaluation sur le corpus réel A1.

### EXP-B-001 — Extracteur à règles, palier Bronze
- **Date** : 2026-10-04
- **Auteur / Lot** : Membre 3 / Lot B
- **Objectif / hypothèse** : mesurer l'extracteur du Lot B (affirmation vérifiable, modalité, triplet
  sujet-prédicat-objet, coréférence) dans les 3 langues / écritures, avec et sans parseur.
- **Données** : `tests/fixtures/linguistic_analysis/eval_30.jsonl`, 34 phrases rédigées pour
  l'évaluation (10 FR, 10 arabe standard, 5 tunisien en lettres arabes, 5 arabizi, 4 mixtes FR/TN),
  22 affirmations, 3 cas de coréférence ; annotation simple (un annotateur) selon
  `docs/lot-b_guide_annotation.md`, cas difficiles déclarés avant exécution.
- **Méthode / configuration** : règles (lexiques FR / AR / TN, patrons positionnels) ; mode « parseurs » :
  spaCy 3.8 `fr_core_news_md` et Stanza 1.15 `ar` (UD), repli sur les règles pour le tunisien ;
  texte normalisé par `normalization.normalize` ; comparaison sur formes repliées. Déterministe (pas de graine).
- **Code** : 1ᵉʳ passage = code de `26a6064` avec le jeu et le script d'évaluation (commités ensuite
  dans `3c0c382`) ; 2ᵉ passage = `3c0c382` (après corrections) ; `linguistic_analysis/evaluate.py`
  (`--rules`, `--errors`).
- **Résultats** :
  - 1ᵉʳ passage — règles : détection 0.97, modalité 0.97, triplet exact 0.41, coréférence 0.67 ;
    parseurs : détection 0.97, modalité 1.00, triplet 0.46, coréférence 1.00.
  - 2ᵉ passage — règles : détection 1.00 (macro-F1 1.00), modalité 1.00, sujet / prédicat / objet
    0.59 / 0.68 / 0.64, triplet 0.46, coréférence 0.67 ; parseurs : détection 1.00, modalité 1.00,
    0.91 / 0.86 / 0.50, triplet 0.46, coréférence 1.00.
  - Triplet exact par groupe (règles / parseurs) : FR 0.50 / 0.50 ; AR 0.29 / 0.43 ;
    TN lettres arabes 0.50 / 0.00 ; arabizi 0.67 / 0.67 ; mixte 0.50 / 0.50.
- **Analyse** : `docs/lot-b_analyse_erreurs_bronze.md`. Sans parseur, erreurs dominées par le lexique
  verbal (13/25, surtout arabe standard) ; avec parseur, par le choix de l'objet (compléments de temps,
  sources) et des arbres faux (12/16). Deux erreurs liées au traitement amont (tā' marbūṭa, tunisien
  analysé comme arabe standard). Les 3 corrections entre les passages ont été faites en voyant le jeu :
  scores du 2ᵉ passage optimistes ; jeu petit et annoté par une seule personne.
- **Décision / suite** : palier Bronze retenu. Silver : règle d'objet (temps / lieu / source), lexique
  verbal et morphologie du mode règles, jeu d'environ 100 phrases en partie issues d'articles réels avec
  double annotation ; points amont à discuter avec le Lot A2.

### EXP-E-001 — Squelette du pipeline bout-en-bout
- **Date** : 2026-10-02
- **Auteur / Lot** : Lot E
- **Objectif / hypothèse** : disposer d'un pipeline exécutable de bout en bout avec des stubs par lot.
- **Données** : échantillon de 2 passages intégré à `data/loaders.py`.
- **Méthode / configuration** : heuristiques simples (regex, recouvrement lexical), NLI neutre.
- **Code** : commit initial, `pipeline.py`
- **Résultats** : 22 tests passent ; le pipeline s'abstient (attendu, NLI non implémentée).
- **Analyse** : —
- **Décision / suite** : chaque lot remplace son stub.
