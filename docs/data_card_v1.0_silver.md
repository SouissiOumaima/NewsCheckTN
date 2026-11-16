# NewsCheck TN — Data Card

**Version :** 1.0 — Proposition Silver  
**Date :** 15 novembre 2026  
**Projet :** NewsCheck TN  
**Lot :** A1 — Données et annotations  
**Statut :** Proposition documentaire pour revue ; validation scientifique collective en attente.  
**Confidentialité :** Les corpus sources et fichiers d'annotation privés ne sont pas autorisés à la diffusion par cette Data Card.

---

## 1. Présentation

NewsCheck TN est un projet de traitement automatique des langues (NLP) portant sur l'analyse d'énoncés multilingues tunisiens et l'inférence en langage naturel (NLI).

Le Lot A1 documente deux ensembles de référence :

- Un corpus de 600 phrases classées en AFFIRMATION, OPINION ou AUTRE.
- Un corpus de 300 paires claim–evidence annotées avec les relations supports, refutes ou neutral.

Il comprend également un pilote historique de 60 phrases, une double annotation de 100 textes, un guide d'annotation et des procédures d'arbitrage.

**AFFIRMATION** désigne un énoncé potentiellement vérifiable, et non un énoncé nécessairement vrai. Les relations NLI décrivent la relation entre un claim et une evidence ; elles ne certifient pas indépendamment la fiabilité de la source.

Cette Data Card décrit les données, les contrôles réalisés et les limites identifiées. Elle ne constitue pas une évaluation des performances des modèles.

## 2. Corpus pilote historique

Le pilote historique comprend 60 phrases :

| Source | Nombre |
|---|---:|
| TArC | 30 |
| Tunifact | 30 |
| **Total** | **60** |

| Label | Nombre |
|---|---:|
| AFFIRMATION | 48 |
| OPINION | 7 |
| AUTRE | 5 |
| **Total** | **60** |

Ces statistiques concernent uniquement le pilote historique. Elles ne doivent pas être confondues avec celles du corpus étendu.

## 3. Corpus A1 — 600 phrases

**Fichier de référence :** `data/annotations/corpus_a1_600_humain_final_prive.jsonl`

### 3.1 Composition documentée

| Origine | Nombre |
|---|---:|
| TArC — forum.tab | 570 |
| Tunifact — textes originaux | 15 |
| Tunifact — reformulations | 15 |
| **Total** | **600** |

Cette composition provient de la documentation du corpus. L'exactitude individuelle de toutes les informations de provenance n'a pas été vérifiée de manière exhaustive.

### 3.2 Distribution des labels

| Label | Nombre | Pourcentage |
|---|---:|---:|
| AFFIRMATION | 127 | 21,2 % |
| OPINION | 203 | 33,8 % |
| AUTRE | 270 | 45,0 % |
| **Total** | **600** | **100 %** |

### 3.3 Distribution linguistique

| Langue déclarée | Nombre | Pourcentage |
|---|---:|---:|
| Tunisien (`tn`) | 565 | 94,2 % |
| Français (`fr`) | 20 | 3,3 % |
| Arabe (`ar`) | 15 | 2,5 % |
| **Total** | **600** | **100 %** |

### 3.4 Distribution des écritures

| Écriture déclarée | Nombre | Pourcentage |
|---|---:|---:|
| Latin | 560 | 93,3 % |
| Mixte | 20 | 3,3 % |
| Arabe | 15 | 2,5 % |
| Arabizi | 5 | 0,8 % |
| **Total** | **600** | **100 %** |

Les pourcentages sont arrondis indépendamment.

Les catégories de langue et d'écriture sont distinctes. Un texte tunisien en caractères latins n'est pas automatiquement enregistré comme Arabizi.

Ces valeurs correspondent aux métadonnées auditées, sans validation linguistique manuelle exhaustive.

### 3.5 Structure et qualité

Les 600 enregistrements possèdent les champs :

