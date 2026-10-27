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
| EXP-C-010 | 2026-10-27 | C | Analyse qualitative cross-seed | 25 erreurs seed42 + 5 seed2026 | 30 erreurs catégorisées | hypothèses 8 ; opinions 13 | prioriser modalités et opinions TN |
| EXP-C-009 | 2026-10-26 | C | NLI (Model 2) palier Bronze : position par lexique | règles (recouvrement, nombres, marqueurs de démenti, négation) ; seuils 0.35 / 0.4 choisis sur train + val ; corpus NLI A1 v3 | macro-F1 (test, n = 56) | 0.471 [IC95 0.33–0.59] vs 0.194 classe majoritaire ; fr 0.50 / ar 0.40 ; ablation TF-IDF 0.405, TF-IDF + lexique 0.534 | composant Bronze de la démo (NLI_BACKEND=bronze par défaut) |
| EXP-C-008 | 2026-10-26 | C | NLI (Model 2) : baseline sans entraînement | mDeBERTa-v3-base xnli (zero-shot), corpus NLI A1 v3, test gelé 56 paires | macro-F1 (test) | 0.798 [IC95 0.67–0.89] ; acc 0.804 ; fr 0.78 / ar 0.78 ; articles Lot D 0.77 | référence hors démo (backend `zero-shot` optionnel) ; chiffres officiels sur v4 |
| EXP-C-010 | 2026-10-25 | C | Détection d'affirmations (Model 1) palier Bronze : TF-IDF caractères | TF-IDF `char_wb` 3–5 + régression logistique `class_weight=balanced`, 600 phrases annotées, split 480 / 120 stratifié, graine 42 | macro-F1 (test, n = 120) | 0.643 vs 0.230 classe majoritaire ; fr 0.58 / ar 0.48 / tn-arabe 0.70 / arabizi 0.55 / mixte 0.81 | composant Bronze de la démo (CLAIM_DETECTOR_BACKEND=tfidf par défaut) |
| EXP-C-007 | 2026-10-24 | C | Ablation raw vs normalisé | XLM-R + LoRA, seed42, test gelé | macro-F1 ; bootstrap | raw 0,7108 vs normalisé 0,6671 ; p=0,188 | raw retenu ; API alignée sur raw |
| EXP-C-006 | 2026-10-24 | C | Baseline neuronale | MiniLM figé + LR, 3 runs | macro-F1 | 0,6350 ± 0,0000 | baseline de comparaison conservée |
| EXP-C-005 | 2026-10-24 | C | Bootstrap apparié | TF-IDF vs XLM-R seed42, 1 000 réplications | Δ macro-F1 ; IC 95 % ; p | +0,0673 ; [-0,0468 ; 0,1860] ; p=0,254 | gain non concluant statistiquement |
| EXP-C-003 | 2026-10-23 | C | Évaluation détaillée XLM-R + LoRA | seed 42, test gelé 120 | macro-F1 | 0.7108 ; FR 0.9148 / AR 0.6989 / TN 0.6445 | analyse d'erreurs à compléter |
| EXP-E-001 | 2026-10-02 | E | Squelette pipeline | stubs | — | pipeline + API OK | base de départ |
| EXP-E-002 | 2026-10-27 | E | Audit d'intégration Bronze | règles + BM25 + NLI lexical + gabarit, 4 contrôles FR versionnés | succès E2E / Macro-F1 / Recall@5 / citations / latence | 1,00 / 1,00 / 1,00 / 0 citation invalide / 5,82 ms moyen | contrôle de régression, non représentatif |
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
| EXP-A2-006 | 2026-10-21 | A2 | Arabizi : modèle réentraîné avec la liste neutre à jour | même configuration qu'EXP-A2-003, graine 13 ; seuil 5.0 | régénération ; FR de test ; eval_30 ; bascules ; échantillon annoté | régénérable (2 essais identiques) ; 0 sur 416 ; eval_30 identique ; 0 sur 20 384 ; TN classé arabizi 61 → 62 sur 67, FR classé arabizi 4 → 5 sur 16 | nouveau modèle retenu ; suite : test de régénération en CI |
| EXP-A2-007 | 2026-10-21 | A2 | Double annotation de la langue (accord entre annotateurs) | 2 annotateurs indépendants par échantillon ; guide envoyé sans les étiquettes du premier | kappa de Cohen, 3 classes | lettres latines 0.84 (accord 0.92) ; lettres arabes 0.65 (accord 0.87) ; 100 textes chacun | guides utilisables ; suite : adjudication, préciser emprunts français et usage de `x` |
| EXP-A2-008 | 2026-10-25 | A2 | Arabizi : chiffre 8 (= غ) | 8 ajouté pour le pipeline ; règle d'origine (235679) gardée pour le tirage et l'entraînement | fausses alertes sur le français ; gain sur les commentaires ; reproductibilité | 0 nouvelle fausse alerte (UD train / dev / test) ; règles +180, décision finale +20 sur 78 173 commentaires ; modèle et tirage inchangés | retenu ; suite : translittération arabizi → arabe (Lot D) |
| EXP-A2-009 | 2026-10-26 | A2 | Adjudication de l'annotation et analyse d'erreurs (≥ 30) | 21 désaccords tranchés à deux ; règles ajoutées au guide ; erreurs classées | langue par classe sur les étiquettes de référence ; erreurs par catégorie | arabe : `a` 23/23, `t` 41/77 ; latin : `f` 12/16, `t` 65/70 ; 45 erreurs en 10 catégories | référence retenue ; suite : lexique élargi, affixes, négation contractée |
| EXP-A2-010 | 2026-10-26 | A2 | Perplexité : repérer les textes bruités | modèle de langue à n-grammes de caractères (ordre 4, interpolé), un par alphabet, graine 13 ; seuil = 95e centile dev | faux signalements sur test ; bruit artificiel repéré ; AUC | arabe : 4,7 % ; encodage 100 %, lettres 99,6 %, mélange 99,5 % ; latin : 5,3 % ; encodage 12,3 % (AUC 0,53), lettres 99,3 %, mélange 99,0 % | retenu pour signaler (pas supprimer) ; suite : règle de détection d'encodage pour les lettres latines |
| EXP-A2-011 | 2026-10-26 | A2 | Revue Bronze : baselines triviales, gel des jeux, normaliseur mesuré, erreurs en 5 familles | `python -X utf8 -m normalization.review` ; baselines « majorité » et « alphabet seul » | macro-F1 langue (test eval_30 ; dev TSAC) ; nombres conservés | test : 0.94 contre 0.19 (majorité) et 0.50 (alphabet seul) ; dev arabe 0.63 contre 0.43 ; dev latin 0.83 contre 0.45 ; nombres 29/29 | chiffres de la revue ; suite : test TSAC neuf, jamais vu |

