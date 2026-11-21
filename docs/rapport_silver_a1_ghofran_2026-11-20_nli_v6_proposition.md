> **Proposition actualisee — 20/11/2026**
>
> Corpus NLI de reference : V6, 300 paires.
> Supports : 152 ; Refutes : 84 ; Neutral : 64.
> Fichier V6 conserve dans le stockage prive hors depot.
> Rapport historique du 15/11/2026 conserve.
> Validation scientifique collective en attente.

---
# NewsCheck TN — Rapport scientifique Silver



**Lot :** A1 — Données et annotations  

**Responsable du livrable :** Ghofran  

**Date :** 20 novembre 2026  

**Version :** 1.1 — Proposition pour revue NLI V6  

**Statut :** Audits techniques réalisés ; validation scientifique collective en attente  

**Confidentialité :** Document interne — corpus et annotations privés



---



## 1. Résumé exécutif



Le Lot A1 du projet NewsCheck TN vise à constituer, annoter, documenter et contrôler des données multilingues destinées à deux tâches de traitement automatique des langues :



- La classification des énoncés en AFFIRMATION, OPINION et AUTRE.

- L'inférence en langage naturel (NLI) entre une affirmation et un élément de preuve.



Les livrables documentés comprennent un corpus A1 de 600 phrases, un corpus NLI de 300 paires et un sous-ensemble de 100 textes ayant fait l'objet d'une double annotation indépendante.



Les audits Silver ont confirmé la validité structurelle des 900 enregistrements, l'unicité de leurs identifiants principaux et la cohérence des distributions calculées.



L'accord interannotateurs initial sur 100 textes est de 69 %, avec un Cohen's Kappa de 0,3481. Les 31 désaccords ont été examinés lors de l'arbitrage Bronze.



Les contrôles des partitions NLI n'ont révélé aucun partage d'identifiants de claims ou d'evidences entre les ensembles actifs d'entraînement, de validation et de test.



Ces résultats établissent une base technique documentée. Ils ne démontrent pas encore l'absence de doublons sémantiques, la validité de toutes les annotations ou la conformité juridique de la redistribution.



## 2. Objectifs et périmètre



### 2.1 Objectif principal



Produire des données annotées, traçables et techniquement contrôlées pour soutenir les expérimentations NLP de NewsCheck TN.



### 2.2 Objectifs spécifiques



1\. Documenter la composition des corpus A1 et NLI.

2\. Vérifier la structure des fichiers et les distributions des labels.

3\. Évaluer l'accord humain sur un sous-ensemble doublement annoté.

4\. Préserver l'historique des arbitrages et des corrections.

5\. Examiner la séparation des données NLI.

6\. Identifier les risques de qualité, de fuite de données et de provenance.

7\. Préparer les livrables scientifiques Silver.



### 2.3 Hors périmètre



Le présent rapport ne constitue pas :



- Une évaluation de performance d'un modèle entraîné.

- Une certification de véracité des affirmations.

- Une validation sémantique exhaustive du corpus NLI.

- Une autorisation de publication des textes sources.

- Une approbation scientifique définitive de l'équipe.



## 3. Données et méthodologie



### 3.1 Corpus de classification A1



**Fichier :** `data/annotations/corpus_a1_600_humain_final_prive.jsonl`



Le corpus comprend 600 phrases réparties entre trois catégories.



| Label | Effectif | Proportion |

|---|---:|---:|

| AFFIRMATION | 127 | 21,2 % |

| OPINION | 203 | 33,8 % |

| AUTRE | 270 | 45,0 % |

| **Total** | **600** | **100 %** |



La catégorie AFFIRMATION désigne un énoncé potentiellement vérifiable. Elle ne signifie pas que l'affirmation est vraie.



La composition documentée est la suivante :



| Origine | Effectif |

|---|---:|

| TArC — forum.tab | 570 |

| Tunifact — textes originaux | 15 |

| Tunifact — reformulations | 15 |

| **Total** | **600** |



La provenance individuelle de chaque enregistrement reste à confirmer.



### 3.2 Caractéristiques linguistiques



| Langue déclarée | Effectif |

|---|---:|

| Tunisien (`tn`) | 565 |

| Français (`fr`) | 20 |

| Arabe (`ar`) | 15 |



