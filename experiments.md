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
| EXP-B-001 | 2026-10-04 | B | Extraction d'affirmations (SPO, modalité, coréférence) | règles ; règles + spaCy FR / Stanza AR | modalité ; triplet SPO exact | modalité 1.00 ; SPO 0.46 (règles et parseurs) | Bronze retenu ; Silver : objets, lexique verbal |
| EXP-B-002 | 2026-10-07 | B | Extraction d'affirmations : compléments de source / temps / lieu hors objet | règles ; règles + spaCy FR / Stanza AR | triplet SPO exact | SPO 0.64 (règles) ; 0.77 (parseurs) | retenu ; suite : lexique verbal du mode règles |
| EXP-B-003 | 2026-10-15 | B | Extraction d'affirmations : lexique verbal du mode règles, sujet verbe-sujet-objet | règles ; règles + spaCy FR / Stanza AR | triplet SPO exact | SPO 0.86 (règles) ; 0.77 (parseurs) | retenu ; suite : jeu d'environ 100 phrases |
| EXP-B-004 | 2026-10-15 | B | Extraction d'affirmations : source du discours rapporté, complément du participe dans le sujet | règles ; règles + spaCy FR / Stanza AR | triplet SPO exact | SPO 0.91 (règles) ; 0.77 (parseurs) | retenu ; jeu de dev saturé |

## Entrées

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
