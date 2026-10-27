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
| EXP-C-008 | 2026-10-26 | C | Analyse qualitative cross-seed | 25 erreurs seed42 + 5 seed2026 | 30 erreurs catégorisées | hypothèses 8 ; opinions 13 | prioriser modalités et opinions TN |
| EXP-C-007 | 2026-10-24 | C | Ablation raw vs normalisé | XLM-R + LoRA, seed42, test gelé | macro-F1 ; bootstrap | raw 0,7108 vs normalisé 0,6671 ; p=0,188 | raw retenu ; API alignée sur raw |
| EXP-C-006 | 2026-10-24 | C | Baseline neuronale | MiniLM figé + LR, 3 runs | macro-F1 | 0,6350 ± 0,0000 | baseline de comparaison conservée |
| EXP-C-005 | 2026-10-24 | C | Bootstrap apparié | TF-IDF vs XLM-R seed42, 1 000 réplications | Δ macro-F1 ; IC 95 % ; p | +0,0673 ; [-0,0468 ; 0,1860] ; p=0,254 | gain non concluant statistiquement |
| EXP-C-003 | 2026-10-23 | C | Évaluation détaillée XLM-R + LoRA | seed 42, test gelé 120 | macro-F1 | 0.7108 ; FR 0.9148 / AR 0.6989 / TN 0.6445 | analyse d'erreurs à compléter |
| EXP-E-001 | 2026-10-02 | E | Squelette pipeline | stubs | — | pipeline + API OK | base de départ |
| EXP-B-001 | 2026-10-04 | B | Extraction d'affirmations (SPO, modalité, coréférence) | règles ; règles + spaCy FR / Stanza AR | modalité ; triplet SPO exact | modalité 1.00 ; SPO 0.46 (règles et parseurs) | Bronze retenu ; Silver : objets, lexique verbal |
| EXP-A2-001 | 2026-10-06 | A2 | Normalisation + identification de langue et de script | règles : stub vs v1 | exactitude langue (eval_30) ; cas FR ciblés | 0.82 (stub = v1) ; cas ciblés 0/5 → 5/5 | v1 retenue ; suite : classifieur TN |
| EXP-B-002 | 2026-10-07 | B | Extraction d'affirmations : compléments de source / temps / lieu hors objet | règles ; règles + spaCy FR / Stanza AR | triplet SPO exact | SPO 0.64 (règles) ; 0.77 (parseurs) | retenu ; suite : lexique verbal du mode règles |
| EXP-B-003 | 2026-10-15 | B | Extraction d'affirmations : lexique verbal du mode règles, sujet verbe-sujet-objet | règles ; règles + spaCy FR / Stanza AR | triplet SPO exact | SPO 0.86 (règles) ; 0.77 (parseurs) | retenu ; suite : jeu d'environ 100 phrases |
| EXP-B-004 | 2026-10-15 | B | Extraction d'affirmations : source du discours rapporté, complément du participe dans le sujet | règles ; règles + spaCy FR / Stanza AR | triplet SPO exact | SPO 0.91 (règles) ; 0.77 (parseurs) | retenu ; jeu de dev saturé |
| EXP-B-005 | 2026-10-20 | B | Extraction d'affirmations : lexiques selon l'écriture, verbe de parole précédé de « و » / « ف » collé | règles ; règles + spaCy FR / Stanza AR | sorties eval_30 inchangées ; tests ciblés | eval_30 identique (SPO 0.91 / 0.77) ; effet non mesuré sur un jeu annoté | retenu ; mesure sur eval_100 |

## Entrées

### EXP-C-008 — Analyse qualitative cross-seed de 30 erreurs Model 1
- **Date** : 2026-10-26
- **Auteur / Lot** : Lot C
- **Objectif / hypothèse** : rendre traçables les erreurs représentatives du
  classifieur Model 1 et identifier les phénomènes à prioriser.
- **Données** : `errors_30_cross_seed.jsonl` : 25 erreurs de `seed42` et 5
  erreurs distinctes de `seed2026`. Ce n'est pas un échantillon aléatoire : il
  sert à l'analyse qualitative, non au calcul d'un taux d'erreur.
- **Méthode / configuration** : catégorisation déterministe à partir du label
  gold, de la modalité et de la prédiction, avec
  `bronze/analyze_model1_errors.py`.
- **Code** : `bronze/analyze_model1_errors.py` ; sortie structurée
  `evaluation/results/model1_errors_30_cross_seed.jsonl`.
- **Résultats** : 30 erreurs : hypothèses non reconnues 8, opinions prises pour
  AFFIRMATION 7, opinions prises pour AUTRE 6, affirmations non reconnues 3,
  autres confusions 2, souhaits 2, question 1, discours rapporté 1.
- **Analyse** : les modalités non factuelles (hypothèse, souhait, question)
  totalisent 11 erreurs ; les opinions 13. Les exemples mélangent FR, arabe et
  tunisien, en particulier arabizi/mixed, ce qui confirme la difficulté des
  formulations informelles.
- **Décision / suite** : rapporter cette analyse dans la revue et prioriser des
  exemples annotés supplémentaires pour ces phénomènes avant tout nouveau
  réglage du modèle. Rapport : `docs/lot-c_error_analysis_cross_seed.md`.

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