`id`, `text`, `lang`, `script`, `source`, `url`, `date`, `decision`, `label`, `origine_annotation`, `statut_annotation`, `remarque`.

L'audit structurel a confirmé :

- 600 enregistrements JSONL lisibles.
- Aucun JSON invalide.
- Aucun doublon d'identifiant `id`.

La présence des champs ne garantit pas l'exactitude ou la complétude de toutes leurs valeurs.

## 4. Corpus NLI — 300 paires

**Fichier de référence :** `data/annotations/nli_corpus_300_consolide_v4_prive.jsonl`

### 4.1 Distribution des relations

| Relation | Nombre | Pourcentage |
|---|---:|---:|
| supports | 152 | 50,7 % |
| refutes | 83 | 27,7 % |
| neutral | 65 | 21,7 % |
| **Total** | **300** | **100 %** |

Les pourcentages sont arrondis indépendamment et peuvent donc totaliser 100,1 %.

### 4.2 Distribution linguistique

| Langue | Claims | Evidences |
|---|---:|---:|
| Français | 112 | 107 |
| Arabe | 188 | 193 |
| **Total** | **300** | **300** |

Ces données ne permettent pas, à elles seules, de déterminer le nombre de paires bilingues.

### 4.3 Structure et identifiants

Les champs suivants sont présents :

`pair_id`, `claim_id`, `claim`, `claim_lang`, `evidence_id`, `evidence`, `evidence_lang`, `label`, `annotateur`, `remarque`.

Résultats de l'audit :

- 300 enregistrements JSONL valides.
- Aucun doublon de `pair_id`.
- 259 `claim_id` distincts.
- 290 `evidence_id` distincts.
- 21 `claim_id` apparaissant dans plusieurs paires.

La répétition d'un `claim_id` peut être légitime lorsqu'une affirmation est associée à plusieurs preuves.

### 4.4 Cohérence des identifiants — P266/P267

Les paires P266 et P267 partagent le même `claim_id` et le même `evidence_id`, mais leurs textes de claim ne sont pas strictement identiques.

Leurs relations enregistrées sont respectivement supports et refutes.

Une validation humaine spécifique est documentée dans `data/annotations/nli_P266_P267_nawaat_valides_v1_prive.jsonl`.

L'audit met en évidence une **incohérence potentielle de réutilisation d'identifiant**, sans démontrer une erreur sémantique des relations.

Aucune correction automatique n'est recommandée avant clarification humaine.

### 4.5 Partitions NLI

**Fichier :** `data/splits/nli_v3_by_article_seed42.json`

| Affectation | Nombre |
|---|---:|
| Train | 174 |
| Validation | 33 |
| Test | 56 |
| **Total des paires actives** | **263** |
| Exclusions documentées | 37 |
| **Total du corpus** | **300** |

Les contrôles ont confirmé :

- La validité des identifiants de paires présents dans le fichier de partition.
- La disjonction des ensembles train, validation et test.
- L'absence de partage des `claim_id` et `evidence_id` entre ces trois ensembles.
- La couverture des 300 paires par une affectation ou une exclusion.
- L'exclusion de P266 et P267.

Ces contrôles concernent les identifiants. Ils ne constituent pas une preuve d'absence de fuite textuelle ou sémantique.

### 4.6 Distinction avec le Lot C

Le fichier `data/splits/claim_detection_multiclass_600_seed42.json` est documenté comme split du corpus `data/processed/claim_detection_600.jsonl`, utilisé par le Model 1 du Lot C.

Ses 120 identifiants de test ne correspondent à aucun identifiant du corpus A1 final audité.

Il ne peut donc pas être présenté comme une partition validée de ce corpus A1.

L'absence de correspondance des identifiants ne démontre pas l'indépendance des contenus textuels.

## 5. Double annotation et accord humain

### 5.1 Méthodologie

Ghofran et Achref ont annoté indépendamment 100 textes communs.

Les annotations initiales ont été conservées pour calculer l'accord avant arbitrage.

