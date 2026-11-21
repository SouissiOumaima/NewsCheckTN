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
| EXP-D-010 | 2026-11-15 | D | Silver officiel : verdict par LLM ouvert ≤ 8 Md contraint aux preuves | CohereLabs/aya-expanse-8b (4 bits, Colab T4), même prompt v1 et mêmes contrôles qu'EXP-D-009, température 0.3, 3 graines locales (13, 42, 2026) ; recherche hybride (EXP-D-008) ; 4 ablations ; bootstrap apparié 10 000 tirages ; aucune donnée envoyée à une API | exactitude / macro-F1 du verdict (test, 21 affirmations) | LLM 0.730 ± 0.028 / 0.410 ± 0.016 (graine 42 : 0.714 / 0.401) vs gabarit + NLI Bronze 0.286 / 0.219 (+0.429, IC95 [0.143 ; 0.714], p = 0.004) et majorité 0.524 / 0.172 (exactitude +0.19, p = 0.055 ; macro-F1 +0.23, p = 0.004) ; couverture 1.00, abstention justifiée 0.00 ; tunisien 0.8 ; 0 citation invalide | résultat officiel du Silver ; exact mais jamais d'abstention (3 affirmations sans preuve jugées « faux ») ; suite : contrôle de pertinence avant le LLM, abstention évaluée (Gold) |
| EXP-D-009 | 2026-11-15 | D | Comparaison (non officiel) : verdict par LLM contraint, API Gemini | gemini-3.5-flash-lite (API gratuite), prompt v1 figé sur le dev (JSON imposé, citations limitées aux passages fournis, abstention), température 0.3 ; recherche hybride (EXP-D-008) ; 3 exécutions ; 4 ablations ; bootstrap apparié 10 000 tirages | exactitude / macro-F1 du verdict (test, 21 affirmations) | LLM 0.810 / 0.844 (3 exécutions : 0.762 ± 0.048 / 0.809 ± 0.032) vs gabarit + NLI Bronze 0.286 / 0.219 (+0.524, IC95 [0.333 ; 0.714]) et majorité 0.524 / 0.172 ; précision sélective 1.00 ; tunisien 0.0 → 0.6 ; 0 citation invalide | comparaison seulement (modèle > 8 Md, données envoyées à une API) ; officiel : EXP-D-010 ; erreurs restantes = abstentions dues à la recherche (langue croisée, arabizi) ; suite : contamination (Gold), NLI fine-tuné |
| EXP-D-008 | 2026-11-14 | D | Silver : recherche dense et hybride sur le test gelé | BM25 / dense e5-base / hybride RRF (BM25 + e5-base, k = 60, retenu a priori sur le dev) ; ablations sans seuil dense et e5-small ; top 5 ; bootstrap apparié 10 000 tirages, graine 42 | Rappel@5 / MRR (test, 18 affirmations avec preuve) | hybride 0.446 / 0.646 vs BM25 0.411 / 0.630 (R@5 +0.035, IC95 [-0.022 ; 0.111], p = 0.17) ; dense seul 0.394 / 0.630 ; fr 0.357 → 0.429 ; dev 0.944 vs 0.667 (EXP-D-003 reproduit) | hybride e5-base retenu pour le Silver ; gain non significatif sur le test ; suite : verdict (NLI fine-tuné du Lot C, LLM contraint) |
| EXP-C-015 | 2026-11-18 | C | NLI (Model 2) palier Gold : seuil d'abstention (« neutral » sous τ) | règle fixée avant calcul ; affiné choisi sur la val (33), zero-shot sur train + val (207) ; critère macro-F1, marge 0.03 / 0.01, plus petit τ ; test non lu | macro-F1 sur les données de choix | affiné : τ = 0 (meilleur 0.738 à τ = 0.80 contre 0.722 sans seuil, dans la marge) ; zero-shot : τ = 0 (0.722 à τ = 0.65 contre 0.714) | aucun seuil retenu ; rien à transmettre au Lot D ni à mesurer |
| EXP-C-014 | 2026-11-18 | C | NLI (Model 2) palier Gold : biais par langue et par source | prédictions Silver d'EXP-C-011 relues, sans nouvelle inférence ; groupes fixés avant calcul ; bootstrap 1000 tirages, graine 20261026 ; règle n ≥ 10 | accuracy et macro-F1 par groupe (test, n = 56) | principal fr 0.760 / ar 0.871 (acc.), écart −0.111 [−0.311 ; +0.090] ; tunifact.org 0.833 (48) / nawaat.org 0.750 (8) ; 2 articles = 25 paires sur 56, 0 erreur du principal sur eux ; sujet (22/11, catégories du Lot A1 tirées des titres) : 2 catégories ≥ 10 paires, Environnement & sciences − reste +0.087 [−0.115 ; +0.275], Société & migrations − reste +0.075 [−0.125 ; +0.263] | aucun écart établi (IC larges) ; test trop concentré pour un biais de source ou de sujet (sujet confondu avec l'article) |
| EXP-C-013 | 2026-11-18 | C | NLI (Model 2) palier Gold : robustesse aux paraphrases | protocole seulement : paraphrases humaines des 56 affirmations du test, même preuve et même label, double vérification, gel SHA-256 avant une mesure unique | taux de changement de prédiction ; macro-F1 | non mesuré | paraphrases générées par IA (Claude) le 18/11, non relues ; sans relecture, résultat exploratoire |
| EXP-C-012 | 2026-11-18 | C | NLI (Model 2) palier Gold : transfert vers le tunisien (question de recherche) | protocole seulement : 56 affirmations du test réécrites en tunisien (lettres arabes obligatoire, arabizi en bonus) par des humains, même preuve et même label, double vérification, gel SHA-256 avant une mesure unique | macro-F1 ; écart apparié tunisien − original | non mesuré | réécritures générées par IA (Claude) le 18/11, relecture par Mouhib prévue ; sans relecture, résultat exploratoire |
| EXP-C-011 | 2026-11-10 | C | NLI (Model 2) palier Silver : fine-tuning mDeBERTa-v3 xnli | protocole fixé avant mesure : hyperparamètres choisis sur val seulement, 3 graines, ablation mDeBERTa-v3-base sans XNLI ; règle v3 / v4 fixée le 10/11 | macro-F1 (test, n = 56) | principal 0.809 ± 0.000 (3 graines) vs zero-shot float32 0.798 (+0.011, IC95 [−0.052 ; +0.071], p = 0.40), Bronze 0.471, majorité 0.194 ; fr 0.745 / ar 0.841 ; ablation sans XNLI 0.427 ± 0.044 | composant Silver : modèle affiné (graine 42), déclaré équivalent au zero-shot (gardé comme backend) ; chiffres v3 (pas de v4 au 12/11) |
| EXP-C-009 | 2026-10-26 | C | NLI (Model 2) palier Bronze : position par lexique | règles (recouvrement, nombres, marqueurs de démenti, négation) ; seuils 0.35 / 0.4 choisis sur train + val ; corpus NLI A1 v3 | macro-F1 (test, n = 56) | 0.471 [IC95 0.33–0.59] vs 0.194 classe majoritaire ; fr 0.50 / ar 0.40 ; ablation TF-IDF 0.405, TF-IDF + lexique 0.534 | composant Bronze de la démo (NLI_BACKEND=bronze par défaut) |
| EXP-C-008 | 2026-10-26 | C | NLI (Model 2) : baseline sans entraînement | mDeBERTa-v3-base xnli (zero-shot), corpus NLI A1 v3, test gelé 56 paires | macro-F1 (test) | 0.798 [IC95 0.67–0.89] ; acc 0.804 ; fr 0.78 / ar 0.78 ; articles Lot D 0.77 | référence hors démo (backend `zero-shot` optionnel) ; chiffres officiels sur v4 |
| EXP-C-010 | 2026-10-25 | C | Détection d'affirmations (Model 1) palier Bronze : TF-IDF caractères | TF-IDF `char_wb` 3–5 + régression logistique `class_weight=balanced`, 600 phrases annotées, split 480 / 120 stratifié, graine 42 | macro-F1 (test, n = 120) | 0.643 vs 0.230 classe majoritaire ; fr 0.58 / ar 0.48 / tn-arabe 0.70 / arabizi 0.55 / mixte 0.81 | composant Bronze de la démo (CLAIM_DETECTOR_BACKEND=tfidf par défaut) |
| EXP-C-007 | 2026-10-24 | C | Ablation raw vs normalisé | XLM-R + LoRA, seed42, test gelé | macro-F1 ; bootstrap | raw 0,7108 vs normalisé 0,6671 ; p=0,188 | raw retenu ; API alignée sur raw |
| EXP-C-006 | 2026-10-24 | C | Baseline neuronale | MiniLM figé + LR, 3 runs | macro-F1 | 0,6350 ± 0,0000 | baseline de comparaison conservée |
| EXP-C-005 | 2026-10-24 | C | Bootstrap apparié | TF-IDF vs XLM-R seed42, 1 000 réplications | Δ macro-F1 ; IC 95 % ; p | +0,0673 ; [-0,0468 ; 0,1860] ; p=0,254 | gain non concluant statistiquement |
| EXP-C-003 | 2026-10-23 | C | Évaluation détaillée XLM-R + LoRA | seed 42, test gelé 120 | macro-F1 | 0.7108 ; FR 0.9148 / AR 0.6989 / TN 0.6445 | analyse d'erreurs à compléter |
| EXP-E-001 | 2026-10-02 | E | Squelette pipeline | stubs | — | pipeline + API OK | base de départ |
| EXP-D-007 | 2026-10-26 | D | Palier Bronze : baselines triviales, verdict avec le NLI Bronze du Lot C, erreurs | BM25 top-5 + NLI Bronze (Lot C) + gabarit ; test Tunifact v1 gelé | Rappel@5 ; exactitude et macro-F1 du verdict | Rappel@5 0.411 vs 0.060 (aléatoire) ; verdict exact. 0.238 vs 0.524 (majorité), macro-F1 0.188 vs 0.172 ; 40 + 16 erreurs classées | configuration Bronze retenue ; suite : translittération A2, jeu de test élargi |
| EXP-D-006 | 2026-10-23 | D | Jeu réel Tunifact v1 (6 articles) | BM25 + NLI par règles + gabarit, sans réglage | Hit@1 / Recall@5 ; exactitude verdict | 0.61 / 0.41 ; verdict 0.14, 1 verdict émis (faux) | nouvelle référence de test ; dense à mesurer (Colab) |
| EXP-D-005 | 2026-10-20 | D | NLI par règles v2 : lecture des nombres | milliers, ×ألف/mille, nombres collés à un nom ignorés | verdicts faux émis (Tunifact) | 3 → 1 ; exactitude 0.20 inchangée ; dev inchangé | retenu ; reste : phrase de verdict qui reprend la rumeur |
| EXP-D-004 | 2026-10-20 | D | 1re évaluation sur données réelles (Tunifact, Lot A1) | BM25 + NLI par règles + gabarit | Hit@1 / Recall@5 ; exactitude verdict | 0.83 / 0.54 ; verdict 0.20, 3 verdicts émis tous faux | NLI par règles inutilisable sur données réelles ; seuil BM25 invalide |
| EXP-D-003 | 2026-10-19 | D | Retrieval dense + hybride RRF | MiniLM / e5-small / e5-base / bge-m3, RRF k=60 | Recall@5 / MRR | hybride e5-base 0.94 / 0.96 (BM25 0.67 / 0.91) ; verdict inchangé | e5-base retenu ; NLI = goulot ; re-ranking S5 |
| EXP-D-002 | 2026-10-07 | D | Verdict par gabarit + abstention v1 | BM25 top-5 + NLI par règles | précision sélective / couverture | 0.92 / 0.65 ; TN 0 verdict émis | retenu pour Bronze ; LLM en S6 |
| EXP-D-001 | 2026-10-07 | D | Retrieval baseline | BM25 (k1=1.5, b=0.75), jeu de dev fictif | Hit@1 / MRR | 0.87 / 0.89 ; arabizi 0.50 | baseline retenue ; dense en S4 |
| EXP-B-001 | 2026-10-04 | B | Extraction d'affirmations (SPO, modalité, coréférence) | règles ; règles + spaCy FR / Stanza AR | modalité ; triplet SPO exact | modalité 1.00 ; SPO 0.46 (règles et parseurs) | Bronze retenu ; Silver : objets, lexique verbal |
| EXP-A2-001 | 2026-10-06 | A2 | Normalisation + identification de langue et de script | règles : stub vs v1 | exactitude langue (eval_30) ; cas FR ciblés | 0.82 sur 34 phrases (stub = v1) ; 5 cas ciblés : 0 → 5 bien classés | v1 retenue ; suite : classifieur TN |
| EXP-A2-002 | 2026-10-07 | A2 | Tunisien en lettres arabes | règle : lexique de 78 marques + négation | langue TN sur eval_30 ; rappel TN sur échantillon annoté | eval_30 (14 phrases TN) : 8 → 12 bien classées ; échantillon (78 TN, 15 standard) : 41 TN et 15 standard bien classées | règle retenue comme référence ; suite : classifieur |
| EXP-A2-003 | 2026-10-07 | A2 | Arabizi sans chiffre (français ou tunisien ?) | régression logistique sur n-grammes de caractères 1-4 ; seuil 5.0 | fausses alertes sur français de test ; rappel TN sur échantillon annoté | 0 sur 416 phrases FR de test ; échantillon (67 TN, 16 FR) : TN 0 → 61 bien classées, FR 12 | modèle retenu ; suite : biais de sujet « tunisiens », règle du seuil |
| EXP-B-002 | 2026-10-07 | B | Extraction d'affirmations : compléments de source / temps / lieu hors objet | règles ; règles + spaCy FR / Stanza AR | triplet SPO exact | SPO 0.64 (règles) ; 0.77 (parseurs) | retenu ; suite : lexique verbal du mode règles |
| EXP-B-003 | 2026-10-15 | B | Extraction d'affirmations : lexique verbal du mode règles, sujet verbe-sujet-objet | règles ; règles + spaCy FR / Stanza AR | triplet SPO exact | SPO 0.86 (règles) ; 0.77 (parseurs) | retenu ; suite : jeu d'environ 100 phrases |
| EXP-B-004 | 2026-10-15 | B | Extraction d'affirmations : source du discours rapporté, complément du participe dans le sujet | règles ; règles + spaCy FR / Stanza AR | triplet SPO exact | SPO 0.91 (règles) ; 0.77 (parseurs) | retenu ; jeu de dev saturé |
| EXP-A2-004 | 2026-10-19 | A2 | Reproductibilité : échantillons annotés et lexique | `normalization.annotation`, `normalization.lexicon` | tirage refait ; lexique retrouvé ; fausses alertes sur la presse | 100/100 et 100/100 ; 55/78 (+ 23 variantes) ; 0/1 589 | tout est refaisable ; suite : kappa, presse d'une autre source |
| EXP-A2-005 | 2026-10-19 | A2 | Biais de sujet : noms de lieux tunisiens | 8 lieux ajoutés aux mots neutres ; modèle inchangé | bascules français → arabizi ; arabizi perdu par le pipeline | 22 → 0 ; 13 sur 7 363, dont 8 en réalité français | liste élargie retenue ; suite : réentraîner, retirer le français des corpus arabizi |
| EXP-B-005 | 2026-10-20 | B | Extraction d'affirmations : lexiques selon l'écriture, verbe de parole précédé de « و » / « ف » collé | règles ; règles + spaCy FR / Stanza AR | sorties eval_30 inchangées ; tests ciblés | eval_30 identique (SPO 0.91 / 0.77) ; effet non mesuré sur un jeu annoté | retenu ; mesure sur eval_100 |
| EXP-B-006 | 2026-10-26 | B | Extraction d'affirmations : prise en compte du tunisien en lettres arabes identifié `tn` par le Lot A2 (PR #3) | règles ; règles + spaCy FR / Stanza AR ; code du Lot B inchangé | triplet SPO exact | parseurs 0.77 → 0.86 (7 → 5 erreurs) ; règles 0.91 inchangé (4 erreurs) | liste d'erreurs attendues mise à jour ; mesure sur eval_100 |
| EXP-B-007 | 2026-10-27 | B | Baselines triviales sur eval_30 (palier Bronze) | détection « toute phrase = affirmation » ; modalité « classe majoritaire » ; SPO par position (prédicat = premier mot du lexique verbal du mode règles, sujet = premier mot de 3 lettres ou plus, objet = mot suivant le prédicat) ; bootstrap graine 20261015, 1000 tirages | exactitude de détection ; exactitude de modalité ; SPO exact | détection 0.647 vs 1.000 ; modalité 0.412 vs 1.000 ; triplet exact 0.000 vs 0.909 (règles) et 0.864 (parseurs) | baselines retenues pour la revue Bronze ; scores sur jeu de mise au point (optimistes) ; suite : eval_100 |
| EXP-B-008 | 2026-10-28 | B | Mesure sur le pilote de 60 textes (deux annotateurs indépendants) | extracteur du Lot B en mode règles, sans modification ; gold d'Achraf, gold de Ghofrane et consensus ; accord entre annotateurs (agreement.py) | détection (exactitude, précision, rappel) ; modalité (exactitude, macro-F1) ; kappa de Cohen | détection 0.617 vs 0.533 (Achraf), 0.767 vs 0.683 (Ghofrane) ; modalité 0.567 vs 0.533 et 0.467 vs 0.433 ; kappa label 0.615, modalité 0.390 | résultats provisoires (60 textes) ; suite : trancher le guide, point L5 avec le Lot C, jeu de test neuf |
| EXP-A2-006 | 2026-10-21 | A2 | Arabizi : modèle réentraîné avec la liste neutre à jour | même configuration qu'EXP-A2-003, graine 13 ; seuil 5.0 | régénération ; FR de test ; eval_30 ; bascules ; échantillon annoté | régénérable (2 essais identiques) ; 0 sur 416 ; eval_30 identique ; 0 sur 20 384 ; TN classé arabizi 61 → 62 sur 67, FR classé arabizi 4 → 5 sur 16 | nouveau modèle retenu ; suite : test de régénération en CI |
| EXP-A2-007 | 2026-10-21 | A2 | Double annotation de la langue (accord entre annotateurs) | 2 annotateurs indépendants par échantillon ; guide envoyé sans les étiquettes du premier | kappa de Cohen, 3 classes | lettres latines 0.84 (accord 0.92) ; lettres arabes 0.65 (accord 0.87) ; 100 textes chacun | guides utilisables ; suite : adjudication, préciser emprunts français et usage de `x` |
| EXP-A2-008 | 2026-10-25 | A2 | Arabizi : chiffre 8 (= غ) | 8 ajouté pour le pipeline ; règle d'origine (235679) gardée pour le tirage et l'entraînement | fausses alertes sur le français ; gain sur les commentaires ; reproductibilité | 0 nouvelle fausse alerte (UD train / dev / test) ; règles +180, décision finale +20 sur 78 173 commentaires ; modèle et tirage inchangés | retenu ; suite : translittération arabizi → arabe (Lot D) |
| EXP-A2-009 | 2026-10-26 | A2 | Adjudication de l'annotation et analyse d'erreurs (≥ 30) | 21 désaccords tranchés à deux ; règles ajoutées au guide ; erreurs classées | langue par classe sur les étiquettes de référence ; erreurs par catégorie | arabe : `a` 23/23, `t` 41/77 ; latin : `f` 12/16, `t` 65/70 ; 45 erreurs en 10 catégories | référence retenue ; suite : lexique élargi, affixes, négation contractée |
| EXP-A2-010 | 2026-10-26 | A2 | Perplexité : repérer les textes bruités | modèle de langue à n-grammes de caractères (ordre 4, interpolé), un par alphabet, graine 13 ; seuil = 95e centile dev | faux signalements sur test ; bruit artificiel repéré ; AUC | arabe : 4,7 % ; encodage 100 %, lettres 99,6 %, mélange 99,5 % ; latin : 5,3 % ; encodage 12,3 % (AUC 0,53), lettres 99,3 %, mélange 99,0 % | retenu pour signaler (pas supprimer) ; suite : règle de détection d'encodage pour les lettres latines |
| EXP-A2-011 | 2026-10-26 | A2 | Revue Bronze : baselines triviales, gel des jeux, normaliseur mesuré, erreurs en 5 familles | `python -X utf8 -m normalization.review` ; baselines « majorité » et « alphabet seul » | macro-F1 langue (test eval_30 ; dev TSAC) ; nombres conservés | test : 0.94 contre 0.19 (majorité) et 0.50 (alphabet seul) ; dev arabe 0.63 contre 0.43 ; dev latin 0.83 contre 0.45 ; nombres 29/29 | chiffres de la revue ; suite : test TSAC neuf, jamais vu |
| EXP-A2-012 | 2026-11-06 | A2 | Silver : lexique élargi et retrait des affixes | `python -X utf8 -m normalization.silver_tuning tune` ; 8 configurations (seuil `MIN_TEXTS` 12 / 8 / 6 / 4 × retrait des affixes) ; dev arabe coupé en deux moitiés fixes (SHA-256) | macro-F1, rappel et précision `tn` (moitié « reglage », N = 47) ; fausses alertes PADT dev | actuel : 0.65, 0 alerte ; seuil 8 + affixes : 0.72 mais 2 alertes ; seuil 4 + affixes : 48 alertes | non retenu, configuration actuelle conservée ; suite : filtrer les candidats contre une grande référence d'arabe standard |
| EXP-A2-013 | 2026-11-06 | A2 | Silver : candidats filtrés par une grande référence d'arabe standard (Leipzig) | `silver_tuning tune --leipzig` : seuil 12 / 8 / 6 / 4 × occurrences tolérées dans Leipzig News 2022 300K (0 / 2 / 5) × affixes ; mesure unique `final --min-texts 4 --max-leipzig 0` | macro-F1 et rappel `tn` (dev, moitié « mesure », N = 53) ; fausses alertes PADT test ; eval_30 | mesure : 0.61 → 0.68, rappel 0.51 → 0.61, précision 1.00 → 1.00 ; eval_30 0.94 → 0.94 ; PADT test 0 → 1 alerte sur 680 | non activé (critère d'adoption : 0 alerte sur PADT test) ; gain confirmé sur données neuves ; suite : analyse de l'alerte, nouvelle presse de test |
| EXP-B-009 | 2026-11-14 | B | Réanalyse du pilote de 60 textes (macro-F1, bootstrap apparié contre la baseline) et ablation des composants | extracteur du Lot B inchangé depuis EXP-B-008, modes règles et parseurs ; `evaluate_double` et `ablation` (commit `88cdb36`) ; IC graine 20261015, 1000 tirages ; apparié graine 42, 2000 tirages | macro-F1 de détection et de modalité, extracteur − baseline ; écarts d'ablation | détection : +0.172 [+0.044 ; +0.288] (Achraf), +0.229 [+0.067 ; +0.361] (Ghofrane), +0.221 [+0.061 ; +0.365] (accord) ; modalité : IC excluant 0 contre les 3 gold en parseurs, contre Achraf seulement en règles ; ablation : factualité −0.324 sur eval_30, verbes de parole −5/22 triplets, lexiques de modalité défavorables sur le pilote | eval_30 et pilote = jeux de mise au point (optimistes) ; mesure sur test gelé : EXP-B-010 ; lexiques de modalité non retouchés d'ici là |
| EXP-B-010 | 2026-11-15 | B | Mesure du système gelé sur un jeu jamais vu (540 textes, P061–P600, un annotateur) | extracteur gelé (`1826244`, aucune modification avant la mesure), modes règles et parseurs ; unité texte ; IC graine 20261015, 1000 tirages ; apparié contre la baseline graine 42, 2000 tirages | détection (exactitude, précision, rappel, macro-F1) ; modalité (exactitude, macro-F1) ; par langue / écriture | détection macro-F1 0.771 [0.733 ; 0.806] vs 0.345 (Δ +0.426 [+0.391 ; +0.460]) ; précision 0.714, rappel 0.986 ; modalité exactitude 0.733 vs 0.385, macro-F1 0.734 ; parseurs − règles non établi (+0.004 [−0.004 ; +0.013]) | première mesure non optimiste du Lot B ; un seul annotateur ; suite : erreurs opinion / souhait / rapporté → assertif, tunisien en lettres arabes, comparaison avec le Lot C |
| EXP-B-011 | 2026-11-15 | B | Mesure exploratoire sur silver_40 (n = 40, une annotation indépendante non garantie, SPO n = 10 dont 3 réserves ouvertes, aucun texte tn en lettres arabes) | extracteur gelé (`1826244`), modes règles et parseurs ; `evaluate_double` (détection, modalité) et `evaluate --eval-set` (SPO, coréférence) ; IC graine 20261015, 1000 tirages | kappa ; détection et modalité par provenance (TArC / Tunifact fr / Tunifact ar) ; triplet exact, F1 de jetons, `resolved_text` | kappa label 0.660 (38 textes ; TArC seul 0.347) ; TArC : 24 textes sur 30 prédits affirmation, aucune affirmation gold chez Ghofrane ; modalité exactitude 0.395 (38) ; triplet exact 1/7 (règles) et 2/7 (parseurs) sans réserve, 0/3 avec réserve ; coréférence 0/1 | exploratoire, non comparable à EXP-B-010 ; 5 textes Tunifact déjà dans le pilote P01–P60 ; suite : arbitrage des réserves, eval_100 |
| EXP-B-013 | 2026-11-20 | B | Question de recherche 1 : extracteur gelé contre le TF-IDF du Lot C (112 textes du test du Lot C dans P061–P600) | extracteur gelé (mesure sur `a48e447`), modes règles et parseurs, unité texte ; TF-IDF d'EXP-C-010 reproduit (0.6435) ; IC graine 20261015, 1000 tirages ; apparié graine 42, 2000 tirages | macro-F1 binaire de détection | Lot B 0.803 [0.725 ; 0.874] vs TF-IDF 0.825 [0.742 ; 0.893] vs baseline 0.345 ; Lot B − TF-IDF −0.023 [−0.124 ; +0.076], non établi, ni par langue (tn-mixte < 15 textes) | aucune différence établie ; un seul annotateur ; XLM-R en attente |
| EXP-B-014 | 2026-11-20 | B | Robustesse (INV) du système gelé : 7 perturbations à sens conservé sur P061–P600 | une perturbation par texte et par type, graine 20261015, empreinte `c8b2a266…` ; modes règles et parseurs ; IC graine 20261015, 1000 tirages ; apparié graine 42, 2000 tirages | taux de changement de `is_claim` / `modality` ; Δ macro-F1 de détection | ponctuation −0.137 [−0.178 ; −0.097] (12 % de changements), presque tout sur les questions sans mot interrogatif du lexique (39 sur 40 contre 0 sur 10) ; fautes −0.019 ; casse et diacritiques 0 ; langue A2 changée par l'arabizi 11.6 % | reconnaissance des questions dépendante du « ? » ; lexique interrogatif de 6 entrées ; non corrigé (système gelé) |

## Entrées

### EXP-B-014 — Robustesse (INV) du système gelé : perturbations à sens conservé
- **Date** : 2026-11-20
- **Auteur / Lot** : Membre 3 / Lot B
- **Objectif / hypothèse** : mesurer la stabilité de l'extracteur gelé face à des perturbations
  de surface qui ne changent pas le sens (critère Gold « INV »). **Mesure seulement** : aucune règle
  n'est modifiée à partir de ces résultats.
- **Données** : test gelé P061–P600 d'EXP-B-010 (540 textes, un annotateur, hors dépôt), SHA-256
  `5514039a5ad44c3b9a1416ef7dd82525aa708b28b78d603281da4693064f9a6b`.
- **Méthode / configuration** :
  - Une perturbation par texte et par type ; graine 20261015, un générateur par type. Un texte
    auquel un type ne s'applique pas est exclu pour ce type :
    - P1 casse (lettres latines en minuscules) : 155 textes ;
    - P2 ponctuation retirée (sauf apostrophe et tiret entre deux lettres, séparateur décimal
      entre deux chiffres) : 341 ;
    - P3 faute de frappe (une lettre supprimée ou doublée dans un mot de 4 lettres ou plus, sans
      chiffre) : 534 ;
    - P4 élongation (lettre latine triplée ; tatweel dans un mot arabe) : 532 ;
    - P5 diacritiques arabes retirés : 9 (les textes sans diacritiques sont exclus) ;
    - P6 variantes arabizi (7→h, 9→q, 3→a, 5→kh, ou kh→5, q→9 ; tn-arabizi et tn-mixte) : 146 ;
    - P7 « !! » ou émoji en fin de texte : 540.
  - Aucun nombre n'est modifié par les perturbations. Empreinte SHA-256 de l'ensemble des
    perturbations : `c8b2a26662634bd4972c23a9ea9b95f0b094963fc6b51f917bff6b4d40730c34`.
  - Mesures, en mode règles et en mode parseurs, à l'unité texte (même décision que
    `evaluate_double.predict_text`) : taux de changement de `is_claim` et de `modality` (IC
    bootstrap, graine 20261015, 1000 tirages) ; macro-F1 de détection et exactitude de modalité
    avant / après, différence appariée (graine 42, 2000 tirages) ; changement de la langue
    détectée par le Lot A2 ; par groupe de langue déclaré, groupes de moins de 15 textes signalés.
  - Décomposition de P2 sur les 50 textes qui contenaient un point d'interrogation : (a) un mot
    interrogatif des lexiques `[questions]` reste présent après perturbation, (b) aucun.
- **Code** : mesure sur `a48e447` (`git diff 1826244 a48e447 -- linguistic_analysis` ne touche que
  `MODEL_CARD.md`) ; script `notebooks/lot_b_linguistic/mesures/inv_robustesse.py`.
- **Commande reproductible** (depuis la racine du dépôt ; test et sortie hors dépôt) :

  ```bash
  python -X utf8 notebooks/lot_b_linguistic/mesures/inv_robustesse.py \
      --gold <test_P061_P600.tsv> --out-dir <dossier hors dépôt> \
      --expect-gold-sha256 5514039a5ad44c3b9a1416ef7dd82525aa708b28b78d603281da4693064f9a6b \
      --expect-perturbations-sha256 c8b2a26662634bd4972c23a9ea9b95f0b094963fc6b51f917bff6b4d40730c34
  ```

  Sorties : `inv_resultats.json`, `inv_resultats.md`, `p2_decompose.csv` (identifiants, labels et
  chiffres ; aucun texte). Contrôle : les textes d'origine redonnent EXP-B-010 (règles 0.771 /
  0.733, parseurs 0.775 / 0.731).