La répartition des écritures déclarées est de 560 textes latins, 20 mixtes, 15 arabes et 5 Arabizi.



Ces distributions montrent une forte concentration sur le tunisien et l'écriture latine.



Les valeurs correspondent aux métadonnées enregistrées et ne constituent pas une validation linguistique manuelle exhaustive.



### 3.3 Corpus NLI



**Fichier :** `nli_corpus_300_consolide_v6_prive.jsonl`



Le corpus comprend 300 paires claim–evidence.



| Relation | Effectif | Proportion |

|---|---:|---:|

| supports | 152 | 50,7 % |

| refutes | 84 | 28,0 % |

| neutral | 64 | 21,3 % |

| **Total** | **300** | **100 %** |



Les proportions sont arrondies indépendamment.



Les claims comprennent 112 textes déclarés en français et 188 en arabe.



Les evidences comprennent 107 textes déclarés en français et 193 en arabe.



La relation NLI décrit le lien annoté entre deux textes ; elle ne garantit pas la fiabilité indépendante de l'evidence.



### 3.4 Méthode d'annotation



La méthodologie du Lot A1 repose sur :



- Un guide de décision pour les classes AFFIRMATION, OPINION et AUTRE.

- Des annotations humaines documentées.

- Une double annotation indépendante sur 100 textes.

- Une comparaison des décisions initiales.

- Un arbitrage des désaccords.

- Une conservation de l'historique des corrections.



Le guide de référence est `docs/annotation_guide_v1.1.md`, dont la validation collective reste en attente.



### 3.5 Corpus pilote



Un pilote historique de 60 phrases a été documenté, comprenant 30 textes TArC et 30 textes Tunifact.



Sa distribution était de 48 AFFIRMATION, 7 OPINION et 5 AUTRE.



Ces statistiques historiques sont distinctes de celles du corpus final de 600 phrases.



## 4. Résultats des contrôles structurels



### 4.1 Corpus A1



Les contrôles ont confirmé :



- 600 enregistrements JSONL valides.

- Aucun doublon d'identifiant principal.

- La présence des champs attendus.

- La cohérence des distributions de labels et des métadonnées linguistiques.



Ces vérifications ne garantissent pas l'exactitude de toutes les valeurs des champs.



### 4.2 Corpus NLI



Les contrôles ont confirmé :



- 300 enregistrements JSONL valides.

- Aucun doublon de `pair_id`.

- 259 `claim_id` distincts.

- 290 `evidence_id` distincts.

- 21 identifiants de claim apparaissant dans plusieurs paires.



La réutilisation d'un identifiant de claim peut être légitime lorsqu'une affirmation possède plusieurs evidences.



### 4.3 Synthèse



| Indicateur | Résultat |

|---|---|

| Corpus A1 | 600 enregistrements |

| Corpus NLI | 300 paires |

| JSONL invalides | 0 |

| Doublons d'identifiants principaux | 0 |

| Contrôles des distributions | Réalisés |

| Validation sémantique exhaustive | Non réalisée |



## 5. Accord interannotateurs et arbitrage



### 5.1 Double annotation



Un sous-ensemble commun de 100 textes a été annoté indépendamment par Ghofran et Achref.



Les résultats initiaux sont les suivants :



| Indicateur | Valeur |

|---|---:|

| Textes comparés | 100 |

| Accords | 69 |

| Désaccords | 31 |

| Accord observé | 69,00 % |

| Accord attendu | 52,45 % |

| Cohen's Kappa | 0,3481 |



Ce Kappa correspond à un accord limité au-delà du hasard et doit être interprété en tenant compte de la distribution des classes.



### 5.2 Matrice de confusion



Lignes : Ghofran. Colonnes : Achref.



| | AFFIRMATION | OPINION | AUTRE |

|---|---:|---:|---:|

| AFFIRMATION | 1 | 0 | 0 |

| OPINION | 2 | 17 | 9 |

| AUTRE | 2 | 18 | 51 |



Les principales divergences concernent la distinction entre OPINION et AUTRE.



### 5.3 Résultats après arbitrage

Les 31 désaccords initiaux disposent de décisions documentées dans un registre de travail ; leur validation humaine finale reste à confirmer.