## Entrées

### EXP-C-010 — Analyse qualitative cross-seed de 30 erreurs Model 1
- **Date** : 2026-10-27
- **Auteur / Lot** : Lot C
- **Objectif / hypothèse** : rendre traçables les erreurs représentatives du classifieur Model 1 et identifier les phénomènes à prioriser.
- **Données** : `errors_30_cross_seed.jsonl` : 25 erreurs de `seed42` et 5 erreurs distinctes de `seed2026`. Ce n'est pas un échantillon aléatoire : il sert à l'analyse qualitative, non au calcul d'un taux d'erreur.
- **Méthode / configuration** : catégorisation déterministe à partir du label gold, de la modalité et de la prédiction, avec `bronze/analyze_model1_errors.py`.
- **Code** : `bronze/analyze_model1_errors.py` ; sortie structurée `evaluation/results/model1_errors_30_cross_seed.jsonl`.
- **Résultats** : 30 erreurs : hypothèses non reconnues 8, opinions prises pour AFFIRMATION 7, opinions prises pour AUTRE 6, affirmations non reconnues 3, autres confusions 2, souhaits 2, question 1, discours rapporté 1.
- **Analyse** : les modalités non factuelles (hypothèse, souhait, question) totalisent 11 erreurs ; les opinions 13. Les exemples mélangent FR, arabe et tunisien, en particulier arabizi/mixed, ce qui confirme la difficulté des formulations informelles.
- **Décision / suite** : rapporter cette analyse dans la revue et prioriser des exemples annotés supplémentaires pour ces phénomènes avant tout nouveau réglage du modèle. Rapport : `docs/lot-c_error_analysis_cross_seed.md`.

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
  `ar`, sinon `fr` : le comportement d'avant le Lot A2). Normaliseur : textes dont les nombres sont
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

### EXP-E-002 — Audit d'intégration classique Bronze
- **Date** : 2026-10-27
- **Auteur / Lot** : Lot E
- **Objectif / hypothèse** : vérifier que les composants classiques intégrés communiquent correctement
  et que la démo ne produit ni citation invalide ni crash sur les sorties attendues.
- **Données** : quatre contrôles français versionnés dans
  `data/annotations/bronze_fr_integration_eval.jsonl` : affirmation confirmée, contradiction
  numérique, absence de preuve et opinion filtrée. Ce jeu est un contrôle E2E, **pas** un test
  statistique de performance.
- **Méthode / configuration** : `python -m evaluation.integration_audit`. Route
  `POST /bronze/check` : normalisation, extraction à règles, BM25, NLI lexical Bronze, gabarit.
  Aucun encodeur dense, LLM ou Model 1 appris.
- **Résultats** : 4/4 sorties attendues ; macro-F1 1,000 et Recall@5 1,000 sur les trois assertions
  ayant un verdict ; 1/3 abstention ; 2 citations, 0 invalide ; latence moyenne 5,82 ms
  (maximum 18,89 ms) sur la machine de mesure. Artefact :
  `evaluation/results/lot-e_integration_bronze_20261027.json`.
- **Analyse** : les scores parfaits viennent du caractère réduit et contrôlé du jeu ; ils démontrent
  l'intégration et non la qualité générale. Les métriques de qualité à présenter restent celles des
  évaluations B, C et D sur leurs jeux dédiés.
- **Décision / suite** : conserver l'audit dans la CI locale et l'étendre seulement avec de nouveaux
  cas annotés avant de le considérer comme un jeu de validation.

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