- **Résultats** (global ; mode règles, puis parseurs quand ils diffèrent) :

  | Type | n | Changement `is_claim` | Changement `modality` | Δ macro-F1 détection | Δ exactitude modalité |
  |---|---|---|---|---|---|
  | P1 casse | 155 | 0.0 % | 0.0 % | +0.000 | +0.000 |
  | P2 ponctuation | 341 | 12.0 % [8.8 ; 15.2] | 12.0 % [8.8 ; 15.2] | **−0.137 [−0.178 ; −0.097]** | **−0.114 [−0.150 ; −0.082]** |
  | P3 faute | 534 | 1.9 % [0.7 ; 3.0] ; parseurs 2.2 % | 4.7 % [3.0 ; 6.4] ; parseurs 5.4 % | **−0.019 [−0.034 ; −0.006]** ; parseurs −0.023 | **−0.041 [−0.060 ; −0.024]** |
  | P4 élongation | 532 | 0.9 % [0.2 ; 1.7] | 2.8 % [1.5 ; 4.1] | −0.007 [−0.018 ; +0.001] | **−0.024 [−0.039 ; −0.011]** |
  | P5 diacritiques ⚠ | 9 | 0.0 % | 0.0 % | +0.000 | +0.000 |
  | P6 arabizi | 146 | 1.4 % [0.0 ; 3.4] | 2.7 % [0.7 ; 5.5] ; parseurs 6.2 % [2.7 ; 10.3] | +0.000 [−0.023 ; +0.023] | −0.014 [−0.041 ; +0.014] ; parseurs **−0.048 [−0.089 ; −0.014]** |
  | P7 fin | 540 | 1.7 % [0.7 ; 2.8] | 0.0 % | **−0.016 [−0.030 ; −0.004]** | +0.000 |

  En gras : IC à 95 % qui exclut 0. ⚠ : moins de 15 textes, non interprétable.
  - **Par langue** (mode règles) : la baisse de P2 est établie en fr (−0.103), ar (−0.074) et
    tn-arabizi (−0.315 [−0.475 ; −0.172]) ; tn-arabe (14 textes, −0.501) n'est pas interprétable.
    P7 : baisse établie en tn-arabizi seulement (−0.050 [−0.092 ; −0.016]). P3 : baisse établie en
    fr en mode parseurs seulement (−0.045 [−0.097 ; −0.003]).
  - **Langue du Lot A2** : inchangée pour P1, P2, P5 et P7 ; changée pour 9 textes sur 534 (P3),
    4 sur 532 (P4) et 17 sur 146 (P6, 11.6 % [6.8 ; 17.1]). Ces changements modifient la décision
    dans 3 couples (texte, type) en mode règles et 8 en mode parseurs.
  - **Causes** (110 couples instables) : marqueur non reconnu après perturbation 75 (règles) et
    77 (parseurs) ; segmentation ou nombre de phrases candidates 10 ; langue du Lot A2 3 et 8.
  - **P2 décomposé** (50 textes avec point d'interrogation, tous gold `interrogatif`) :
    - (a) mot interrogatif du lexique encore présent, toujours en tête : 10 textes, **0
      changement sur 10** dans les deux modes (moins de 15 textes : non interprétable) ;
    - (b) aucun mot interrogatif du lexique : 40 textes, `is_claim` changé 39 fois sur 40 (97.5 %
      [92.5 ; 100]), modalité 40 sur 40, dans les deux modes ;
    - sur les 291 autres textes de P2, 2 changements (0.7 %).
- **Analyse** :
  - La casse et les diacritiques ne changent rien. Fautes de frappe, élongations et fin de texte
    donnent des baisses faibles (au plus −0.05), parfois établies.
  - **La reconnaissance des questions repose presque entièrement sur le point d'interrogation ;
    le lexique interrogatif ne compte que 6 entrées (fr 2, ar 1, tn 3) ; limite de couverture,
    non corrigée (système gelé).**
  - Observation : dans P061–P600, les questions sont regroupées en blocs d'identifiants
    consécutifs (38 des 50 questions dans 4 blocs : P236–P245, P345–P354, P450–P459, P537–P544).
    La provenance par bloc est à confirmer avec le Lot C.
  - **Limites** : un seul annotateur ; une seule perturbation par texte et par type, une seule
    graine ; « sens conservé » non vérifié par une personne (retirer « ? » d'une question sans mot
    interrogatif ne le conserve pas toujours) ; causes classées automatiquement à partir des
    catégories d'indices.
- **Décision / suite** : résultat de robustesse du Lot B pour le palier Gold, reporté dans
  `linguistic_analysis/MODEL_CARD.md` (§6.4). Aucune correction : une extension du lexique
  interrogatif serait à mesurer sur un autre jeu.

### EXP-B-013 — Question de recherche 1 : extracteur gelé du Lot B contre le TF-IDF du Lot C
- **Date** : 2026-11-20
- **Auteur / Lot** : Membre 3 / Lot B
- **Objectif / hypothèse** : comparer, sur des textes vierges pour les deux lots, la détection
  d'affirmations de l'extracteur à règles (Lot B) et du Model 1 TF-IDF (Lot C, EXP-C-010).
  Numéro EXP-B-012 réservé à la première mesure sur eval_100.
- **Données** :
  - Gold : test P061–P600 d'EXP-B-010, SHA-256
    `5514039a5ad44c3b9a1416ef7dd82525aa708b28b78d603281da4693064f9a6b`.
  - Textes : les **112** identifiants du test gelé du Lot C
    (`data/splits/claim_detection_multiclass_600_seed42.json`, 120 identifiants) présents dans
    P061–P600. AFFIRMATION 59, AUTRE 37, OPINION 16 ; 8 textes marqués « doute ».
  - Source commune : `claim_detection_600.xlsx` (SHA-256
    `e59096862bb9e012e15f3ee55c4947dae53b0dbb516ba85edad76e098f307b0b`, hors dépôt). Le fichier
    du Lot C est régénéré par `data/prepare_claim_detection_dataset.py` (600 lignes). Contrôle :
    les 540 textes communs avec le gold ont la même empreinte (espaces normalisés), le même label
    et la même modalité ; 112 sur 112 pour les textes mesurés.
- **Méthode / configuration** :
  - Reproduction d'EXP-C-010 avec sa commande (venv séparé, scikit-learn 1.9.1) : macro-F1
    **0.6435** sur les 120 textes, comme l'entrée d'origine.
  - Lot B : `is_claim` au niveau du texte (`evaluate_double.predict_text`), modes règles et
    parseurs (spaCy FR, Stanza AR chargés). Lot C : prédiction TF-IDF ramenée à AFFIRMATION /
    non-AFFIRMATION. Baseline « tout = affirmation ».
  - Macro-F1 binaire, IC bootstrap (graine 20261015, 1000 tirages) ; différences appariées
    (graine 42, 2000 tirages) ; groupes de langue déclarés ; groupes de moins de 15 textes
    signalés.
- **Code** : mesure sur `a48e447` (`linguistic_analysis/` identique à `1826244` hors
  `MODEL_CARD.md`) ; script `notebooks/lot_b_linguistic/mesures/qr1_compare.py`.
- **Commandes reproductibles** (depuis la racine du dépôt ; données et sorties hors dépôt) :

  ```bash
  # 1. Fichier du Lot C (venv avec openpyxl)
  python data/prepare_claim_detection_dataset.py <claim_detection_600.xlsx> <claim_detection_600.jsonl>
  # 2. Prédictions TF-IDF : commande d'EXP-C-010 (venv avec scikit-learn)
  python models/baselines/claim_detection_multiclass_tfidf.py <claim_detection_600.jsonl> \
      --split-file data/splits/claim_detection_multiclass_600_seed42.json \
      --output <tfidf_test.json> --save-model <tfidf.joblib>
  # 3. Comparaison
  python -X utf8 notebooks/lot_b_linguistic/mesures/qr1_compare.py \
      --gold <test_P061_P600.tsv> --ids data/splits/claim_detection_multiclass_600_seed42.json \
      --tfidf <tfidf_test.json> --out-dir <dossier hors dépôt> \
      --expect-gold-sha256 5514039a5ad44c3b9a1416ef7dd82525aa708b28b78d603281da4693064f9a6b
  ```

- **Résultats** (macro-F1 binaire [IC 95 %] ; règles et parseurs identiques, aucun désaccord sur
  les 112 textes) :

  | Groupe | n (affirmations) | Lot B | TF-IDF Lot C | Baseline | Lot B − TF-IDF |
  |---|---|---|---|---|---|
  | global | 112 (59) | 0.803 [0.725 ; 0.874] | 0.825 [0.742 ; 0.893] | 0.345 | −0.023 [−0.124 ; +0.076] |
  | fr | 23 (14) | 0.852 [0.662 ; 1.000] | 0.795 [0.555 ; 0.951] | 0.378 | +0.057 [−0.138 ; +0.270] |
  | ar | 29 (17) | 0.964 [0.875 ; 1.000] | 0.847 [0.678 ; 0.964] | 0.370 | +0.117 [+0.000 ; +0.271] |
  | tn, lettres arabes | 18 (9) | 0.542 [0.308 ; 0.766] | 0.778 [0.550 ; 0.944] | 0.333 | −0.236 [−0.554 ; +0.105] |
  | tn, arabizi | 28 (11) | 0.678 [0.490 ; 0.854] | 0.750 [0.569 ; 0.893] | 0.282 | −0.072 [−0.301 ; +0.142] |
  | tn, mixte ⚠ | 14 (8) | 0.925 [0.754 ; 1.000] | 1.000 [1.000 ; 1.000] | 0.364 | −0.075 [−0.286 ; +0.000] |

  - Lot B − baseline : +0.458 [+0.378 ; +0.531] ; TF-IDF − baseline : +0.480 [+0.399 ; +0.549].
  - ⚠ : moins de 15 textes, non interprétable.
- **Analyse** :
  - Les deux systèmes dépassent nettement la baseline. **La différence Lot B − TF-IDF n'est pas
    établie**, ni au global ni dans aucun groupe (en ar, la borne basse de l'IC est à 0).
  - Observation : dans P061–P600, les questions sont regroupées en blocs d'identifiants
    consécutifs (voir EXP-B-014). La provenance par bloc est à confirmer avec le Lot C.
  - **Limites** : un seul annotateur ; unité texte (eval_100 mesurera à l'unité phrase) ;
    tâche binaire (le TF-IDF prédit 3 classes ; sa macro-F1 à 3 classes, 0.643, n'est pas
    comparable) ; le Model 1 a été entraîné sur 428 autres textes de P061–P600 (même source et
    même style) ; 18 à 29 textes par groupe.
- **Décision / suite** : XLM-R + LoRA (EXP-C-003) **en attente** : la même commande accepte
  `--xlmr <graine1> <graine2> <graine3>` (fichiers `id,label_predit`), une mesure par graine puis
  moyenne ± écart-type. À vérifier avec le Lot C : les 3 graines utilisent le split seed 42.

### EXP-C-015 — NLI (Model 2), palier Gold : abstention par seuil de confiance (protocole et choix du seuil, sans le test)
- **Date** : 2026-11-18 (protocole et règle de choix écrits avant tout calcul de probabilité)
- **Auteur / Lot** : Membre 4 (Wiem) / Lot C
- **Objectif / hypothèse** : quand le NLI n'est pas assez sûr de lui, répondre « neutral » plutôt que « supports » ou « refutes » limite-t-il les positions fausses qui faussent le verdict ? On choisit ici le seuil ; son effet sera mesuré plus tard, une seule fois, sur des jeux jamais vus.
- **Règle d'abstention** : la confiance est celle que `predict_stances` renvoie déjà à l'API et au Lot D (probabilité de la classe prédite, softmax du modèle, chargement float32). Si la classe prédite est « supports » ou « refutes » et que sa confiance est strictement inférieure au seuil τ, la sortie devient « neutral » ; une prédiction « neutral » ne change jamais.
- **Données de choix (le test v3 n'est pas utilisé)** :
  - modèle affiné (principal, graine 42, EXP-C-011) : la val v3 seulement (33 paires), car il a appris sur le train ;
  - zero-shot float32 : train + val v3 (174 + 33 = 207 paires), qu'il n'a jamais vues.
- **Grille (fixée avant calcul)** : τ ∈ {0 (pas d'abstention), 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95} ; la confiance de la classe prédite étant au moins 1/3, tout τ ≤ 0.33 équivaut à τ = 0.
- **Règle de choix (fixée avant calcul)** :
  - critère : macro-F1 sur les 3 classes fixes (comme EXP-C-011), après application du seuil, sur les données de choix du modèle ;
  - marge d'équivalence : 0.03 pour le modèle affiné (val de 33 paires, une paire ≈ 3 points), 0.01 pour le zero-shot (207 paires, environ deux paires) ; tout τ dont la macro-F1 est à moins de cette marge de la meilleure est jugé équivalent ;
  - parmi les équivalents, on garde **le plus petit τ** (le moins d'abstention, le plus proche du système actuel) ; si τ = 0 est dans la marge, on conclut qu'un seuil n'apporte rien sur les données de choix, et il n'y a rien à mesurer ensuite pour ce modèle.
- **Rapporté pour chaque τ, sans servir au choix** : accuracy, F1 par classe, couverture (part des paires où le modèle répond « supports » ou « refutes »), précision de ces réponses, nombre de prédictions changées en « neutral » et combien étaient justes avant.
- **Seuil transmis au Lot D** : seul le seuil du **modèle affiné (checkpoint graine 42)** sera transmis au Lot D ; celui du zero-shot est calculé comme comparaison seulement.
- **Lien avec le Lot D** : le verdict officiel (Aya Expanse 8B, EXP-D-010) **ne reçoit pas** les positions du NLI : les lui donner comme indices faisait passer l'exactitude de 0.714 à 0.619 (EXP-D-011, branche `lot-d-silver-nli`, non encore fusionnée). La règle prévue avec la responsable du Lot D (Hadil) s'applique donc **après** Aya : si aucun des passages cités par Aya n'est jugé « supports » ou « refutes » par le NLI affiné avec une confiance ≥ τ, le verdict devient « preuves insuffisantes ». Pour mémoire, le verdict par gabarit (`rag_llm/verdict.py`, repli sans GPU) ignore déjà les positions de confiance inférieure à `MIN_CONFIDENCE = 0.6`, et un τ ≤ 0.6 ne le change pas.
- **Code** : `python -X utf8 -m models.nli.gold_abstention` ; probabilités privées dans `data/interim/lot_c/nli/gold/` (non versionné), chiffres dans `evaluation/results/lot-c_nli-gold_abstention_val_<date>.json` (non versionné, comme les autres résultats) ; commit `a270105`.
- **Mesure prévue (plus tard, une seule fois, τ gelé et noté ici avant)** : sur les jeux d'EXP-C-012 (tunisien) et d'EXP-C-013 (paraphrases), avec et sans le seuil ; sur le verdict du Lot D seulement si sa responsable accepte, avec un protocole noté avant. Rien d'autre n'est mesuré.
- **Résultats (2026-11-18, données de choix seulement, test non lu)** : `evaluation/results/lot-c_nli-gold_abstention_val_20261118.json` ; probabilités privées dans `data/interim/lot_c/nli/gold/`. Contrôles : sans seuil, le modèle affiné redonne exactement les 33 prédictions de val de son journal (macro-F1 0.722, comme EXP-C-011) ; le zero-shot float32 redonne 0.692 sur la val seule.

  | τ | affiné, val (33) : macro-F1 / couverture / → neutral (justes avant) | zero-shot, train + val (207) : macro-F1 / couverture / → neutral (justes avant) |
  |---|---|---|
  | 0 (aucune abstention) | **0.722** / 0.697 / 0 | **0.714** / 0.758 / 0 |
  | 0.40–0.45 | 0.722 / 0.697 / 0 | 0.714–0.705 / 0.758–0.739 / 0–4 (3) |
  | 0.50–0.60 | 0.723 / 0.667 / 1 (0) | 0.701–0.715 / 0.725–0.705 / 7–11 (4–5) |
  | 0.65 | 0.688 / 0.636 / 2 (1) | 0.722 / 0.686 / 15 (6) |
  | 0.70–0.75 | 0.714 / 0.606 / 3 (1) | 0.711–0.701 / 0.657–0.647 / 21–23 (10–12) |
  | 0.80 | 0.738 / 0.515 / 6 (2) | 0.683 / 0.618 / 29 (17) |
  | 0.85 | 0.714 / 0.455 / 8 (3) | 0.668 / 0.556 / 42 (25) |
  | 0.90 | 0.611 / 0.364 / 11 (6) | 0.659 / 0.512 / 51 (31) |
  | 0.95 | 0.506 / 0.242 / 15 (9) | 0.652 / 0.473 / 59 (35) |

  - **modèle affiné : τ choisi = 0 (pas d'abstention)**. Meilleure macro-F1 0.738 à τ = 0.80 (6 réponses changées en « neutral », dont 2 étaient justes), soit +0.016, dans la marge de 0.03 (moins d'une paire sur 33) ; τ = 0 est dans la marge, donc la règle garde τ = 0 ;
  - **zero-shot : τ choisi = 0**. Meilleure 0.722 à τ = 0.65 (+0.008, dans la marge de 0.01) ; au-dessus, la macro-F1 baisse ;
  - la précision des réponses « supports » / « refutes » monte avec τ (affiné 0.65 → 0.76 à τ = 0.80 ; zero-shot 0.79 → 0.91 à τ = 0.95), mais au prix de réponses justes perdues : sur ces données, le gain de précision ne compense pas la perte selon le critère fixé.
- **Décision** : conformément à la règle fixée avant calcul, **aucun seuil d'abstention n'est retenu** pour le NLI (τ = 0 pour les deux modèles) ; rien n'est transmis au Lot D, et il n'y a rien à mesurer ensuite sur les jeux d'EXP-C-012 et d'EXP-C-013 ni sur le verdict. Le NLI reste tel quel ; l'abstention du système reste celle du Lot D (pertinence des passages, `MIN_CONFIDENCE` du gabarit). Limite : la val ne compte que 33 paires ; un seuil vers 0.80 pourrait aider sur des données plus grandes, sans que ces données permettent de le dire.

### EXP-C-013 — NLI (Model 2), palier Gold : robustesse aux paraphrases (protocole, non mesuré)
- **Date** : 2026-11-18 (protocole écrit avant la construction du jeu et avant toute mesure)
- **Auteur / Lot** : Membre 4 (Wiem) / Lot C
- **Objectif / hypothèse** : une reformulation de l'affirmation, dans la même langue, qui garde le même fait change-t-elle la position prédite ? Test d'invariance (« INV paraphrases » du cahier des charges) : idéalement, aucune prédiction ne change.
- **Données (à construire)** : les 56 paires du test v3 (mêmes `pair_id` qu'EXP-C-011) ; pour chacune, une paraphrase de l'affirmation dans sa langue d'origine (fr ou ar), obligatoire, et une seconde en bonus ; la preuve et le label ne changent pas. Gabarit privé : `data/interim/lot_c/nli/gold/paraphrases_v1.csv` (créé par `python -X utf8 -m models.nli.gold_templates`, non versionné).
- **Règles de construction** :
  - paraphrases écrites par des humains ; changements permis : ordre des mots, synonymes, voix active / passive, découpage de la phrase ; interdits : ajouter ou retirer une information, changer un nombre, une date, un nom ou la modalité (« selon X », conditionnel) ;
  - une autre personne vérifie chaque paraphrase (`verif_sens_identique`, `verif_label_tient`) ; une paraphrase avec un « non » est écartée (`statut = ecarte`) et le nombre d'écartées est rapporté ;
  - aide d'une IA possible seulement si elle est déclarée ligne par ligne (`ia_utilisee` : outil et rôle) et relue et corrigée par un humain ;
  - aucun modèle n'est lancé sur les paraphrases avant le gel.
- **Gel** : une fois le fichier rempli et vérifié, il est copié en `paraphrases_v1_gele.csv` (privé) et son SHA-256 est noté ici **avant** la mesure ; une seule mesure, par un script qui refuse une seconde exécution.
- **Modèles mesurés** : principal (graine 42), zero-shot float32 et règles Bronze, avec `predict_stances` (même code que l'API) ; aucun réglage. Les prédictions sur les affirmations d'origine sont celles déjà sauvegardées par EXP-C-011 (pas de nouvelle inférence sur le test d'origine).
- **Métriques** :
  - taux de changement : part des paires gardées dont la prédiction sur la paraphrase diffère de celle sur l'original, sur toutes les paires gardées et sur celles qui étaient justes au départ ;
  - macro-F1 et accuracy sur les paraphrases, et écart apparié paraphrase − original sur les mêmes paires (bootstrap apparié, 1000 tirages, graine 20261026) ;
  - par langue d'origine (fr / ar) ; avec 2 paraphrases, chacune est comptée séparément et l'accord entre les deux est rapporté.
- **Règle de lecture** : si moins de 40 paires sont gardées, le résultat est déclaré exploratoire.
- **Mise à jour du protocole (2026-11-18, avant toute mesure et avant tout gel)** : faute de temps de l'équipe, les paraphrases sont **générées par IA** : une par affirmation, écrite par l'assistant (Claude), dans la langue d'origine, en gardant le sens, les nombres, les dates et les noms propres ; colonne `auteur_paraphrase_1` = « IA : Claude », `ia_utilisee` renseignée ; aucune seconde paraphrase. Le vérificateur reste vide pour l'instant. **Sans relecture humaine ligne par ligne, le résultat sera déclaré exploratoire**, quel que soit le nombre de paires. Rien n'est mesuré ni gelé avant l'accord explicite de Membre 4.
- **Transmission externe** : les paraphrases ont été générées avec un service externe (Claude) à partir des affirmations du test v3, sans accord explicite de l'équipe demandé avant ; accord demandé le 2026-11-22 ; fichiers privés (`data/interim/lot_c/nli/gold/`), non publiés ; compatibilité avec l'audit des droits Tunifact (PR #37) à vérifier.
- **Résultats** : non mesuré.

### EXP-C-012 — NLI (Model 2), palier Gold : transfert vers des affirmations en tunisien (protocole, non mesuré)
- **Date** : 2026-11-18 (protocole écrit avant la construction du jeu et avant toute mesure)
- **Auteur / Lot** : Membre 4 (Wiem) / Lot C
- **Question de recherche (cahier des charges)** : le NLI multilingue transfère-t-il vers des paires affirmation tunisienne / preuve française ou arabe ? Mesure : la perte de performance quand seule la langue de l'affirmation change (mêmes faits, même preuve, même label). Le corpus NLI v3 (et la v4 décrite par le Lot A1 le 2026-11-15) ne contient aucune paire tunisienne : le jeu doit être construit.
- **Données (à construire)** : les 56 paires du test v3 (mêmes `pair_id` qu'EXP-C-011 ; choix de Membre 4 du 2026-11-18, la val restant propre pour le seuil d'abstention) ; l'affirmation de chaque paire est réécrite en tunisien **en lettres arabes (obligatoire)** et **en arabizi (bonus, si le temps le permet)** ; la preuve (fr ou ar) et le label ne changent pas. Les paires du train sont exclues (vues par le modèle affiné). Gabarit privé : `data/interim/lot_c/nli/gold/reecritures_tn_v1.csv` (créé par `python -X utf8 -m models.nli.gold_templates`, non versionné).
- **Règles de construction** :
  - réécriture par une personne tunisophone (nom dans `auteur_tn_arabe` / `auteur_arabizi`) ; traduction faite ou relue par un humain dans tous les cas ;
  - garder exactement les nombres, les dates, les noms propres et la modalité (« selon X », conditionnel) ; ne rien ajouter ni retirer ;
  - vérification par une **autre** personne tunisophone (`verificateur`) : `verif_sens_identique` et `verif_label_tient` ; une réécriture avec un « non » est écartée (`statut = ecarte`), et le nombre d'écartées est rapporté ;
  - aide d'une IA possible seulement si elle est déclarée ligne par ligne (`ia_utilisee` : outil et rôle) et relue et corrigée par un humain ;
  - contrôle par `normalization.tag_lang` (Lot A2) : part des réécritures reconnues `tn` et écriture détectée, **rapportée seulement**, sans écarter de paire (le jugement humain prime) ;
  - aucun modèle n'est lancé sur les réécritures avant le gel.
- **Gel** : une fois le fichier rempli et vérifié, il est copié en `reecritures_tn_v1_gele.csv` (privé) et son SHA-256 est noté ici **avant** la mesure ; une seule mesure, par un script qui refuse une seconde exécution.
- **Modèles mesurés** : principal (graine 42), zero-shot float32 et règles Bronze, avec `predict_stances` (même code que l'API) ; aucun réglage, aucun seuil choisi sur ce jeu. Les prédictions sur les affirmations d'origine sont celles déjà sauvegardées par EXP-C-011 (pas de nouvelle inférence sur le test d'origine). Bonus, seulement s'il est décidé et noté ici avant le gel : translittération de l'arabizi en lettres arabes par le Lot A2 avant le NLI, comme ablation.
- **Métriques** :
  - macro-F1 et accuracy par variante (original, tunisien en lettres arabes, arabizi), sur les mêmes paires gardées, avec IC 95 % par bootstrap ;
  - écart apparié tunisien − original sur les mêmes paires (bootstrap apparié, 1000 tirages, graine 20261026) ;
  - taux de changement de prédiction entre l'original et sa réécriture ;
  - par langue de la preuve (fr / ar) : affirmation tunisienne / preuve française et affirmation tunisienne / preuve arabe ;
  - accord de `tag_lang` avec la variante prévue.
- **Règle de lecture** : si moins de 40 paires sont gardées pour une variante, son résultat est déclaré exploratoire ; un écart dont l'IC 95 % contient 0 est déclaré non établi.
- **Mise à jour du protocole (2026-11-18, avant toute mesure et avant tout gel)** : faute de temps de l'équipe, les réécritures en tunisien sont **générées par IA** : écrites par l'assistant (Claude) en lettres arabes (et en arabizi), en gardant les nombres, les dates et les noms propres ; colonnes d'auteur = « IA : Claude », `ia_utilisee` renseignée. Une IA n'est pas locutrice native du tunisien : ses réécritures peuvent être trop proches de l'arabe standard ou contenir des tournures peu naturelles. Relecture prévue par Mouhib, ligne par ligne (`verif_sens_identique`, `verif_label_tient` : oui / non). **Sans cette relecture humaine, le résultat sera déclaré exploratoire** et ne répondra pas à lui seul à la question de recherche. Rien n'est mesuré ni gelé avant l'accord explicite de Membre 4.
- **Transmission externe** : les réécritures en tunisien ont été générées avec un service externe (Claude) à partir des affirmations du test v3, sans accord explicite de l'équipe demandé avant ; accord demandé le 2026-11-22 ; fichiers privés (`data/interim/lot_c/nli/gold/`), non publiés ; compatibilité avec l'audit des droits Tunifact (PR #37) à vérifier.
- **Résultats** : non mesuré.

### EXP-C-014 — NLI (Model 2), palier Gold : biais par langue et par source (prédictions Silver déjà sauvegardées)
- **Date** : 2026-11-18 (protocole écrit avant tout calcul)
- **Auteur / Lot** : Membre 4 (Wiem) / Lot C
- **Objectif / hypothèse** : le NLI retenu au Silver (EXP-C-011) se trompe-t-il davantage pour une langue ou pour une source que pour les autres ? Aucune hypothèse de sens fixée à l'avance ; il s'agit de décrire les écarts et leur incertitude, avec les effectifs.
- **Données** : test v3 gelé (56 paires, mêmes `pair_id` qu'EXP-C-011). **Aucun modèle n'est relancé** : on relit seulement les prédictions déjà sauvegardées par la mesure unique du 2026-11-14 (`data/interim/lot_c/nli/silver_test/`, privé) et les labels de référence de `nli_v3_test.jsonl`. Rien n'est choisi d'après ces chiffres : aucun réglage, aucun seuil.
- **Modèles décrits** : principal (graine 42 ; les graines 123 et 2026 ont les mêmes prédictions), zero-shot float32, règles Bronze (reconstituées, EXP-C-011), classe majoritaire.
- **Groupes (fixés avant calcul)** :
  - langue de l'affirmation (`claim_lang`) : fr, ar ; tunisien : 0 paire dans la v3, traité par EXP-C-012 ;
  - source, à deux niveaux : site (préfixe de `article_id` : `tunifact-*` → tunifact.org, URL → domaine de l'URL) et article (`article_id`) ;
  - sujet : **reporté**, faute de champ sujet dans la v3 (demandé au Lot A1).
- **Métriques** : pour chaque groupe et chaque modèle, effectif, répartition des labels de référence, accuracy et macro-F1 (3 classes fixes, comme EXP-C-011 : une classe absente du groupe compte 0, ce qui fait baisser la macro-F1 des petits groupes ; l'accuracy est donc la mesure principale par article), IC 95 % par bootstrap (1000 tirages, graine 20261026) ; écart entre groupes (fr − ar ; entre sites) avec IC 95 % par bootstrap rééchantillonnant chaque groupe séparément.
- **Règle de lecture (fixée avant calcul)** : un écart n'est discuté que si les deux groupes ont au moins 10 paires ; en dessous, les chiffres sont donnés à titre descriptif seulement ; un écart dont l'IC 95 % contient 0 est déclaré non établi.
- **Code** : `python -X utf8 -m models.nli.gold_bias` ; écrit `evaluation/results/lot-c_nli-gold_biais_test_<date>.json` (chiffres et identifiants d'articles seulement, aucun texte du corpus) ; commit `5d217a9` (langue et source), `faa7e5e` (biais par sujet).
- **Résultats (2026-11-18)** : `evaluation/results/lot-c_nli-gold_biais_test_20261118.json` ; contrôle : les chiffres par langue redonnent ceux d'EXP-C-011 (principal fr 0.745 / ar 0.841, zero-shot 0.779 / 0.776 en macro-F1). Accuracy [IC 95 %] / macro-F1 :

  | Groupe | n (supports / refutes / neutral) | principal | zero-shot float32 | Bronze (acc.) | majorité (acc.) |
  |---|---|---|---|---|---|
  | ar | 31 (13 / 13 / 5) | 0.871 [0.742 ; 0.968] / 0.841 | 0.806 / 0.776 | 0.419 | 0.419 |
  | fr | 25 (10 / 6 / 9) | 0.760 [0.560 ; 0.920] / 0.745 | 0.800 / 0.779 | 0.520 | 0.400 |
  | tunifact.org | 48 (19 / 17 / 12) | 0.833 [0.729 ; 0.917] / 0.821 | 0.812 / 0.807 | 0.438 | 0.396 |
  | nawaat.org (n < 10) | 8 (4 / 2 / 2) | 0.750 [0.500 ; 1.000] / 0.730 | 0.750 / 0.730 | 0.625 | 0.500 |

  - écart fr − ar : principal −0.111 d'accuracy (IC 95 % [−0.311 ; +0.090]), −0.096 de macro-F1 ([−0.370 ; +0.147]) ; zero-shot −0.006 ([−0.223 ; +0.195]) ; **non établi** (IC contenant 0) ;
  - écart tunifact.org − nawaat.org : principal +0.083 ([−0.208 ; +0.396]) ; nawaat.org n'a que 8 paires : **non interprétable** selon la règle ;
  - par article (10 articles) : seuls deux ont au moins 10 paires, tunifact-938 (14) et tunifact-933 (11), avec une accuracy du principal de 1.000 sur les deux (zero-shot 0.929 et 0.909) ; les 8 autres ont de 3 à 5 paires (descriptif seulement, accuracy du principal de 0.333 à 1.000) ; la macro-F1 de tunifact-933 (0.667 pour une accuracy de 1.000) illustre l'effet d'une classe absente (aucune paire « neutral ») ;
  - observation descriptive, **non prévue au protocole** (donc non testée) : les 10 erreurs du principal sont toutes hors des deux gros articles ; sur les 31 paires des 8 autres articles, son accuracy est de 21 / 31 = 0.677. La performance globale dépend donc beaucoup de deux articles qui font 25 des 56 paires (45 %).
- **Analyse** : aucun écart de langue ni de source n'est établi ; ce n'est pas une preuve d'absence de biais, car les IC sont larges (environ ±0.2 par groupe). Le principal fait mieux en arabe et moins bien en français que le zero-shot, comme déjà noté dans EXP-C-011, mais sans écart significatif. Le test est trop concentré (2 articles = 45 % des paires, 2 sites dont un à 8 paires) pour mesurer un biais de source.
- **Décision / suite** : à reprendre dans la section Limitations ; biais par sujet quand le Lot A1 aura fourni le sujet de chaque article ; le tunisien sera traité par EXP-C-012.
- **Complément — biais par sujet : protocole (écrit le 2026-11-22, avant tout calcul sur les prédictions)** :
  - sujets : `nli_v4_articles_sujets_sources_categories.csv` (Lot A1, privé, SHA-256 `3cf40c0b…31668160`), colonne `categorie_thematique` ; **catégories proposées par le Lot A1 à partir des titres** des articles (`base_categorisation` = « Titre de l'article » pour les 49 articles), non vérifiées sur le contenu ni par un second annotateur ;
  - lien : `article_id` des paires du test v3 (`nli_v3_test.jsonl` ; la v5 n'a pas ce champ), comparé à l'`article_id` du CSV après retrait du « / » final et passage en minuscules (même normalisation que `models.nli.data.article_id`). Contrôle fait avant d'écrire ce protocole, sur les effectifs seulement (ni labels ni prédictions) : les 56 paires trouvent leur article ; 6 catégories sur 12 sont présentes dans le test, chacune avec 1 ou 2 articles ;
  - mêmes prédictions (aucune nouvelle inférence), mêmes modèles, métriques, bootstrap (1000 tirages, graine 20261026) et règle n ≥ 10 que ci-dessus ; pour chaque catégorie, on donne aussi le nombre d'articles ;
  - comparaisons fixées à l'avance : chaque catégorie d'au moins 10 paires contre le reste du test (toutes les autres catégories réunies), bootstrap séparé dans chaque groupe ; un écart dont l'IC 95 % contient 0 est déclaré non établi ; pas de correction pour comparaisons multiples (peu de comparaisons, lecture exploratoire) ; **aucune conclusion pour une catégorie de moins de 10 paires** ;
  - limite connue avant calcul : avec 1 ou 2 articles par catégorie, un écart de sujet ne peut pas être séparé d'un effet d'article (voir l'observation sur les deux gros articles ci-dessus) ;
  - code : `python -X utf8 -m models.nli.gold_bias` (axe « sujet » ajouté ; les axes langue, site et article sont recalculés à l'identique) ; commit `faa7e5e`.
- **Complément — biais par sujet : résultats (2026-11-22)** : `evaluation/results/lot-c_nli-gold_biais_test_20261122.json` ; contrôle : les groupes langue, site et article et les écarts fr − ar et tunifact.org − nawaat.org sont identiques à ceux du fichier du 2026-11-18. Catégories **proposées par le Lot A1 à partir des titres**. Accuracy [IC 95 %] / macro-F1 [IC 95 %] :

  | Catégorie (proposée par le Lot A1) | n (supports / refutes / neutral) | articles | principal | zero-shot float32 (acc.) | Bronze (acc.) | majorité (acc.) |
  |---|---|---|---|---|---|---|
  | Environnement & sciences | 17 (6 / 6 / 5) | 2 (tunifact-938 : 14, tunifact-937 : 3) | 0.882 [0.706 ; 1.000] / 0.882 [0.658 ; 1.000] | 0.824 | 0.412 | 0.353 |
  | Société & migrations | 16 (8 / 5 / 3) | 2 (tunifact-933 : 11, tunifact-698 : 5) | 0.875 [0.688 ; 1.000] / 0.832 [0.574 ; 1.000] | 0.875 | 0.500 | 0.500 |
  | Politique & institutions (n < 10) | 8 (4 / 2 / 2) | 2 | 0.750 / 0.730 | 0.750 | 0.625 | 0.500 |
  | Économie & emploi (n < 10) | 7 (3 / 3 / 1) | 2 | 0.571 / 0.567 | 0.571 | 0.286 | 0.429 |
  | Santé (n < 10) | 5 (1 / 2 / 2) | 1 | 1.000 / 1.000 | 1.000 | 0.400 | 0.200 |
  | Éducation (n < 10) | 3 (1 / 1 / 1) | 1 | 0.667 / 0.556 | 0.667 | 0.667 | 0.333 |

  - écarts fixés à l'avance (catégorie − reste du test) : Environnement & sciences, principal +0.087 d'accuracy (IC 95 % [−0.115 ; +0.275]), +0.102 de macro-F1 ([−0.151 ; +0.297]) ; zero-shot +0.029 ([−0.174 ; +0.241]) ; Société & migrations, principal +0.075 ([−0.125 ; +0.263]), macro-F1 +0.036 ([−0.251 ; +0.272]) ; zero-shot +0.100 ([−0.113 ; +0.300]) ; **tous non établis** (IC contenant 0) ;
  - 4 catégories sur 6 ont moins de 10 paires (3 à 8) : chiffres descriptifs seulement, **aucune conclusion** ; 6 des 12 catégories du CSV n'ont aucune paire dans le test ;
  - « Politique & institutions » regroupe exactement les 8 paires de nawaat.org (2 articles) : ce groupe est le même que celui du site, déjà jugé non interprétable.
- **Analyse (sujet)** : aucun écart de sujet n'est établi. Les deux seules catégories interprétables sont chacune portées par un gros article (tunifact-938 : 14 paires sur 17 ; tunifact-933 : 11 sur 16), les deux articles où le principal ne fait aucune erreur : leur avantage apparent sur le reste reflète surtout ces deux articles, et l'effet de sujet ne peut pas être séparé de l'effet d'article (limite notée avant calcul). Les catégories viennent des titres seulement, sans second annotateur. Avec 56 paires, 10 articles et 6 catégories, le test ne permet pas de mesurer un biais par sujet.
- **Décision / suite (sujet)** : rien n'est changé dans le modèle ; à reprendre dans la section Limitations (test trop petit et trop concentré pour les biais de source et de sujet) ; un test futur plus grand, échantillonné par article et par catégorie, serait nécessaire.

### EXP-B-011 — Mesure exploratoire sur silver_40 (détection, modalité, SPO, coréférence)
- **Statut** : **exploratoire, n = 40, une annotation indépendante non garantie, SPO n = 10 dont
  3 réserves ouvertes, aucun texte tn en lettres arabes**.
- **Date** : 2026-11-15
- **Auteur / Lot** : Membre 3 / Lot B
- **Objectif / hypothèse** : mesurer le système gelé sur le jeu silver_40 livré par le Lot A1
  (livraison provisoire), pour la détection, la modalité, le triplet SPO et la coréférence. Pas
  d'hypothèse chiffrée : il s'agit d'une première lecture, sur un petit jeu.
- **Données** (hors dépôt ; aucun texte reproduit ici) :
  - Textes de référence : `silver_40_ghofran_livraison_provisoire.tsv` (40 textes corrigés).
    - Par rapport aux fichiers d'annotation, 5 textes ont des corrections mineures (encodage,
      apostrophes ; similarité ≥ 0.989).
    - 2 textes ont été remplacés : `tarc-forum-0424` → `tarc-forum-0169` et `tarc-forum-0333` →
      `tarc-forum-0152`.
  - Annotations :
    - Achraf : `silver_40_achraf.tsv`, 38 textes communs (pas de label pour 0152 et 0169).
    - Ghofrane : `silver_40_ghofran.tsv` pour 38 textes ; livraison provisoire pour 0152 et 0169.
      Sur les 38 textes communs, les labels de la livraison et du fichier initial sont identiques.
    - Modalités normalisées sur une copie de travail (`rapport?` → `rapporté`, `hypoth?tique` →
      `hypothétique`).
  - Provenance : TArC 30, Tunifact fr 5, Tunifact ar 5 (langue Tunifact : fichier de métadonnées
    de la livraison).
  - Labels (Ghofrane, 40) : AUTRE 21, OPINION 9, AFFIRMATION 10. Les 10 affirmations sont toutes
    Tunifact : **label et provenance sont confondus**.
  - Aucun texte tunisien en lettres arabes ; groupes linguistiques de la livraison provisoires
    (2 textes TArC « à vérifier »).
  - SPO : `silver_40_spo_ghofran_propositions_v2.jsonl`, 10 propositions (5 fr, 5 ar, toutes
    Tunifact), converties au format JSONL d'eval_30.
    - 7 sans réserve ; 3 avec réserve ouverte : `tunifact-797-003`, `tunifact-698-s0004`,
      `tunifact-933-s0022`.
    - `resolved_text` présent pour 1 proposition seulement (`tunifact-698-s0004`, avec réserve).
    - `phenomena`, champ obligatoire du format : repris de la livraison quand il existe, sinon
      rempli mécaniquement (`rapporté` d'après la modalité ; `coréférence_affixe` pour
      `tunifact-933-s0022` d'après l'addendum ; valeur technique pour 2 propositions). Les
      métriques globales sont identiques sans ce champ (vérifié) ; les résultats par phénomène
      ne sont pas utilisés.
    - SHA-256 de la conversion (10 propositions) :
      `54ab22cdfb7d15c120364922a016056d4b10164b067a3badef5437d2b198fe07`.
- **Vérifications avant la mesure** :
  - **CSV de relecture de #18** (`data/annotations/a1_relecture_achref_31_sans_textes.csv`,
    branche `a1/relecture-achref`, même contenu sur `lot-a1-data`) :
    - seuls **8 des 30** identifiants TArC de silver_40 y figurent (22 n'y sont pas ; 23
      identifiants du CSV ne sont pas dans silver_40) ;
    - sur ces 8, les labels d'Achraf sont égaux à `label_achref` (8/8), **pas** à
      `decision_achref` (6/8 ; écarts : `tarc-forum-0210`, `tarc-forum-0353`).
    - L'hypothèse « mêmes 30 identifiants, labels = `decision_achref` » n'est donc pas vérifiée.
      Cela ne prouve pas l'indépendance : la livraison indique qu'elle n'est pas confirmée.
      L'accord ci-dessous est donc rapporté **sans garantie d'indépendance**.
  - **Recouvrements de textes** (comparaison après repli : casse, ponctuation, diacritiques) :
    - eval_30, fixtures et tests du Lot B : aucun ;
    - P061–P600 (test d'EXP-B-010) : aucun ;
    - **P01–P60 (pilote, jeu de mise au point d'EXP-B-008 / B-009) : 5 textes identiques**,
      tous Tunifact et tous parmi les propositions SPO : `tunifact-797-001` (P17),
      `tunifact-937-s0004` (P36), `tunifact-890-001` (P48), `tunifact-797-003` (P56),
      `tunifact-698-s0001` (P58). Sur ces 5 textes, les modalités silver diffèrent de celles du
      pilote pour 3 textes chez Achraf et 3 chez Ghofrane (rapporté au lieu d'assertif).
    - Les mesures sont donc aussi données **hors pilote (35 textes)**.
- **Méthode / configuration** :
  - Système gelé, aucune modification : extracteur du commit `1826244`, mesure sur `ae1c142`
    (branche `lot-b-silver40-exp`, issue de `lot-b-freeze`). `git diff 1826244 ae1c142 --
    linguistic_analysis` ne touche que `MODEL_CARD.md`.
  - Détection et modalité : `linguistic_analysis/evaluate_double.py` (unité texte, convention
    d'EXP-B-008 : AFFIRMATION → affirmation), puis découpage par provenance avec les mêmes
    fonctions (`detection_block`, `modality_block`, `agreement.cohen_kappa`).
  - SPO et coréférence : `python -X utf8 -m linguistic_analysis.evaluate --eval-set <copie>
    [--rules] --exp-id EXP-B-011 --out-dir <hors dépôt>`, sur 10, 7 et 3 propositions.
  - IC : bootstrap percentile 95 %, graine 20261015, 1000 tirages ; extracteur − baseline :
    apparié, graine 42, 2000 tirages.
  - **Avertissement d'effectif** : 5 textes par groupe Tunifact, 28 à 30 TArC. Aucune mesure par
    langue n'est fiable ; les groupes sont des provenances, pas des langues.
- **Résultats** :
  - **Accord entre annotateurs** (38 textes communs, indépendance non garantie) :

    | Sous-ensemble | N | Kappa label (3 classes) | Kappa affirmation | Kappa modalité |
    |---|---|---|---|---|
    | tous | 38 | 0.660 [0.434 ; 0.858] (30/38) | 0.934 [0.782 ; 1.000] | 0.900 [0.768 ; 1.000] |
    | TArC | 28 | 0.347 [−0.029 ; 0.674] (20/28) | 0.000 (27/28, une seule affirmation) | 0.862 [0.690 ; 1.000] |
    | Tunifact fr | 5 | accord 5/5 | accord 5/5 | accord 5/5 |
    | Tunifact ar | 5 | accord 5/5 | accord 5/5 | accord 5/5 |
    | hors pilote | 33 | 0.573 [0.267 ; 0.806] | 0.891 [0.602 ; 1.000] | 0.884 [0.730 ; 1.000] |

    Le kappa global est tiré vers le haut par les 10 textes Tunifact, tous AFFIRMATION chez les
    deux annotateurs.
  - **Détection et modalité, mode règles** (macro-F1 de détection ; exactitude de modalité ;
    baseline entre parenthèses) :

    | Sous-ensemble | Gold | N | Détection macro-F1 | Modalité exactitude |
    |---|---|---|---|---|
    | tous | Achraf | 38 | 0.438 [0.282 ; 0.603] (0.224) | 0.395 [0.237 ; 0.553] (0.289) |
    | tous | Ghofrane | 40 | 0.394 [0.242 ; 0.545] (0.200) | 0.375 [0.225 ; 0.525] (0.225) |
    | tous | accord | 30 / 35 | 0.486 [0.299 ; 0.667] (0.250) | 0.400 [0.257 ; 0.571] (0.257) |
    | TArC | Ghofrane | 30 | 0.167 [0.062 ; 0.268] (0.000) | 0.267 [0.133 ; 0.433] (0.133) |
    | Tunifact fr | les deux | 5 | 1.000 (1.000) | 0.800 [0.400 ; 1.000] (0.600) |
    | Tunifact ar | les deux | 5 | 1.000 (1.000) | 0.600 [0.200 ; 1.000] (0.400) |
    | hors pilote | Ghofrane | 35 | 0.314 [0.160 ; 0.457] (0.125) | 0.371 [0.229 ; 0.543] (0.229) |

    - Extracteur − baseline, macro-F1 de détection (38 textes) : +0.213 [+0.084 ; +0.347]
      (Achraf), +0.206 [+0.081 ; +0.338] (Ghofrane), +0.236 [+0.087 ; +0.388] (accord).
    - Mode parseurs : détection identique (aucun texte ne change) ; modalité : un seul texte
      change (`tarc-forum-0097`). Le macro-F1 de modalité varie pourtant de 0.399 à 0.544
      (Ghofrane, 38) : sur ce jeu, cette mesure est instable (classes à 1–3 exemples).
    - Rappel 1.000 partout où il est défini. **TArC : 24 textes sur 30 prédits affirmation**, alors que le gold
      n'en compte aucune (Ghofrane) ou une (Achraf).
    - Modalité (Ghofrane, 40, règles) : 25 erreurs, dont 24 vers `assertif` (opinion 11,
      rapporté 6, interrogatif 4, conditionnel, hypothétique, souhait 1 chacun).
    - Tunifact : détection triviale (que des affirmations ; la baseline fait aussi 1.000).
  - **SPO et coréférence** (`evaluate.py`, triplet exact ; F1 de jetons par rôle) :

    | Jeu | Mode | N | Triplet exact | Sujet / prédicat / objet exacts | F1 de jetons S / P / O | Coréférence |
    |---|---|---|---|---|---|---|
    | 7 sans réserve | règles | 7 | 1/7 (0.14 [0.00 ; 0.43]) | 0.29 / 0.14 / 0.14 | 0.50 / 0.23 / 0.43 | — (0) |
    | 7 sans réserve | parseurs | 7 | 2/7 (0.29 [0.00 ; 0.71]) | 0.71 / 0.29 / 0.29 | 0.71 / 0.33 / 0.59 | — (0) |
    | 3 avec réserve | règles | 3 | 0/3 | 0.33 / 0.33 / 0.00 | 0.33 / 0.33 / 0.27 | 0/1 |
    | 3 avec réserve | parseurs | 3 | 0/3 | 0.33 / 0.67 / 0.33 | 0.33 / 0.67 / 0.38 | 0/1 |
    | 10 (ensemble) | règles | 10 | 1/10 | 0.30 / 0.20 / 0.10 | 0.45 / 0.26 / 0.39 | 0/1 |
    | 10 (ensemble) | parseurs | 10 | 2/10 | 0.60 / 0.40 / 0.30 | 0.60 / 0.43 / 0.53 | 0/1 |

    - Par écriture (10 propositions) : règles, triplet exact 0/5 en arabe, 1/5 en français ;
      parseurs, 1/5 et 1/5.
    - Les triplets exacts (`tunifact-797-001` dans les deux modes, `tunifact-890-001` en
      parseurs) portent sur des textes du pilote.
    - Coréférence : la seule annotation (`tunifact-698-s0004`, réserve ouverte) porte sur un
      « Nous » qui renvoie à l'unité de vérification. Le système ne produit aucune résolution
      (journal vide) ; en mode règles, il ne trouve pas non plus de sujet ni de prédicat.
  - Non-régression eval_30 (`exp_id` EXP-B-011) : détection 1.000, modalité 1.000, triplet exact
    20/22 (règles) et 19/22 (parseurs), comme EXP-B-010.
- **Analyse** :
  - Sur les textes de forum TArC, l'extracteur considère presque tout comme une affirmation. Les
    annotateurs n'y voient pas d'affirmation. C'est la même erreur qu'en EXP-B-010 (opinions et
    autres textes prédits affirmations), en plus marqué sur des messages de forum.
  - La modalité reste dominée par le défaut `assertif`, comme en EXP-B-009 et B-010.
  - Sur Tunifact, la détection ne mesure rien (une seule classe). La modalité et le SPO y portent
    sur 5 textes par écriture, dont 5 au total déjà vus dans le pilote.
  - SPO : les parseurs semblent meilleurs que les règles sur le sujet, mais avec 7 propositions
    sans réserve, l'écart n'est pas établi.
  - Ces chiffres ne remplacent pas EXP-B-010 (540 textes) et ne permettent aucune conclusion par
    langue.
- **Limites** :
  - n = 40 (38 en double annotation) ; une annotation indépendante non garantie ;
  - label confondu avec la provenance ; aucune affirmation TArC ; aucun texte tn en lettres
    arabes ; aucune affirmation tunisienne pour le SPO ;
  - SPO n = 10, dont 3 réserves ouvertes ; coréférence n = 1, avec réserve ;
  - 5 textes déjà dans le pilote de mise au point ; livraison provisoire (classification
    linguistique et triplets non validés).
- **Décision / suite** :
  - Résultat exploratoire, à ne pas citer comme mesure Silver de référence.
  - Après arbitrage des 3 réserves et confirmation de l'indépendance : refaire la mesure avec les
    mêmes commandes (2ᵉ passage, système toujours gelé).
  - Demander, pour eval_100 : des affirmations tunisiennes (arabizi, mixte, lettres arabes) et
    des triplets sur des textes jamais vus par le Lot B.

### EXP-B-010 — Mesure du système gelé sur un jeu de test jamais vu (P061–P600)
- **Date** : 2026-11-15
- **Auteur / Lot** : Membre 3 / Lot B
- **Objectif / hypothèse** : obtenir une première mesure non optimiste de l'extracteur, sur un jeu
  qui n'a servi ni à écrire ni à régler les règles. Hypothèse : l'écart à la baseline mesuré sur
  le pilote (EXP-B-009) se confirme.
- **Données** :
  - Lignes P061 à P600 du jeu de 600 phrases du Lot A1 : **540 textes**, extraits de
    `claim_detection_600.xlsx` vers un fichier tabulé hors dépôt (`id`, `texte`, `label`,
    `modalite`, `doute`, `source`, `langue`, `script`).
  - **SHA-256 du fichier mesuré** :
    `5514039a5ad44c3b9a1416ef7dd82525aa708b28b78d603281da4693064f9a6b`. L'empreinte a été notée
    avant la mesure, et le fichier est en lecture seule depuis.
  - **Un seul annotateur** : pas d'accord inter-annotateurs ni de consensus. 47 textes sont
    marqués « doute ».
  - Labels : AFFIRMATION 284, AUTRE 175, OPINION 81.
  - Modalités : assertif 208, rapporté 92, opinion 84, interrogatif 50, souhait 47,
    hypothétique 39, conditionnel 20.
  - Langue et écriture déclarées par le jeu : fr 140, ar 135, tn en arabizi 135, tn en lettres
    arabes 81, tn mixte 49.
  - **Indépendance** : jeu vierge pour le Lot B.
    - Aucun fichier du Lot B, sur aucune branche, ne cite ces identifiants. La seule occurrence
      est un test synthétique de plage d'identifiants.
    - Les mesures précédentes (EXP-B-008, B-009) excluaient explicitement ces lignes.
    - Aucun texte n'est identique à un texte du pilote, d'eval_30 ou des tests.
- **Méthode / configuration** :
  - **Système gelé avant la mesure** (entrée « Gel du système du Lot B pour EXP-B-010 »).
  - Unité : le texte. Un texte est une affirmation si l'une de ses phrases candidates l'est ; sa
    modalité est celle de la première affirmation, sinon de la première candidate.
  - **Convention de détection, comme EXP-B-008** : AFFIRMATION → affirmation ; OPINION et AUTRE →
    non-affirmation. Ces deux labels n'ont pas d'équivalent direct dans `is_claim`.
  - Baselines : « tout = affirmation » et « tout = assertif ».
  - IC : bootstrap percentile 95 %, graine 20261015, 1000 tirages.
  - Extracteur − baseline : bootstrap apparié, graine 42, 2000 tirages.
  - Parseurs − règles : bootstrap apparié, graine 20261015, 1000 tirages.
  - Groupes : langue et écriture déclarées par le jeu ; contrôle avec la langue donnée par le
    Lot A2.
- **Code** : extracteur du commit `1826244`. Mesure faite sur `c6ed6ad` (branche `lot-b-freeze`,
  `main` `5d93800` fusionné). `git diff 1826244 c6ed6ad -- linguistic_analysis` ne touche que
  `MODEL_CARD.md`. Fonctions de mesure : `linguistic_analysis/evaluate_double.py` (lecture,
  prédiction par texte, métriques, bootstrap), avec un seul fichier d'annotation.
- **Commande reproductible** (depuis la racine du dépôt ; fichier de test et sortie hors dépôt ;
  le même fichier est passé comme annotateur A et B, puisqu'il n'y a qu'une annotation) :

  ```bash
  python -X utf8 -m linguistic_analysis.evaluate_double \
      --a <test_P061_P600.tsv> --b <test_P061_P600.tsv> --name-a A --name-b A_bis \
      --exp-id EXP-B-010 --out-dir <dossier hors dépôt> \
      --seed 20261015 --resamples 1000 --paired-seed 42 --paired-resamples 2000
  ```

  - Vérifier d'abord le SHA-256 du fichier (ci-dessus).
  - Vérifiée le 2026-11-20 sur `a48e447` (diff nul avec `1826244` dans `linguistic_analysis/` hors
    `MODEL_CARD.md`) : elle redonne à l'identique, en mode règles et en mode parseurs, les chiffres
    globaux du tableau ci-dessous (détection, modalité, IC, extracteur − baseline).
  - Les groupes de cette commande suivent la langue donnée par le Lot A2 (fr 161, ar 176,
    tn-arabizi 163, tn-arabic 40), pas la langue déclarée par le jeu. Le tableau « par langue /
    écriture déclarée » et la comparaison parseurs − règles viennent d'un script de mesure hors
    dépôt qui appelle les mêmes fonctions (`read_annotation`, `predict_all`, `detection_block`,
    `modality_block`, `paired_vs_baseline`).
- **Analyse d'erreurs** : 40 erreurs tirées (graine 20261015) et classées dans
  [`docs/lot-b_analyse_erreurs_silver.md`](docs/lot-b_analyse_erreurs_silver.md).
- **Résultats** :

  | Mesure (540 textes) | Règles [IC 95 %] | Parseurs [IC 95 %] | Baseline |
  |---|---|---|---|
  | Détection, exactitude | 0.785 [0.750 ; 0.820] | 0.789 [0.754 ; 0.824] | 0.526 |
  | Détection, précision | 0.714 [0.670 ; 0.757] | 0.718 [0.674 ; 0.761] | 0.526 |
  | Détection, rappel | 0.986 [0.972 ; 0.997] | 0.986 [0.972 ; 0.997] | 1.000 |
  | Détection, macro-F1 | 0.771 [0.733 ; 0.806] | 0.775 [0.737 ; 0.810] | 0.345 |
  | Modalité, exactitude | 0.733 [0.696 ; 0.769] | 0.731 [0.696 ; 0.767] | 0.385 |
  | Modalité, macro-F1 | 0.734 [0.690 ; 0.772] | 0.729 [0.686 ; 0.767] | 0.079 |

  - **Extracteur − baseline (macro-F1, mode règles)** :
    - détection : +0.426 [+0.391 ; +0.460] ;
    - modalité : +0.655 [+0.613 ; +0.691].
  - **Parseurs − règles** : aucune différence établie.
    - Détection, macro-F1 : +0.004 [−0.004 ; +0.013].
    - Modalité, exactitude : −0.002 [−0.013 ; +0.009].
    - Seuls 4 textes diffèrent en détection et 10 en modalité.
  - **Par langue / écriture déclarée** (mode règles) :

    | Groupe | N | Macro-F1 de détection | Exactitude de modalité | Macro-F1 de modalité |
    |---|---|---|---|---|
    | fr | 140 | 0.731 | 0.750 | 0.705 |
    | ar | 135 | 0.794 | 0.748 | 0.738 |
    | tn, lettres arabes | 81 | 0.713 | 0.667 | 0.573 |
    | tn, arabizi | 135 | 0.780 | 0.704 | 0.703 |
    | tn, mixte | 49 | 0.868 | 0.837 | 0.757 |

  - **Doute** (mode règles) :
    - 47 textes « doute » : macro-F1 de détection 0.668, exactitude de modalité 0.660 ;
    - 493 autres : 0.780 et 0.740.
  - **Faux positifs** (mode règles) :
    - 54 OPINION sur 81 et 58 AUTRE sur 175 sont prédits comme affirmations ;
    - 4 AFFIRMATION sur 284 sont manquées.
  - **Confusions principales de modalité** (mode règles, gold → prédit) :
    - opinion → assertif : 55 sur 84 ;
    - rapporté → assertif : 33 sur 92 ;
    - souhait → assertif : 30 sur 47 ;
    - hypothétique → assertif : 17 sur 39.
    - En revanche, interrogatif 50/50 et conditionnel 20/20.
- **Analyse** :
  - Sur un jeu jamais vu, l'extracteur dépasse nettement les deux baselines. L'écart sur la
    baseline est **établi**, avec un IC loin de 0.
  - Les scores sont plus élevés que sur le pilote (macro-F1 de détection 0.60–0.74), surtout en
    tunisien arabizi. Ce jeu semble formé de phrases plus courtes et plus nettes que les messages
    du pilote. Ce point reste à vérifier : nombre de phrases par texte.
  - L'erreur dominante reste **le défaut `assertif`** pour les opinions, les souhaits et une partie
    du discours rapporté. C'est cohérent avec l'ablation d'EXP-B-009.
  - Le tunisien en lettres arabes est le groupe le plus faible. Le Lot A2 en classe 41 sur 81 comme
    arabe standard, et aucun parseur ne le couvre.
  - Les parseurs n'apportent rien de mesurable sur ce jeu.
  - **Limites** :
    - un seul annotateur (pas de kappa, pas de gold adjugé) ;
    - même annotateur que le gold « A » du pilote ;
    - pas de gold de triplet, de source ni de coréférence sur ce jeu.
- **Décision / suite** :
  - Ces chiffres sont **la référence Silver du Lot B**. Toute modification ultérieure des règles
    rend une nouvelle mesure sur ce jeu optimiste : elle sera rapportée comme un « 2ᵉ passage ».
  - Pistes, à mesurer sur un autre jeu :
    - opinions évaluatives sans marqueur à la 1re personne ;
    - souhaits et injonctions ;
    - discours rapporté sans verbe de parole connu ;
    - tunisien en lettres arabes.
  - Comparaison avec l'encodeur du Lot C (question de recherche 1) : ce jeu a servi à entraîner
    et à tester le Model 1 du Lot C. Son test gelé
    (`data/splits/claim_detection_multiclass_600_seed42.json`, 120 identifiants) en a **112 dans
    P061–P600**. La comparaison équitable se fera sur ces 112 textes, vierges pour les deux lots.

### Gel du système du Lot B pour EXP-B-010 (pas une expérience)
- **Date** : 2026-11-14
- **Auteur / Lot** : Membre 3 / Lot B
- **Code gelé** : commit `1826244`, branche `lot-b-freeze`. Le commit de gel qui suit ne modifie
  que la documentation.
  - Après fusion, vérifier que
    `git diff 1826244 <commit mesuré> -- linguistic_analysis ':!linguistic_analysis/MODEL_CARD.md'`
    est vide.
- **Règles ajoutées depuis EXP-B-009** (lexiques `opinion_<langue>.txt` et `factuality.py`, avec
  tests) :
  - **R1 Salutation conventionnelle seule → `souhait`** (`62c7a9c`), validée par le Lot A1. Elle
    n'est retenue qu'en tête de phrase et sans indice factuel.
  - **R2 Formules de politesse ou requête → `souhait`** (`9df1c30`) : « merci d'avance », « svp »
    et leurs équivalents en arabe et en tunisien.
  - **R4 Appréciation à la 1re personne → `opinion`** (`1826244`) : « j'aime », « je déteste » et
    leurs équivalents. Le verbe n'est compté qu'à la 1re personne ; « préférer » est exclu.
- **Chiffres sur le pilote P01–P60, mode règles, avant → après** (`evaluate_double`, mêmes réglages
  qu'EXP-B-009) :
  - **détection, textes d'accord (47)** :
    - exactitude 0.745 → 0.809 ;
    - précision 0.721 → 0.775 ;
    - rappel 1.000 → 1.000 ;
    - macro-F1 0.619 → 0.741 ;
  - **détection, macro-F1** : 0.519 → 0.603 (Achraf), 0.635 → 0.737 (Ghofrane) ;
  - **faux positifs** : 23 → 20 (Achraf), 14 → 11 (Ghofrane) ; aucun faux négatif ;
  - **modalité, exactitude** :
    - 0.567 → 0.600 (Achraf) ;
    - 0.467 → 0.450 (Ghofrane) ;
    - 0.571 → 0.600 sur les 35 textes d'accord ;
  - **textes changés : 3** (P06 par R4, P37 par R1, P52 par R2), tous de vrai à faux en détection ;
  - **McNemar exact sur l'accord** : détection 0 cassé et 3 corrigés, p = 0.25 ; modalité p = 1.0.
    **Gain non établi**, et mesuré sur le jeu qui a servi à choisir les règles (optimiste).
  - **eval_30 inchangé** : détection et modalité 1.000, triplet exact 20/22 en règles et 19/22 en
    parseurs.
- **Règle de gel** : aucune modification du code ni des lexiques de `linguistic_analysis/` entre ce
  commit et la mesure EXP-B-010. Exceptions : la documentation et `MODEL_CARD.md`.
  - L'empreinte du jeu de test est notée avant la mesure.
  - Toute modification après avoir vu les résultats est rapportée comme un « 2ᵉ passage ».

### EXP-E-002 — Sélecteur de verdict et trace Silver C/D
- **Date** : 2026-11-15
- **Auteur / Lot** : Lot E, développement et vérifications assistés par IA.
- **Objectif** : relier les composants C (#21) et D (#25) sans modifier le contrat Verdict.
- **Données** : exemples fictifs des tests ; aucun test scientifique relancé.
- **Méthode** : VERDICT_BACKEND gabarit/llm partagé par pipeline et API ; repli visible ;
  construction d'un fournisseur distant refusée sans LLM_ALLOW_EXTERNAL=1 ; cache du moteur local.
- **Code** : common/verdict_runtime.py, pipeline.py, api/main.py ; tests/test_verdict_runtime.py.
- **Résultats** : 657 tests passés, 1 skipped, 77 deselected, 6 xfailed (suite non slow) ;
  Ruff et syntaxe JavaScript de l'accueil et de la page D vérifiés.
- **Limites** : générateur fictif pendant les tests ; aucun Aya 8B, e5-base ou appel API externe
  exécuté. Les chiffres scientifiques D-008 à D-010 et C-011 ne sont pas recalculés.
- **Suite** : validation machine de démo avec ressources réelles ; accord collectif avant tout
  envoi à une API externe. Le modèle Aya officiel reste distinct de la comparaison Gemini.

- **Suivi de relecture Lot D** : reprise des champs input/normalized (texte, langue,
  écriture) et du helper _claims_from_doc de lot-e-demo, dans une unique route
  /check/detail ; normalisation exécutée une fois. Repli citation_hors_liste distinct
  de llm_unavailable. 659 passed, 1 skipped, 77 deselected, 6 xfailed ; Ruff/JS OK.



### EXP-D-010 — Silver officiel : verdict par LLM ouvert (≤ 8 Md) contraint aux preuves
- **Date** : 2026-11-15
- **Auteur / Lot** : Membre 5 (Hadil) / Lot D
- **Objectif / hypothèse** : refaire EXP-D-009 dans les conditions du cahier des charges (modèle
  ouvert de 8 milliards de paramètres au plus en inférence) et sans envoyer de données Tunifact à
  une API (décision de l'équipe, 15/11/2026). Le LLM ouvert fait-il mieux que le gabarit Bronze ?
- **Données** : dev fictif (20 affirmations) ; test Tunifact v1 **gelé le 23/10/2026** (21
  affirmations : fr 9, ar 7, tunisien 5 ; 84 passages), empreintes vérifiées avant la mesure.
  Calcul dans une session Colab ; aucune donnée envoyée à une API.
- **Méthode / configuration** :
  - LLM : `CohereLabs/aya-expanse-8b` (8 Md, 23 langues dont l'arabe et le français ; licence
    CC-BY-NC, accès contrôlé), chargé en 4 bits (bitsandbytes) sur GPU T4. Choisi avant la mesure :
    dans le benchmark tunisien d'EMNLP 2025, son prédécesseur Aya-23-8B est le meilleur petit
    modèle ouvert évalué (devant Llama-3.1-8B).
  - **Même prompt v1** et mêmes contrôles par le code qu'EXP-D-009 (JSON, citations parmi les
    passages fournis, repli sur le gabarit) ; recherche hybride BM25 + e5-base, top 5 ; positions
    NLI du NLI Bronze (gabarit, repli, ablation « indices NLI »).
  - Température 0.3, top-p 0.9, **3 graines fixées localement** (13, 42, 2026) ; référence : 42.
  - Ablations (graine 42) : indices NLI ; 3 passages ; 1 passage ; recherche BM25.
  - Bootstrap apparié contre le gabarit (10 000 tirages, graine 42).
- **Code** : `rag_llm/llm_verdict.py`, `rag_llm/silver_verdict.py`,
  `notebooks/lot_d_rag/02_silver_verdict_llm.ipynb` (branche `lot-d-silver`).
- **Résultats — test gelé (21 affirmations)** :

  | Système | Exactitude | Macro-F1 | Couverture | Précision sélective | fr (9) | ar (7) | tunisien (5) |
  |---|---|---|---|---|---|---|---|
  | gabarit + NLI Bronze (recherche hybride) | 0.286 | 0.219 | 0.381 | 0.500 | 0.444 | 0.286 | 0.000 |
  | **LLM Aya 8B (graine 42)** | **0.714** | **0.401** | 1.000 | 0.714 | 0.667 | 0.714 | 0.800 |
  | LLM Aya 8B, moyenne des 3 graines | 0.730 ± 0.028 | 0.410 ± 0.016 | 1.000 ± 0.000 | — | | | |
  | ablation : + indices NLI | 0.714 | 0.408 | 1.000 | 0.714 | 0.556 | 0.714 | 1.000 |
  | ablation : 3 passages | 0.714 | 0.401 | 1.000 | 0.714 | 0.667 | 0.714 | 0.800 |
  | ablation : 1 passage | 0.619 | 0.438 | 0.905 | 0.632 | 0.556 | 0.714 | 0.600 |
  | ablation : recherche BM25 | 0.667 | 0.374 | 1.000 | 0.667 | 0.556 | 0.714 | 0.800 |
  | majorité (« faux », du dev) | 0.524 | 0.172 | 1.000 | | | | |
  | toujours s'abstenir | 0.143 | 0.062 | 0.000 | | | | |

  - Par graine : 13 → 0.762 / 0.428 ; 42 → 0.714 / 0.401 ; 2026 → 0.714 / 0.401. Sorties valides
    1.00, 0 citation invalide, **abstention justifiée 0.00** pour les 3 graines.
  - Bootstrap (graine 42 contre le gabarit) : exactitude +0.429 [0.143 ; 0.714], p = 0.004 ;
    macro-F1 +0.182 [0.009 ; 0.441], p = 0.020.
  - Bootstrap (graine 42 contre la classe majoritaire « faux », mêmes prédictions, calculé après
    coup à la demande de la relecture, sans nouvelle génération) : exactitude +0.190
    [0.000 ; 0.429], p = 0.055 (non significatif) ; macro-F1 +0.229 [0.115 ; 0.387], p = 0.004.
  - Erreurs (graine 42, 6) : 3 affirmations sans preuve jugées « faux » (`tf-c13`, `tf-c14`,
    `tf-c15`) ; 2 « trompeur » jugés « vrai » (`tf-c05`, `tf-c09`) ; 1 position inversée en arabizi
    (`tf-c11`, « faux » jugé « vrai »).
- **Résultats — dev (20 affirmations)** : gabarit 0.50 / 0.375 ; LLM 0.75 / 0.557 (3 graines
  identiques, écart-type 0), couverture 0.95, sorties valides 1.00 ; bootstrap +0.25 [-0.05 ; 0.50],
  p = 0.054 ; ablations : indices NLI 0.75, 3 passages 0.75, 1 passage 0.85, BM25 0.75.
- **Comparaison avec EXP-D-009 (Gemini, même prompt, même test)** : exactitude proche (0.730 ±
  0.028 contre 0.762 ± 0.048), mais macro-F1 0.410 contre 0.809, précision sélective 0.714 contre
  1.000 et abstention justifiée 0.00 contre 1.00. Le petit modèle est aussi exact, mais il ne suit
  pas la consigne « dans le doute, preuves_insuffisantes » et ne produit jamais « trompeur ».
- **Analyse** :
  1. Le LLM ouvert **dépasse nettement le gabarit** (+0.43, significatif). Face à la classe
     majoritaire, il est **significativement meilleur en macro-F1** (+0.23, p = 0.004) mais **pas
     significativement en exactitude** (0.71 contre 0.52, p = 0.055) : la moitié des affirmations
     du test sont « faux », ce qui rend la majorité forte en exactitude. Le Bronze restait sous elle.
  2. **Il ne s'abstient jamais** : les 3 affirmations inventées reçoivent un verdict « faux », avec
     des citations qui existent bien (le contrôle de format passe) mais ne parlent pas du même
     fait. C'est l'erreur `tf-c13` du Bronze, revenue sous une autre forme : le contrôle des
     citations vérifie qu'elles existent, pas qu'elles sont pertinentes.
  3. « trompeur » n'est jamais produit (2 erreurs) ; une position inversée en arabizi (`tf-c11`).
  4. Tunisien : 0.8 (4 sur 5), meilleur que le gabarit (0.0) ; échantillon très petit.
  5. Ablations : un seul passage fait perdre 0.10 ; la recherche hybride apporte +0.05 au verdict
     par rapport à BM25 ; les indices NLI ne changent pas l'exactitude globale.
  6. Variabilité : 0.71 à 0.76 selon la graine sur le test (0 sur le dev : à température 0.3, le
     modèle est presque déterministe).
  7. **Limites** : petit test (21 affirmations ; macro-F1 très sensible aux 3 affirmations sans
     preuve) ; modèle quantifié en 4 bits ; contamination possible (articles publics), non mesurée.
- **Décision / suite** : **résultat officiel du palier Silver** pour le verdict (recherche hybride +
  Aya Expanse 8B + prompt v1), EXP-D-009 restant une comparaison. Suite : refuser un verdict quand
  la preuve citée ne parle pas du même fait (contrôle de pertinence avant le LLM, ou seuil sur la
  recherche) ; abstention évaluée et audit des preuves citées (Gold) ; NLI fine-tuné du Lot C.

### EXP-D-009 — Comparaison (non officiel) : verdict par LLM contraint, API Gemini (3 exécutions, ablations, bootstrap)
- **Date** : 2026-11-15
- **Auteur / Lot** : Membre 5 (Hadil) / Lot D
- **Objectif / hypothèse** : un LLM avec prompt contrôlé, obligé de citer les passages fournis,
  fait-il mieux que le gabarit Bronze (règles d'abstention + NLI par lexique), en particulier sur le
  tunisien, et sans inventer de preuves ?
- **Données** : dev fictif (20 affirmations, 15 passages) ; test Tunifact v1 **gelé le 23/10/2026**
  (21 affirmations : fr 9, ar 7, tunisien 5 ; 84 passages), empreintes vérifiées avant la mesure.
  Les affirmations et les passages ont été envoyés à l'API Gemini (offre gratuite : Google indique
  que ce contenu peut servir à améliorer ses produits) ; à valider par l'équipe pour les données
  Tunifact (droits de redistribution non confirmés, voir la Data Card du Lot A1).
- **Méthode / configuration** :
  - LLM : `gemini-3.5-flash-lite` via l'API compatible OpenAI de Google (offre gratuite : 15
    requêtes / min, 500 / jour). `gemini-3.6-flash` et `gemini-3.8-flash` écartés avant toute mesure :
    quota gratuit de 20 requêtes / jour (et pas de réponse pour 3.8 Flash).
  - Prompt **v1** (`rag_llm/llm_verdict.py`), figé après le dev, inchangé pour le test : passages
    numérotés P1…P5, réponse JSON (`label`, `citations`, `explication`), 4 labels dont « trompeur »,
    « preuves_insuffisantes » en cas de doute. Contrôles faits par le code : JSON lisible, label
    connu, citations parmi les passages fournis, au moins une citation pour vrai / faux / trompeur ;
    sinon sortie rejetée et remplacée par le verdict du gabarit.
  - Recherche : hybride BM25 + e5-base, top 5 (EXP-D-008). Positions NLI : NLI Bronze du Lot C
    (utilisées par le gabarit, le repli et l'ablation « indices NLI »).
  - Température 0.3, top-p 0.9, `LLM_REASONING_EFFORT=low`. **3 exécutions** étiquetées 13 / 42 /
    2026 : l'API a refusé le champ `seed`, retiré automatiquement ; la variabilité mesurée est donc
    celle de l'échantillonnage, et les sorties exactes sont conservées dans le cache (non versionné).
    Exécution de référence fixée avant la mesure : 42.
  - Ablations (exécution 42) : indices NLI dans le prompt ; 3 passages ; 1 passage ; recherche BM25.
  - Bootstrap apparié contre le gabarit (10 000 tirages, graine 42), exactitude et macro-F1.
- **Code** : `rag_llm/llm_verdict.py`, `rag_llm/silver_verdict.py` (branche `lot-d-silver`) ;
  `python -X utf8 -m rag_llm.silver_verdict --splits dev`, puis `--splits test` (une fois).
- **Résultats — test gelé (21 affirmations)** :

  | Système | Exactitude | Macro-F1 | Couverture | Précision sélective | fr (9) | ar (7) | tunisien (5) |
  |---|---|---|---|---|---|---|---|
  | gabarit + NLI Bronze (recherche hybride) | 0.286 | 0.219 | 0.381 | 0.500 | 0.444 | 0.286 | 0.000 |
  | **LLM (exécution 42)** | **0.810** | **0.844** | 0.667 | **1.000** | 0.778 | 1.000 | 0.600 |
  | LLM, moyenne des 3 exécutions | 0.762 ± 0.048 | 0.809 ± 0.032 | 0.619 ± 0.048 | — | | | |
  | ablation : + indices NLI | 0.810 | 0.844 | 0.667 | 1.000 | 0.778 | 1.000 | 0.600 |
  | ablation : 3 passages | 0.810 | 0.844 | 0.667 | 1.000 | 0.778 | 1.000 | 0.600 |
  | ablation : 1 passage | 0.619 | 0.659 | 0.524 | 0.909 | 0.667 | 0.857 | 0.200 |
  | ablation : recherche BM25 | 0.762 | 0.803 | 0.619 | 1.000 | 0.667 | 1.000 | 0.600 |
  | majorité (« faux », du dev) | 0.524 | 0.172 | 1.000 | | | | |
  | toujours s'abstenir | 0.143 | 0.062 | 0.000 | | | | |

  - Par exécution : 13 → 0.714 / 0.781 (3 sorties rejetées, JSON invalide) ; 42 → 0.810 / 0.844
    (0 rejet) ; 2026 → 0.762 / 0.803 (1 rejet). Sorties valides : 0.936 ± 0.073.
  - Toutes exécutions : abstention justifiée 1.00 (3 affirmations sans preuve, dont `tf-c13`, erreur
    la plus grave du Bronze) ; **0 citation invalide**.
  - Bootstrap (exécution 42 contre le gabarit) : exactitude +0.524 [0.333 ; 0.714], p < 0.001 ;
    macro-F1 +0.626 [0.396 ; 0.779], p < 0.001. Ablations : 1 passage +0.333 [0.095 ; 0.571] ;
    recherche BM25 +0.476 [0.286 ; 0.667].
  - Erreurs de l'exécution 42 (4, toutes des abstentions sur des affirmations fausses) : `tf-c08`
    (fr), `tf-c17` (fr), `tf-c11` (arabizi), `tf-c19` (arabizi).
- **Résultats — dev (20 affirmations)** : gabarit 0.50 / 0.375 ; LLM 0.80 / 0.705 (3 exécutions :
  0.817 ± 0.029 / 0.709 ± 0.007), sorties valides 1.00 ; majorité 0.60 / 0.187 ; ablations : indices
  NLI 0.75 (1 sortie rejetée), 3 passages 0.80, 1 passage 0.85, BM25 0.85. Bootstrap LLM − gabarit :
  +0.30 [0.10 ; 0.50], p < 0.001.
- **Analyse** :
  1. Le LLM contraint **dépasse largement le gabarit et la classe majoritaire** sur le test
     (0.81 contre 0.29 et 0.52), écart significatif. Le Bronze restait sous la majorité (EXP-D-007).
  2. **Aucun verdict faux** : les 14 verdicts émis sont justes (précision sélective 1.00). Les 4
     erreurs sont des abstentions de trop, le côté le moins dangereux pour un vérificateur.
  3. Les erreurs restantes semblent venir de la **recherche** : `tf-c17` (affirmation française,
     preuves arabes) et `tf-c11` (arabizi) figurent déjà parmi les erreurs de recherche classées
     dans EXP-D-007 ; `tf-c19` (arabizi) et `tf-c08` sont à vérifier dans les sorties. Le goulot
     passe du NLI à la recherche.
  4. Tunisien : 0.0 → 0.6 ; l'arabizi reste difficile quand la preuve n'est pas retrouvée.
  5. Ablations : un seul passage fait perdre 0.19 (les preuves se complètent) ; la recherche
     hybride apporte +0.05 au verdict par rapport à BM25 ; les indices du NLI Bronze n'apportent
     rien au LLM.
  6. Variabilité : 0.71 à 0.81 selon l'exécution ; l'exécution 42 est la meilleure des trois, la
     moyenne (0.762 ± 0.048) est le chiffre à retenir. 4 sorties sur 63 rejetées (JSON invalide)
     et remplacées par le gabarit : le contrôle par le code est nécessaire.
  7. **Limites** : (a) contamination possible : les articles Tunifact sont publics, le LLM a pu les
     voir à l'entraînement ; indices rassurants (0 citation invalide, abstention sur les 3
     affirmations inventées), mais non mesuré ; (b) graine refusée par l'API : résultats non
     reproductibles à l'identique (sorties gardées en cache) ; (c) modèle d'API qui peut changer ;
     (d) petit test (21 affirmations).
- **Décision / suite** : **comparaison seulement**, pas le résultat officiel du Silver : le cahier des
  charges limite le système évalué à 8 Md de paramètres en inférence, et l'équipe a préféré ne pas
  envoyer les données Tunifact à une API (15/11/2026). Résultat officiel : EXP-D-010 (Aya Expanse 8B,
  même prompt). Ce qui a été envoyé à Google : les 21 affirmations du test et les 5 passages
  retrouvés pour chacune (phrases d'articles publics de Tunifact), sans annotation ni label. Suite : relancer avec le NLI fine-tuné du Lot C (repli et
  indices) ; mesurer la contamination (LLM sans passages, Gold) ; 2e LLM ouvert (Gemma) pour une
  ablation « choix du modèle » ; corriger la recherche en langue croisée et en arabizi.

### EXP-D-008 — Silver : recherche dense et hybride mesurées sur le test gelé
- **Date** : 2026-11-14
- **Auteur / Lot** : Membre 5 (Hadil) / Lot D
- **Objectif / hypothèse** : la recherche « par le sens » (encodeur multilingue) corrige-t-elle la
  première cause d'erreur du Bronze, la langue croisée (24 erreurs sur 52 dans EXP-D-007) ?
  Hypothèse : l'hybride BM25 + e5-base, meilleur sur le dev (EXP-D-003), fait mieux que BM25 sur
  le test réel.
- **Données** : dev fictif (15 passages, 18 affirmations avec preuve) ; test Tunifact v1 **gelé le
  23/10/2026** (84 passages, 21 affirmations dont 18 avec preuve : fr 7, ar 6, tunisien 5 = 2 en
  lettres arabes + 3 en arabizi). Empreintes vérifiées par `freeze_test` avant la mesure.
- **Méthode / configuration** :
  - `bm25` (baseline Bronze, k1 = 1.5, b = 0.75) ; `dense` (`intfloat/multilingual-e5-base`,
    préfixes « query: » / « passage: », seuil de similarité 0.4) ; `hybrid` = fusion RRF des deux
    (k = 60, 20 candidats par méthode) — **configuration retenue a priori**, choisie sur le dev dans
    EXP-D-003, avant toute mesure sur le test.
  - Ablations : hybride sans seuil de similarité dense ; hybride avec `multilingual-e5-small`.
  - Top 5 pour le Rappel@5, profondeur 10 pour le MRR ; moyenne globale et par langue.
  - Bootstrap apparié contre BM25 (mêmes affirmations tirées pour les deux systèmes), 10 000
    tirages, graine 42 ; IC 95 % par percentiles ; p unilatéral (part des tirages ≤ 0).
  - 3 exécutions de la configuration retenue (encodeur rechargé, sans cache disque).
  - Aucun paramètre réglé sur le test.
- **Code** : `rag_llm/silver_retrieval.py` (branche `lot-d-silver`) ;
  `python -X utf8 -m rag_llm.silver_retrieval`.
- **Résultats** (test gelé, 18 affirmations avec preuve) :

  | Configuration | Rappel@5 | MRR | Hit@1 | R@5 fr (7) | R@5 ar (6) | R@5 tunisien (5) |
  |---|---|---|---|---|---|---|
  | BM25 (baseline Bronze) | 0.411 | 0.630 | 0.611 | 0.357 | 0.650 | 0.200 |
  | dense e5-base | 0.394 | 0.630 | 0.556 | 0.362 | 0.672 | 0.107 |
  | **hybride e5-base (retenu)** | **0.446** | **0.646** | 0.556 | **0.429** | **0.672** | 0.200 |
  | ablation : hybride sans seuil dense | 0.446 | 0.646 | 0.556 | 0.429 | 0.672 | 0.200 |
  | ablation : hybride e5-small | 0.432 | 0.667 | 0.611 | 0.393 | 0.672 | 0.200 |

  Bootstrap apparié contre BM25 (différence, IC 95 %, p) :
  - hybride e5-base : Rappel@5 +0.035 [-0.022 ; 0.111], p = 0.171 ; MRR +0.016 [-0.065 ; 0.081], p = 0.323 ;
  - dense e5-base : Rappel@5 -0.017 [-0.135 ; 0.096], p = 0.596 ; MRR -0.000 [-0.189 ; 0.176], p = 0.493 ;
  - hybride e5-small : Rappel@5 +0.021 [-0.022 ; 0.074], p = 0.218 ; MRR +0.037 [0.006 ; 0.080], p = 0.010.

  Dev : BM25 0.667 / 0.907 ; dense 0.917 / 0.956 ; hybride 0.944 / 0.956 (Rappel@5 +0.278
  [0.167 ; 0.389], p < 0.001), identique à EXP-D-003. Les 3 exécutions de l'hybride donnent des
  classements identiques (encodeur déterministe en inférence : variance nulle).
- **Analyse** :
  1. **Reproductibilité** : les chiffres du dev d'EXP-D-003 sont retrouvés exactement.
  2. Sur le test réel, l'hybride ne fait **pas significativement mieux** que BM25 (+0.035 de
     Rappel@5, intervalle qui contient 0). Le gain vient du français (0.357 → 0.429), c'est-à-dire
     de la langue croisée, comme attendu, mais il reste petit.
  3. Le dense seul n'est pas meilleur que BM25 et **recule sur le tunisien** (0.200 → 0.107) :
     e5 a peu vu de dialecte tunisien ni d'arabizi. La fusion RRF garde le meilleur des deux.
  4. **Écart dev / test** : +0.278 sur le dev contre +0.035 sur le test. Le dev a été écrit par
     nous (phrases courtes, traductions directes) : il surestime nettement le dense.
  5. Ablation du seuil : aucun effet, aucun passage candidat n'a une similarité inférieure à 0.4
     (les cosinus d'e5 sont resserrés vers le haut). Ce seuil ne peut donc pas servir de signal
     d'abstention pour le dense ; à revoir (règle A2 du verdict).
  6. e5-small obtient le meilleur MRR sur le test (seul écart significatif, p = 0.010). Il **n'est
     pas retenu** : le choisir maintenant reviendrait à régler sur le test. Résultat noté comme
     ablation.
  7. Puissance faible : 18 affirmations ; un écart de quelques points ne peut pas être significatif.
- **Décision / suite** : hybride BM25 + e5-base gardé comme recherche du palier Silver (choix fait
  sur le dev, gain non significatif sur le test, rapporté tel quel). Suite : mesurer le verdict
  avec cette recherche et le NLI fine-tuné du Lot C (EXP-C, 0.809), puis le verdict par LLM
  contraint (3 graines) ; relire les preuves en langue croisée encore manquées ; test élargi.

### EXP-C-011 — NLI (Model 2), palier Silver : fine-tuning de mDeBERTa-v3 (protocole fixé avant mesure)
- **Date** : 2026-11-10 (protocole et règle de version) ; 2026-11-14 (grille, mesure unique du test, décision, intégration) ; résultats complétés ; revue Silver le 2026-11-16
- **Auteur / Lot** : Membre 4 (Wiem) / Lot C
- **Objectif / hypothèse** : affiner sur le train du corpus A1 le modèle NLI d'EXP-C-008 améliore-t-il la macro-F1 par rapport à ce modèle sans entraînement (0.798), aux règles Bronze d'EXP-C-009 (0.471) et à la classe majoritaire (0.194) ?
- **Données** : corpus NLI du Lot A1 (privé, non versionné). Règle de version fixée le 2026-11-10, avant tout entraînement et toute mesure :
  - si la v4 n'est pas disponible le jeudi 2026-11-12 à midi, ou si elle change le test gelé, les chiffres Silver sont ceux de la v3 (`data/splits/nli_v3_by_article_seed42.json` : train 174, val 33, test 56) ;
  - « change le test gelé » : le test v4 n'a pas exactement les mêmes `pair_id` que le test v3, ou l'une de ces paires a une affirmation, une preuve ou un label différent ;
  - sinon : réentraînement sur le train v4 avec les hyperparamètres choisis sur la val v3, puis une seule mesure du test v4 ;
  - état connu le 2026-11-10 : P135, P136 et P138 ne sont pas encore validées dans la v4 (déjà écartées comme brouillons dans la v3) ; pas de paires en tunisien attendues dans la v4.
- **Méthode / configuration** (prévue) : `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` affiné sur le train ; hyperparamètres (taux d'apprentissage, nombre d'époques, l'époque 0 sans affinage restant candidate) choisis sur la val seulement, d'après la moyenne de 3 graines (42, 123, 2026) ; test mesuré une seule fois à la fin. Ablation : `microsoft/mdeberta-v3-base` (même architecture, sans pré-entraînement XNLI), même protocole. Comparaisons par bootstrap apparié contre les règles Bronze, la classe majoritaire et le modèle sans entraînement ; résultats par langue ; au moins 30 erreurs classées.
- **Note** : le dossier `models/checkpoints/nli_mdeberta-ft_v3_seed42` du 2026-10-26 (15:18) a des poids identiques à ceux du modèle de base (sauvegarde de l'époque 0, exécution interrompue, sans journal) et n'a jamais été évalué sur le test : il n'est pas utilisé (supprimé le 2026-11-10).
- **Zero-shot re-mesuré en float32 (décidé le 2026-11-14, avant toute mesure Silver du test)** : sur la val v3, le même modèle zero-shot donne une macro-F1 de 0.662 chargé en float16 (format dans lequel il est stocké, chargé tel quel par `stance.py` avec transformers 5) et de 0.692 en float32 (comme `train.py`) ; la taille des lots (4 ou 16) ne change rien. `stance.py` charge désormais en float32. Le zero-shot sera donc re-mesuré une seule fois sur le test, en float32, au moment de la mesure finale du Silver, et c'est ce chiffre qui servira aux comparaisons ; l'ancien 0.798 d'EXP-C-008 reste dans le journal, sans être modifié.
- **Grille et règle de choix (fixées le 2026-11-14, avant toute exécution de la grille)** :
  - modèle principal : lr ∈ {1e-5, 2e-5, 3e-5} × graines {42, 123, 2026} = 9 exécutions ; ablation `microsoft/mdeberta-v3-base` (tête neuve) : lr ∈ {2e-5, 3e-5, 5e-5} × les mêmes graines = 9 exécutions (réduite à {2e-5, 5e-5} si le temps manque) ;
  - chaque exécution : 6 époques, `--no-save`, lot effectif 8 (4 × 2), embeddings gelés ; la val est notée aux époques 0 à 6 ; le journal de chaque exécution est copié dans `models/checkpoints/grid_v3/` (non versionné) ;
  - choix : la configuration (lr, époque k) de meilleure macro-F1 moyenne sur les 3 graines ; la val n'ayant que 33 paires (une paire ≈ 3 points), toute configuration dont la moyenne est à moins de 0.03 de la meilleure est jugée équivalente, et on garde alors d'abord l'époque la plus ancienne (l'époque 0, sans affinage, si elle est dans cette marge), puis le lr le plus petit ;
  - modèle final : relance de la configuration choisie avec `--epochs 6 --keep-epoch k` (même planning du taux d'apprentissage que la grille, calculs déterministes) pour les 3 graines, avec les poids ;
  - l'essai du 2026-11-10 (lr 1e-5, 1 époque, graine 42) n'est pas réutilisé : son planning du taux d'apprentissage est différent ;
  - si la mémoire graphique manque (pic de 5,61 Go sur 6 Go à l'essai) : `--batch-size 2 --grad-accum 4`, même lot effectif.
- **Code** : `models/nli/train.py` (entraînement, val seulement) ; `models/nli/run_grid.ps1` (grille en série, journaux dans `models/checkpoints/grid_v3/`, non versionné) ; `models/nli/analyse_grid.py` (moyenne ± écart-type de la val par lr et par époque, choix par la règle ; ne lit que les journaux de val et refuse tout journal contenant une clé de test).
- **Résultats — grille principale (2026-11-14, val v3 seulement, 9 exécutions sur 9)** : macro-F1 de val, moyenne ± écart-type sur les graines 42, 123 et 2026 (`python models/nli/analyse_grid.py main`) :

  | lr | ép. 0 | ép. 1 | ép. 2 | ép. 3 | ép. 4 | ép. 5 | ép. 6 |
  |---|---|---|---|---|---|---|---|
  | 1e-5 | 0.692 ± 0.000 | **0.722 ± 0.000** | 0.722 ± 0.000 | 0.731 ± 0.016 | 0.731 ± 0.016 | 0.722 ± 0.000 | 0.722 ± 0.000 |
  | 2e-5 | 0.692 ± 0.000 | 0.702 ± 0.034 | 0.740 ± 0.016 | 0.700 ± 0.011 | 0.730 ± 0.033 | 0.730 ± 0.033 | 0.730 ± 0.033 |
  | 3e-5 | 0.692 ± 0.000 | 0.699 ± 0.032 | 0.718 ± 0.005 | 0.710 ± 0.026 | 0.729 ± 0.047 | 0.719 ± 0.032 | 0.709 ± 0.035 |

  - **choix par la règle : lr 1e-5, époque 1 (moyenne 0.722)**. Meilleure moyenne : 0.740 (lr 2e-5, époque 2) ; 14 configurations à moins de 0.03 (moyenne > 0.710) ; l'époque 0 (0.692) est à 0.048, hors de la marge ; parmi les équivalentes, l'époque la plus ancienne est l'époque 1, et le lr le plus petit 1e-5 ;
  - gain sur la val par rapport au zero-shot (époque 0, float32) : +0.030, soit environ **une paire sur 33** : dans le bruit de la val, seul le test dira s'il est réel ;
  - écart-type nul : l'époque 0 est le même modèle pour toutes les graines (aucun pas d'entraînement ; la graine ne change que l'ordre des paires) ; pour lr 1e-5, les 3 graines donnent la même macro-F1 aux époques 1, 2, 5 et 6 (pour 123 et 2026, mêmes prédictions de val à l'époque gardée) alors que leurs pertes d'entraînement diffèrent (époque 1 : 0.653 / 0.687 / 0.678) : sur 33 paires, des modèles différents peuvent donner les mêmes prédictions ;
  - relances : l'exécution lr 2e-5 / graine 42 a échoué à 13h02 (mémoire graphique pleine, `CUDA out of memory`, après l'époque 0) ; l'exécution lr 3e-5 / graine 2026 a été interrompue à 13h54 (fenêtre de la grille fermée ou Ctrl+C, après l'époque 0) ; les deux ont été refaites à l'identique (mêmes réglages, lots de 4 × 2) à 14h12 et 14h15 ; l'époque 0 des premières tentatives (0.692) est identique à celle des relances ; les journaux des tentatives sont gardés (`*.oom.log`, `*.interrompu.log`) ;
  - durée d'une exécution de 6 époques : de 2,5 à 18 min selon l'état de la carte (bridée à 25 W au début, sans doute sur batterie ou en économie d'énergie) ; pic de mémoire graphique 5,61–5,63 Go.
- **Résultats — ablation `microsoft/mdeberta-v3-base` (2026-11-14, val v3 seulement, 9 exécutions sur 9)** : tête à 3 classes neuve, même protocole (`python models/nli/analyse_grid.py ablation`) :

  | lr | ép. 0 | ép. 1 | ép. 2 | ép. 3 | ép. 4 | ép. 5 | ép. 6 |
  |---|---|---|---|---|---|---|---|
  | 2e-5 | 0.167 ± 0.000 | 0.167 ± 0.000 | 0.197 ± 0.052 | 0.167 ± 0.000 | 0.306 ± 0.126 | 0.330 ± 0.146 | 0.355 ± 0.163 |
  | 3e-5 | 0.167 ± 0.000 | 0.167 ± 0.000 | 0.167 ± 0.000 | 0.273 ± 0.092 | 0.259 ± 0.131 | 0.335 ± 0.084 | 0.373 ± 0.098 |
  | 5e-5 | 0.167 ± 0.000 | 0.194 ± 0.047 | 0.265 ± 0.093 | 0.251 ± 0.116 | 0.320 ± 0.166 | **0.401 ± 0.121** | 0.426 ± 0.078 |

  - **choix par la règle : lr 5e-5, époque 5 (moyenne 0.401)**. Meilleure moyenne : 0.426 (lr 5e-5, époque 6) ; 2 configurations à moins de 0.03 (époques 5 et 6 de lr 5e-5) ; on garde la plus ancienne, l'époque 5 ;
  - 0.167 = une seule classe prédite pour toutes les paires (tête neuve tirée au hasard à l'époque 0, puis modèle qui n'a pas encore appris) ; une exécution (lr 2e-5, graine 2026) reste à 0.167 jusqu'à l'époque 6 ;
  - l'ablation n'a pas fini d'apprendre en 6 époques : la perte d'entraînement baisse encore (lr 5e-5, époque 6 : 0.44 à 0.75 selon la graine) et la moyenne de val monte encore à l'époque 6 ; écarts-types élevés (0.08 à 0.17). Limite connue, laissée telle quelle pour respecter la grille fixée avant exécution ;
  - même à son meilleur, l'ablation (0.43) reste très loin du modèle pré-entraîné sur XNLI, avec ou sans affinage (0.69 à 0.74) : avec 174 paires d'entraînement, le pré-entraînement NLI fait l'essentiel du travail ;
  - relance : le PC a redémarré à 15h25 pendant l'exécution lr 3e-5 / graine 2026 (après l'époque 0) ; elle a été refaite à l'identique à 15h42 (journal de la tentative gardé : `*.redemarrage.log`), suivie des 3 exécutions lr 5e-5.
- **Relance finale avec les poids (2026-11-14, 15h58–18h42, `models/nli/run_final.ps1`)** : modèle principal lr 1e-5, `--epochs 6 --keep-epoch 1` ; ablation lr 5e-5, `--epochs 6 --keep-epoch 5` ; graines 42, 123, 2026 ; 6 exécutions sur 6 OK (pause probable du PC en veille entre 16h17 et 18h37 pendant la dernière, sans effet sur le résultat). Contrôles, sur la val seulement :
  - pour chacune des 6 relances, la macro-F1 de val aux époques 0 à 6 et la perte d'entraînement de chaque époque sont identiques à celles de la grille (calculs déterministes) ; val à l'époque gardée : principal 0.722 / 0.722 / 0.722, ablation 0.290 / 0.530 / 0.382 ;
  - poids écrits (`model.safetensors`, 1,12 Go, avec config et tokenizer) dans `models/checkpoints/nli_mdeberta-ft_v3_lr1e-05_e6_seed<graine>/` et `nli_mdeberta-v3-base-ft_v3_lr5e-05_e6_seed<graine>/` (non versionnés) ;
  - rechargés par `stance.py` (même chemin que l'API, float32, sur processeur), les 6 modèles redonnent exactement les prédictions de val de l'époque gardée notées dans leur journal (0 différence sur 33 pour chacun).
- **Mesure du test prévue (fixée le 2026-11-14, avant toute lecture des labels du test par un modèle Silver)** — une seule fois, par `python -m models.nli.measure_test` (vérifications seules : `--dry-run` ; le script refuse une seconde exécution) :
  - contrôle du gel : SHA-256 de `data/splits/nli_v3_by_article_seed42.json` = `59582eb7…3552c` (valeur gelée le 26/10, vérifiée le 14/11) et mêmes 56 `pair_id` dans `nli_v3_test.jsonl` (vérifié le 14/11 ; ce fichier privé n'avait pas de SHA-256 noté : `f8f12d7f…5cb869`, noté ici avant la mesure) ;
  - modèles mesurés, avec `predict_stances` (même code que l'API et le Lot D, chargement en float32) : (1) le zero-shot `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` en float32 ; (2) les 3 modèles principaux (graines 42, 123, 2026) ; (3) les 3 modèles d'ablation (mêmes graines) ;
  - baselines déjà mesurées, non re-mesurées : règles Bronze (prédictions d'EXP-C-009 reconstituées à partir de `erreurs_bronze_v3_test.csv`, les autres paires étant justes ; contrôle : macro-F1 0.471) et classe majoritaire du train (« supports ») ;
  - métriques : macro-F1 (et accuracy) de chaque modèle ; pour le principal et l'ablation, moyenne ± écart-type sur les 3 graines, globale, par langue de l'affirmation (fr / ar) et sur les paires des articles du test du Lot D ; IC 95 % par bootstrap pour chaque modèle ;
  - comparaisons : bootstrap apparié (1000 tirages, graine 20261026) de chacun des 3 modèles principaux contre les règles Bronze, la classe majoritaire et le zero-shot float32 ;
  - sorties : `evaluation/results/lot-c_nli-silver_test_<date>.json` (chiffres seulement) ; prédictions privées dans `data/interim/lot_c/nli/silver_test/` (non versionné) pour l'analyse d'erreurs (au moins 30 erreurs classées) ; les anciennes prédictions zero-shot float16 du 26/10 ne sont pas écrasées ;
  - aucun réglage ne sera changé après la mesure.
- **Résultats — test v3 (mesure unique, 2026-11-14, `python -m models.nli.measure_test`, n = 56 : 25 fr, 31 ar, 30 paires des articles du Lot D)** : contrôle du gel OK (découpage `59582eb7…`, 56 `pair_id`) ; fichier `evaluation/results/lot-c_nli-silver_test_20261114.json` ; prédictions privées dans `data/interim/lot_c/nli/silver_test/`.

  | Modèle | macro-F1 (IC 95 %) | accuracy | fr (n = 25) | ar (n = 31) | articles Lot D (n = 30) |
  |---|---|---|---|---|---|
  | Zero-shot float32 | 0.798 [0.669 ; 0.891] | 0.804 | 0.779 | 0.776 | 0.767 |
  | **Principal (lr 1e-5, ép. 1), 3 graines** | **0.809 ± 0.000** [0.689 ; 0.905] | 0.821 ± 0.000 | 0.745 ± 0.000 | 0.841 ± 0.000 | 0.759 ± 0.000 |
  | Ablation sans XNLI (lr 5e-5, ép. 5), 3 graines | 0.427 ± 0.044 (0.378 / 0.440 / 0.463) | 0.530 ± 0.027 | 0.450 ± 0.161 | 0.325 ± 0.056 | 0.505 ± 0.050 |
  | Règles Bronze (EXP-C-009, reconstitué) | 0.471 | 0.464 | 0.504 | 0.400 | 0.475 |
  | Classe majoritaire (« supports ») | 0.194 | 0.411 | 0.190 | 0.197 | 0.167 |

  - contrôle Bronze : la reconstitution redonne 0.4708, soit le 0.471 d'EXP-C-009 (et fr 0.50 / ar 0.40, comme dans EXP-C-009) ; les scores Bronze et majorité par langue et Lot D sont calculés à partir des prédictions sauvegardées, sans nouvelle mesure ;
  - bootstrap apparié (1000 tirages, graine 20261026) ; les 3 graines du principal ont exactement les mêmes prédictions de test, donc les mêmes chiffres :

    | Principal contre | différence de macro-F1 | IC 95 % | p |
    |---|---|---|---|
    | règles Bronze | +0.339 | [+0.185 ; +0.491] | 0.000 |
    | classe majoritaire | +0.615 | [+0.484 ; +0.712] | 0.000 |
    | zero-shot float32 | +0.011 | [−0.052 ; +0.071] | 0.398 |

  - zero-shot float32 : 0.798, comme le 0.798 d'EXP-C-008 (float16 probable), qui reste dans le journal sans être modifié ; sur le test, les prédictions float32 et celles du 26/10 sont identiques (0 différence sur 56) : l'écart float16 / float32 vu sur la val (0.662 / 0.692) ne se produit pas sur le test ;
  - principal et zero-shot ne diffèrent que sur 3 paires sur 56 : le principal en corrige 2 et en abîme 1.
- **Analyse** :
  - le modèle affiné dépasse nettement les règles Bronze (+0.34) et la classe majoritaire (+0.62), avec des IC 95 % loin de 0 ;
  - en revanche, son gain sur le même modèle sans affinage (+0.011, une paire nette sur 56) n'est pas significatif (IC 95 % contenant 0, p = 0.40) : avec 174 paires d'entraînement et une seule époque à lr 1e-5, l'affinage change très peu le modèle XNLI ; cela confirme ce que montrait la val (+0.03, une paire sur 33) ;
  - par langue, le principal gagne en arabe (0.841 contre 0.776) et perd en français (0.745 contre 0.779) par rapport au zero-shot ; effectifs très petits (25 et 31 paires), à ne pas surinterpréter ;
  - écart-type nul : les 3 graines donnent les mêmes prédictions de test (déjà vu sur la val), ce qui ne mesure pas la variance d'un affinage plus fort ; l'ablation (même architecture sans pré-entraînement XNLI) reste à 0.43, sous les règles Bronze : le pré-entraînement NLI fait l'essentiel du travail ; l'ablation n'avait pas fini d'apprendre en 6 époques (limite déjà notée) ;
  - aucun réglage n'a été changé après la mesure du test.
- **Décision / suite (2026-11-14, prise après la mesure du test, sans changer aucun réglage)** :
  - **composant Silver retenu : le modèle affiné choisi par la règle fixée sur la val (lr 1e-5, époque 1), checkpoint de la graine 42** (`models/checkpoints/nli_mdeberta-ft_v3_lr1e-05_e6_seed42/`, non versionné). Raison : c'est la configuration désignée à l'avance par le protocole (choix sur la val seulement, règle fixée avant exécution), pas un choix fait d'après le test ; les 3 graines donnant exactement les mêmes prédictions (val et test), la graine 42 les représente toutes ;
  - il est déclaré **statistiquement équivalent au zero-shot float32** (+0.011, IC 95 % [−0.052 ; +0.071], p = 0.40) : on ne revendique pas de gain de l'affinage sur le zero-shot ; le zero-shot reste disponible comme backend (`NLI_BACKEND=zero-shot`) ;
  - données : la v4 n'étant pas arrivée le jeudi 2026-11-12 à midi, les chiffres Silver sont ceux de la v3, selon la règle fixée le 2026-11-10 ;
  - suite : analyse d'erreurs (CSV privé, catégories proposées, validation manuelle par Membre 4) ; intégration du modèle affiné comme nouveau backend (`NLI_BACKEND`), avec tests et vérification de l'API et du verdict du Lot D.
- **Statut de l'analyse d'erreurs (à lire avant les deux paragraphes suivants)** : toutes les catégories d'erreurs ci-dessous (colonnes `categorie_proposee` et `categorie_finale` du CSV) ont été **proposées par l'assistant (Claude)** ; elles **ne sont validées par aucun humain** : faute de temps, Membre 4 (Wiem) a décidé le 2026-11-18 de ne pas remplir la colonne `categorie_validee`, qui reste vide (0 ligne sur 50) ; elles doivent être lues comme une proposition, pas comme une annotation. Sur les **50 erreurs**, **28 viennent de l'ablation** (`microsoft/mdeberta-v3-base`, graine 42, test) ; seules **22** concernent le modèle Silver retenu ou le zero-shot (12 sur le test, 10 sur la val), et le modèle Silver seul ne fait que 10 erreurs sur le test.
- **Analyse d'erreurs (préparée le 2026-11-14, catégories proposées, à valider par Membre 4)** : `python -m models.nli.silver_errors` écrit `data/interim/lot_c/nli/erreurs_silver_v3.csv` (privé), avec une colonne `categorie_validee` vide. Le test ne compte que **12 erreurs** distinctes (principal 10, dont 9 communes avec le zero-shot ; zero-shot 11) : l'objectif de 30 erreurs ne peut pas être atteint sur le test avec ces deux modèles ; on y ajoute les **10 erreurs de la val** (principal et zero-shot float32), soit 22 erreurs, analysées en entier ; pour dépasser 30, une section séparée (colonne `modele`) ajoute les **28 erreurs de l'ablation (graine 42) sur le test**, soit **50 erreurs** en tout. L'ablation prédit « supports » pour 48 paires sur 56 ; catégories proposées pour elle : recouvrement trompeur 11, négation 6, démenti implicite 4, nombres 4, méta-affirmation 2, marqueur de démenti trompeur 1. Paires « annotation à vérifier » (toutes dans la val, signalées au Lot A1, aucun label modifié) : NLI-P035, NLI-P037, P297. Catégories : celles du Bronze quand c'est possible, plus « confirmation implicite non détectée », « méta-affirmation », « preuve dans l'autre langue » et « annotation à vérifier ». Proposition initiale (principal / zero-shot) sur le test : nombres mal comparés 3, démenti implicite non détecté 3, paraphrase non reconnue 2, recouvrement trompeur 1, confirmation implicite 1, méta-affirmation 1, négation 1 ; sur la val : annotation à vérifier 3, recouvrement trompeur 2, et 1 pour chacune des autres. Chiffres finaux : paragraphe suivant.
- **Analyse d'erreurs — catégories finales (2026-11-14)** : colonne `categorie_finale` du CSV, remplie par relecture de chacune des 50 lignes par Claude (Membre 4 n'a pas encore rempli `categorie_validee`, qui reste vide) ; catégorie proposée gardée pour 49 lignes, une seule correction (P236 de l'ablation : chiffre absent de la preuve → recouvrement trompeur, comme P278 et P293, et non nombres mal comparés). Une erreur commune au principal et au zero-shot compte une fois dans chacune des deux colonnes.

  | Catégorie finale | principal (19 : 10 test, 9 val) | zero-shot float32 (21 : 11 test, 10 val) | exemples typiques |
  |---|---|---|---|
  | nombres mal comparés | 4 (3 test) | 3 (2 test) | NLI-P004, P255, NLI-P012 |
  | démenti implicite non détecté | 4 (3 test) | 4 (3 test) | NLI-P006, NLI-P007, P140 |
  | recouvrement trompeur (même sujet, autre fait) | 3 (1 test) | 3 (1 test) | NLI-P010, NLI-P053, P145 |
  | annotation à vérifier | 3 (0 test) | 3 (0 test) | NLI-P035, NLI-P037, P297 |
  | négation mal interprétée | 2 (1 test) | 2 (1 test) | P277, P300 |
  | paraphrase non reconnue (recouvrement faible) | 1 (1 test) | 2 (2 test) | P276, P207 |
  | méta-affirmation (« selon X », « X a vérifié ») | 0 | 2 (1 test) | P188, P279 |
  | confirmation implicite non détectée | 1 (1 test) | 1 (1 test) | NLI-P057 |
  | preuve dans l'autre langue (fr / ar) | 1 (0 test) | 1 (0 test) | P299 |

  Sur 22 paires en erreur, 18 sont communes aux deux modèles ; le principal corrige les 2 méta-affirmations et P207, et se trompe seul sur NLI-P004 (nombres).

  | Catégorie finale | ablation graine 42 (28, test) | exemples typiques |
  |---|---|---|
  | recouvrement trompeur (même sujet, autre fait) | 12 | NLI-P011, P231, P278 |
  | négation mal interprétée | 6 | NLI-P074, P209, P232 |
  | démenti implicite non détecté | 4 | NLI-P001, P234, P290 |
  | nombres mal comparés | 3 | NLI-P004, NLI-P012, P255 |
  | méta-affirmation (« selon X », « X a vérifié ») | 2 | P189, P252 |
  | marqueur de démenti trompeur | 1 | NLI-P005 |

  Lecture : les erreurs du principal et du zero-shot viennent surtout de ce qu'il faut **comparer** (nombres, dates) ou **déduire** (démenti d'une rumeur sans reprendre son contenu, confirmation implicite) ; 3 des 9 erreurs de val tiennent sans doute au label (signalées au Lot A1). L'ablation, qui prédit « supports » pour 48 paires sur 56, échoue surtout dès que la preuve parle du même sujet (recouvrement trompeur, 12) ou contient une négation (6) : sans pré-entraînement NLI, 174 paires ne suffisent pas à apprendre la négation. Effectifs petits : ces chiffres décrivent des cas, pas des taux.
- **Intégration (2026-11-14)** : nouveau moteur `NLI_BACKEND=fine-tuned` dans `models/nli/stance.py` (checkpoint Silver graine 42 par défaut ; `CHECKPOINT_DIR` / `NLI_FINETUNED_MODEL` pour un autre chemin ; float32 ; checkpoint absent → « neutre », confiance 0) ; le moteur par défaut reste `bronze` et `zero-shot` reste disponible. L'API (`/nli`, `/verdict`, `/verdict/detail`, `/check`), le pipeline et le verdict du Lot D passent tous par `predict_stances` : aucun changement de leur code. Tests : sélection du checkpoint, surcharge par variable, repli « neutre », passage par l'API (faux modèle, CI légère) ; suite complète 641 passés. Vérification avec le vrai checkpoint : routes de l'API en 200, `backend_info` = `fine-tuned` ; verdict du Lot D sur le jeu de développement **fictif** (n = 20, pas le test gelé du Lot D, aucun fichier écrit) : macro-F1 0.503 avec le modèle affiné, 0.530 avec le zero-shot, 0.524 avec les règles du Lot D (écarts d'une ou deux affirmations sur 20 : non interprétables).
- **Suite pour la v4 — labels douteux de la val (source : mail du Lot A1, Ghofrane, 2026-11-15)** : décisions du Lot A1 sur les 3 paires « annotation à vérifier », à appliquer dans la v4 seulement ; **la v3 reste inchangée** et tous les chiffres ci-dessus restent ceux de la v3 :
  - NLI-P035 : label v3 `neutral` → `refutes` ;
  - NLI-P037 : `neutral` conservé ;
  - P297 : affirmation à reformuler (nouvelle formulation dans le corpus du Lot A1, hors dépôt), label `refutes` → `supports`.
- **Livraison v5 du corpus (2026-11-22, contrôlée le jour même ; aucun nouveau découpage, aucun entraînement, aucune mesure)** : le Lot A1 a livré `nli_corpus_300_consolide_v5_prive.jsonl` (SHA-256 `234b4528d798bb1ef827a841dbb83af9f50be70d9b38160097502df038ec08a3`) et `nli_v4_articles_sujets_sources_categories.csv` (SHA-256 `3cf40c0bcbf243096d1e66a35cb7b350615d71489e9b4089129f65ce31668160` ; 49 articles, source, 12 catégories thématiques), privés, dans `data/interim/lot_c/nli/` (ignorés par git, vérifié par `git check-ignore`). SHA-256 recalculés : identiques aux valeurs annoncées. Contrôles (identifiants et comptes seulement, aucun texte affiché) :
  - **test inchangé** : les 56 paires du test v3 sont dans la v5 avec exactement la même affirmation, la même preuve et le même label (0 différence) ; aucune n'y est marquée « Brouillon non valide » ; découpage gelé (`59582eb7…`) et test privé (`f8f12d7f…`) inchangés ;
  - de la v3 à la v5 (mêmes 300 `pair_id`, 37 brouillons de part et d'autre ; la v5 n'a pas de champ `article_id`) : **NLI-P035 (val) `neutral` → `refutes`**, conformément à la décision du Lot A1 du 2026-11-15 ; NLI-P004 (test) : seule la remarque change (justification du label réécrite, avec validation humaine explicite), affirmation, preuve et label identiques ; aucune autre différence. Cohérent avec le Lot A1, pour qui seule NLI-P035 change par rapport à la v4 ;
  - P297 est identique dans la v3 et la v5 : la reformulation annoncée le 2026-11-15 n'est pas appliquée (à signaler au Lot A1) ;
  - conséquence : selon la définition du 2026-11-10, le test gelé n'est pas changé ; P035 est dans la val, qui a servi au choix des hyperparamètres avec l'ancien label (une paire sur 33) ; ce choix n'est pas refait. **Les chiffres Silver ci-dessus (v3) restent valables** ; rien n'est réentraîné ni re-mesuré.

### EXP-B-009 — Réanalyse du pilote (macro-F1, bootstrap apparié) et ablation des composants
- **Date** : 2026-11-14
- **Auteur / Lot** : Membre 3 / Lot B
- **Objectif / hypothèse** : compléter EXP-B-008 avec les mesures demandées par la fiche du projet,
  à savoir :
  - macro-F1 de détection ;
  - différence avec la baseline par bootstrap apparié ;
  - ablation des composants.

  Hypothèse : l'extracteur dépasse la baseline en détection, ce que l'exactitude n'établissait pas
  dans EXP-B-008.
- **Données** :
  - **eval_30** (34 phrases, 5 groupes).
  - **Pilote P01–P60 du Lot A1** :
    - annoté par texte, indépendamment, par Achraf et Ghofrane ;
    - non adjugé ;
    - langue selon le Lot A2 : fr 26, ar 15, tn-arabizi 19.
  - Fichiers hors dépôt, dans l'espace de travail du Lot A1 :
    - `annotation_achraf.xlsx`, lignes P01–P60 seulement, SHA-256
      `ec50eda9f0cafd810c196f98b871b66126774b670c4e2918c74a7d4e3ace2f08` ;
    - `annotation_pilote_A1_Ghofran_utf8.csv`, SHA-256
      `d0eb33fc2c51346dd8ed82bcfa991dc0ee5b0d3d22730cdd39bb9cdafc51dc87`.
  - **Les deux jeux ont servi à la mise au point** :
    - eval_30 pour les règles (EXP-B-001 à EXP-B-006) ;
    - le pilote pour l'analyse d'erreurs d'EXP-B-008 et le choix de corrections.
    - Les chiffres ci-dessous sont donc **optimistes**. La mesure sur un jeu de test gelé sera
      **EXP-B-010**.
- **Méthode / configuration** :
  - extracteur sans aucune modification de règle ni de lexique depuis EXP-B-008 ;
  - unité : le texte, affirmation si l'une de ses phrases l'est ;
  - gold : label AFFIRMATION, contre chaque annotateur et sur les textes d'accord (47 pour le
    label, 35 pour la modalité) ;
  - baselines : « tout = affirmation » et « tout = assertif » ;
  - IC : bootstrap percentile 95 %, graine 20261015, 1000 tirages ;
  - extracteur − baseline : bootstrap apparié sur les textes, graine 42, 2000 tirages ;
  - ablation : retrait en mémoire de chaque composant, sans toucher aux fichiers :
    - lexiques de modalité ;
    - coréférence ;
    - règles de factualité ;
    - verbes de parole ;
    - parseurs.
- **Code** : commit `88cdb36`, `linguistic_analysis/evaluate_double.py` et
  `linguistic_analysis/ablation.py`. Le code de l'extracteur est identique à `main` (`9e19647`).
  Ce commit est sur `main` tel quel : fusion `f6eaf81` de la PR #20, par commit de fusion et sans
  squash, donc le SHA est inchangé.
  Commandes, depuis la racine du dépôt :
  - `python -X utf8 -m linguistic_analysis.evaluate_double --a <annotation_achraf.xlsx> --b <annotation_pilote_A1_Ghofran_utf8.csv> --name-a Achraf --name-b Ghofrane --ids P01-P60 --exp-id EXP-B-009 --out-dir <hors dépôt>` ;
  - `python -X utf8 -m linguistic_analysis.ablation --a <…> --b <…> --name-a Achraf --name-b Ghofrane --ids P01-P60`.
- **Résultats** :
  - **accord** :
    - label : 47/60, kappa 0.615 [0.410 ; 0.785] ;
    - oui/non : 49/60, kappa 0.624 [0.421 ; 0.799] ;
    - modalité : 35/60, kappa 0.390 [0.207 ; 0.561].
  - **Détection** (identique dans les deux modes) :

    | Gold | Exactitude | Précision | Rappel | Macro-F1 [IC] | Baseline macro-F1 |
    |---|---|---|---|---|---|
    | Achraf | 0.617 | 0.582 | 1.000 | 0.519 [0.394 ; 0.644] | 0.348 |
    | Ghofrane | 0.767 | 0.745 | 1.000 | 0.635 [0.477 ; 0.773] | 0.406 |
    | Accord (47) | 0.745 | 0.721 | 1.000 | 0.619 [0.439 ; 0.769] | 0.397 |

  - **Modalité** :

    | Mode | Exactitude Achraf / Ghofrane / accord (35) | Macro-F1 Achraf / Ghofrane / accord |
    |---|---|---|
    | règles | 0.567 / 0.467 / 0.571 | 0.412 / 0.198 / 0.363 |
    | parseurs | 0.600 / 0.500 / 0.629 | 0.441 / 0.217 / 0.404 |

    Baseline « tout = assertif » : exactitude 0.533 / 0.433 / 0.514.
  - **Extracteur − baseline (apparié)** :
    - détection, macro-F1 :
      - Achraf : +0.172 [+0.044 ; +0.288] ;
      - Ghofrane : +0.229 [+0.067 ; +0.361] ;
      - accord : +0.221 [+0.061 ; +0.365] ;
    - modalité, macro-F1, mode règles :
      - Achraf : +0.313 [+0.040 ; +0.409] ;
      - Ghofrane : +0.097 [−0.007 ; +0.218] ;
      - accord : +0.228 [−0.006 ; +0.419] ;
    - modalité, macro-F1, mode parseurs :
      - Achraf : +0.341 [+0.072 ; +0.440] ;
      - Ghofrane : +0.117 [+0.014 ; +0.243] ;
      - accord : +0.268 [+0.057 ; +0.473].
  - **Ablation**, mode règles, écart au système complet :

    | Variante | eval_30 : détection / modalité / triplet / coréférence | Pilote : macro-F1 de détection (A / G) / macro-F1 de modalité sur l'accord |
    |---|---|---|
    | sans lexiques de modalité | −0.029 / −0.118 / 0 / 0 | −0.063 / −0.081 / **+0.061** |
    | sans coréférence | 0 / 0 / 0 / −3 (sur 3) | 0 / 0 / 0 |
    | sans règles de factualité | −0.324 / −0.324 / 0 / 0 | −0.031 / −0.039 / −0.169 |
    | sans verbes de parole | 0 / −0.118 / −5 (sur 22) / 0 | 0 / 0 / −0.055 |
    | sans parseurs (contre parseurs complet) | 0 / 0 / +1 / 0 | 0 / 0 / −0.041 |

  - **Non-régression eval_30** (`exp_id` EXP-B-009) : identique à EXP-B-008.
    - Détection et modalité : 1.000 dans les deux modes.
    - Triplet exact : 20/22 en règles, 19/22 en parseurs.
- **Analyse** :
  - **Macro-F1 de détection** : l'extracteur dépasse la baseline contre chaque gold. L'IC apparié
    exclut 0, alors qu'en exactitude les IC recouvraient la baseline (EXP-B-008). La baseline n'a
    aucune bonne réponse sur la classe non-affirmation.
  - **Modalité** :
    - le gain sur la baseline est établi en mode parseurs ;
    - en mode règles, il ne l'est que contre Achraf.
    - Le macro-F1 est très défavorable à la baseline « tout = assertif », une seule classe. Elle
      reste plus juste en exactitude, où les écarts sont de +0.03 à +0.12 seulement.
  - **Ablation** :
    - la factualité porte la détection ;
    - les verbes de parole portent le triplet et le rapporté ;
    - la coréférence n'a d'effet que sur `resolved_text`, mesuré sur 3 phrases ;
    - les parseurs aident la modalité en fr et ar.
    - **Les lexiques de modalité aident sur eval_30 mais nuisent à la modalité sur le pilote** :
      sur-ajustement probable au jeu de développement.
  - Les écarts d'ablation portent sur 0 à 7 textes du pilote. Ils sont indicatifs, sans IC.
- **Décision / suite** :
  - `evaluate_double` et `ablation` sont retenus comme protocole (`docs/lot-b_protocole_eval_100.md`
    §8).
  - Aucune règle ni aucun lexique n'est modifié avant EXP-B-010, la mesure sur un jeu de test neuf
    et gelé, empreinte notée avant la mesure.
  - Vérifier sur ce jeu l'effet des lexiques de modalité.
  - Points ouverts :
    - adjudication du pilote ;
    - point L5 avec le Lot C (classe AUTRE).

### EXP-A2-013 — Silver : candidats filtrés par une grande référence d'arabe standard (Leipzig)
- **Date** : 2026-11-06
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : suite d'EXP-A2-012, dont les fausses alertes venaient d'un filtre trop
  petit (« absent de PADT `train` »). Hypothèse : en n'ajoutant que des mots (presque) absents d'une
  grande référence d'arabe standard, on relève le rappel du tunisien en lettres arabes sans fausse
  alerte sur la presse.
- **Données** : même découpage qu'EXP-A2-012 (référence d'EXP-A2-009, 100 textes : « reglage » 47,
  « mesure » 53). Référence d'arabe standard : Leipzig Corpora Collection, arabe, News 2022, 300 000
  phrases (`ara_news_2022_300K.tar.gz`, SHA-256
  `63b50fc6756002b2896055aafc3773cf2169a41a3947bac6ec39eb0febe5215d`), CC BY, téléchargée le
  2026-11-06, non versionnée (`data/raw/langid/leipzig/`), lue sans extraction ; citation :
  Goldhahn, Eckart et Quasthoff, LREC 2012. Corpus de presse maghrébine écartés volontairement
  (citations possibles en dialecte). Réglage : PADT `dev` (909 phrases). Mesure unique : moitié
  « mesure », PADT `test` (680 phrases), eval_30 (34 phrases).
- **Méthode / configuration** : `python -X utf8 -m normalization.silver_tuning tune --leipzig`.
  Grille : seuil `MIN_TEXTS` 8 / 6 / 4 × nombre maximal de phrases Leipzig contenant le mot ajouté
  (0 / 2 / 5) × retrait des affixes, plus le lexique actuel (seuil 12) ; le lexique actuel n'est
  jamais filtré. Règle de choix fixée avant le lancement : meilleur macro-F1 sur « reglage » parmi
  les configurations à 0 fausse alerte sur PADT `dev` ; égalité : seuil le plus haut, filtre le plus
  strict, sans affixes. Critère d'adoption fixé avant la mesure finale : sur la moitié « mesure »,
  macro-F1 au moins égal à l'actuel ; 0 fausse alerte sur PADT `test` ; aucune baisse sur eval_30.
  Mesure unique : `python -X utf8 -m normalization.silver_tuning final --min-texts 4 --max-leipzig 0`.
  Non-régression : `tune` sans option redonne le tableau d'EXP-A2-012 à l'identique.
- **Code** : `normalization/silver_tuning.py` (`read_leipzig_sentences`, `reference_counts`,
  option `--leipzig`, `--max-leipzig`) ; 2 tests ajoutés dans `tests/test_langid_affixes.py`
  (10 au total) ; tableau gardé hors dépôt (`data/interim/langid/silver_tuning_leipzig.tsv`).
- **Résultats** :
  - réglage (moitié « reglage », N = 47) : sans affixes, 0 alerte sur PADT `dev` pour N = 0 et 2
    à tous les seuils (contre 2 à 15 sans filtre, EXP-A2-012) ; avec affixes, 5 à 17 alertes dès le
    seuil 6. Retenu : seuil 4, N = 0, sans affixes, 445 marques (78 + 367) : macro-F1 0.65 → 0.68,
    rappel `tn` 0.56 → 0.64, précision 1.00 → 0.96 ;
  - mesure unique, configuration actuelle → retenue :

    | Jeu | Macro-F1 | Rappel tn | Précision tn | Fausses alertes |
    |---|---|---|---|---|
    | dev, moitié « mesure » (N = 53) | 0.61 → 0.68 | 0.51 → 0.61 | 1.00 → 1.00 | — |
    | eval_30 (N = 34) | 0.94 → 0.94 | 0.86 → 0.86 | 1.00 → 1.00 | — |
    | PADT `test` (680 phrases) | — | — | — | 0 → 1 |

  - tests : 637 réussis ; `ruff check` sans remarque.
- **Analyse** : l'hypothèse tient en grande partie. Le filtre Leipzig supprime presque toutes les
  fausses alertes d'EXP-A2-012, et le gain se confirme sur des données jamais vues (+0.07 de
  macro-F1, +10 points de rappel, précision intacte sur les commentaires). Il reste une fuite : une
  phrase de presse sur 680 classée tunisienne. Les affixes n'apportent rien et recréent des alertes :
  abandonnés. Limites : petits effectifs (53 textes ; 1 texte pèse environ 0.02), un seul
  annotateur de référence par texte après adjudication ; eval_30 ne contient que 5 phrases en
  tunisien en lettres arabes, donc il ne peut guère montrer de gain.
  Analyse de l'alerte de PADT `test` (faite après la mesure, sans aucun réglage) :
  la phrase, de la presse égyptienne en arabe standard, bascule sur une seule marque
  ajoutée, « الطحان », ici un nom
  de famille (5 textes TSAC, 0 phrase Leipzig) : un nom propre rare passe tout filtre de
  fréquence. Relecture des 367 marques ajoutées : 45 commencent par l'article « ال » (noms
  communs, noms de famille ; les 3 marques d'origine en « ال » sont de vraies marques) ; la
  liste automatique mêle aussi des injures et termes vulgaires, des fautes de frappe et des
  mots d'arabe standard. Le critère « fréquent dans TSAC, absent de la presse » retient ce qui
  est propre aux commentaires, pas seulement ce qui est tunisien : une liste automatique ne
  peut pas entrer telle quelle dans le lexique (ni dans le dépôt).
- **Décision / suite** : **non activé** : le critère d'adoption fixé avant la mesure (0 alerte sur
  PADT `test`) n'est pas rempli ; le pipeline garde le lexique actuel (78 marques, `STRIP_AFFIXES =
  False`). La moitié « mesure » et PADT `test` ont servi pour cette configuration : toute correction
  devra être mesurée sur de nouvelles données (une presse de test neuve et un échantillon TSAC neuf
  annoté à deux, déjà prévu par EXP-A2-011). Suite : analyser la phrase en cause (mot responsable),
  puis préparer ce nouveau jeu de test.
  Suite révisée (EXP-A2-014) : relecture humaine des 367 candidats selon des critères écrits
  avant de commencer (garder les mots-outils et formes verbales dialectales ; rejeter noms
  propres, injures, mots d'arabe standard et fautes de frappe), sans regarder le dev ni les
  tests ; mesure sur un jeu neuf.

### EXP-A2-012 — Silver : lexique élargi et retrait des affixes (résultat négatif)
- **Date** : 2026-11-06
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : suite d'EXP-A2-009 (lexique plus grand, affixes). Relever le rappel
  du tunisien en lettres arabes (0.53, EXP-A2-011) sans perdre la précision (1.00) ni créer de
  fausse alerte sur la presse. Hypothèse : des marques plus rares et le retrait des affixes collés
  (« ولقيتها » → « لقيت ») relèvent le rappel sans toucher la presse.
- **Données** : référence en lettres arabes d'EXP-A2-009 (`tsac_arabic_sample_reference.tsv`,
  100 textes, non versionnée) coupée en deux moitiés fixes selon l'empreinte SHA-256 de chaque
  texte : « reglage » (47 textes) et « mesure » (53, non utilisée ici). Presse : PADT `dev`
  (909 phrases) pour régler. Candidats : TSAC en lettres arabes hors textes annotés, absents de
  PADT `train` (même critère qu'EXP-A2-004). PADT `test` et eval_30 non utilisés.
- **Méthode / configuration** : 8 configurations = seuil `MIN_TEXTS` du lexique (12 = lexique
  actuel ; 8, 6, 4 : ajout des mots vus dans 4 à 11 textes, d'au moins 3 lettres, hors verbes en
  ن et mots écartés dans l'en-tête de `tn_markers.txt` ; les mots à 12 textes ou plus déjà écartés
  ne reviennent pas) × retrait d'un préfixe (و ف ب ل ك) et d'un suffixe (ني ك ه ها نا كم هم),
  forme restante d'au moins 3 lettres. Règle de choix fixée avant le lancement : meilleur
  macro-F1 sur « reglage » parmi les configurations à 0 fausse alerte sur PADT `dev` ; égalité :
  seuil le plus haut, puis sans affixes. Déterministe (aucune graine). Contrôle : la configuration
  actuelle sur toute la référence redonne 0.63 (EXP-A2-011).
- **Code** : `normalization/silver_tuning.py` (commande `tune`) ; `normalization/langid.py` :
  `affix_variants`, options `markers` et `strip_affixes` (désactivées par défaut,
  `STRIP_AFFIXES = False`) ; 8 tests dans `tests/test_langid_affixes.py` (ce commit).
  Commande : `python -X utf8 -m normalization.silver_tuning tune` ; tableau gardé hors dépôt
  (`data/interim/langid/silver_tuning.tsv`).
- **Résultats** (moitié « reglage », N = 47 ; alertes = phrases de PADT `dev` classées `tn`) :

  | Seuil | Affixes | Marques | Macro-F1 | Rappel tn | Précision tn | Alertes PADT dev |
  |---|---|---|---|---|---|---|
  | 12 | non | 78 | 0.65 | 0.56 | 1.00 | 0 |
  | 12 | oui | 78 | 0.65 | 0.56 | 1.00 | 0 |
  | 8 | non | 291 | 0.70 | 0.67 | 0.96 | 2 |
  | 8 | oui | 291 | 0.72 | 0.69 | 0.96 | 2 |
  | 6 | non | 476 | 0.70 | 0.67 | 0.96 | 7 |
  | 6 | oui | 476 | 0.72 | 0.69 | 0.96 | 16 |
  | 4 | non | 965 | 0.71 | 0.72 | 0.93 | 15 |
  | 4 | oui | 965 | 0.71 | 0.72 | 0.93 | 48 |

  Tests : 635 réussis ; `ruff check` sans remarque.
- **Analyse** : l'hypothèse ne tient pas sous la contrainte de précision. Les affixes seuls
  n'apportent rien avec 78 marques (surtout des mots-outils, rarement affixés). Un lexique plus
  grand relève le rappel (0.56 → 0.67 à 0.72) mais crée des fausses alertes sur la presse et fait
  baisser la précision ; avec les affixes, les nouvelles marques s'accrochent aussi à des mots de
  presse (48 alertes au seuil 4). Cause : le filtre « absent de PADT `train` » (quelques milliers
  de phrases) est trop petit pour écarter les mots rares d'arabe standard, qu'on trouve aussi
  dans les commentaires. Limites : N = 47, un écart de 0.05 correspond à environ 2 textes ; la
  négation contractée (EXP-A2-009) n'est pas traitée ici.
- **Décision / suite** : abandonné en l'état : configuration actuelle conservée (lexique inchangé,
  affixes désactivés) ; l'outil de réglage et l'option restent pour la suite. Pas de mesure
  `final` : la moitié « mesure » reste intacte. Suite (EXP-A2-013) : filtrer les candidats contre
  une référence d'arabe standard beaucoup plus grande, même protocole (réglage sur « reglage » et
  PADT `dev`, mesure unique sur « mesure » et PADT `test`).

### EXP-B-008 — Mesure sur le pilote de 60 textes (deux annotateurs indépendants)
- **Date** : 2026-10-28
- **Auteur / Lot** : Membre 3 / Lot B
- **Objectif / hypothèse** : mesurer l'extracteur du Lot B sur des textes jamais vus pendant la mise
  au point (eval_30 est un jeu de développement) et mesurer l'accord entre deux annotateurs.
- **Données** : pilote P01 à P60 (Lot A1), annoté indépendamment par deux personnes (label
  affirmation / opinion / autre ; modalité à 7 étiquettes). Annotation par texte, pas par phrase
  (5 textes de plusieurs phrases). Langue déduite par `normalize` (Lot A2) : fr 26, ar 15,
  tn-arabizi 19, aucun tn-arabe ni tn-mixte. Fichiers hors dépôt (données non commitées).
- **Méthode / configuration** : extracteur en mode règles, aucune règle modifiée ; gold = `is_claim`
  si label AFFIRMATION ; mesure contre chaque gold et contre le sous-ensemble en accord ; bootstrap
  graine 20261015 ; accord avec `agreement.py`, recoupé par un calcul direct.
- **Code** : script de mesure conservé hors dépôt (données non commitées) ;
  `linguistic_analysis/agreement.py`.
- **Résultats** :
  - accord : label 47/60, kappa 0.615 [0.410 ; 0.785] ; affirmation oui/non 49/60, kappa 0.624 ;
    modalité 35/60, kappa 0.390 [0.207 ; 0.561] ;
  - détection : exactitude 0.617 (baseline 0.533, gold Achraf) et 0.767 (0.683, gold Ghofrane),
    rappel 1.000, précision 0.582 et 0.745 ;
  - modalité : exactitude 0.567 (0.533) et 0.467 (0.433), macro-F1 0.412 (0.099) et 0.198 (0.101) ;
  - 49 erreurs (23 détection, 26 modalité).
- **Analyse** : l'extracteur ne rate aucune affirmation mais en déclare 55 textes sur 60 ; les
  intervalles de confiance recouvrent la baseline en détection. Cause principale : la classe AUTRE
  (salutations, demandes, récits personnels) n'a pas d'équivalent dans `is_claim` (point L5 avec le
  Lot C). En modalité, « rapporté » et « opinion » sont prédits « assertif ». Désaccords entre
  annotateurs : 13 de label, 25 de modalité (dont 13 rapporté / assertif). Limites : 60 textes, un
  texte pèse 0.017 ; gold non adjugé ; pas de gold pour le triplet ; groupes arabe (trivial) et
  arabizi (1 à 3 affirmations) peu interprétables.
- **Décision / suite** : trancher le guide (critère « source citée » pour rapporté, phrase personnelle
  invérifiable = AUTRE) et adjuger ; décider avec le Lot C qui écarte AUTRE ; constituer un jeu de
  test neuf avant de modifier les règles.

### EXP-B-007 — Baselines triviales sur eval_30 (palier Bronze)
- **Date** : 2026-10-27
- **Auteur / Lot** : Membre 3 / Lot B
- **Objectif / hypothèse** : situer les scores d'eval_30 par rapport à des baselines triviales
  (exigées par la revue Bronze). Hypothèse : le système dépasse nettement ces baselines.
- **Données** : `tests/fixtures/linguistic_analysis/eval_30.jsonl`, 34 phrases, 22 affirmations ;
  répartition des modalités du gold : assertif 14, rapporté 7, opinion 5, interrogatif 4, souhait 2,
  conditionnel 1, hypothétique 1.
- **Méthode / configuration** : trois baselines triviales : détection « toute phrase = affirmation » ;
  modalité « classe majoritaire » ; SPO par position (prédicat = premier mot du lexique verbal du mode
  règles, sujet = premier mot de 3 lettres ou plus, objet = mot suivant le prédicat). Mesure SPO
  identique à `evaluate.py` (elle redonne 0.909 et 0.864) ; écart et IC 95 % par bootstrap apparié
  (graine 20261015, 1000 tirages) ; déterministe.
- **Code** : commit `365209c`, `linguistic_analysis/baselines_bronze.py` ; commande :
  `python -X utf8 -m linguistic_analysis.baselines_bronze` (option `--rules-only` pour éviter spaCy
  et Stanza).
- **Résultats** (N = 34 phrases, N = 22 affirmations pour le SPO) :
  - détection : exactitude 0.647 (système 1.000, écart +0.353 [0.176 ; 0.500]), précision 0.647,
    rappel 1.000 (système 1.000), macro-F1 0.393 ;
  - modalité : exactitude 0.412 (système 1.000, écart +0.588 [0.412 ; 0.765]) ;
  - SPO : triplet exact 0.000 (règles 0.909, parseurs 0.864), sujet 0.227, prédicat 0.364, objet 0.000.
- **Analyse** : en détection, le système ne gagne que sur la précision (la baseline a un rappel de 1.0
  par construction) ; le macro-F1 de modalité (0.083) n'est pas interprétable (conditionnel et
  hypothétique : 1 phrase chacun) ; la baseline SPO réutilise le lexique verbal du mode règles, donc
  elle est un peu favorable, et son triplet exact à 0.000 la rend peu informative : citer aussi les
  scores sujet et prédicat. Limites : eval_30 a servi à mettre au point les règles (scores
  optimistes), un seul annotateur, aucune seconde annotation, effectifs petits (une phrase pèse
  environ 0.03 en détection et 0.045 en SPO).
- **Décision / suite** : baselines retenues pour la revue Bronze ; mesurer sur `eval_100` (double
  annotation, test fixé) ; ajouter un test unitaire pour `baselines_bronze.py`.

### EXP-C-009 — NLI (Model 2), palier Bronze : position par lexique et règles
- **Date** : 2026-10-26
- **Auteur / Lot** : Membre 4 (Wiem) / Lot C
- **Objectif / hypothèse** : composant classique exigé pour la revue Bronze (« position par lexique ») : des indices lexicaux simples (recouvrement, nombres, marqueurs de démenti, négation) suffisent-ils à dépasser nettement la classe majoritaire ?
- **Données** : mêmes parties qu'EXP-C-008 (`data/splits/nli_v3_by_article_seed42.json`) : train 174, val 33, test 56 (25 fr, 31 ar, 0 tunisien ; 30 paires des articles du test du Lot D).
- **Test gelé** : SHA-256 `59582eb759df4cd9e15f7a17d1df7e85dfae411717a111d52d536fc1c6c3552c` (fichier versionné dans git), gelé le 26/10/2026 au commit 967de8e, mesuré une seule fois.
- **Méthode / configuration** : `models/nli/bronze.py`. Texte normalisé par le Lot A2. Règles dans l'ordre : R1 recouvrement des mots pleins (5 premières lettres) < 0.35 → neutral ; R2 nombres de l'affirmation absents de la preuve qui en cite → refutes ; R3 marqueur de démenti dans la preuve seulement (« faux », « démenti », « زائف », « مضلل », « mouch s7i7 »…) → refutes ; R4 négation d'un seul côté → refutes ; R5 recouvrement ≥ 0.4 ou nombres identiques → supports ; R6 sinon neutral. Seuils choisis sur train + val (grille 7 × 6, macro-F1 0.632), test évalué une seule fois. Baseline triviale : classe majoritaire du train (« supports »). Ablation (scikit-learn, régression logistique `class_weight=balanced`, C choisi sur val) : TF-IDF de n-grammes de caractères (2–5, `char_wb`) sur « affirmation || preuve », seul puis avec les 5 indices lexicaux. Déterministe.
- **Code** : `python -m models.nli.bronze_eval --version v3 --tune` puis `python -m models.nli.bronze_eval --version v3 --split test --exp-id EXP-C-009`.
- **Résultats (test, n = 56)** :
  - classe majoritaire : macro-F1 0.194, accuracy 0.411 ;
  - **règles par lexique : macro-F1 0.471** (IC 95 % [0.333 ; 0.591]), accuracy 0.464 ; supports F1 0.50, refutes F1 0.35, neutral F1 0.56 ;
  - par langue : fr 0.504 (n = 25, majorité 0.190) ; ar 0.400 (n = 31, majorité 0.197) ; articles du test du Lot D 0.475 (n = 30) ;
  - ablation : TF-IDF seul 0.405 (val 0.248) ; TF-IDF + lexique 0.534 (val 0.571) ;
  - prétraitement (train + val, seuils re-choisis) : texte brut 0.634, normalisation A2 0.632, A2 + accents retirés 0.633 : écart négligeable.
- **Analyse** : 30 erreurs sur 56 (`data/interim/lot_c/nli/erreurs_bronze_v3_test.csv`, privé) : paraphrase non reconnue (recouvrement faible) 8, démenti implicite 6, négation mal interprétée 6, nombres mal comparés 5, marqueur de démenti trompeur 3, recouvrement trompeur 2. Exemples : « 7 000 personnes » lu comme 7 et 000 (séparateur de milliers) → conflit de nombres à tort ; « غير النظامي » (irrégulier) pris pour une négation → refutes à tort ; « démenti » accentué non reconnu par le lexique écrit sans accent (P290) ; « و » collé cache la négation (« وغير »). Le TF-IDF seul apprend peu sur 174 paires ; les indices lexicaux apportent l'essentiel. Le prétraitement ne change presque rien ; les seuils de recouvrement et les règles R3 / R4 pèsent le plus. La combinaison TF-IDF + lexique fait mieux sur le test (0.534), mais le composant Bronze a été fixé avant la mesure (règles, sans données d'entraînement à livrer) : il n'est pas changé après coup.
- **Décision / suite** : règles retenues comme composant Bronze de la démo (`NLI_BACKEND=bronze`, défaut). Corrections identifiées (séparateur de milliers, accents du lexique, « غير » de composition, « و » collé) : à faire sur train + val puis mesurer une seule fois sur la v4 ; pas de nouvelle mesure du test v3.

### EXP-C-008 — NLI (Model 2) : baseline sans entraînement
- **Date** : 2026-10-26
- **Auteur / Lot** : Membre 4 (Wiem) / Lot C
- **Objectif / hypothèse** : remplacer le stub NLI (toujours « neutre ») par un modèle multilingue déjà entraîné sur XNLI, utilisé tel quel, et mesurer le seuil que le Model 2 entraîné devra dépasser.
- **Données** : corpus NLI du Lot A1, `nli_corpus_300_consolide_v3_prive.jsonl` (privé, non versionné). 37 paires en attente de validation (« Brouillon non valide ») mises de côté → 263 paires. Découpage par groupe d'articles (graine 42) : train 174, val 33, test 56. Le test contient les 30 paires des articles du jeu de test du Lot D (Tunifact 613, 698, 797, 890, 933, 937). Aucun texte partagé entre les parties. Identifiants : `data/splits/nli_v3_by_article_seed42.json`. Langues du test : 25 fr, 31 ar, 0 tunisien.
- **Méthode / configuration** : `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`, sans entraînement. Prémisse = preuve, hypothèse = affirmation ; entailment → supports, contradiction → refutes. Troncature de la preuve à 512 tokens. CPU, 191 s pour 56 paires. Déterministe.
- **Code** : `python -m models.nli.data --version v3 --input …` puis `python -m models.nli.evaluate --version v3 --split test --exp-id EXP-C-008`.
- **Résultats (test, n = 56)** : accuracy 0.804, **macro-F1 0.798** (IC 95 % bootstrap [0.669 ; 0.891]).
  - supports : P 0.95, R 0.83, F1 0.88 ; refutes : P 0.93, R 0.68, F1 0.79 ; neutral : P 0.59, R 0.93, F1 0.72.
  - Confusion (vrai → prédit) : supports → neutral 4 ; refutes → neutral 5, refutes → supports 1 ; neutral → refutes 1.
  - Par langue : fr 0.779 (n = 25), ar 0.776 (n = 31). Articles du test du Lot D : 0.767 (n = 30).
- **Analyse** : le modèle tranche rarement à tort (précision 0.93–0.95 sur supports / refutes) ; ses erreurs vont presque toutes vers « neutral », ce qui mène le verdict du Lot D à s'abstenir plutôt qu'à affirmer une erreur. Pas d'écart entre français et arabe. Limites : petit test (IC large), corpus v3 encore en correction, aucune paire en tunisien ou en arabizi.
- **Décision / suite** : baseline retenue et branchée dans `models/nli/stance.py` (utilisable par le Lot D). Suite : affiner ce même modèle sur le train (plutôt qu'entraîner XLM-R depuis zéro sur 174 paires), 3 graines, comparaison bootstrap à cette baseline ; mesures officielles une seule fois sur la v4 du corpus ; demander au Lot A1 des paires en tunisien.

### EXP-A2-011 — Revue Bronze : baselines triviales, gel des jeux, normaliseur mesuré
- **Date** : 2026-10-26
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : donner, pour chaque composant du Lot A2, le score sur un jeu gelé à côté
  d'une baseline triviale, séparer dev et test, mesurer le normaliseur et regrouper les erreurs en
  4 à 6 familles, comme l'exige le guide de la revue Bronze. Aucun réglage : mesure seulement.
- **Données** :
  - **test** : `tests/fixtures/linguistic_analysis/eval_30.jsonl` (34 phrases : 10 FR, 10 arabe
    standard, 14 tunisien dont 5 en lettres arabes, 5 en arabizi, 4 mixtes), jamais utilisé pour
    écrire les règles du Lot A2 (EXP-A2-002) ; gelé au commit `85fb77d` (2026-10-20),
    SHA-256 `1d0bcfaa4b2a01fbd428fb18240174e309ac9877dc474a4dc1399e15e9dd34ce` ;
  - **dev (mise au point)** : références adjudiquées d'EXP-A2-009, non versionnées, gelées le
    2026-10-26 : `tsac_arabic_sample_reference.tsv` (100 textes : 77 `t`, 23 `a`), SHA-256
    `a59f3d27621a4f4d4297f7d73b80301418767197316fb785cb7f0f32bb4ad92f` ; `tsac_latin_sample_reference.tsv` (86 textes décidés : 70 `t`, 16 `f`), SHA-256
    `1703f003cc0132c148ca46bf92b86ea05270d8851eb3d447109e366985877a46`. Ces échantillons ont servi à écrire le guide et à choisir des mots (EXP-A2-002) :
    ils ne sont pas un test ;
  - rappel, tests de fausses alertes : PADT `test` (680 phrases, EXP-A2-004), UD French-GSD `test`
    (416 phrases, EXP-A2-003 / 008).
- **Méthode / configuration** : `python -X utf8 -m normalization.review` (déterministe). Baselines :
  « majorité » (toujours la classe la plus fréquente du jeu) ; « alphabet seul » (lettres arabes →
  `ar`, sinon `fr` : baseline triviale ; le normaliseur d'origine faisait mieux : exactitude 0.82, EXP-A2-001). Normaliseur : textes dont les nombres sont
  identiques avant et après `normalize` (chiffres arabes-indiens convertis comptés comme conservés),
  et mots différents avant / après, contre la baseline « copie de la source ». Erreurs du dev
  exportées avec leur catégorie d'EXP-A2-009, regroupées en 5 familles. Sortie gardée hors dépôt :
  `data/interim/langid/bronze_review.txt` et `bronze_erreurs.csv` (textes du corpus, non versionnés).
- **Code** : `normalization/review.py`, 3 tests dans `tests/test_normalization_review.py` (ce commit) ;
  tableaux de la revue dans `docs/lot-a2_revue_bronze.md`.
- **Résultats** (macro-F1 / exactitude) :
  - test eval_30 : système 0.94 / 0.94 ; majorité 0.19 / 0.41 ; alphabet seul 0.50 / 0.59. Par
    classe : `ar` F1 0.95, `fr` 0.95, `tn` 0.92 (rappel 0.86). Par langue et alphabet : ar/arabe
    10/10, fr/latin 10/10, tn/arabe 4/5, tn/arabizi 5/5, tn/mixte 3/4 ;
  - dev lettres arabes : système 0.63 / 0.64 ; majorité 0.43 / 0.77 ; alphabet seul 0.19 / 0.23.
    `ar` : précision 0.39, rappel 1.00 ; `tn` : précision 1.00, rappel 0.53 ;
  - dev lettres latines : système 0.83 / 0.90 ; majorité 0.45 / 0.81 ; alphabet seul 0.16 / 0.19.
    `fr` F1 0.73 ; `tn` F1 0.94 ;
  - normaliseur (220 textes des trois jeux) : nombres conservés 29/29 textes (copie : 29/29) ;
    mots différents 1 366 → 1 340, soit 1.9 % de moins (copie : 0 %) ;
  - erreurs du dev (45) : lexique incomplet 13, morphologie dialectale 11, texte trop court ou sous
    le seuil 9, effet d'une règle choisie 7, étiquette discutable 5 ; aucune sans catégorie ;
  - tests : 540 réussis ; `ruff check .` sans remarque.
- **Analyse** : sur le test, le Lot A2 dépasse nettement les deux baselines (0.94 contre 0.50 pour
  l'alphabet seul, qui ne voit jamais le tunisien). Sur le dev en lettres arabes, la majorité a une
  meilleure exactitude (0.77 contre 0.64) mais une macro-F1 bien plus basse (0.43 contre 0.63) : elle
  répond `tn` partout et ne trouve jamais l'arabe standard ; avec 77 % de `tn`, seule la macro-F1
  rend compte des deux classes. Le système est prudent (précision `tn` 1.00, aucune presse classée
  tunisienne) au prix du rappel (0.53). Le normaliseur respecte la règle d'or ; sa réduction du
  vocabulaire est modeste, car son rôle est une forme canonique, pas une réduction forte. Limites :
  test petit (34 phrases, 5 en tunisien lettres arabes), annoté par une seule personne (Lot B) ;
  les scores du dev sont optimistes, ce jeu ayant servi à la mise au point.
- **Décision / suite** : chiffres retenus pour la revue Bronze (tableaux dans
  `docs/lot-a2_revue_bronze.md`). Suite : tirer un échantillon TSAC neuf, jamais vu, et le faire
  annoter par deux personnes pour disposer d'un vrai test du tunisien.

### EXP-A2-010 — Perplexité : repérer les textes bruités
- **Date** : 2026-10-26
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : repérer les segments bruités (encodage abîmé, lettres au hasard) avant
  l'annotation et l'analyse (plan S3). Hypothèse : un modèle de langue appris sur des commentaires
  donne une perplexité nettement plus haute à un texte cassé qu'à un commentaire ordinaire.
- **Données** : commentaires TSAC (4 fichiers) et Tunizi (`tunizi_train`), préparés par `normalize`,
  minuscules, emojis et symboles retirés, 3 mots ou plus, doublons retirés, non versionnés. Rangés par
  alphabet (≥ 90 % de lettres arabes ou ≤ 10 %, textes mêlés exclus), mélangés (graine 13), découpés
  80 / 10 / 10 : lettres arabes 4 556 / 569 / 569 ; lettres latines 53 804 / 6 725 / 6 725.
- **Méthode / configuration** : modèle de langue à n-grammes de caractères, ordre 4, interpolation des
  ordres 1 à 4 (poids 0,1 / 0,2 / 0,3 / 0,4), lissage add-one à l'ordre 1 ; un modèle par alphabet.
  Seuil = 95e centile des perplexités de dev (5 % de fausses alertes visées) ; le test ne sert qu'à
  mesurer. Bruit artificiel sur 1 000 textes de test : « encodage » (UTF-8 relu en Windows-1252),
  « lettres » (30 % des lettres remplacées au hasard), « mélange » (lettres de chaque mot mélangées).
  AUC sur 300 textes propres × 300 bruités ; baseline aléatoire : AUC 0,5.
  Commande : `python -X utf8 -m normalization.perplexity` ; sortie gardée hors dépôt
  (`data/interim/langid/exp010_perplexity.txt`), modèle dans `data/interim/langid/perplexity_model.pkl`.
- **Code** : `normalization/perplexity.py` (`perplexity`, `is_noisy`), 3 tests dans
  `tests/test_normalization.py` (ce commit).
- **Résultats** :
  - lettres arabes : seuil 11,4 ; textes propres de test signalés 4,7 % ; repérés : encodage 100 %
    (AUC 1,000), lettres 99,6 % (0,999), mélange 99,5 % (0,997) ;
  - lettres latines : seuil 13,2 ; textes propres de test signalés 5,3 % ; repérés : encodage 12,3 %
    (AUC 0,532), lettres 99,3 % (0,996), mélange 99,0 % (0,990) ;
  - textes réels de dev les plus « surprenants » : en lettres latines, accents décoratifs dans de
    l'arabizi (« jàwna a7là jàw »), suites de chiffres, répétitions ; en lettres arabes, lettres rares
    mais propres au tunisien (ڨ) et lettres d'autres alphabets proches (ھ) ;
  - tests : 477 réussis ; `ruff check .` sans remarque.
- **Analyse** : l'hypothèse tient pour les lettres au hasard et mélangées (≥ 99 %) dans les deux
  alphabets, et pour l'encodage abîmé en lettres arabes. Le taux de fausses alertes sur test (4,7 % et
  5,3 %) confirme le seuil réglé sur dev. Limite : en lettres latines, l'encodage abîmé n'est presque
  pas repéré (AUC 0,53, proche du hasard), car l'arabizi n'a presque pas de lettres accentuées et la
  relecture en Windows-1252 le laisse quasi inchangé. Les textes réels les plus surprenants ne sont pas
  du bruit mais une écriture atypique : la perplexité mesure l'écart à un commentaire ordinaire, et
  pénalise des lettres légitimes du tunisien (ڨ), rares dans TSAC.
- **Décision / suite** : retenu pour **signaler** les textes (`is_noisy`), pas pour les supprimer
  (risque de perdre du tunisien authentique). Suite : règle de détection des motifs d'encodage abîmé
  (« Ã », « Ø ») pour les lettres latines ; mesurer le taux de textes signalés sur les nouvelles
  annotations du Lot A1.

### EXP-A2-009 — Adjudication de l'annotation et analyse d'erreurs
- **Date** : 2026-10-26
- **Auteur / Lot** : Membre 2 / Lot A2, avec les secondes annotatrices des Lots B et D
- **Objectif / hypothèse** : (a) fixer des étiquettes de référence pour les deux échantillons
  annotés, en tranchant les 21 désaccords d'EXP-A2-007 ; (b) analyser au moins 30 erreurs de
  l'identification de langue, classées par cause, comme l'exige le palier Bronze.
- **Données** : les deux échantillons d'EXP-A2-004 (TSAC, 100 textes chacun, non versionnés).
  Fichiers de référence créés à côté des fichiers d'origine, qui restent inchangés (le kappa
  d'EXP-A2-007 reste vérifiable) : `tsac_arabic_sample_reference.tsv` et
  `tsac_latin_sample_reference.tsv`.
- **Méthode / configuration** : séance d'adjudication commune (lettres arabes avec le Lot D, lettres
  latines avec le Lot B), une règle écrite par décision. Lettres arabes : 10 étiquettes changées sur 13
  désaccords ; lettres latines : 4 sur 8. Après la séance, l'annotateur 1 a remis en question 3 lignes
  sur lesquelles les deux annotateurs étaient d'accord (74, 82, 86) et une ligne tranchée à deux (44) :
  les étiquettes communes sont gardées, ces lignes sont signalées (catégorie A8). Puis
  `normalization.evaluate --errors` sur les fichiers de référence et classement des erreurs.
- **Code** : `normalization/evaluate.py` (commit `3df2b10`) ; guide `docs/lot-a2_guide_annotation.md`
  et analyse `docs/lot-a2_analyse_erreurs.md` (ce commit).
- **Résultats** :
  - règles ajoutées au guide : insultes et mots étrangers mis de côté (jamais une raison de `x`) ;
    `حلو` / `حلوة` compté comme marque tunisienne ; `معاك` / `معاه` en fin de phrase standard ne
    suffit pas ; vœu en arabe standard → `a` ; en lettres latines, un emprunt ou un mot français
    isolé ne rend pas la phrase mélangée ; seuil de 3 mots pour `x` discuté, non retenu ;
  - sur les étiquettes de référence : lettres arabes, `a` 23/23, `t` 41/77 (0,53) ; lettres latines,
    `f` 12/16, `t` 65/70 (0,93). Première passe, pour comparaison : `a` 15/15, `t` 41/78 ; `f` 11/16,
    `t` 62/67 ;
  - 45 erreurs classées en 10 catégories (détail : `docs/lot-a2_analyse_erreurs.md`). Lettres arabes
    (36) : mot absent du lexique 7, variante orthographique 6, affixe collé 5, négation contractée 4,
    texte très court 4, marque écartée par choix 3, construction 2, étiquette discutable 5. Lettres
    latines (9) : « bravo + nom » 4, texte court ou sous le seuil 5.
- **Analyse** : le rappel du tunisien en lettres arabes (0,53) ne change pas avec l'adjudication ; ses
  erreurs ont des causes précises. 21 sur 36 (A1 à A4) sont réparables par des règles (lexique plus
  grand, variantes, affixes, négation contractée), à condition de remesurer les fausses alertes sur la
  presse. Les erreurs en lettres latines viennent surtout de textes de 1 à 3 mots, prix du seuil
  prudent, et de la règle fragile « bravo + nom ». Limites : une seule séance d'adjudication ; `حلو`
  compté comme marque sur 2 lignes seulement ; 4 lignes signalées restent à revoir.
- **Décision / suite** : étiquettes de référence retenues pour les mesures suivantes. Suite :
  lexique élargi, affixes et négation contractée (une expérience, mesurée sur la presse et sur ces
  références) ; revoir les lignes A8 avec la seconde annotatrice.

### EXP-A2-008 — Arabizi : chiffre 8 (= غ) dans la règle à chiffres
- **Date** : 2026-10-25
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : suggestion de la revue de la PR #3 (Lot D) : en arabizi tunisien, 8
  remplace غ (« 8ali », « 8odwa »), absent de la règle (`235679`). Hypothèse : l'ajouter ne crée
  aucune fausse alerte sur le français et apporte un gain, sans changer les résultats déjà publiés.
- **Données** : UD French-GSD (train 14 450, dev 1 476, test 416 phrases) ; commentaires TSAC + Tunizi
  en lettres latines, sans doublon (78 173) ; échantillon annoté en lettres latines (100 textes).
- **Méthode / configuration** : mesure avant tout changement de code, avec la liste de chiffres
  modifiée en mémoire seulement (script hors dépôt `data/interim/langid/exp008_digit8.py`, sortie
  `exp008_digit8.txt`) ; lecture des 40 mots avec 8 les plus fréquents. Puis code : deux constantes
  publiques, `ARABIZI_DIGITS_V1` (règle d'origine) et `ARABIZI_DIGITS` (avec le 8, utilisée par le
  pipeline) ; `annotation.py` et `train_langid.py` gardent la règle d'origine, pour que l'échantillon
  publié (EXP-A2-004) et le modèle (EXP-A2-006) ne changent pas. « 8bit » et « 8bits » ajoutés aux
  faux amis.
- **Code** : commit `76e92e8` : `normalization/normalize.py`, `normalization/annotation.py`,
  `normalization/train_langid.py`, `tests/test_normalization.py`.
- **Résultats** :
  - français classé arabizi par les règles : train 7 → 7, dev 1 → 1, test 0 → 0 : aucune nouvelle
    fausse alerte ;
  - commentaires en lettres latines reconnus arabizi par les règles seules : 50 166 → 50 346
    (+180) ; décision finale (règles + modèle) modifiée pour 20 textes, tous de `latin` à `arabizi`
    (« darban lou8a », « el 8ira », « ye 8oul »…) ;
  - mots avec 8 reconnus : tous tunisiens parmi les 40 plus fréquents (8ir, 8ali, 8alta, 8oul,
    8odwa…) ; un faux ami vu dans les exemples, « 8bits », dans un commentaire par ailleurs tunisien ;
  - échantillon annoté : aucune ligne ne change ;
  - preuves après le changement : 470 tests réussis (12 nouveaux), modèle régénéré à l'identique
    (test lent), tirage latin refait identique (100 sur 100), `ruff check .` sans remarque.
- **Analyse** : l'hypothèse tient. Sur 180 textes gagnés par les règles, 160 étaient déjà reconnus
  par le modèle à n-grammes : le gain net pour la détection est faible (20 sur 78 173). Ce chiffre
  est optimiste pour le modèle, car Tunizi fait partie de ses données d'entraînement. L'intérêt
  principal du 8 est ailleurs : les textes trop courts pour que le modèle se prononce, et la future
  translittération arabizi → arabe (« 8ali » → غالي). Garder deux règles explicites évite qu'un
  changement de la règle du pipeline modifie en silence un résultat déjà publié.
- **Décision / suite** : retenu. Suite : translittération arabizi → arabe pour le Lot D (3 candidats
  par mot avec score, meilleure phrase, nombres et mots français intacts).

### EXP-A2-007 — Double annotation de la langue : accord entre annotateurs (kappa)
- **Date** : 2026-10-21
- **Auteur / Lot** : Membre 2 / Lot A2 ; secondes annotatrices : Membre 3 / Lot B (lettres
  latines), une membre du Lot D (lettres arabes)
- **Objectif / hypothèse** : vérifier que les guides d'annotation sont utilisables par une autre
  personne, en mesurant l'accord avec le kappa de Cohen. Repères usuels (Landis et Koch) : au-dessus
  de 0.6, accord substantiel ; au-dessus de 0.8, presque parfait.
- **Données** : les deux échantillons d'EXP-A2-004 (TSAC, 100 commentaires chacun, graine 13, non
  versionnés) : lettres arabes (`t` / `a` / `x`) et lettres latines (`t` / `f` / `x`). Annotateur 1 :
  première passe d'EXP-A2-002 et EXP-A2-003, après application des règles écrites.
- **Méthode / configuration** : copie vierge (`annotation blank`, toutes les étiquettes à `?`, textes
  vérifiés identiques ligne à ligne), envoyée en privé avec une version du guide sans les comptages ni
  les remarques sur des lignes de la première passe ; annotation seule, sans voir les sorties du
  modèle. Une ligne oubliée (`?`) a été complétée par l'annotatrice, sans indication. Calcul :
  `python -m normalization.annotation kappa` (3 classes) ; sorties gardées hors dépôt
  (`data/interim/langid/kappa_latin.txt`, `kappa_arabic.txt`).
- **Code** : `normalization/annotation.py`, commande `kappa` (commit `e001a7d`).
- **Résultats** :
  - lettres latines : accord observé 0.92, attendu par hasard 0.50, **kappa 0.84** ; 8 désaccords ;
    répartitions 67 `t` / 16 `f` / 17 `x` (annotateur 1) et 67 `t` / 15 `f` / 18 `x` ;
  - lettres arabes : accord observé 0.87, attendu par hasard 0.63, **kappa 0.65** ; 13 désaccords ;
    répartitions 78 `t` / 15 `a` / 7 `x` (annotateur 1) et 76 `t` / 23 `a` / 1 `x` ;
  - avec 100 textes, intervalle à 95 % d'environ ± 0.11 (latin) et ± 0.18 (arabe).
- **Analyse** :
  - latin : aucun texte `t` de l'annotateur 1 n'est `f` pour l'annotatrice ; 7 des 8 désaccords
    opposent `x` à une langue. Cause principale (lignes 6, 26, 61, 84) : le guide ne dit pas quand un
    mot d'origine française rend la phrase mélangée (emprunt courant comme « patron », ou mot
    grammatical comme « mais ») ; l'annotateur 1 n'a pas tranché ces cas de la même façon partout.
    Lignes 37 et 52 : écarts de l'annotateur 1 à son propre guide (« bravo » est passe-partout) ;
    ligne 14 : écart de l'annotatrice au cas « bravo + nom → `f` » ; ligne 43, notée douteuse à la
    première passe : `t` pour l'annotatrice ;
  - arabe : aucun des 7 `x` de l'annotateur 1 n'est partagé (lignes 10, 15, 28, 43, 47, 76, 95) : la
    règle « formule figée ou trop courte pour décider » n'a pas de seuil. Lignes 12, 33, 44, 71 : `t`
    de l'annotateur 1 sur des textes standard dont le seul indice est une non-marque du guide (mot
    familier commun, insulte, mot étranger). Ligne 20 : le cas ouvert « … معاك ». Ligne 40 : cas
    réellement difficile. Le kappa est aussi abaissé par le déséquilibre des classes (77 % de `t`),
    d'où un accord attendu par hasard de 0.63 ;
  - lecture complémentaire, calculée après avoir vu les résultats et non retenue comme résultat : sur
    les 92 lignes arabes sans `x` d'aucun côté, 87 accords et kappa d'environ 0.82. Le désaccord porte
    surtout sur l'usage de `x`, peu sur tunisien / arabe standard ;
  - limites : un seul second annotateur par échantillon ; 100 textes. Les deux annotatrices ont relu
    la PR #3 avant d'annoter ; le guide du dépôt y cite des lignes douteuses de la première passe
    (latin : ligne 43, avec son étiquette ; arabe : lignes 12, 20, 33, 71, 86, sans étiquette). La
    ligne 43 latine et 4 de ces lignes arabes sont parmi les désaccords : influence possible, non
    mesurable.
- **Décision / suite** : guides retenus comme utilisables (latin : presque parfait ; arabe :
  substantiel). Suite : adjudication des 21 désaccords avec chaque annotatrice pour fixer les
  étiquettes de référence ; préciser dans les guides les emprunts français et l'usage de `x` ; retirer
  du guide du dépôt les comptages et numéros de ligne avant toute nouvelle annotation ; remesurer les
  modèles sur les étiquettes de référence.

### EXP-A2-006 — Arabizi : modèle réentraîné avec la liste de mots neutres à jour
- **Date** : 2026-10-21
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : rendre le fichier de poids régénérable avec le code actuel. Le modèle
  d'EXP-A2-003 (7 oct.) a été entraîné avant l'ajout de 8 noms de lieux aux mots neutres
  (EXP-A2-005, 19 oct.). Comme `prepare_latin` retire aussi ces mots à l'entraînement,
  `python -m normalization.train_langid` ne redonnait plus le fichier commité (19 983 lignes sur
  environ 20 000 différentes). Hypothèse : le réentraînement ne dégrade aucune mesure du pipeline.
- **Données** : mêmes corpus et même graine (13) qu'EXP-A2-003 : arabizi, 66 241 textes pour
  apprendre et 7 360 mis de côté ; français, 35 194 morceaux pour apprendre et 1 476 phrases `dev`
  (2 941 textes avec leurs 5 premiers mots) ; français de test (416) ; eval_30 (34 phrases) ;
  échantillon annoté en lettres latines (67 `t`, 16 `f`) ; test de bascule d'EXP-A2-005 (2 912 textes
  × 7 ajouts = 20 384 variantes).
- **Méthode / configuration** : réentraînement sans autre changement (régression logistique,
  n-grammes de caractères 1-4, C = 0.5, 20 000 poids exportés). Comparaison de l'ancien et du nouveau
  modèle sur exactement les mêmes textes, au même seuil 5.0 (script hors dépôt
  `data/interim/langid/exp006_compare.py`). Entraînement lancé deux fois : fichiers identiques.
  `train_langid.py` dit désormais quand le seuil est choisi par repli.
- **Code** : commit `e365e55` : `normalization/resources/arabizi_ngrams.json`,
  `normalization/train_langid.py`.
- **Résultats** (ancien → nouveau modèle) :
  - nettoyage du corpus arabizi : 60 → 57 textes retirés comme français ;
  - français `dev` classé arabizi au seuil 5.0 : 0 → 1 sur 2 941. Ce texte est « can you feel it a »
    (score 4.79 → 5.10), de l'anglais rangé dans UD French-GSD. Aucun seuil n'atteint 0 : le script
    garde 5.0 par repli ;
  - français de test : 0/416 → 0/416 ; eval_30 identique : FR 10/10, AR 10/10, TN 12/14 ;
  - bascules dues aux noms de lieux : 0 → 0 sur 20 384 ;
  - échantillon annoté : TN classé arabizi 61 → 62 sur 67 (gagné : « Kalib rcd . ») ; FR classé
    arabizi 4 → 5 sur 16 (perdu : « Bravo Mme Meherziya », cas « bravo + nom » que le guide laisse
    ouvert) ;
  - arabizi mis de côté retrouvé : 6 687 sur 7 360 (91,24 %). Pas strictement comparable aux 6 701
    sur 7 363 d'EXP-A2-005 : changer la liste modifie les doublons, donc le tirage ;
  - tests : 518 réussis ; `ruff check .` sans remarque.
- **Analyse** : l'hypothèse tient. Le seul écart négatif sur le français `dev` vient d'une erreur
  d'étiquette du corpus (texte anglais) ; l'écart sur l'échantillon porte sur un cas que le guide ne
  tranche pas nettement. Les mesures utiles au pipeline sont inchangées. Le seuil n'est pas réajusté
  après avoir vu les résultats : il reste celui d'EXP-A2-003. Limite : le critère « aucun français
  `dev` classé arabizi » n'est plus atteint au sens strict, à cause de ce texte anglais ; à revoir avec
  le nettoyage des corpus.
- **Décision / suite** : nouveau modèle retenu, régénérable à l'identique. Suite : test de
  régénération (sauté sans corpus ni scikit-learn), exception dans `CONTRIBUTING.md`,
  `linguist-generated` dans `.gitattributes`.
### EXP-C-010 — Détection d'affirmations (Model 1), palier Bronze : TF-IDF de caractères

- **Date / auteur** : 2026-10-25, Achref (Lot C) ; branchement dans l'API 2026-10-26.
- **Objectif / hypothèse** : un classifieur classique (TF-IDF + régression logistique) suffit-il à distinguer AFFIRMATION / OPINION / AUTRE nettement mieux que la classe majoritaire, en français, arabe, tunisien et arabizi ?
- **Données** : 600 phrases annotées (`claim_detection_600.jsonl`, privé, non versionné). Split stratifié `data/splits/claim_detection_multiclass_600_seed42.json` : train 480, test 120 (AFFIRMATION 63, AUTRE 38, OPINION 19).
- **Test gelé** : SHA-256 `9a25686286ccb3271ca98fe9b03046e2a0cb55cf6e5b7f43ab467669b5a8cee0` (fichier versionné dans git), gelé le 2026-10-25 au commit 533071d, mesuré une seule fois.
- **Méthode / configuration** : `models/baselines/claim_detection_multiclass_tfidf.py`. TF-IDF de n-grammes de caractères 3–5 (`char_wb`) + régression logistique `class_weight=balanced`. Représentation caractères choisie d'avance (robuste aux variantes d'écriture du tunisien et de l'arabizi) ; comparaison en validation croisée 5 plis sur le train : BoW mots 0.679, TF-IDF mots 0.717, caractères 0.679, caractères + normalisation A2 0.671. Baseline triviale : classe majoritaire du train. Déterministe.
- **Code** : `python models/baselines/claim_detection_multiclass_tfidf.py data/interim/lot_c/claim_detection_600.jsonl --split-file data/splits/claim_detection_multiclass_600_seed42.json --output evaluation/results/lot-c_claim-detection_tfidf_test.json --save-model models/checkpoints/claim_detection_tfidf_seed42.joblib`
- **Résultats (test, n = 120)** : macro-F1 **0.643** (reproduit : 0.6435) ; accuracy 0.733 vs **0.230** classe majoritaire (acc 0.525). Par langue : fr 0.576 (n = 26), ar 0.478 (n = 30), tunisien arabe 0.704 (n = 18), arabizi 0.554 (n = 28), mixte 0.813 (n = 18) ; petits effectifs, écarts indicatifs. Mesures sur le test des autres représentations, pour information seulement (pas de choix sur le test) : BoW 0.605, TF-IDF mots 0.550, caractères 0.643, caractères + A2 0.680.
- **Analyse d'erreurs** : 32 erreurs sur 120 : opinion non reconnue 11, question / souhait 8, hypothèse / conditionnel 6, récit personnel pris pour un fait 4, fait tunisien classé opinion 3.
- **Décision** : composant Bronze de la démo. L'API garde la classe la plus probable (argmax), comme dans l'évaluation. XLM-R + LoRA reste disponible avec `CLAIM_DETECTOR_BACKEND=xlmr` (après le Bronze).
- **Numérotation** : EXP-C-010, car EXP-C-001 désigne déjà le pilote binaire du 2026-10-21 (60 extraits, 0.4286), conservé tel quel.

### EXP-D-007 — Palier Bronze : baselines triviales, verdict avec le NLI Bronze du Lot C, erreurs
- **Date** : 2026-10-26
- **Auteur / Lot** : Membre 5 / Lot D
- **Objectif / hypothèse** : mesurer les composants Bronze du Lot D (retrieval BM25, verdict par
  gabarit) sur le test gelé, face aux baselines triviales exigées par la revue Bronze ; remplacer
  le NLI provisoire du Lot D par le NLI Bronze du Lot C ; classer les erreurs.
- **Données** :
  - dev : jeu fictif v2 (`tests/fixtures/rag_llm/`, 20 affirmations, 15 passages) ;
  - test : Tunifact v1, **gelé le 23/10/2026** (EXP-D-006, commit `ff08633`) ; 21 affirmations
    (18 avec preuve), 84 passages reconstruits depuis `lot-a1-data@77a00b9`. Empreintes SHA-256
    dans `data/splits/lot_d_tunifact_v1.json` : affirmations `9e2acf6f1d1954d9e91e24ada642b62ddf495047f84424a7335ab09b74a625b8`,
    corpus `ae0a351a32f6ce47046e78739ccf35a8076e9647a2fef7a1d70a7e7f134af362`
    (vérification : `python -m rag_llm.freeze_test --check`). Le test n'a servi à régler aucun
    paramètre.
- **Méthode / configuration** :
  - retrieval BM25 (k1 = 1.5, b = 0.75), top 5 ; verdict par gabarit (seuils inchangés depuis
    EXP-D-002) ;
  - NLI : **NLI Bronze du Lot C** (`models/nli/bronze.py`, règles R1–R6, seuils réglés par le
    Lot C sur train + val du corpus NLI v3, dont le split test contient les 6 articles de ce test :
    pas de fuite). Ce choix est fixé par l'architecture (le NLI relève du Lot C ;
    `rag_llm/baseline_stance.py` est documenté comme provisoire depuis EXP-D-002), il n'a pas été
    fait au vu des scores du test. Le NLI provisoire du Lot D est mesuré pour comparaison ;
  - baselines : passage aléatoire (espérance exacte du tirage, sans graine), classe majoritaire du
    dev (`faux`) appliquée partout, toujours s'abstenir ;
  - correctif de `baseline_stance.py` : un chiffre collé à des lettres en arabizi (« 5obez »,
    « 3am ») n'est plus lu comme un nombre. Trouvé en démonstration sur une phrase hors test
    (« soum 5obez 190 millimes »), puis vérifié : dev 0.70 et test 0.143 inchangés.
  - Composants déterministes : un seul passage sur le test. Nécessite le NLI Bronze du Lot C
    (PR #7) dans le dépôt.
- **Code** : `python -m rag_llm.bronze_report` (`--stance rules` pour la comparaison) ;
  erreurs dans `docs/lot-d_erreurs_bronze.csv` (sans texte de preuve) et
  `evaluation/results/lot-d_erreurs_lot-c.csv` (avec les textes, non versionné : droits Tunifact).
- **Résultats — tableau 1 (test ; dev entre parenthèses)** :

  | Composant | Méthode Bronze | Baseline triviale | Métrique | Baseline | Bronze | N test |
  |-----------|----------------|-------------------|----------|----------|--------|--------|
  | Retrieval | BM25 | passage aléatoire | Rappel@5 (↑) | 0.060 (0.333) | **0.411** (0.667) | 18 |
  | Retrieval | BM25 | passage aléatoire | MRR (↑) | 0.116 (0.302) | **0.630** (0.907) | 18 |
  | Verdict | gabarit + NLI Bronze C | classe majoritaire (`faux`) | exactitude (↑) | **0.524** (0.600) | 0.238 (0.500) | 21 |
  | Verdict | gabarit + NLI Bronze C | classe majoritaire (`faux`) | macro-F1 (↑) | 0.172 (0.187) | **0.188** (0.375) | 21 |
  | Verdict | gabarit + NLI Bronze C | toujours s'abstenir | exactitude (↑) | 0.143 (0.100) | **0.238** (0.500) | 21 |

  Verdict (test) : couverture 0.333, précision sélective 0.429 (3 verdicts justes sur 7 émis),
  abstention justifiée 0.667 (2 sur 3), 0 citation invalide. Avec le NLI provisoire du Lot D :
  exactitude 0.143, macro-F1 0.065, couverture 0.048 (dev : 0.700, 0.524, 0.650).
- **Résultats — tableau 2 (test, par langue / écriture)** :

  | Groupe | N | Rappel@5 BM25 | Rappel@5 aléatoire | Exactitude du verdict |
  |--------|---|---------------|--------------------|-----------------------|
  | FR | 9 | 0.357 | 0.060 | 0.444 |
  | AR | 7 | 0.650 | 0.060 | 0.143 |
  | Tunisien (arabe) | 2 | 0.167 | 0.060 | 0.000 |
  | Tunisien (arabizi) | 3 | 0.222 | 0.060 | 0.000 |

  Rappel@5 calculé sur les affirmations qui ont une preuve (FR 7, AR 6, tunisien 2 + 3).
- **Résultats — tableau 3 (erreurs ; test + dev)** :
  - retrieval BM25, chaque preuve attendue absente du top 5 : **52** (40 test + 12 dev) — langue
    croisée 24 (16 + 8), arabizi 12 (10 + 2), tunisien en lettres arabes 9 (7 + 2), même langue
    classé après le top 5 : 4 (4 + 0), paraphrase sans mot commun 3 (3 + 0) ;
  - verdict : **26** (16 test + 10 dev), toutes les erreurs des deux jeux — preuve retrouvée mais
    non décisive 8, bonne preuve non retrouvée 7, position inversée vrai ↔ faux 5, « trompeur »
    non produit par le gabarit 3, preuves jugées contradictoires 2, verdict émis sans preuve 1.
    Moins de 30 : le test ne compte que 21 affirmations ; aucune erreur n'est omise.
- **Analyse** :
  1. BM25 bat nettement le hasard (Rappel@5 × 7, MRR × 5). 45 de ses 52 échecs viennent du
     croisement de langues et du dialecte : sans mot commun, BM25 ne peut rien retrouver. C'est ce
     que corrige la recherche dense (EXP-D-003, hors palier Bronze) et ce que la translittération
     arabizi du Lot A2 doit améliorer.
  2. Le NLI Bronze du Lot C rend le verdict utile : couverture 0.048 → 0.333, exactitude 0.143 →
     0.238, et le démenti « Tunifact a classé comme fausse… » est enfin reconnu (`tf-c02`,
     `tf-c03`). Les affirmations françaises en profitent le plus (0.444).
  3. En exactitude, le verdict reste **sous la classe majoritaire** (0.238 contre 0.524) : le test
     est déséquilibré (11 affirmations fausses sur 21, comme la plupart des articles de
     fact-checking) et « tout est faux » n'est jamais en abstention. En macro-F1, qui compte
     chaque verdict à égalité, le système dépasse légèrement cette baseline (0.188 contre 0.172).
  4. Erreur la plus grave : `tf-c13` (« Le ministère de l'Éducation a annulé l'examen du
     baccalauréat 2026 ») reçoit « faux » en citant deux phrases de l'article sur le bac, qui ne
     parlent pas d'annulation : l'abstention justifiée passe de 1.00 à 0.67.
  5. Petit jeu (21 affirmations, 6 articles) : chiffres indicatifs.
- **Décision / suite** : configuration Bronze retenue : BM25 + NLI Bronze du Lot C + gabarit. Suite :
  translittération arabizi (Lot A2), test élargi à d'autres articles du Lot A1, label « trompeur »
  et recherche dense au palier Silver.
### EXP-C-007 — Ablation texte brut contre texte normalisé et alignement API
- **Date** : 2026-10-24
- **Auteur / Lot** : Lot C
- **Objectif / hypothèse** : vérifier l'effet de la normalisation A2 sur Model 1 et éviter que le modèle déployé reçoive une représentation différente de celle du test.
- **Données** : `claim_detection_600.jsonl`, test gelé de 120 phrases ; XLM-R seed42.
- **Méthode / configuration** : même architecture et split ; entraînement/évaluation `--text-mode raw`, puis `--text-mode normalized`. Bootstrap apparié à 1 000 réplications.
- **Code** : `models/encoders/train_xlmr_claim_detection.py`, `models/encoders/evaluate_claim_detection.py`, `pipeline.py`, `api/main.py`.
- **Résultats** : raw = 0,7108 ; normalisé = 0,6671 ; différence normalisé − raw = −0,0436 ; IC 95 % [-0,1184 ; 0,0202], p = 0,188. FR reste à 0,9148 ; AR 0,6989 → 0,6527 ; TN 0,6445 → 0,5791. Tests manuels API : `/extract` arabe et tunisien, puis `/check`, tous HTTP 200.
- **Analyse** : la baisse observée après normalisation n'est pas statistiquement significative, mais le raw est supérieur sur ce test. Le pipeline extrait toujours les claims normalisés pour les lots aval ; il classe désormais leurs phrases brutes correspondantes avec fallback normalisé si les segmentations divergent.
- **Décision / suite** : raw retenu pour Model 1 et inférence API alignée. Ne pas sélectionner un checkpoint sur le test ; seed42 reste le checkpoint de référence.

### EXP-C-006 — Baseline neuronale MiniLM figée
- **Date** : 2026-10-24
- **Auteur / Lot** : Lot C
- **Objectif / hypothèse** : ajouter la baseline neuronale exigée et mesurer ce qu'apporte un encodeur multilingue sans fine-tuning.
- **Données** : mêmes 480 entraînement / 120 test gelé que les autres systèmes.
- **Méthode / configuration** : `paraphrase-multilingual-MiniLM-L12-v2` utilisé comme embeddings figés, puis régression logistique multiclasses ; seeds 42, 123 et 2026.
- **Code** : `models/baselines/claim_detection_embedding_logreg.py`.
- **Résultats** : macro-F1 = 0,6350 ± 0,0000 ; FR 0,8228, AR 0,8002, TN 0,4886.
- **Analyse** : MiniLM aide FR/AR, mais échoue nettement sur le tunisien et reste sous TF-IDF globalement.
- **Décision / suite** : baseline conservée pour comparaison ; XLM-R + LoRA reste le modèle avancé.

### EXP-C-005 — Bootstrap apparié TF-IDF contre XLM-R
- **Date** : 2026-10-24
- **Auteur / Lot** : Lot C
- **Objectif / hypothèse** : déterminer si l'écart seed42 XLM-R contre baseline classique est compatible avec le hasard d'échantillonnage du test.
- **Données** : les mêmes 120 prédictions de TF-IDF et XLM-R seed42, appariées par identifiant.
- **Méthode / configuration** : 1 000 rééchantillonnages avec remise ; macro-F1 ; p-value bilatérale.
- **Code** : `models/evaluation/bootstrap_paired_macro_f1.py`.
- **Résultats** : TF-IDF 0,6435 ; XLM-R 0,7108 ; Δ = +0,0673 ; IC 95 % [-0,0468 ; 0,1860] ; p = 0,254.
- **Analyse** : l'IC contient zéro ; le test de 120 phrases ne permet pas de conclure à une amélioration statistiquement significative.
- **Décision / suite** : rapporter l'amélioration observée avec son incertitude ; augmenter le test pour une conclusion plus forte.

### EXP-C-003 — Évaluation par langue du checkpoint Model 1 déployé
- **Date** : 2026-10-23
- **Auteur / Lot** : Lot C
- **Objectif / hypothèse** : mesurer le checkpoint de référence (`seed42`) sur le test gelé et vérifier
  si les performances varient selon la langue.
- **Données** : 120 exemples de test de `claim_detection_600.jsonl` ; métadonnées de langue revues,
  soit 26 FR, 30 AR et 64 TN dans le test.
- **Méthode / configuration** : checkpoint XLM-R + LoRA `claim_detection_xlmr_lora_seed42` ; même
  protocole qu'EXP-C-002. Évaluation par `models/encoders/evaluate_claim_detection.py` sur Colab GPU.
- **Code** : fichiers `models/encoders/evaluate_claim_detection.py` et
  `data/prepare_claim_detection_dataset.py`.
- **Résultats** : exactitude 0.7917 ; macro-F1 globale **0.7108**. Macro-F1 par langue : FR =
  **0.9148** (n=26), AR = **0.6989** (n=30), TN = **0.6445** (n=64). F1 par classe : AFFIRMATION
  0.8824, OPINION 0.5000, AUTRE 0.7500. Aucun exemple `unk`.
- **Analyse** : la classe OPINION est la plus difficile (rappel 0.4211), donc le modèle la confond
  encore fréquemment avec les deux autres classes. Le score TN, plus faible et porté par le plus grand
  groupe, demande une revue ciblée des erreurs arabizi/mixed. Les sous-groupes FR et AR restent petits.
- **Décision / suite** : retenir seed42 pour l'intégration (choix fixé avant cette évaluation) ; analyser
  les erreurs exportées avant toute modification de modèle. L'analyse de 30 erreurs est documentée
  dans `docs/lot-c_error_analysis_results.md` : 25 erreurs seed42 et 5 erreurs distinctes seed2026.

### EXP-B-006 — Tunisien en lettres arabes identifié par le Lot A2 : liste d'erreurs attendues
- **Date** : 2026-10-26
- **Auteur / Lot** : Membre 3 / Lot B
- **Objectif / hypothèse** : prise en compte de la PR #3 d'A2 (tunisien en lettres arabes identifié
  `tn`, donc analysé par les règles au lieu de Stanza) ; mise à jour de la liste d'erreurs attendues.
  Hypothèse : les erreurs du mode parseurs dues au tunisien envoyé à Stanza (catégories E7 et E2)
  disparaissent, sans effet sur le mode règles.
- **Données** : `eval_30.jsonl` (34 phrases, 22 affirmations, gold inchangé), jeu de **développement**,
  un seul annotateur. Langue fournie par A2 pour les 5 phrases de tunisien en lettres arabes : `tn`
  pour tn-a1, tn-a2, tn-a4 et tn-a5, `ar` pour tn-a3 (toujours analysée par Stanza).
- **Méthode / configuration** : aucun changement du code du Lot B. Fusion de `main` (PR #3 du Lot A2,
  `add268e`) dans `lot-b-linguistic`, puis `python -m linguistic_analysis.evaluate --compare` avant et
  après la fusion (bootstrap apparié, 1000 tirages, graine 20261015). spaCy 3.8 `fr_core_news_md`,
  Stanza 1.15 `ar`. Les fichiers de résultats portent encore l'identifiant `EXP-B-005` (constante
  `EXP_ID` de `evaluate.py`, non modifiée dans ce commit).
- **Code** : branche `lot-b-linguistic`, fusion de `origin/main` et mise à jour de
  `tests/fixtures/linguistic_analysis/error_categories.json` (section `corrigees_exp_b_006`).
- **Résultats** (avant → après la fusion) :
  - parseurs : sujet / prédicat / objet 0.95 / 0.91 / 0.82 → 0.95 / 0.95 / 0.86 ; triplet exact
    0.77 → 0.86 ; 7 → 5 erreurs (disparues : tn-a1:obj et tn-a4:predicate ; aucune erreur nouvelle) ;
  - règles : inchangé (sujet / prédicat / objet 0.95 / 0.95 / 0.91, triplet 0.91, 4 erreurs) ;
  - triplet exact par groupe en mode parseurs : TN lettres arabes 0.00 → 1.00 (2 affirmations) ; FR
    0.88, AR 0.86, arabizi 1.00 et mixte 0.50 inchangés ;
  - détection d'affirmation, modalité et coréférence inchangées (1.00) ;
  - comparaison appariée parseurs − règles, triplet exact : −0.14 [−0.35 ; +0.05] → −0.04
    [−0.21 ; +0.10] ; différence toujours non établie.
- **Analyse** : le gain vient entièrement de l'amont : les deux phrases concernées sont maintenant
  analysées par les règles, déjà correctes sur elles. Le groupe TN en lettres arabes ne compte que
  2 affirmations : l'écart de 0.00 à 1.00 ne doit pas être lu comme une mesure. tn-a3, toujours
  étiquetée `ar`, reste analysée par Stanza. Erreurs restantes avec parseurs : arbre spaCy faux (fr-02,
  3 erreurs), découpage dû au repli ة → ه (ar-01, point L7) et objet de mx-2. Limites : eval_30 est un
  jeu de développement, annoté par une seule personne ; aucun gold pour la source, le temps et le lieu.
- **Décision / suite** : liste d'erreurs attendues mise à jour (`corrigees_exp_b_006`). Mesure de
  référence sur `eval_100` une fois verrouillé.

### EXP-D-006 — Jeu de test réel Tunifact v1 (6 articles)
- **Date** : 2026-10-23
- **Auteur / Lot** : Membre 5 / Lot D
- **Objectif / hypothèse** : agrandir le jeu de test réel avec la nouvelle livraison du Lot A1
  (verdict et date fournis par article) et mesurer la chaîne actuelle, sans aucun réglage.
- **Données** : Lot A1, branche `lot-a1-data`, commit `77a00b9` :
  `data/exports/lot_d/tunifact_sentences_46.jsonl` (articles 698 → vrai, 933 → faux,
  937 → trompeur ; segmentation automatique) + articles 613, 797, 890 de v0 + 30 phrases TArC.
  Seul l'article 933 (nationalité des enfants de migrants, 25 phrases AR) est nouveau ; 698 et
  937 sont des versions complètes d'articles de v0 (+2 et +4 phrases). Construction : 1re phrase
  de chaque article écartée, fragments de moins de 15 caractères écartés (1 : « أبدا !! ») →
  84 passages (54 Tunifact de 6 articles, 30 TArC). Affirmations : 21 = les 15 de v0
  (identifiants convertis) + 6 sur l'article 933 (4 faux : AR, FR, TN lettres arabes, arabizi ;
  2 vrai : AR, FR). Rédigées par une seule personne ; traductions TN / arabizi à valider.
- **Méthode / configuration** : identique à EXP-D-005 (BM25, NLI par règles v2, gabarit). La
  reconstruction de v0 redonne exactement les résultats d'EXP-D-005 (exactitude 0.20, couverture
  0.067). Déterministe.
- **Code** : `python -m rag_llm.build_tunifact_eval` ; `evaluate_retrieval` et `evaluate_verdict`
  avec `--corpus data/interim/lot_d/evidence_tunifact_v1.jsonl --claims tests/fixtures/rag_llm/claims_tunifact_v1.jsonl`.
- **Résultats — retrieval (BM25, n = 18 avec preuve)** : Hit@1 0.611, Hit@5 0.667,
  Recall@5 0.411, MRR 0.630. Par groupe (Hit@1) : ar-arabic 0.83 (6), fr-latin 0.57 (7),
  tn-arabic 0.50 (2), tn-arabizi 0.33 (3). Échecs (aucune preuve dans le top 5) : `tf-c08`,
  `tf-c11`, `tf-c17`, `tf-c18`, `tf-c19`, `tf-c21` — toutes des affirmations FR, TN ou arabizi
  dont l'article est en arabe. Score du 1er passage : 4.7 à 36.2 quand il est correct ; 2.7 à
  12.1 pour les 3 affirmations sans preuve.
- **Résultats — verdict** : exactitude 0.143, couverture 0.048, précision sélective 0.00
  (1 verdict émis, faux : `tf-c03`), abstention justifiée 1.00, macro-F1 0.065, 0 citation invalide.
  Les 6 affirmations de l'article 933 : abstention (preuves non décisives).
- **Analyse** : la baisse par rapport à v0 (Hit@1 0.83 → 0.61) vient du nouvel article : il est
  en arabe, et 4 de ses 6 affirmations sont dans une autre langue ou en tunisien, que BM25 ne
  relie pas. C'est le cas que le retrieval hybride (EXP-D-003) doit corriger : à mesurer sur ce
  jeu. Le verdict reste limité par le NLI par règles (aucune règle de nombre ni de démenti ne
  s'applique aux affirmations juridiques de 933). Jeu encore petit (6 articles, 1 seul « vrai »,
  1 seul article en français) : chiffres indicatifs.
- **Décision / suite** : v1 devient le jeu de test du Lot D (v0 conservé pour la traçabilité) ;
  mesurer l'hybride e5-base / bge-m3 sur v1 (notebook, section 7) ; demander au Lot A1 des
  articles « vrai » et en français ; NLI du Lot C.

### EXP-D-005 — NLI par règles v2 : lecture des nombres
- **Date** : 2026-10-20
- **Auteur / Lot** : Membre 5 / Lot D
- **Objectif / hypothèse** : corriger les deux défauts **génériques** de lecture des nombres
  révélés par EXP-D-004 (séparateurs de milliers ; nombres faisant partie d'un nom), sans
  toucher au 3e défaut (phrase de verdict qui reprend la rumeur), qui demande un vrai NLI.
- **Données** : développement = jeu fictif v2 (`claims_dev.jsonl`) ; test = Tunifact v0
  (EXP-D-004), mesuré **une seule fois**, après les corrections.
- **Méthode / configuration** : `rag_llm/baseline_stance.py`, fonction `_numbers` :
  « 39 000 », « 39.000 », espace insécable → 39000 (groupe de 3 chiffres exactement, sinon
  décimal : « 16,4 », « 9.3 ») ; « 13 ألف », « 3 آلاف », « mille », « million(s) », « مليون »
  → multiplication ; nombre précédé d'une lettre latine ou d'une lettre + tiret ignoré
  (« Covid-19 », « كوفيد-19 », « G20 », « A320 »), préfixe arabe collé accepté (« و3 »).
  `rag_llm/retrieval/text.py` : signes arabes ٫ ٬ ٪ convertis. Reste inchangé (EXP-D-002).
- **Code** : `python -m rag_llm.evaluate_verdict` (dev), puis avec `--corpus
  data/interim/lot_d/evidence_tunifact_v0.jsonl --claims tests/fixtures/rag_llm/claims_tunifact_v0.jsonl`.
- **Résultats** :

  | Jeu | Exactitude | Couverture | Précision sélective | Verdicts faux émis | Abst. justifiée |
  |-----|------------|------------|---------------------|--------------------|-----------------|
  | dev fictif v2 (avant = après) | 0.70 | 0.65 | 0.92 | 1 | 1.00 |
  | Tunifact v0, avant (EXP-D-004) | 0.20 | 0.20 | 0.00 | 3 | 1.00 |
  | Tunifact v0, après | 0.20 | 0.07 | 0.00 | **1** | 1.00 |

  Détail Tunifact : `tf-c01` (698, vrai) faux → *preuves contradictoires* (la preuve donne
  3 300 médecins, la phrase de verdict 3 000 : désaccord réel entre les deux phrases de
  l'article) ; `tf-c02` (Covid-19) vrai → *preuves non décisives* ; `tf-c03` reste faussement
  « vrai » (3e défaut, attendu).
- **Analyse** : les corrections ne rendent pas le système plus juste (exactitude inchangée),
  mais **plus prudent** : 2 des 3 verdicts erronés et assurés deviennent des abstentions, ce qui
  est préférable pour un outil de vérification. Le 3e défaut est hors de portée de règles
  lexicales : « classé comme fausse l'information … 67 % » contient les mêmes nombres que la
  rumeur. Les corrections sont génériques (pas de mot ou de nombre propre aux 5 articles) ; elles
  ont cependant été motivées par ce jeu : il ne doit plus servir à régler les règles.
- **Décision / suite** : v2 retenue (moins d'erreurs assurées, dev inchangé). Le NLI par règles
  a atteint sa limite : brancher le NLI multilingue du Lot C ; S5 re-ranking.

### EXP-D-004 — Première évaluation sur données réelles : Tunifact v0
- **Date** : 2026-10-20
- **Auteur / Lot** : Membre 5 / Lot D
- **Objectif / hypothèse** : mesurer la chaîne retrieval → NLI par règles → verdict sur des
  articles de fact-checking réels, et vérifier si les conclusions tirées du jeu fictif tiennent.
- **Données** : Lot A1, branche `lot-a1-data` (commit `19976a4`) : 5 articles Tunifact découpés
  en phrases (698, 613, 797 en FR ; 890, 937 en AR). Corpus = 25 phrases Tunifact (la phrase
  `-001` de chaque article, qui reformule la rumeur, est exclue) + 30 phrases TArC (forum
  tunisien) comme distracteurs = 55 passages. 15 affirmations rédigées par le Lot D
  (`claims_tunifact_v0.jsonl`) : 5 dans la langue de l'article, 7 traduites (autre langue,
  tunisien, arabizi), 3 sans preuve dans le corpus. Labels = verdict publié par Tunifact
  (1 article vrai, 3 faux, 1 trompeur). Limites : 5 articles seulement ; les articles 613, 797
  et 890 sont des **reformulations** du Lot A1 ; affirmations et traductions écrites par une
  seule personne ; droits de redistribution Tunifact non confirmés (corpus non versionné).
- **Méthode / configuration** : identique à EXP-D-002 (BM25 k1 = 1.5, b = 0.75 ; NLI par
  règles ; gabarit ; seuil A2 = 1.0). Aucun réglage sur ce jeu. Déterministe.
- **Code** : `python -m rag_llm.build_tunifact_eval` puis
  `python -m rag_llm.evaluate_retrieval|evaluate_verdict --corpus data/interim/lot_d/evidence_tunifact_v0.jsonl --claims tests/fixtures/rag_llm/claims_tunifact_v0.jsonl`.
- **Résultats — retrieval (BM25, n = 12 avec preuve)** : Hit@1 0.833, Hit@5 0.833,
  Recall@5 0.542, MRR 0.833. Par groupe (Hit@1) : ar-arabic 1.00 (4), fr-latin 0.80 (5),
  tn-arabic 1.00 (1), tn-arabizi 0.50 (2). Échecs : `tf-c08` (FR → article AR) et `tf-c11`
  (arabizi). Score BM25 du 1er passage : 3.8 à 29.1 quand il est correct ; **2.0 à 9.6** pour les
  3 affirmations sans preuve.
- **Résultats — verdict** : exactitude 0.20, couverture 0.20, **précision sélective 0.00**
  (3 verdicts émis, tous faux), abstention justifiée 1.00, macro-F1 0.10, 0 citation invalide.
- **Analyse** :
  1. Le retrieval tient à peu près (Hit@1 0.83) ; les passages « croisés » trouvés par BM25 le
     sont grâce à des nombres ou des mots français cités dans l'article arabe (937-002 contient le
     titre français d'une dépêche) — chance, pas compréhension.
  2. **Le seuil d'abstention BM25 (1.0) ne vaut que pour le jeu fictif** : ici, une affirmation
     sans preuve (`tf-c13`, bac 2026 annulé) obtient 9.6, plus qu'une bonne preuve (3.8).
  3. **Le NLI par règles échoue sur des articles réels**, pour trois causes identifiées :
     - séparateurs de milliers : « 39 000 » devient {39, 000}, « 39.000 » est lu comme 39,0 →
       la preuve de l'article *vrai* 698 est jugée contradictoire (`tf-c01` → faux) ;
     - nombres dans les noms : « Covid-19 » donne le nombre 19, commun à l'affirmation et au
       verdict de Tunifact → « soutient » (`tf-c02` → vrai) ;
     - une phrase de verdict reprend l'affirmation pour la réfuter (« Tunifact a classé comme
       fausse l'information … 67 % … 33 % ») : mêmes nombres → « soutient » (`tf-c03` → vrai) ;
       « fausse », « زائفة », « مضللة » ne sont pas des marqueurs de démenti de la liste.
  4. Les 3 verdicts émis sont faux avec une incertitude faible : sur données réelles, le système
     se trompe **avec assurance**, ce qui est le pire cas pour un fact-checker. Les conclusions
     d'EXP-D-002 (précision sélective 0.92) étaient un artefact du jeu fictif, écrit en même
     temps que les règles.
- **Décision / suite** :
  - ce jeu devient le jeu de **test** du Lot D (ne plus régler de règle en le regardant) ;
  - NLI : priorité au modèle multilingue du Lot C ; en attendant, corriger les 2 défauts
    génériques des règles (séparateurs de milliers, nombres collés à des lettres) sur le jeu de dev,
    puis re-mesurer ici une seule fois ;
  - seuil d'abstention : ne plus utiliser le score BM25 brut ; re-ranker (S5) ;
  - demander au Lot A1 davantage d'articles (texte complet + verdict) pour dépasser 5 articles.

### EXP-B-005 — Lexiques selon l'écriture et verbe de parole précédé de « و » / « ف » collé
- **Date** : 2026-10-20
- **Auteur / Lot** : Membre 3 / Lot B
- **Objectif / hypothèse** : (a) une phrase en lettres arabes doit consulter les mêmes lexiques
  d'opinion et de modalité, que le Lot A2 l'étiquette `ar` ou `tn` : avec la table par langue, le
  tunisien étiqueté `tn` perdait les marqueurs de l'arabe standard (اعتقد, حسب, اذا) ; (b) un verbe
  de parole précédé de « و » / « ف » collé (« وقال », très fréquent en tête de phrase dans la presse)
  doit donner un triplet, la modalité `rapporté` et la source, dans les deux modes.
- **Données** : `eval_30.jsonl` (34 phrases, gold inchangé), jeu de **développement** ; 12 phrases de
  démonstration rédigées pour un audit (3 FR, 3 arabe standard, 3 tunisien en lettres arabes,
  3 arabizi), **non annotées**. Aucun jeu annoté hors développement : `eval_100` n'existe pas encore.
- **Méthode / configuration** : (a) `factuality.lexicon_codes` : phrase contenant des lettres arabes
  → lexiques tn puis ar (plus fr si des lettres latines s'y mêlent), quelle que soit la langue ;
  sinon table par langue inchangée ; le premier lexique prime en cas de conflit de clé
  (`modality._markers`). (b) Avec arbre : si la racine est « و » / « ف » (CCONJ), le verbe rattaché
  en `parataxis` ou `conj` devient la racine ; sans arbre : verbe de parole cherché aussi sans la
  conjonction collée (`preprocessing._verb_candidates`, préfixe retiré seulement au-delà de 3 lettres).
  Normalisation v1 du Lot A2 (fusionnée depuis `main`), spaCy 3.8 `fr_core_news_md`, Stanza 1.15 `ar`.
- **Code** : branche `lot-b-linguistic`, commits `15d02f9` (`fix(lot-b): lexiques de modalité et
  d'opinion choisis selon l'écriture`) et `1fdd355` (`fix(lot-b): verbe de parole précédé de « و » ou
  « ف » collé`) ; `python -m linguistic_analysis.evaluate --compare`.
- **Résultats** :
  - eval_30 : sorties **identiques** avant / après chaque commit, en mode règles et en mode parseurs,
    sur tous les champs (indices compris) ; scores inchangés (triplet exact 0.91 règles, 0.77
    parseurs ; 4 et 7 erreurs). eval_30 ne contient aucune phrase concernée par (b), et (a) ne change
    rien tant que le tunisien en lettres arabes reste étiqueté `ar` ;
  - tests ciblés, qui échouaient avant et passent après : (a) 6 tests, résultat identique avec `lang`
    forcé à `ar` et à `tn` pour ar-03, ar-07, ar-09 et 3 phrases construites (opinion, rapporté,
    incertitude) ; (b) 4 tests (arbre Stanza reproduit à la main, vraie sortie Stanza, mode règles
    avec « و », mode règles avec « ف » et un piège : « و » + verbe qui n'est pas un verbe de parole) ;
  - 12 phrases de démonstration : seule la phrase arabe « و + verbe de parole » change (triplet vide
    et `assertif` → triplet, `rapporté`, source = locuteur) ; les 11 autres sont identiques ;
  - **effet non mesuré sur un jeu annoté**.
- **Analyse** : défaut connu de (b) : le prédicat garde la conjonction (« وقال » au lieu de « قال »,
  convention du gold d'ar-04), car Stanza ne donne pas de position aux mots d'un token multi-mots :
  ils reçoivent l'empan du token entier ; en mode règles, le token n'est pas découpé. Non corrigé.
  Cas voisin non corrigé, cause en amont : avec Stanza, une phrase arabe standard du type « ارتفعت
  نسبة التضخم… » (démonstration D-AR-1) donne un sujet réduit à un mot et un objet faux, parce que
  `Document.text` replie ة → ه : Stanza découpe alors le mot en nom + pronom affixe ه et l'arbre
  change. Sur les phrases en lettres arabes d'eval_30, 18 des 24 mots finissant par ة sont découpés
  ainsi après normalisation, 0 sur le texte brut. Point L7, à traiter côté Lot A2 (texte moins
  normalisé ou correspondance des positions) ; un essai côté Lot B (Stanza sur le texte brut aligné)
  laisse eval_30 à 7 erreurs en mode parseurs (ar-01 corrigé, ar-10 nouveau) et n'est pas retenu.
- **Décision / suite** : retenu. Mesurer (a) et (b) sur `eval_100` une fois verrouillé ; prédicat
  sans conjonction collée à traiter ; point L7 à porter en réunion avec le Lot A2.

### EXP-D-003 — Retrieval dense multilingue et hybride RRF (S4)
- **Date** : 2026-10-19
- **Auteur / Lot** : Membre 5 / Lot D
- **Objectif / hypothèse** : un encodeur multilingue relie une affirmation française à la preuve
  arabe équivalente (et inversement), ce que BM25 ne peut pas faire (EXP-D-001 : Recall@5 ≈ 0.67) ;
  l'hybride RRF garde la précision lexicale de BM25 et ajoute ces correspondances.
- **Données** : `tests/fixtures/rag_llm/` v2 (15 passages **fictifs**, 20 affirmations dont 18 avec
  preuve). Une affirmation = 0.056 de Hit@1 : écarts à confirmer sur le corpus réel.
- **Méthode / configuration** : `rag_llm/retrieval/dense.py` (embeddings normalisés, cosinus ;
  préfixes `query:` / `passage:` pour e5) ; `hybrid.py` : RRF (k = 60) sur 20 candidats BM25 +
  20 candidats denses, passages denses de cosinus < 0.4 écartés avant fusion. 4 modèles :
  paraphrase-multilingual-MiniLM-L12-v2, multilingual-e5-small, multilingual-e5-base, bge-m3.
  Verdict : gabarit + NLI par règles (EXP-D-002). Colab, GPU T4. Déterministe.
- **Code** : commit `ee18993` ; `python -m rag_llm.evaluate_retrieval --method all --model …` ;
  `notebooks/lot_d_rag/01_m5_dense_retrieval.ipynb`.
- **Résultats — retrieval (GLOBAL, n = 18)** :

  | Modèle | Méthode | Hit@1 | Hit@5 | Recall@5 | MRR | tn-arabic Hit@1 | tn-arabizi Hit@5 |
  |--------|---------|-------|-------|----------|-----|-----------------|------------------|
  | — | BM25 | 0.889 | 0.944 | 0.667 | 0.907 | 0.5 | 0.5 |
  | MiniLM | dense | 0.722 | 0.722 | 0.639 | 0.722 | 0.0 | 0.0 |
  | MiniLM | hybride | 0.889 | 0.944 | 0.778 | 0.907 | 0.5 | 0.5 |
  | e5-small | dense | 0.944 | 0.944 | 0.861 | 0.951 | 1.0 | 0.5 |
  | e5-small | hybride | 0.944 | 0.944 | 0.861 | 0.951 | 1.0 | 0.5 |
  | e5-base | dense | 0.944 | 1.000 | 0.917 | 0.956 | 1.0 | 1.0 |
  | **e5-base** | **hybride** | **0.944** | **1.000** | **0.944** | **0.956** | **1.0** | **1.0** |
  | bge-m3 | dense | 0.944 | 0.944 | 0.917 | 0.944 | 1.0 | 0.5 |
  | bge-m3 | hybride | 0.944 | 0.944 | 0.917 | 0.944 | 1.0 | 0.5 |

- **Résultats — score dense du 1er passage (calibration de l'abstention)** :

  | Modèle | Bonne preuve (min – max) | Sans preuve : dev-c16 / dev-c17 |
  |--------|--------------------------|---------------------------------|
  | MiniLM | 0.406 – 0.970 | < 0.4 (écartées) / < 0.4 |
  | e5-small | 0.835 – 0.934 | 0.790 / 0.835 |
  | e5-base | 0.796 – 0.916 | 0.742 / 0.820 |
  | bge-m3 | 0.446 – 0.957 | 0.417 / < 0.4 |

  En hybride, le score RRF du 1er passage vaut 0.032–0.033 quand il est trouvé par BM25 **et** par
  le dense, 0.016 quand il n'est trouvé que par une seule méthode (cas des 2 affirmations sans preuve).
- **Résultats — verdict de bout en bout** : BM25 et hybride e5-base donnent **exactement** les mêmes
  métriques (exactitude 0.70, couverture 0.65, précision sélective 0.92, abstention justifiée 1.00,
  macro-F1 0.52, 0 citation invalide). Seule différence : les 2 affirmations sans preuve sont
  désormais arrêtées par la règle A3 (preuves non décisives) au lieu de A1 (aucune preuve).
  Les cellules de seuil (MIN_DENSE_SIMILARITY 0.3 à 0.6) ont tourné avec MiniLM en hybride par
  erreur de notebook : résultats identiques, non informatifs (cellule corrigée).
- **Analyse** :
  1. Hypothèse confirmée : le dense e5 retrouve la preuve dans l'autre langue ; Recall@5 passe de
     0.67 (BM25) à 0.94 (hybride e5-base). Le tunisien en lettres arabes passe de 0.5 à 1.0 (Hit@1).
     Avec e5-base, même l'arabizi `dev-c05` retrouve une preuve dans le top 5.
  2. Le choix de l'encodeur est décisif : MiniLM fait **moins bien** que BM25 et échoue sur tout le
     tunisien.
  3. Avec e5, le cosinus ne permet plus de détecter l'absence de preuve : les affirmations sans preuve
     ont des scores (0.74–0.84) dans la plage des bonnes preuves. Un seuil absolu sur le cosinus
     n'est pas fiable ; bge-m3 sépare mieux (0.417 vs ≥ 0.446) mais avec une marge très faible.
  4. Le retrieval s'améliore mais le verdict ne bouge pas : le NLI par règles compare des mots, il
     ne peut pas exploiter une preuve arabe pour une affirmation française. **Le goulot est
     désormais le NLI**, plus le retrieval. Sécurité : sans preuve, l'abstention repose maintenant
     sur le NLI (A3) et plus sur le retrieval (A1/A2) — fragile avec un vrai NLI.
- **Décision / suite** :
  - modèle par défaut : `intfloat/multilingual-e5-base` en hybride (meilleur Recall@5, tourne sur
    CPU) ; bge-m3 à re-tester sur le corpus réel ; `RETRIEVAL_METHOD` reste `bm25` par défaut pour
    la CI et l'API tant que le Lot E n'a pas validé la dépendance sentence-transformers ;
  - S5 : re-ranking cross-encoder multilingue, dont le score sert de seuil d'abstention (A2) ;
    signal complémentaire à tester : accord BM25 / dense (score RRF 0.016 vs 0.032) ;
  - Lot C : brancher le NLI multilingue pour que le gain de retrieval se traduise dans le verdict.

### EXP-A2-005 — Biais de sujet : noms de lieux tunisiens rendus neutres
- **Date** : 2026-10-19
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : mesurer, puis corriger, le biais vu dans EXP-A2-003 (« les quatorze
  meilleurs clubs tunisiens » : score 3.33). Hypothèse : un nom de lieu s'écrit pareil dans une
  phrase française et dans un commentaire en arabizi ; l'ignorer supprime les bascules sans perte
  notable d'arabizi.
- **Données** :
  - (a) test de bascule : les 2 912 textes français `dev` d'EXP-A2-003 (phrases entières et leurs
    5 premiers mots, sans doublon), auxquels on ajoute un seul groupe de mots parmi 7 : « en Tunisie »,
    « selon les Tunisiens », « à Tunis », « à Sfax », « à Kairouan », « selon Kaïs Saïed », « en Tunisie
    et à Sfax » (20 384 variantes). Seul l'ajout change : toute bascule lui est due ;
  - (b) français `dev` (2 912) et `test` (416) ; (c) les 7 363 textes arabizi mis de côté
    d'EXP-A2-003 ; (d) l'échantillon annoté en lettres latines (67 `t`, 16 `f`).
- **Méthode / configuration** : 8 formes ajoutées à `resources/neutral_latin_words.txt` : `tunisie`,
  `tunisien`, `tunisiens`, `tunisiene`, `tunisienes`, `tunis`, `sfax`, `kairouan` (lettres doublées
  écrites une fois, comme le reste de la liste). Modèle inchangé, entraîné avec l'ancienne liste de
  18 mots : les mots neutres sont retirés au moment de la lecture. Ordre suivi : essai de la nouvelle
  liste en mémoire, comparé à l'ancienne sur les mêmes jeux ; lecture un par un des textes arabizi
  perdus, avec la décision du pipeline complet (`normalize(...).script`) ; puis seulement, modification
  du fichier.
- **Code** : commit `d7d31b1` : `normalization/resources/neutral_latin_words.txt` ; 3 tests ajoutés
  à `tests/test_normalization.py`.
- **Résultats** :
  - (a) bascules : avant, 22 sur 20 384 (par ajout : 4, 1, 8, 2, 2, 0, 5), dont 19 sur des textes de
    5 mots ou moins ; après, 0 ;
  - (b) français : 0/2 912 et 0/416 avant comme après ;
  - (c) arabizi retrouvé par le modèle seul : 6 715 → 6 701. Des 14 textes perdus, 1 est rattrapé par
    la règle à chiffres du pipeline. Lecture des 13 autres : 8 sont écrits en français (« vive la
    tunisie libre », « voyage en tunisie c bien »…), 1 n'a aucun mot de langue (un nom de personne et
    un nom de pays), 4 sont vraiment tunisiens, tous de 2 à 4 mots (« sfax maaak »…) ;
  - (d) échantillon annoté : inchangé, t 61/67, f 4/16 ;
  - tests : 415 réussis, aucun échec ; `ruff check .` sans remarque.
- **Analyse** : l'hypothèse tient. La « perte » est surtout un gain : 8 des 13 textes étaient du
  français rangé avec l'arabizi dans les corpus. Conséquence : le score « arabizi retrouvé »
  d'EXP-A2-003 (0.91) est faussé par ces erreurs d'étiquette, et une partie de ses « erreurs » sont des
  réponses justes. Le vrai coût est de 4 commentaires tunisiens très courts. Limites : le test de
  bascule est artificiel (lieux ajoutés en fin de phrase) ; la liste est fermée : d'autres lieux
  (Sousse, Gabès…) et les noms de personnes ne sont pas couverts ; « selon Kaïs Saïed » ne fait pas
  basculer ce modèle, mais un modèle d'essai plus permissif (seuil 2.0) y était sensible ; le modèle
  n'a pas été réentraîné avec la nouvelle liste.
- **Décision / suite** : liste élargie retenue. Suite : réentraîner avec la nouvelle liste et
  remesurer ; retirer le français des corpus arabizi, puis mesurer le rappel sur de l'arabizi vérifié
  à la main ; traiter les textes très courts.

### EXP-A2-004 — Reproductibilité : échantillons annotés et lexique des marques
- **Date** : 2026-10-19
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : rendre refaisables, par le code du dépôt, les étapes d'EXP-A2-002 et
  EXP-A2-003 faites jusque-là hors dépôt : tirage des deux échantillons annotés, copie vierge pour un
  second annotateur, kappa, extraction du lexique tunisien, contrôle sur la presse. Hypothèse : refaites
  ainsi, elles redonnent exactement les mêmes fichiers et les mêmes chiffres.
- **Données** (corpus bruts non versionnés, dans `data/raw/langid/`) : TSAC (LGPL-3.0) ; UD Arabic-PADT
  (CC BY-NC-SA 3.0, `git clone --depth 1`), presse en arabe standard : `train` (6 075 phrases) pour
  choisir les mots, `dev` (909) et `test` (680) pour le contrôle seulement ; les deux échantillons
  annotés d'EXP-A2-002 (lettres arabes) et d'EXP-A2-003 (lettres latines).
- **Méthode / configuration** : déterministe (graine 13 pour les tirages).
  - `python -m normalization.annotation sample arabic|latin --check` : refait le tirage et compare,
    ligne par ligne, aux fichiers déjà annotés ; `blank`, `count` et `kappa` remplacent les scripts
    collés dans le terminal ;
  - `python -m normalization.lexicon candidates` : mots présents dans au moins 12 commentaires TSAC en
    lettres arabes (hors échantillons annotés) et dans aucune phrase de PADT `train`, comptés en
    textes et sous la forme repliée que lit la règle ;
  - `python -m normalization.lexicon press` : décision du pipeline complet (`normalize(...).lang`) sur
    PADT `dev` et `test`.
- **Code** : commits `e001a7d` (`normalization/annotation.py`) et `04314d3`
  (`normalization/lexicon.py`) ; 7 tests ajoutés à `tests/test_normalization.py`.
- **Résultats** :
  - tirages refaits : lettres arabes 100/100 lignes identiques, lettres latines 100/100 ; comptage de
    l'échantillon en lettres latines : 67 `t`, 16 `f`, 17 `x` ;
  - lexique : 6 899 commentaires TSAC, 351 candidats ; 55 des 78 marques en font partie ; les 23
    autres sont des variantes ajoutées à la main (`متاعو`, `ماهوش`…), trop rares pour le seuil de
    12 textes, et toutes absentes de la presse ;
  - presse : 0 phrase classée tunisien sur 909 (`dev`) et 0 sur 680 (`test`) ; aucune des 78 marques
    n'y apparaît, même une seule fois ;
  - tests : 412 réussis, aucun échec ; `ruff check .` sans remarque. Résultats identiques sur deux
    machines (Windows et Linux).
- **Analyse** : l'hypothèse tient. Un point appris en route : une graine fixe ne suffit pas à rendre un
  tirage reproductible. Avec le code actuel, qui compte aussi les lettres arabes « déjà dessinées »
  (anciens codes Unicode), 17 textes de plus entraient dans la liste des candidats, et le tirage en
  lettres arabes ne redonnait plus aucune des 100 lignes. Le module compte donc les lettres comme au
  premier tirage. Limites : le contrôle sur la presse utilise le même corpus que la sélection des
  mots (PADT `train` d'un côté, `dev` et `test` de l'autre) : le 0/1 589 est optimiste et ne dit rien
  d'une autre presse, par exemple tunisienne en arabe standard ; le tri manuel des 351 candidats
  n'est pas consigné mot par mot.
- **Décision / suite** : outils retenus ; les prochaines expériences du lot passeront par eux. Suite :
  kappa dès le retour du second annotateur (`python -m normalization.annotation kappa …`) ; contrôle
  sur une presse d'une autre source ; puis les faiblesses d'EXP-A2-003 (biais de sujet, règle du seuil).

### EXP-B-004 — Source du discours rapporté et complément du participe
- **Date** : 2026-10-15
- **Auteur / Lot** : Membre 3 / Lot B
- **Objectif / hypothèse** : (1) remplir `source` pour tout discours rapporté (locuteur d'un verbe
  de parole + complétive, incise « …, a déclaré X ») ; (2) garder dans le sujet d'un verbe arabe en
  tête le complément d'un participe (« عدد السياح الوافدين على تونس »), dernière erreur de sujet
  du mode règles sur `eval_30` (ar-01).
- **Données** : `eval_30.jsonl` (gold inchangé), désormais jeu de **développement** : `eval_100`
  (protocole `docs/lot-b_protocole_eval_100.md`) sera la référence.
- **Méthode / configuration** : (1) source = sujet du verbe de parole (antécédent si pronom résolu) ;
  incise après une virgule (règles : auxiliaire facultatif + verbe de parole + groupe nominal ;
  spaCy : `parataxis` à tête verbe de parole) → source, retirée de l'objet, modalité `rapporté` ;
  « حسب ما أفاد به X » → X. (2) Verbe intransitif en tête : préposition (على، إلى، من، في، عن،
  مع) suivie d'un nom, après un participe défini reconnu à sa forme, gardée dans le sujet ; pas si
  la préposition est suivie d'un nombre.
- **Code** : branche `lot-b-linguistic`, commits `feat(lot-b): source du discours rapporté
  (locuteur et incise)` et `feat(lot-b): complément du participe dans le sujet verbe-sujet-objet`.
- **Résultats** (EXP-B-003 → EXP-B-004) :
  - (1) aucune variation sur `eval_30` : le gold n'a pas de champ `source`, l'attribution n'est
    donc **pas mesurée** ; vérifiée par 13 tests sur des phrases hors du jeu (dont 3 pièges sans incise) ;
  - (2) règles : sujet / prédicat / objet 0.91 / 0.95 / 0.86 → 0.95 / 0.95 / 0.91 ; triplet
    0.86 → 0.91 ; 6 → 4 erreurs ; parseurs inchangés (0.77, 7 erreurs) ;
  - détection d'affirmation, modalité et coréférence inchangées (1.00).
- **Analyse** : erreurs restantes en mode règles : phrase nominale arabe (ar-02, 3 erreurs) et objet
  de mx-2 (adverbe, temps et apposition). Avec parseurs : arbres spaCy / Stanza faux (fr-02, tn-a4),
  traitement amont (ar-01 « نسبة », tn-a1 : E7) et mx-2. Un premier essai de (2) a cassé le
  regroupement auxiliaire + participe en français (constante de module redéfinie) : détecté par les
  tests, corrigé, et un test garde-fou ajouté. Règles écrites en voyant `eval_30` : avec 4 et 7
  erreurs sur 34 phrases, ce jeu ne mesure plus de différence fiable entre les modes.
- **Décision / suite** : retenu. Plus de réglage sur `eval_30` ; la prochaine mesure de référence
  se fera sur `eval_100` une fois verrouillé.

### EXP-B-003 — Lexique verbal du mode règles et sujet verbe-sujet-objet
- **Date** : 2026-10-15
- **Auteur / Lot** : Membre 3 / Lot B
- **Objectif / hypothèse** : priorités 2 et 6 de l'analyse d'erreurs Bronze. Sans parseur (CI,
  tunisien), la plupart des erreurs viennent de verbes inconnus (E3) ; une fois le verbe trouvé,
  le sujet d'un verbe arabe en tête limité à un mot devient la cause principale. Étendre le
  lexique et le sujet doit améliorer le mode règles sans dégrader le mode parseurs.
- **Données** : identiques à EXP-B-001 / EXP-B-002 (`eval_30.jsonl`, gold inchangé).
- **Méthode / configuration** : `linguistic_analysis/resources/verbs.json` ; formes générées à
  partir de 94 lemmes français en -er (3e personne, participes) et de 94 verbes de l'arabe standard
  au passé (passé, présent, futur ; conjonction و / ف collée retirée), plus des formes listées
  (irrégulières, auxiliaires au conditionnel, modaux, tunisien en lettres arabes et en arabizi) ;
  ش / ch final de la négation ما…ش retiré. Mot précédé d'un déterminant : pas un verbe. Modal +
  infinitif regroupés. Verbe arabe en tête : sujet jusqu'à une préposition, un nombre ou un
  complément pour les verbes intransitifs listés, sinon chaîne d'annexion et adjectifs de relation.
  Coréférence : une annexion dont le complément porte l'article est un antécédent défini.
- **Code** : branche `lot-b-linguistic`, commit `feat(lot-b): lexique verbal du mode règles et
  sujet verbe-sujet-objet` ; `python -m linguistic_analysis.evaluate [--rules] --errors`.
- **Résultats** (EXP-B-002 → EXP-B-003) :
  - règles : sujet / prédicat / objet 0.64 / 0.68 / 0.77 → 0.91 / 0.95 / 0.86 ; triplet 0.64 → 0.86 ;
    coréférence 0.67 → 1.00 ; 21 → 6 erreurs ;
  - parseurs : 0.91 / 0.86 / 0.86 → 0.95 / 0.91 / 0.82 ; triplet 0.77 → 0.77 ; 8 → 7 erreurs
    (seul le cas mixte mx-2, toujours analysé par règles, change) ;
  - triplet exact par groupe (règles / parseurs) : FR 1.00 / 0.88 ; AR 0.71 / 0.86 ;
    TN lettres arabes 1.00 / 0.00 ; arabizi 1.00 / 1.00 ; mixte 0.50 / 0.50 ;
  - détection d'affirmation et modalité inchangées (1.00).
- **Analyse** : erreurs corrigées dans la section `corrigees_exp_b_003` de
  `tests/fixtures/linguistic_analysis/error_categories.json`. Une erreur nouvelle : l'objet de mx-2,
  juste auparavant par hasard (aucun triplet, gold `null`) ; maintenant que « tal3ou » est reconnu,
  l'adverbe, le temps et l'apposition passent dans l'objet (E4). Restent en mode règles : phrase
  nominale arabe (ar-02) et complément du participe dans le sujet (ar-01). Le tunisien en lettres
  arabes reste à 0.00 avec parseurs parce que l'amont l'étiquette `ar` et l'envoie à Stanza (E7,
  point de réunion) : en mode règles il est à 1.00. Comme pour EXP-B-002, règles écrites en voyant
  le jeu : gains optimistes ; vérification sur 14 phrases hors du jeu (tests), avec des pièges
  (nom après déterminant, verbe absent du lexique). Limites : verbes absents de la liste, noms
  homographes d'un verbe (« سجل », « تراجع » en tête de phrase).
- **Décision / suite** : retenu. Le jeu de 34 phrases ne départage plus les deux modes (6 et 7
  erreurs) : priorité au jeu d'environ 100 phrases, en partie tiré d'articles réels et annoté sans
  voir les sorties, pour mesurer la généralisation.

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

### EXP-A2-003 — Arabizi sans chiffre : modèle à n-grammes de caractères
- **Date** : 2026-10-07
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : séparer le français du tunisien écrit en lettres latines sans chiffre
  d'arabizi (« barcha », « mahlek »), que les règles classaient toujours `fr`. Hypothèse : les suites
  de 1 à 4 lettres suffisent à distinguer les deux langues, sans dictionnaire ni gros modèle.
- **Données** (corpus bruts non versionnés, dans `data/raw/langid/`) :
  - arabizi : Tunizi (Zenodo, CC BY 4.0) et lignes de TSAC (LGPL-3.0) reconnues par la règle à
    chiffres ; après dédoublonnage, 66 272 textes pour apprendre, 7 363 mis de côté (10 %, graine 13) ;
  - français : UD French-GSD (CC BY-SA 4.0) ; `train` découpé en 35 356 morceaux de la longueur des
    commentaires, `dev` pour choisir le seuil, `test` (416 phrases) consulté une seule fois, à la fin ;
  - (c) 100 commentaires TSAC en lettres latines sans chiffre d'arabizi (3 mots ou plus, graine 13),
    annotés `t` / `f` / `x` par un annotateur : 67 `t`, 16 `f`, 17 `x`. Jamais appris, mais ils ont
    servi à repérer le défaut du mot « bravo » : jeu de mise au point, pas jeu de test.
- **Méthode / configuration** : `python -m normalization.train_langid` (scikit-learn 1.7.2, graine 13).
  Présence, mot par mot, des n-grammes de 1 à 4 caractères (ignorés s'ils sont vus dans moins de
  5 textes) ; régression logistique (C = 0.5, classes équilibrées). Deux passages : le premier sert à
  retirer les textes « arabizi » jugés nettement français (score < -2.0 : 60 textes), le second donne
  le modèle. Les 20 000 poids les plus forts sont exportés dans `resources/arabizi_ngrams.json`
  (315 Ko) ; à l'usage, score = somme des poids des n-grammes présents, en Python pur (ni les tests
  ni la CI n'ont besoin de scikit-learn). Seuil : le plus petit de la grille 0 à 5 sans aucune fausse
  alerte sur le français `dev` ; valeur retenue 5.0, borne haute de la grille. Garde-fous : 18 mots
  neutres ignorés (`resources/neutral_latin_words.txt` : « bravo », « merci »…) et aucune décision
  en dessous de 2 mots.
- **Code** : commit `6113840` : `normalization/train_langid.py`, `normalization/langid.py` ; dans
  `normalization/normalize.py`, `detect_script` interroge le modèle quand les règles répondent `latin`.
- **Résultats** :
  - français `test`, jamais consulté avant : 0 phrase classée arabizi sur 416 ;
  - arabizi mis de côté : 6 715 retrouvés sur 7 363 (0.91) ;
  - grille des seuils (score seul, 2 941 textes français `dev`) : à 2.0, 97.3 % d'arabizi retrouvé et
    2 textes français classés arabizi ; à 4.0, 93.9 % et 1 ; à 5.0, 91.4 % et 0 ;
  - (c) avant → après, 83 lignes décidées : TN 0/67 → 61/67 ; FR 16/16 → 12/16 ; exactitude
    0.19 → 0.88 ; moyenne par classe 0.50 → 0.83. Les chiffres « avant » sont connus d'avance :
    l'échantillon a été tiré parmi les textes que les règles classaient `fr` ;
  - eval_30 (langue) : inchangé, FR 10/10, AR 10/10, TN 12/14 ; échantillon en lettres arabes
    d'EXP-A2-002 : inchangé, AR 15/15, TN 41/78 ;
  - tests : 405 réussis, aucun échec ; `ruff check .` sans remarque.
- **Analyse** : l'hypothèse tient : sans dictionnaire, le modèle retrouve 9 textes tunisiens sur 10 et
  ne déclenche aucune fausse alerte sur le français de presse. Les 12 textes `dev` les mieux notés
  « arabizi », relus un par un, et les erreurs de (c) montrent quatre faiblesses :
  1. le seuil tient à un seul texte : « can you feel it a » (score 4.79), fragment anglais du corpus
     français. Sans lui, 4.0 suffisait (93.9 % retrouvés au lieu de 91.4 %) ;
  2. biais de sujet : « les quatorze meilleurs clubs tunisiens » obtient 3.33, porté par `tun`, `tuni`.
     Tunizi parle souvent de la Tunisie, et les affirmations à vérifier aussi : c'est le principal
     risque pour le pipeline ;
  3. noms propres : 3 des 4 erreurs FR → TN de (c) sont « bravo » accompagné d'un nom tunisien
     (« bravo » est ignoré, il ne reste que le nom) ; côté `dev`, « billie holiday », « baník okd »,
     « keating » montent de 1.1 à 1.8. La 4e erreur de (c) (ligne 43) est une annotation discutable ;
  4. français familier et textes courts : ` ca `, ` c `, `tu ` comptent pour l'arabizi, car Tunizi
     contient du français familier (le nettoyage n'en retire que 60) ; ce registre est presque absent
     des mesures (« chauchard tu es une bête » : 0.62). Les 6 erreurs TN → FR de (c) ont 1 à 3 mots.
  Limites : (c) a servi à la mise au point et n'a que 16 lignes `f`, surtout des « bravo + nom » ;
  un seul annotateur ; ni français familier ni phrase mêlant les deux langues dans les mesures
  (`mx-4` d'eval_30 reste `fr`).
- **Décision / suite** : modèle retenu, seuil 5.0 inchangé pour l'instant, la règle à chiffres passant
  toujours en premier. Suite (EXP-A2-004) : rendre reproductibles tirages, kappa et lexique ; revoir
  la règle du seuil (un texte anglais ne devrait pas la décider) ; apprendre aussi du français qui
  parle de la Tunisie et du français familier ; double annotation de (c) ; échantillon neuf pour un
  vrai test.

### EXP-A2-002 — Tunisien en lettres arabes : règle à lexique de marques
- **Date** : 2026-10-07
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : reconnaître le tunisien écrit en lettres arabes (point E7 d'EXP-B-001),
  jusque-là toujours classé `ar`. Hypothèse : quelques dizaines de mots-outils suffisent pour une règle
  sans fausse alerte, qui servira de référence à tout classifieur.
- **Données** : (a) `tests/fixtures/linguistic_analysis/eval_30.jsonl` du Lot B (34 phrases), non
  utilisé pour construire la règle ; (b) 100 commentaires TSAC en lettres arabes (3 mots ou plus,
  graine 13), annotés `t` / `a` / `x` par un annotateur selon `docs/lot-a2_guide_annotation.md` :
  78 `t`, 15 `a`, 7 `x`. Cet échantillon a servi à écrire le guide et à choisir les mots : c'est un
  jeu de mise au point, pas un jeu de test. Corpus brut non versionné (TSAC, licence LGPL-3.0).
- **Méthode / configuration** : règle déterministe, sans graine (`normalization/langid.py`) : 78 formes
  dans `resources/tn_markers.txt`, plus la négation en ما…ش (collée ou en deux mots, hors verbes
  standard en ش). Texte déclaré dialectal s'il contient au moins un mot du lexique et au moins 2 % de
  mots dialectaux. Lexique : mots fréquents dans TSAC et absents d'un corpus de presse en arabe
  standard (UD Arabic-PADT), puis tri manuel ; formes ambiguës exclues (`الي`, `لي`, `ياسر`, `شنوا`).
  Cette extraction a été faite hors dépôt : à rendre reproductible (EXP-A2-003).
- **Code** : commit `9810bcd`, `normalization/langid.py` ; `normalization/evaluate.py` lit maintenant
  aussi les fichiers d'annotation `.tsv`.
- **Résultats** :
  - (a) eval_30 (34 phrases : 10 FR, 10 AR, 14 TN), phrases bien classées, avant (`e2fdbe7`) → après :
    FR 10/10 → 10/10 ; AR 10/10 → 10/10 ; TN 8/14 → 12/14 ;
    exactitude 0.82 → 0.94 ; moyenne par classe 0.86 → 0.95. Script inchangé (0.88).
  - (b) échantillon annoté, 93 lignes décidées : AR 15/15 ; TN 41/78 (0.53) ; moyenne par classe 0.76.
    L'ancien code classait tout texte en lettres arabes en `ar`.
  - Tests : 385 réussis, aucun échec ; `ruff check .` sans remarque.
- **Analyse** : règle sûre (aucune des 25 phrases standard de (a) et (b) n'est classée tunisien) mais
  rappel partiel : un lexique ne voit ni la morphologie (pronom en ـو, négation sans ما, verbes en نـ)
  ni le vocabulaire ouvert. Erreurs restantes sur (a) : `tn-a3` (aucun mot du lexique) et `mx-4`
  (arabizi sans chiffre). Effet de bord : la fixture `mock_documents.jsonl` du Lot B a été régénérée
  par son propre script (1 ligne, `ar` → `tn`). Limites : 15 lignes standard seulement dans (b) ; un
  seul annotateur ; (b) a servi à la mise au point, donc son score est optimiste ; `ديما` et `راني`
  sont aussi des prénoms.
- **Décision / suite** : règle retenue comme référence. Suite : double annotation et kappa sur (b) ;
  contrôle des fausses alertes sur la presse et essai d'un classifieur à n-grammes de caractères, à
  rendre reproductibles (EXP-A2-003) ; échantillon neuf pour un vrai test.

### EXP-B-002 — Compléments de source, de temps et de lieu hors de l'objet
- **Date** : 2026-10-07
- **Auteur / Lot** : Membre 3 / Lot B
- **Objectif / hypothèse** : 1ʳᵉ priorité de l'analyse d'erreurs Bronze (catégorie E4). Retirer de
  l'objet les compléments de temps et de lieu et les sources (« selon X », « حسب X »), comme le
  demande le guide d'annotation, doit améliorer l'objet dans les deux modes sans toucher au reste.
- **Données** : identiques à EXP-B-001 (`eval_30.jsonl`, 34 phrases, 22 affirmations, gold inchangé).
- **Méthode / configuration** : lexique `linguistic_analysis/resources/adjuncts.json` (marqueurs de
  source, prépositions et noms de temps FR / AR / TN, gouvernorats et villes de Tunisie), commun aux
  deux modes. Avec arbre, un complément reconnu n'est jamais choisi comme objet ; dans les deux modes,
  les compléments placés en fin d'objet en sont retirés, et une source en tête de phrase est retirée
  du sujet (mode règles). Les compléments sont rangés dans les champs internes `source`, `time` et
  `location` de `ExtractedClaim` (`Claim` inchangé). Mêmes versions de spaCy / Stanza qu'EXP-B-001.
- **Code** : branche `lot-b-linguistic`, commit `feat(lot-b): compléments de source, de temps et de
  lieu hors de l'objet` ; `python -m linguistic_analysis.evaluate [--rules] --errors`.
- **Résultats** (avant → après) :
  - règles : sujet / prédicat / objet 0.59 / 0.68 / 0.64 → 0.64 / 0.68 / 0.77 ; triplet 0.46 → 0.64 ;
    25 → 21 erreurs ;
  - parseurs : 0.91 / 0.86 / 0.50 → 0.91 / 0.86 / 0.86 ; triplet 0.46 → 0.77 ; 16 → 8 erreurs ;
  - triplet exact par groupe (règles / parseurs) : FR 0.88 / 0.88 ; AR 0.29 / 0.86 ;
    TN lettres arabes 0.50 / 0.00 ; arabizi 1.00 / 1.00 ; mixte 0.50 / 0.50 ;
  - détection d'affirmation, modalité et coréférence inchangées ; aucune nouvelle erreur.
- **Analyse** : les 12 erreurs corrigées (4 en règles, 8 avec parseurs) sont listées dans la section
  `corrigees_exp_b_002` de `tests/fixtures/linguistic_analysis/error_categories.json` ; les erreurs
  restantes relèvent du lexique verbal (E3), d'arbres faux (E2) et du traitement amont (E7).
  Les règles ont été écrites en voyant le jeu d'évaluation : les gains sont donc optimistes. Pour
  limiter ce biais, elles ont été vérifiées sur 14 phrases hors du jeu (tests), dont des cas qui
  doivent rester dans l'objet (« 100 jours en poste », « 2024 voitures », « à dix ans de prison »,
  « au Président »). Limites : lieux absents de la liste, préposition arabe collée (« بصفاقس »),
  compléments en milieu d'objet. Point à relire : le gold d'ar-02 garde « في المناطق الداخلية »
  dans l'objet, alors que le guide exclut les compléments de lieu.
- **Décision / suite** : retenu. Suite : lexique verbal et morphologie du mode règles (E3, 13 erreurs
  sur 21 sans parseur), puis attribution de la source du discours rapporté et jeu d'environ 100 phrases.

### EXP-A2-001 — Normalisation v1 et identification de langue par règles
- **Date** : 2026-10-06
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : remplacer le stub de normalisation ; vérifier que la détection d'arabizi
  ne classe plus en tunisien le français contenant un chiffre collé à une lettre (G20, A320, 5G),
  sans dégrader le reste.
- **Données** : (a) `tests/fixtures/linguistic_analysis/eval_30.jsonl`, 34 phrases annotées par le
  Lot B (10 FR, 10 arabe standard, 5 tunisien en lettres arabes, 5 arabizi, 4 mixtes), un annotateur,
  étiquettes `lang` et `script` ; (b) 5 phrases françaises ciblées, rédigées pour reproduire le défaut
  (`test_french_with_digits_is_not_arabizi`). Pas de split : aucune donnée d'apprentissage.
- **Méthode / configuration** : règles déterministes (pas de graine). Stub = `normalize.py` de
  `fe99c66` ; v1 = `6a3d92d`. v1 : mot arabizi sous conditions (au moins 2 lettres, chiffre isolé
  parmi 2-3-5-6-7-9, pas tout en majuscules, pas une unité), seuil de 5 % des mots latins, script
  décidé à la majorité (80 %), liens et adresses ignorés ; chiffres arabes convertis, nombres, sigles
  et liens jamais modifiés.
- **Code** : commit `6a3d92d`, `normalization/normalize.py`, `tests/test_normalization.py` ;
  `normalization/evaluate.py` (`python -m normalization.evaluate --errors`).
- **Résultats** :
  - (a) eval_30, identiques pour le stub et la v1. Langue : FR 10/10, AR 10/10, TN 8/14 (0.57) ;
    exactitude 0.82, moyenne par classe 0.86. Script : arabic 15/15, arabizi 5/5, latin 10/10,
    mixed 0/4 ; exactitude 0.88, moyenne par classe 0.75.
  - (b) phrases ciblées : stub 0/5 (classées arabizi), v1 5/5.
  - Tests du lot : stub 55 réussis / 15 échecs ; v1 70 réussis, 2 échecs attendus (xfail).
    Projet entier avec la v1 : 370 réussis, aucun échec ; `ruff check .` sans remarque.
- **Analyse** : eval_30 ne contient aucune phrase française avec un chiffre collé à une lettre : il ne
  distingue pas les deux versions, d'où le jeu (b). Les 9 erreurs restantes sur eval_30 : 5 phrases
  tunisiennes en lettres arabes classées `ar` (l'alphabet seul ne suffit pas) ; 1 arabizi sans chiffre
  classé `fr` (`mx-4`) ; 4 `mixed`, où le Lot B entend « mélange de langues FR/TN en lettres latines »
  et le code « mélange d'alphabets » : définition à fixer. La v1 conserve ة → ه et ى → ي du stub, qui
  gênent l'analyse syntaxique (EXP-B-001, E7). Limites : jeu petit, un seul annotateur ; les phrases
  (b) ont été rédigées en connaissant les règles : elles prouvent la correction du défaut, pas une
  performance générale.
- **Décision / suite** : v1 retenue. À discuter avec les Lots B et D : texte léger (orthographe
  conservée) dans `Document.text` et repli séparé pour la recherche ; sens de `script = mixed`.
  Suite : classifieur de langue (n-grammes de caractères) pour le tunisien en lettres arabes et
  l'arabizi sans chiffres ; jeu d'évaluation A2 de phrases réelles.

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

### EXP-C-001 — Baseline TF-IDF + régression logistique pour la détection d'affirmations
- **Date** : 2026-10-21
- **Auteur / Lot** : Lot C
- **Objectif / hypothèse** : établir une baseline reproductible de check-worthiness binaire :
  `AFFIRMATION` contre `OPINION` ou `AUTRE`. Les n-grammes de caractères doivent donner un point de
  comparaison qui tolère partiellement les écritures arabes, arabizi et françaises, sans modèle pré-entraîné.
- **Données** : 60 extraits revus par Lot A1, lus dans
  `data/annotations/normalized/tarc_review_30.jsonl` (18 affirmations, 7 opinions, 5 autres ; 25 TN,
  5 FR) et `data/annotations/normalized/tunifact_review_30.jsonl` (30 affirmations ; 15 AR, 15 FR).
  Les 60 phrases sans labels, les annotations privées et les extraits sans annotation ne sont pas utilisés.
  Le corpus est très déséquilibré (48 positifs / 12 négatifs) et trop petit pour une conclusion générale.
- **Méthode / configuration** : split stratifié 80/20, graine 42, avec les 12 IDs de test figés dans
  `data/splits/claim_detection_pilot_seed42.json` avant toute itération. TF-IDF de caractères
  `char_wb`, n-grammes 3-5, puis `LogisticRegression(max_iter=1000, class_weight="balanced")`.
  Code : `models/baselines/claim_detection_tfidf.py`.
- **Résultats** : 48 entraînement / 12 test ; macro-F1 = **0.4286**. Macro-F1 par langue dans le
  test : AR 0.5000, FR 0.5000, TN 0.2000. Rapport brut :
  `evaluation/results/claim_detection_tfidf_seed42.json`.
- **Analyse** : résultat de référence uniquement, non publiable : le test comprend très peu de négatifs
  et les sources/langues sont confondues avec les labels (Tunifact est entièrement positif). Les scores
  par langue reposent sur des sous-groupes minuscules et ne permettent aucune comparaison fiable.
- **Décision / suite** : baseline conservée; ne pas régler ses hyperparamètres sur ce test. Quand Lot A1/B
  livre des annotations supplémentaires, conserver ce test ou définir un nouveau split documenté, ajouter
  trois graines et comparer à XLM-R. Le NLI attend le fichier de paires `claim/evidence/label`.

### EXP-C-002 — XLM-RoBERTa + LoRA pour la détection d'affirmations
- **Date** : 2026-10-23
- **Auteur / Lot** : Lot C
- **Objectif / hypothèse** : comparer un encodeur multilingue fine-tuné à la baseline classique sur les
  trois classes `AFFIRMATION`, `OPINION`, `AUTRE`.
- **Données** : `data/processed/claim_detection_600.jsonl`, 600 phrases originales annotées. Test fixé :
  120 IDs dans `data/splits/claim_detection_multiclass_600_seed42.json`. Pour chaque seed, les 480 autres
  phrases sont séparées en 408 entraînement et 72 validation, sans toucher au test.
- **Méthode / configuration** : `FacebookAI/xlm-roberta-base`, LoRA (r=8, alpha=16, dropout=0.1,
  modules query/value), 8 époques, learning rate 2e-4, batch size 8, meilleure époque sélectionnée sur
  macro-F1 validation. Exécution GPU Colab. Code : `models/encoders/train_xlmr_claim_detection.py`.
- **Résultats** : macro-F1 test : seed 42 = 0.7108 ; seed 123 = 0.7715 ; seed 2026 = 0.7250 ;
  moyenne ± écart-type = **0.7357 ± 0.0317**. Baseline TF-IDF = 0.6435.
- **Analyse** : XLM-R améliore la baseline de 0.0922 point de macro-F1 sur ce test. L'écart-type de 0.0317
  signale une variance non négligeable, attendue avec 600 exemples et 120 exemples de test. Les résultats
  par langue du checkpoint retenu sont documentés dans EXP-C-003.
- **Décision / suite** : XLM-R + LoRA est retenu comme modèle avancé du Model 1. Conserver les trois
  checkpoints et le split; compléter l'analyse d'erreurs, les résultats par langue et le bootstrap apparié
  contre la baseline avant le rapport final.