La traçabilité des 100 textes distingue deux catégories :
- ACCORD_INITIAL : 69 cas.
- ARBITRAGE_HUMAIN : 31 cas.

La consolidation des 100 textes présente :

| Label final | Effectif |
|---|---:|
| AFFIRMATION | 8 |
| OPINION | 33 |
| AUTRE | 59 |
| **Total** | **100** |

Ces résultats concernent exclusivement le sous-ensemble doublement annoté
de 100 textes et non la distribution des 600 phrases A1.

Parmi les 31 désaccords initiaux, 27 concernent la distinction
entre OPINION et AUTRE.

La comparaison de ces 27 cas avec le corpus consolidé
de 540 annotations a relevé :
- 13 concordances.
- 14 divergences.

Cette analyse porte sur des cas sélectionnés pour leurs difficultés.
Elle ne peut pas être généralisée à l'ensemble du corpus.

Les labels arbitrés ne doivent pas être utilisés pour recalculer
l'accord entre deux annotations indépendantes.

### 5.4 Révisions et décisions ouvertes



La correction du cas `tarc-forum-0289` a été documentée, avec un label final OPINION.



Trois propositions restent non appliquées :



| Identifiant | Label actuel | Proposition |

|---|---|---|

| tarc-forum-0054 | AUTRE | OPINION |

| tarc-forum-0066 | AUTRE | AFFIRMATION |

| tarc-forum-0462 | AUTRE | OPINION |



Leur application nécessite une décision humaine explicite.



## 6. Audit des partitions NLI



### 6.1 Répartition



**Fichier :** `data/splits/nli_v3_by_article_seed42.json`



| Ensemble | Nombre |

|---|---:|

| Train | 174 |

| Validation | 33 |

| Test | 56 |

| Exclusions | 37 |

| **Total** | **300** |



Les ensembles actifs comprennent 263 paires.



### 6.2 Résultats



Les contrôles ont confirmé :



- L'absence de chevauchement des identifiants de paires entre train, validation et test.

- L'absence de partage des `claim_id` entre ces ensembles.

- L'absence de partage des `evidence_id` entre ces ensembles.

- La couverture des 300 paires par les partitions ou exclusions.



Ces résultats concernent uniquement les identifiants.



Ils ne prouvent pas l'absence de fuite textuelle ou sémantique.



### 6.3 Cas P266/P267



Les paires P266 et P267 partagent les identifiants `claim_id` et `evidence_id`, mais leurs claims ne sont pas textuellement identiques.



Leurs relations enregistrées sont supports et refutes.



Une validation humaine spécifique existe.



L'audit relève une incohérence potentielle de réutilisation d'identifiant, sans démontrer que les relations annotées sont incorrectes.



Les deux paires sont exclues des partitions actives.



### 6.4 Compatibilité avec le Lot C



Le split `claim_detection_multiclass_600_seed42.json` concerne le corpus traité `claim_detection_600.jsonl` du Model 1.



Ses 120 identifiants de test ne correspondent à aucun identifiant du corpus A1 final audité.



Il ne peut donc pas être considéré comme un split validé du corpus A1 final.



L'indépendance textuelle des deux corpus reste à vérifier.



## 7. Qualité, traçabilité et reproductibilité



### 7.1 Traçabilité



Les données comprennent des métadonnées de source, de langue, d'écriture et d'annotation.



L'historique Bronze permet de distinguer les annotations initiales, les arbitrages et certaines corrections.



La présence de métadonnées ne garantit pas leur exactitude individuelle.



### 7.2 Reproductibilité

Le manifeste de reproductibilité Silver A1 v1.0 est disponible :

`docs/manifeste_reproductibilite_silver_a1_v1.0.md` (référence historique ; proposition actualisée pour NLI V6 : `docs/manifeste_reproductibilite_silver_a1_v1.1_proposition.md`, en attente de validation scientifique).

Il centralise les références des corpus, les empreintes SHA-256 disponibles,
les partitions et les contrôles documentés.

Le contrôle canonique des 12 références SHA-256 du manifeste a été effectué le 15/11/2026 : 12/12 empreintes conformes. Ce contrôle confirme l'intégrité des fichiers vérifiés, mais ne valide pas à lui seul les versions logicielles ni les scripts de génération.

La correspondance entre les corpus utilisés par les différents lots reste
à clarifier.

