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
| EXP-A2-001 | 2026-10-06 | A2 | Normalisation + identification de langue et de script | règles : stub vs v1 | exactitude langue (eval_30) ; cas FR ciblés | 0.82 (stub = v1) ; cas ciblés 0/5 → 5/5 | v1 retenue ; suite : classifieur TN |
| EXP-A2-002 | 2026-10-07 | A2 | Tunisien en lettres arabes | règle : lexique de 78 marques + négation | langue TN sur eval_30 ; rappel TN sur échantillon annoté | 8/14 → 12/14 ; 41/78, standard 15/15 | règle retenue comme référence ; suite : classifieur |

## Entrées

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
  - (a) eval_30, avant (`e2fdbe7`) → après : FR 10/10 → 10/10 ; AR 10/10 → 10/10 ; TN 8/14 → 12/14 ;
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
