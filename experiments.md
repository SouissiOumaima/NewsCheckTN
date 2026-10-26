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

## Entrées

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