**Référence :** `docs/rapport_bronze_a1_ghofran_achref_2026-11-14.md`

### 5.2 Accord initial

| Indicateur | Résultat |
|---|---:|
| Textes comparés | 100 |
| Accords initiaux | 69 |
| Désaccords initiaux | 31 |
| Accord observé | 69,00 % |
| Accord attendu | 52,45 % |
| Cohen's Kappa | 0,3481 |

Le Kappa indique un accord limité au-delà du hasard. Il doit être interprété en tenant compte du déséquilibre des classes.

Les labels arbitrés ne constituent pas une seconde annotation indépendante et ne doivent pas servir à remplacer le Kappa initial.

### 5.3 Matrice de confusion initiale

Lignes : Ghofran. Colonnes : Achref.

| Ghofran / Achref | AFFIRMATION | OPINION | AUTRE |
|---|---:|---:|---:|
| AFFIRMATION | 1 | 0 | 0 |
| OPINION | 2 | 17 | 9 |
| AUTRE | 2 | 18 | 51 |

### 5.4 Arbitrage et annotations finales

Les 31 désaccords initiaux ont été examinés par arbitrage humain.

La consolidation technique a produit :

| Label final | Nombre |
|---|---:|
| AFFIRMATION | 8 |
| OPINION | 33 |
| AUTRE | 59 |
| **Total** | **100** |

Ces résultats concernent exclusivement le sous-ensemble doublement annoté de 100 textes, et non la distribution des 600 phrases A1.

Parmi les 31 désaccords initiaux, 27 concernent OPINION et AUTRE.

La comparaison de ces 27 cas avec le corpus consolidé de 540 annotations a relevé 13 concordances et 14 divergences.

Cette analyse porte sur des cas sélectionnés pour leurs difficultés ; elle n'est pas généralisable à l'ensemble du corpus.

### 5.5 Correction documentée

Le cas `tarc-forum-0289` a fait l'objet d'une correction du texte source et d'une révision documentée du label final vers OPINION.

**Historique :** `data/annotations/a1_historique_revision_0289_prive.csv`

### 5.6 Propositions non appliquées

| Identifiant | Label actuel | Label proposé |
|---|---|---|
| tarc-forum-0054 | AUTRE | OPINION |
| tarc-forum-0066 | AUTRE | AFFIRMATION |
| tarc-forum-0462 | AUTRE | OPINION |

Ces trois propositions restent soumises à validation humaine explicite.

Elles n'ont pas été appliquées au corpus final.

**Bilan :** consolidation technique Bronze terminée et audit PASS ; validation scientifique collective encore en attente.

## 6. Guide d'annotation

**Document :** `docs/annotation_guide_v1.1.md`

Le guide décrit les catégories AFFIRMATION, OPINION et AUTRE, les critères de décision, les cas ambigus, la double annotation et l'arbitrage.

Il a servi de référence lors de la revue qualitative Bronze.

**Statut :** proposition v1.1, en attente de validation définitive par l'équipe.

Les évolutions futures doivent être versionnées pour conserver la traçabilité des décisions.

## 7. Contrôles techniques

### 7.1 Contrôles antérieurs — 07/11/2026

La Data Card v0.2 documentait les contrôles suivants pour les corpus A1 et NLI :

- Validité JSON.
- Unicité des identifiants principaux.
- Présence des champs requis.
- Conformité des labels aux catégories attendues.
- Conformité des codes linguistiques aux règles utilisées.

Ces résultats appartiennent à l'audit Bronze antérieur.

### 7.2 Contrôles Silver

Les vérifications effectuées lors de la préparation Silver ont confirmé :

