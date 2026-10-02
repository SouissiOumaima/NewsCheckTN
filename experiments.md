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

## Entrées

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