### 7.3 Confidentialité



Les fichiers privés ne doivent pas être publiés sans vérification des droits et autorisation de l'équipe.



Les rapports scientifiques peuvent présenter des statistiques agrégées sans reproduire les contenus privés.



## 8. Limites et risques scientifiques



### 8.1 Déséquilibre des classes



Les classes de classification A1 ne sont pas équilibrées.



Ce déséquilibre doit être pris en compte lors des futures évaluations.



### 8.2 Représentativité linguistique



Le corpus A1 est principalement tunisien et écrit en caractères latins.



Les conclusions ne peuvent pas être généralisées automatiquement à d'autres langues ou écritures.



### 8.3 Fiabilité des annotations



Le Cohen's Kappa initial de 0,3481 indique un accord limité.



Les décisions difficiles, notamment OPINION contre AUTRE, nécessitent une attention particulière.



### 8.4 Qualité sémantique



Les contrôles structurels ne garantissent ni la pertinence des preuves ni l'exactitude des relations NLI.



La cohérence des identifiants P266/P267 doit être clarifiée.



### 8.5 Fuites de données



Les contrôles d'identifiants sont satisfaisants pour les partitions NLI auditées.



Les risques de doublons textuels, de paraphrases proches et de fuites sémantiques restent à examiner.



### 8.6 Licences et provenance



La documentation existante mentionne CC BY-NC-SA 4.0 pour TArC, sans confirmation complète de son applicabilité aux données utilisées.



Les droits de redistribution des contenus Tunifact et des reformulations restent à vérifier.



## 9. Travaux restant à réaliser

### Validation humaine et scientifique

1. Obtenir la réponse d'Achref sur la traçabilité et la clôture des 31 arbitrages.
2. Documenter précisément la version des annotations utilisée pour le Kappa initial, en distinguant les données indépendantes des corrections ultérieures.
3. Confirmer la provenance et le processus de constitution des 540 annotations.
4. Maintenir les trois propositions `tarc-forum-0054`, `tarc-forum-0066` et `tarc-forum-0462` en attente de décision humaine.
5. Confirmer le guide d'annotation v1.1.
6. Clarifier la cohérence des claims et des relations P266/P267.

### Qualité scientifique

7. Réaliser, si nécessaire, une analyse des doublons textuels et quasi-doublons.
8. Compléter la revue sémantique des relations NLI.
9. Examiner les risques de fuites textuelles et sémantiques entre partitions.
10. Compléter la vérification de provenance individuelle.

### Conformité et reproductibilité

11. Vérifier les licences et les droits de redistribution.
12. Confirmer les règles de confidentialité.
13. [x] Vérifier les empreintes des 12 références du manifeste : 12/12 PASS le 15/11/2026.
14. Confirmer les versions et scripts de génération des partitions.
15. Clarifier les correspondances éventuelles entre A1 et Lot C.

### Finalisation des livrables

16. Obtenir la revue scientifique collective de la Data Card et du rapport.
17. Vérifier leur cohérence avec les résultats Bronze et le manifeste.
18. Préparer une PR documentaire isolée après autorisation.

## 10. Conclusion scientifique



Le Lot A1 dispose de deux corpus structurés, totalisant 900 enregistrements, ainsi que d'un historique de double annotation humaine sur 100 textes.



Les contrôles techniques réalisés confirment la validité des fichiers JSONL, l'unicité des identifiants principaux et la cohérence des distributions documentées.



L'analyse de l'accord humain met en évidence 31 désaccords initiaux et un Cohen's Kappa de 0,3481. Les arbitrages Bronze ont été documentés, tandis que certaines propositions restent soumises à validation.



L'audit des partitions NLI confirme une séparation correcte au niveau des identifiants, mais ne démontre pas l'absence de fuite sémantique.



La Data Card Silver v1.0 et ce rapport constituent des livrables documentaires pour la revue scientifique du Lot A1.



**Conclusion générale : les contrôles structurels Silver sont réalisés ; la validation scientifique collective et plusieurs contrôles complémentaires restent nécessaires.**



---



## Références internes



- `docs/data_card_v1.0_silver.md`

- `docs/data_card_v0.2.md`

- `docs/annotation_guide_v1.1.md`

- `docs/rapport_bronze_a1_ghofran_achref_2026-11-14.md`