| Contrôle | Résultat |
|---|---|
| JSONL A1 | 600 valides |
| JSONL NLI | 300 valides |
| Doublons d'identifiants principaux | Aucun |
| Distributions A1 des labels | Vérifiées |
| Métadonnées linguistiques A1 | Distributions vérifiées |
| Métadonnées des écritures A1 | Distributions vérifiées |
| Distributions NLI | Vérifiées |
| Partitions NLI | 263 affectées, 37 exclues |
| Partage des `claim_id` entre splits actifs | Aucun |
| Partage des `evidence_id` entre splits actifs | Aucun |
| Cohérence P266/P267 | Point de vigilance documenté |
| Split Model 1 appliqué au corpus A1 | Incompatible au niveau des identifiants |

Ces résultats ne constituent pas une validation sémantique exhaustive.

### 7.3 Contrôles restant nécessaires

- Détection exhaustive des doublons textuels et quasi-doublons.
- Recherche des fuites textuelles et sémantiques entre partitions.
- Vérification individuelle des preuves et relations NLI.
- Vérification de la provenance de chaque enregistrement.
- Vérification des droits de réutilisation et de redistribution.
- Revue scientifique indépendante des décisions d'annotation.

### 7.4 Reproductibilité

Les fichiers de référence et les statistiques des contrôles sont documentés.

Pour figer une version scientifique reproductible, il reste à confirmer la disponibilité d'un manifeste précisant les versions, les empreintes des corpus, les paramètres des partitions et les scripts de validation.

L'existence d'un tel manifeste complet n'a pas été établie pendant cet audit.

## 8. Sources et traçabilité

### 8.1 Sources A1

La documentation identifie 570 phrases TArC issues de `forum.tab` et 30 entrées Tunifact, dont 15 originales et 15 reformulées.

Le rapport linguistique TArC consulté documente un sous-ensemble historique de 30 phrases.

Il ne constitue pas une vérification individuelle de provenance de l'ensemble des 570 phrases.

### 8.2 Métadonnées

Les champs `source`, `url`, `date`, `origine_annotation` et `statut_annotation` sont présents dans le corpus A1.

Leur présence ne garantit pas l'exactitude des valeurs enregistrées.

La distinction entre textes originaux et reformulations doit être préservée.

### 8.3 TunSwitch

Un rapport de qualité existe pour des candidats TunSwitch.

Leur provenance individuelle et leurs conditions de redistribution nécessitent des vérifications.

Les documents examinés ne démontrent pas leur intégration dans le corpus A1 final de 600 phrases.

### 8.4 Traçabilité des arbitrages

Les annotations indépendantes, les décisions d'arbitrage, les corrections appliquées et les propositions non appliquées doivent rester distinguables.

Les fichiers d'historique et de propositions Bronze assurent une partie de cette traçabilité.

## 9. Licences et confidentialité

Les conditions d'utilisation des contenus TArC et Tunifact doivent être examinées séparément.

La documentation existante mentionne une licence CC BY-NC-SA 4.0 associée à TArC. Son applicabilité exacte à la version des données utilisée doit être confirmée.

Aucun droit général de redistribution des contenus Tunifact n'est présumé.

Les reformulations ne sont pas automatiquement libres de restrictions.

Les corpus et fichiers d'annotation identifiés comme privés ne doivent pas être publiés intégralement sans vérification des droits, contrôle des éventuelles données personnelles et autorisation de l'équipe.

La publication de statistiques agrégées et de méthodes doit être distinguée de la diffusion des textes sources.

**Cette Data Card ne constitue pas une autorisation de redistribution des données.**

## 10. Limites

### 10.1 Représentativité

Le corpus A1 est déséquilibré entre les classes et fortement concentré sur les textes tunisiens.

Les métadonnées montrent également une prédominance de l'écriture latine.

Le corpus NLI présente un déséquilibre entre ses relations.

Ces caractéristiques limitent les conclusions pouvant être généralisées à d'autres langues, sources ou domaines.

### 10.2 Accord humain

Le sous-ensemble doublement annoté comprend 100 textes.

Le Cohen's Kappa initial de 0,3481 montre un accord limité au-delà du hasard.

