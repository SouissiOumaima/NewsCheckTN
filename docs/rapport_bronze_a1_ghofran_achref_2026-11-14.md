# NewsCheck TN — Rapport scientifique Bronze A1

**Date :** 14 novembre 2026
**Lot :** A1 — Double annotation Ghofran / Achref
**Statut :** Consolidation technique validée ; propositions en attente de validation humaine

## 1. Objectif

Le lot Bronze A1 vise à consolider des annotations humaines
de textes multilingues tunisiens selon trois catégories :

- AFFIRMATION : proposition factuelle potentiellement vérifiable.
- OPINION : jugement, évaluation ou appréciation subjective.
- AUTRE : texte sans proposition factuelle identifiable ni opinion explicite.

Les données comprennent notamment du français, de l'arabe tunisien
et de l'Arabizi.

## 2. Méthodologie

Deux annotateurs, Ghofran et Achref, ont annoté indépendamment
un ensemble commun de 100 textes.

Les désaccords ont été examinés par arbitrage humain.

Les labels initiaux ont été conservés pour calculer
l'accord interannotateurs, indépendamment des décisions finales.

Le guide d'annotation A1 v1.1 a servi de référence lors
de la revue qualitative. Sa validation définitive par
l'équipe reste à confirmer.

## 3. Accord interannotateurs

- Textes doublement annotés : 100
- Accords initiaux : 69
- Désaccords initiaux : 31
- Accord observé : 69,00 %
- Accord attendu : 52,45 %
- Cohen's Kappa : 0,3481

Le Kappa indique un accord limité au-delà du hasard.
Les résultats doivent être interprétés en tenant compte
du déséquilibre des classes.

## 4. Matrice de confusion initiale

Lignes : Ghofran. Colonnes : Achref.

| Ghofran / Achref | AFFIRMATION | OPINION | AUTRE |
|---|---:|---:|---:|
| AFFIRMATION | 1 | 0 | 0 |
| OPINION | 2 | 17 | 9 |
| AUTRE | 2 | 18 | 51 |

## 5. Distribution des labels finaux

| Label | Nombre |
|---|---:|
| AFFIRMATION | 8 |
| OPINION | 33 |
| AUTRE | 59 |
| **Total** | **100** |

## 6. Arbitrages humains

- Accords initiaux conservés : 69
- Désaccords arbitrés : 31
- Annotations finales : 100

Le cas tarc-forum-0289 a fait l'objet d'une correction
documentée du texte source et d'une révision du label
final vers OPINION.

L'historique de cette intervention est conservé
dans un fichier distinct.

## 7. Analyse qualitative des désaccords

Parmi les 31 désaccords initiaux, 27 concernent
l'opposition entre OPINION et AUTRE.

La comparaison de ces 27 cas avec le corpus consolidé
de 540 annotations a identifié :

- 13 concordances entre corpus.
- 14 divergences entre corpus.
- Aucune correspondance absente ou multiple.

Ces résultats concernent un sous-ensemble sélectionné
pour ses difficultés d'annotation et ne doivent pas
être généralisés à l'ensemble du corpus.

## 8. Propositions de révision non appliquées

| Identifiant | Label actuel | Label proposé | Statut |
|---|---|---|---|
| tarc-forum-0054 | AUTRE | OPINION | PROPOSITION_A_VALIDER |
| tarc-forum-0066 | AUTRE | AFFIRMATION | PROPOSITION_A_VALIDER |
| tarc-forum-0462 | AUTRE | OPINION | PROPOSITION_A_VALIDER |

Ces propositions sont documentées séparément.
Elles ne remplacent pas les labels du corpus final.

Leur application nécessite une validation humaine explicite.

## 9. Contrôles qualité

L'audit technique final a confirmé :

- 100 annotations.
- 100 identifiants uniques.
- Aucun label final invalide.
- Aucun champ essentiel manquant.
- 31 arbitrages humains.
- Trois propositions de révision cohérentes avec le corpus final.

Résultat de l'audit : PASS.

## 10. Limites méthodologiques

1. L'échantillon de double annotation comprend 100 textes.
2. La classe AFFIRMATION est très minoritaire dans les annotations initiales.
3. Plusieurs textes mélangent témoignages, jugements et faits rapportés.
4. Le français, le tunisien et l'Arabizi introduisent des ambiguïtés linguistiques.
5. Les divergences entre corpus ne prouvent pas qu'un label est incorrect.
6. Trois propositions de révision restent à valider.
7. Le guide A1 v1.1 doit encore être confirmé par l'équipe.

## 11. Conclusion

La consolidation technique du lot Bronze A1 est terminée.

Les 100 annotations finales ont été vérifiées,
les 31 désaccords ont été arbitrés et les statistiques
d'accord interannotateurs ont été calculées.

Le corpus peut servir de version de référence technique,
à condition de conserver la traçabilité des arbitrages
et de signaler les propositions encore en attente.

La clôture scientifique définitive dépend des validations
humaines restantes.

## 12. Livrables principaux

- a1_annotations_finales_ghofran_achref_100_prive.csv
- a1_historique_revision_0289_prive.csv
- a1_propositions_revision_ghofran_achref_100_prive.csv
- rapport_bronze_a1_ghofran_achref_2026-11-14.md