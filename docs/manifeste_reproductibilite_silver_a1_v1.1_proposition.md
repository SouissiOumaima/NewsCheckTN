# NewsCheck TN — Manifeste de reproductibilité Silver A1

**Version :** 1.1 — Proposition  
**Date :** 20/11/2026  
**Statut :** Proposition documentaire — en attente de revue scientifique  
**Périmètre :** Lot A1 — classification et NLI

## 1. Objectif

Ce manifeste centralise les références des fichiers utilisés dans
la préparation Silver, leurs empreintes SHA-256 disponibles,
les paramètres connus et les limites de reproductibilité.

Les 12 références SHA-256 recensées dans ce manifeste ont été vérifiées sur leurs chemins canoniques le 15/11/2026 : 12/12 conformes, aucune référence absente et aucune divergence.

## 2. Corpus A1 — annotations humaines

| Fichier | SHA-256 |
|---|---|
| a1_540_a_annoter.json | `243797B15BE42477688A1290C9890C71B658C0067699B4EAF64777C1DBED4C41` |
| a1_annotation_independante_540_prive.csv | `84D48392ACB196BF6E9CF043D44523155EC88CD90C207E1FDD28C3E1C4E8CB2E` |
| a1_humain_540_consolide_prive.csv | `965DBE80FABD724258CE7417CE233296C6A2BB459D4CDD36A12A6B3CB1DA83C5` |
| a1_validation_humaine_540_prive.csv | `7FD863A9A2D137066980660402FA0661F14BC0ACFA094EEDA56F8634EEC3307E` |

Le corpus A1 de référence comprend 600 phrases :
570 phrases TArC et 30 entrées Tunifact, dont 15 originales
et 15 reformulées.

Le sous-ensemble consolidé de 540 annotations humaines constitue
un artefact distinct du corpus complet de 600 phrases.

## 3. Double annotation et accord humain

| Fichier | SHA-256 |
|---|---|
| a1_double_annotation_ghofran_100_prive.csv | `F42547075D7F282E18C426793CB57E632C74234360C9A647B84B240D7BFE8CFE` |
| a1_double_annotation_achref_100_prive.csv | `25EC56DFADADC2F70C6AB6FFD625ED04D2189F1F61CE5E098766DFD3F5013789` |
| a1_annotations_finales_ghofran_achref_100_prive.csv | `497CD40F67C366707E269C541D0265D314D0E8C4599A0A2FA5C5218EB791CAAE` |

### Résultats initiaux

- Textes comparés : 100
- Accords : 69
- Désaccords : 31
- Accord observé : 0,69
- Accord attendu : 0,5245
- Cohen's Kappa : 0,3481

Le Kappa se rapporte aux annotations indépendantes initiales,
et non aux labels finaux après arbitrage.

Le cas tarc-forum-0289 était absent des deux fichiers
d'annotation indépendante. Sa restauration dans le corpus
consolidé de 540 ne constitue donc pas une modification
de ces deux fichiers de calcul.

### Traçabilité de l'arbitrage

Le fichier des annotations finales distingue :
- ACCORD_INITIAL : 69 cas.
- ARBITRAGE_HUMAIN : 31 cas.

La version finale consolidée doit être distinguée du fichier
de travail historique contenant l'ancienne valeur `#NOM?`
pour tarc-forum-0289.

Les trois propositions suivantes restent en attente :
- tarc-forum-0054
- tarc-forum-0066
- tarc-forum-0462

## 4. Corpus NLI

| Fichier | SHA-256 |
|---|---|
| nli_corpus_300_consolide_v4_prive.jsonl | `0AF15AAE3AD520C38DDBAACEA9B8281A20291FF133975E4349EF46C512C5F2F9` |

Le corpus de référence comprend 300 paires NLI.

Répartition documentée :
- supports : 152
- refutes : 83
- neutral : 65

Les cas P266/P267 font l'objet d'une vigilance particulière :
la cohérence des identifiants et la vérification de la source
primaire doivent rester documentées.

## 5. Partitions et paramètres

| Fichier | SHA-256 |
|---|---|
| nli_v3_by_article_seed42.json | `59582EB759DF4CD9E15F7A17D1DF7E85DFAE411717A111D52D536FC1C6C3552C` |
| claim_detection_multiclass_600_seed42.json | `9A25686286CCB3271CA98FE9B03046E2A0CB55CF6E5B7F43AB467669B5A8CEE0` |

Paramètre documenté : seed 42.

Pour le split NLI :
- 263 paires affectées.
- 37 paires exclues.
- Aucun partage des claim_id entre partitions actives.
- Aucun partage des evidence_id entre partitions actives.

Le split Model 1 n'est pas directement compatible avec
le corpus A1 au niveau des identifiants.

## 6. Documents scientifiques

| Document | SHA-256 |
|---|---|
| docs/data_card_v1.0_silver.md | `2D19D84030A0E292691D18E05BF5C1DC14586F461C5FD4B669869D47C6C50AE0` |
| docs/rapport_silver_a1_ghofran_2026-11-15.md | `497C6CDBBC4023C95CE477B33DC98F4B775B756574634DDED486F9B9BA4D1B8B` |

## 7. Contrôles déjà documentés

- Validité structurelle des corpus A1 et NLI.
- Unicité des identifiants principaux.
- Vérification des distributions de labels.
- Vérification des métadonnées linguistiques.
- Contrôle des identifiants entre partitions NLI.
- Analyse des répétitions internes.
- Recherche de répétitions normalisées entre partitions.
- Recherche de quasi-doublons au seuil 0,80.
- Inventaire des fichiers de provenance et de licences.
- Traçabilité des 31 arbitrages et de la correction 0289.