L'arbitrage des 31 désaccords a été documenté, mais trois propositions de révision et le guide v1.1 restent soumis à validation.

### 10.3 Validité sémantique

La conformité structurelle ne garantit pas la véracité des affirmations, la pertinence des preuves ou la justesse des relations NLI.

La réutilisation de l'identifiant de claim pour P266/P267 reste à clarifier.

### 10.4 Partitions

Les contrôles NLI portent sur les identifiants.

L'absence de fuite textuelle ou sémantique n'est pas démontrée.

Aucun split compatible du corpus A1 final n'a été validé dans le périmètre de cet audit.

### 10.5 Provenance et droits

La provenance individuelle exhaustive, les licences applicables et les droits de redistribution ne sont pas encore confirmés.

Ces limites doivent être conservées dans toute version diffusée.

## 11. Prochaines étapes

### Validation humaine

1. Obtenir la revue du rapport Bronze A1 par l'équipe.
2. Valider ou rejeter les trois propositions de révision.
3. Confirmer le guide d'annotation v1.1.
4. Clarifier la politique d'identification des claims pour P266/P267.

### Qualité scientifique

5. Contrôler les doublons textuels et quasi-doublons.
6. Compléter la validation sémantique NLI.
7. Rechercher les fuites potentielles entre partitions au niveau du contenu.
8. Vérifier la provenance individuelle des textes.

### Conformité et reproductibilité

9. Vérifier les licences et les droits de redistribution.
10. Confirmer les règles de confidentialité.
11. Préparer ou vérifier le manifeste de versions et d'empreintes.
12. Clarifier les correspondances éventuelles entre les corpus A1 et Lot C.

### Livrables Silver

13. Faire valider cette Data Card.
14. Rédiger la section Données du rapport scientifique.
15. Vérifier la cohérence entre les deux livrables et les résultats Bronze.
16. Préparer une PR documentaire isolée après autorisation.

## 12. Historique des versions

| Version | Date | Description | Statut |
|---|---|---|---|
| v0.1 | Historique | Pilote de 60 phrases | Historique |
| v0.2 | 07/11/2026 | Corpus A1 et NLI, double annotation, contrôles structurels | Proposition Bronze |
| v1.0 Silver | 15/11/2026 | Résultats Bronze consolidés, audits Silver, partitions, traçabilité et limites | Proposition pour revue |

### Références internes principales

**Corpus et partitions**

- `data/annotations/corpus_a1_600_humain_final_prive.jsonl`
- `data/annotations/nli_corpus_300_consolide_v4_prive.jsonl`
- `data/splits/nli_v3_by_article_seed42.json`
- `data/splits/claim_detection_multiclass_600_seed42.json`

**Documentation A1**

- `docs/data_card_v0.2.md`
- `docs/annotation_guide_v1.1.md`
- `docs/rapport_bronze_a1_ghofran_achref_2026-11-14.md`
- `data/annotations/README_corpus_a1_600.md`
- `data/annotations/tarc_rapport_linguistique.md`
- `data/annotations/tunswitch_rapport_qualite.md`

**Documentation Model 1**

- `docs/model1_reproducibility.md`
- `docs/model1_claim_detection_detailed_report.md`
- `docs/lot-c_error_analysis.md`

### Conclusion scientifique

Le Lot A1 dispose de deux corpus structurés totalisant 900 enregistrements : 600 phrases de classification et 300 paires NLI.

Les audits ont confirmé la validité JSONL, l'unicité des identifiants principaux et les distributions documentées. Les partitions NLI ont été contrôlées au niveau des identifiants.

La consolidation Bronze de 100 annotations humaines est documentée, avec 31 désaccords arbitrés et un Cohen's Kappa initial de 0,3481.

Ces résultats constituent une base pour les livrables Silver.

Les validations sémantiques, documentaires, juridiques et collectives encore nécessaires sont explicitement identifiées.

**Conclusion : Data Card Silver v1.0 proposée pour revue scientifique. Validation définitive non acquise.**