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
| EXP-C-002 | 2026-10-26 | C | NLI (Model 2) : baseline sans entraînement | mDeBERTa-v3-base xnli (zero-shot), corpus NLI A1 v3, test gelé 56 paires | macro-F1 (test) | 0.798 [IC95 0.67–0.89] ; acc 0.804 ; fr 0.78 / ar 0.78 ; articles Lot D 0.77 | baseline retenue et branchée ; chiffres officiels sur v4 |
| EXP-E-001 | 2026-10-02 | E | Squelette pipeline | stubs | — | pipeline + API OK | base de départ |

## Entrées

### EXP-C-002 — NLI (Model 2) : baseline sans entraînement
- **Date** : 2026-10-26
- **Auteur / Lot** : Membre 4 (Wiem) / Lot C
- **Objectif / hypothèse** : remplacer le stub NLI (toujours « neutre ») par un modèle multilingue déjà entraîné sur XNLI, utilisé tel quel, et mesurer le seuil que le Model 2 entraîné devra dépasser.
- **Données** : corpus NLI du Lot A1, `nli_corpus_300_consolide_v3_prive.jsonl` (privé, non versionné). 37 paires en attente de validation (« Brouillon non valide ») mises de côté → 263 paires. Découpage par groupe d'articles (graine 42) : train 174, val 33, test 56. Le test contient les 30 paires des articles du jeu de test du Lot D (Tunifact 613, 698, 797, 890, 933, 937). Aucun texte partagé entre les parties. Identifiants : `data/splits/nli_v3_by_article_seed42.json`. Langues du test : 25 fr, 31 ar, 0 tunisien.
- **Méthode / configuration** : `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`, sans entraînement. Prémisse = preuve, hypothèse = affirmation ; entailment → supports, contradiction → refutes. Troncature de la preuve à 512 tokens. CPU, 191 s pour 56 paires. Déterministe.
- **Code** : `python -m models.nli.data --version v3 --input …` puis `python -m models.nli.evaluate --version v3 --split test --exp-id EXP-C-002`.
- **Résultats (test, n = 56)** : accuracy 0.804, **macro-F1 0.798** (IC 95 % bootstrap [0.669 ; 0.891]).
  - supports : P 0.95, R 0.83, F1 0.88 ; refutes : P 0.93, R 0.68, F1 0.79 ; neutral : P 0.59, R 0.93, F1 0.72.
  - Confusion (vrai → prédit) : supports → neutral 4 ; refutes → neutral 5, refutes → supports 1 ; neutral → refutes 1.
  - Par langue : fr 0.779 (n = 25), ar 0.776 (n = 31). Articles du test du Lot D : 0.767 (n = 30).
- **Analyse** : le modèle tranche rarement à tort (précision 0.93–0.95 sur supports / refutes) ; ses erreurs vont presque toutes vers « neutral », ce qui mène le verdict du Lot D à s'abstenir plutôt qu'à affirmer une erreur. Pas d'écart entre français et arabe. Limites : petit test (IC large), corpus v3 encore en correction, aucune paire en tunisien ou en arabizi.
- **Décision / suite** : baseline retenue et branchée dans `models/nli/stance.py` (utilisable par le Lot D). Suite : affiner ce même modèle sur le train (plutôt qu'entraîner XLM-R depuis zéro sur 174 paires), 3 graines, comparaison bootstrap à cette baseline ; mesures officielles une seule fois sur la v4 du corpus ; demander au Lot A1 des paires en tunisien.

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