Ces contrôles ne constituent pas une validation sémantique exhaustive.

## 8. Limites et points à confirmer

1. Vérification individuelle de la provenance des textes.
2. Confirmation des droits de réutilisation et de redistribution.
3. Confirmation des règles de confidentialité.
4. Contrôle SHA-256 des 12 références : effectué le 15/11/2026 (12/12 PASS). La confirmation des versions logicielles et des scripts de génération reste à réaliser.
5. Conservation des scripts exacts de génération des partitions.
6. Vérification sémantique des relations NLI.
7. Revue scientifique des trois propositions A1.
8. Clarification des cas P266/P267.
9. Clarification de la correspondance entre A1 et Lot C.

Aucune licence générale de redistribution n'est présumée.

Les fichiers privés ne doivent pas être publiés sans autorisation
et vérification des droits applicables.

## 9. Statut scientifique

Ce manifeste est une proposition de documentation Silver.

Le contrôle SHA-256 confirme l'intégrité des 12 fichiers vérifiés, sans établir à lui seul la reproductibilité de leur génération.

Les éléments non confirmés sont explicitement conservés comme limites.

**Statut final : en attente de revue scientifique et validation collective.**

---

## Actualisation Silver A1 — S3

Date : 2026-11-20
Statut : PROPOSITION — approbation collective en attente.

### Corpus NLI officiel

- Version de reference actuelle : V6.
- 300 paires : 152 supports, 84 refutes, 64 neutral.
- Split v3, seed 42.
- Train : 174 ; validation : 33 ; test : 56.
- Exclusions documentees : 37.
- Ancienne reference V4 conservee dans l'historique.

SHA-256 V6 :
fbb13f118f4a2f3b604c86ba1729295bed5a6bea4a7edbf80262cf15835b7b29

### Controle de reproductibilite

Manifeste JSON :
`manifest_silver_a1_provisoire_v1.json` (artefact prive hors depot, non inclus dans la livraison ; empreintes verifiees localement)

- 6 fichiers verifies.
- 6 empreintes SHA-256 conformes.
- Aucune anomalie d'integrite.
- Aucun chevauchement d'article detecte entre splits.
- Reproductibilite complete de generation non encore demontree.

### Corpus A1

- 600 enregistrements dans le corpus original.
- 16 corrections dans une copie de synchronisation verifiee.
- P0289 restaure, label OPINION.
- P0462 soumis a confirmation humaine.
- Corpus officiel original conserve.
- Empreintes a actualiser apres integration approuvee.

### Documentation associee

- Data Card v1.2 revue S3.
- Audit des droits Silver A1.
- Rapport des limites semantiques Silver A1.

### Restrictions

- Droits de redistribution non entierement confirmes.
- Donnees privees : diffusion restreinte.
- Validation scientifique collective en attente.

## Réconciliation A1 — 21 novembre 2026

Statut : proposition non validée.

- Arbitrages documentés : 31.
- Concordances actuelles : 22.
- Divergences actuelles : 9.
- Bilan historique S3 : conservé, à réconcilier.
- Corpus et annotations originaux : inchangés.

### Empreintes des références

Registre arbitrage A1 :
497CF0E1023540C51EC47E86C782B709696EC1C51A3E3369C988481CEDFAC80A

Corpus humain 540 :
965DBE80FABD724258CE7417CE233296C6A2BB459D4CDD36A12A6B3CB1DA83C5

Corpus A1 600 :
5741A6E84459772DE84930C5493786DFB5F065E0F50EE43026F64F22D81443FF

Data Card V1.2 candidate :
8CF9950722684DCA54D1C7A94515CCD744978C04AAB95067A5D4FA76DFFD7C49

Décisions ouvertes :
21606A7DFF3AC00B0C33FEB541B670B02D88CFD35FA720071AC047C22DA55BB0

Ces empreintes identifient des versions de travail.
Elles ne constituent pas un gel officiel.

## Actualisation — Validation Achref du 20 novembre 2026

- Validation individuelle : 16 accords, 1 accord sous
  reserve, 1 cas en revision.
- Source de validation : Achref Chabene, 20/11/2026.
- 0066 : AFFIRMATION sous reserve.
- 0071 : EN_REVISION, sans nouveau label.
- Gel collectif : NON EFFECTUE.

### Empreintes documentaires actualisees

- Data Card V1.2 : 8CF9950722684DCA54D1C7A94515CCD744978C04AAB95067A5D4FA76DFFD7C49
- Rapport Silver A1 : 46D7B303D14DD868447BC04D6C99E8FE483A7DC6A1014CCAA55EB2ED64241452
- Decisions ouvertes : D5F61988819A81F08430A4A4EA02345E24A4704D7144866874A414F88686406A
- CSV Achref normalise (prive) : A20B69DE199BA3DE35ADEE018F457848AC3F9F72ED06C7E277A9D9B1DF9D41E5
- CSV original Achref (prive) :
  B0E4F154508A482ECFB91B6697B1CD4C16335519616BB1E8B099341573004BE7

Les fichiers prives sont conserves hors depot Git.
Les donnees originales ne sont pas modifiees.

Note : les empreintes anterieures documentent des instantanes historiques ; la derniere empreinte des decisions ouvertes correspond a la version actuelle.