- `data/annotations/corpus_a1_600_humain_final_prive.jsonl`

- `nli_corpus_300_consolide_v6_prive.jsonl`

- `data/splits/nli_v3_by_article_seed42.json`

- `data/splits/claim_detection_multiclass_600_seed42.json`

- `data/annotations/nli_P266_P267_nawaat_valides_v1_prive.jsonl`

- `data/annotations/a1_historique_revision_0289_prive.csv`

**Fin du rapport — Version 1.0, proposition Silver.**

## Actualisation A1 — 21 novembre 2026

**Statut : proposition scientifique non validée.**

### Réconciliation des annotations

- 31 arbitrages documentés.
- 22 concordances entre le registre et le corpus A1 600 actuel.
- 9 divergences constatées.
- Le bilan historique de 18 divergences est conservé,
  mais son écart avec le bilan actuel reste à expliquer.
- Aucun label officiel modifié automatiquement.

Les divergences actuelles concernent :
tarc-forum-0497, tarc-forum-0462, tarc-forum-0066,
tarc-forum-0353, tarc-forum-0054, tarc-forum-0289,
tarc-forum-0210, tarc-forum-0035 et tarc-forum-0145.

Les propositions concernant 0054, 0066, 0462 et
la provenance historique de 0289 nécessitent
une confirmation humaine.

### Conditions de clôture

- Valider les décisions scientifiques ouvertes.
- Confirmer les règles d'annotation concernées.
- Conserver les restrictions de redistribution.
- Actualiser les artefacts officiels après approbation.

Référence : docs/silver_a1_decisions_ouvertes_2026-11-21.md

## Actualisation ? Validation Achref du 20 novembre 2026

**Statut : validation individuelle documentee ; validation collective en attente.**

- 18 cas examines par Achref Chabene le 20/11/2026.
- 16 labels valides sans reserve.
- 1 label valide sous reserve : 0066 = AFFIRMATION.
- 1 cas en revision : 0071, sans nouveau label valide.
- 0054, 0462 et 0289 : OPINION valide par Achref.
- Pour 0289, la validation concerne le texte restaure.
  L'historique de correction et la provenance restent conserves.
- Pour 0066, la regle des temoignages personnels
  necessite une validation collective.
- Pour 0071, le contexte medical d'origine reste necessaire.
- Les 9 divergences precedemment mesurees restent
  un instantane historique, non recalcule apres approbation.
- Aucun label officiel n'est remplace automatiquement.

Reference : `docs/silver_a1_decisions_ouvertes_2026-11-21.md`.

### Detail des 18 decisions d'Achref

| Identifiant | Label valide | Statut |
|---|---|---|
| tarc-forum-0329 | AUTRE | VALIDE_PAR_ACHREF |
| tarc-forum-0462 | OPINION | VALIDE_PAR_ACHREF |
| tarc-forum-0429 | AFFIRMATION | VALIDE_PAR_ACHREF |
| tarc-forum-0541 | AUTRE | VALIDE_PAR_ACHREF |
| tarc-forum-0066 | AFFIRMATION | VALIDE_PAR_ACHREF_SOUS_RESERVE |
| tarc-forum-0071 | AUCUN | EN_REVISION |
| tarc-forum-0353 | OPINION | VALIDE_PAR_ACHREF |
| tarc-forum-0407 | OPINION | VALIDE_PAR_ACHREF |
| tarc-forum-0015 | OPINION | VALIDE_PAR_ACHREF |
| tarc-forum-0075 | AUTRE | VALIDE_PAR_ACHREF |
| tarc-forum-0408 | AFFIRMATION | VALIDE_PAR_ACHREF |
| tarc-forum-0054 | OPINION | VALIDE_PAR_ACHREF |
| tarc-forum-0289 | OPINION | VALIDE_PAR_ACHREF |
| tarc-forum-0078 | OPINION | VALIDE_PAR_ACHREF |
| tarc-forum-0200 | AUTRE | VALIDE_PAR_ACHREF |
| tarc-forum-0210 | AUTRE | VALIDE_PAR_ACHREF |
| tarc-forum-0035 | AUTRE | VALIDE_PAR_ACHREF |
| tarc-forum-0337 | OPINION | VALIDE_PAR_ACHREF |
