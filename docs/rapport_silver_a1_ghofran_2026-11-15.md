# NewsCheck TN — Rapport scientifique Silver



**Lot :** A1 — Données et annotations  

**Responsable du livrable :** Ghofran  

**Date :** 15 novembre 2026  

**Version :** 1.0 — Proposition pour revue  

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



**Fichier :** `data/annotations/nli_corpus_300_consolide_v4_prive.jsonl`



Le corpus comprend 300 paires claim–evidence.



| Relation | Effectif | Proportion |

|---|---:|---:|

| supports | 152 | 50,7 % |

| refutes | 83 | 27,7 % |

| neutral | 65 | 21,7 % |

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



Les 31 désaccords initiaux ont été examinés.



La consolidation des 100 textes présente :



| Label final | Effectif |

|---|---:|

| AFFIRMATION | 8 |

| OPINION | 33 |

| AUTRE | 59 |

| **Total** | **100** |



Les labels arbitrés ne doivent pas être utilisés pour recalculer l'accord entre deux annotations indépendantes.



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



Les noms des corpus et partitions de référence sont documentés.



Une reproductibilité scientifique renforcée nécessite encore de confirmer :



- Les versions exactes des fichiers.

- Les empreintes de contrôle.

- Les paramètres et scripts de génération des partitions.

- Les scripts et résultats d'audit.

- La correspondance entre les corpus utilisés par les différents lots.



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



### 9.1 Validation humaine



- Revue collective du rapport Bronze.

- Décision sur les trois propositions de révision.

- Validation du guide d'annotation v1.1.

- Clarification du cas P266/P267.



### 9.2 Contrôles scientifiques complémentaires



- Recherche des doublons et quasi-doublons textuels.

- Vérification sémantique des relations NLI.

- Contrôle des fuites sémantiques entre partitions.

- Vérification de la provenance individuelle.

- Clarification de la relation entre les corpus A1 et Lot C.



### 9.3 Conformité et reproductibilité



- Vérification des licences applicables.

- Revue des contraintes de confidentialité.

- Confirmation des versions et empreintes des corpus.

- Consolidation des éléments nécessaires à la reproduction des audits.



### 9.4 Livrables Silver



- Revue scientifique de la Data Card v1.0.

- Revue du présent rapport.

- Vérification de cohérence entre les deux documents.

- Préparation d'une PR documentaire isolée après autorisation.



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

- `data/annotations/nli_corpus_300_consolide_v4_prive.jsonl`

- `data/splits/nli_v3_by_article_seed42.json`

- `data/splits/claim_detection_multiclass_600_seed42.json`

- `data/annotations/nli_P266_P267_nawaat_valides_v1_prive.jsonl`

- `data/annotations/a1_historique_revision_0289_prive.csv`

**Fin du rapport — Version 1.0, proposition Silver.**
