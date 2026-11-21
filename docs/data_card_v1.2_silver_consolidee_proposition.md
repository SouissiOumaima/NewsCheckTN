# Actualisation scientifique — Silver A1

**Version :** 1.2 consolidée — Proposition pour validation collective

Ce complément actualise les informations historiques de la
Data Card ci-dessous. Il ne remplace aucun corpus officiel.

## Corpus NLI V6

- 300 paires : 152 supports, 84 refutes, 64 neutral.
- Split v3, seed 42.
- Train : 174 paires (85/53/36).
- Validation : 33 paires (11/10/12).
- Test : 56 paires (23/19/14).
- Exclusions documentées : 37 paires (33/2/2).
- Total affecté aux splits : 263 paires.
- NLI-P035 : correction neutral vers refutes prise en compte.
- 34 rattachements techniques contrôlés.
- Aucun chevauchement d'articles détecté entre splits.
- Absence globale de fuite sémantique non démontrée.
- Cas linguistiques 0184 et 0220 : non appliqués.

Les distributions entre parenthèses sont dans l'ordre
supports / refutes / neutral.

## Arbitrages A1

- 31 désaccords documentés dans un registre de travail.
- 16 corrections dans une copie synchronisée vérifiée.
- Aucun remplacement automatique du corpus original.
- Comparaison historique sur 27 cas : 13 concordances
  et 14 divergences.
- Comparaison historique S3 sur 31 cas (version et methode a reconcilier) :
  13 concordances et 18 divergences.
- Les deux comparaisons portent sur des périmètres différents.
- P0289 : texte lisible et OPINION dans le corpus consolidé ;
  correction du fichier historique non démontrée.
- P0462 : décision humaine finale à confirmer.
- Reconciliation actuelle du 21/11/2026 : 22 concordances
  et 9 divergences entre les 31 arbitrages documentes et
  le corpus A1 600 actuellement utilise.
- Divergences : tarc-forum-0497, tarc-forum-0462,
  tarc-forum-0066, tarc-forum-0353, tarc-forum-0054,
  tarc-forum-0289, tarc-forum-0210, tarc-forum-0035,
  tarc-forum-0145.
- Les 18 divergences de l'audit historique S3 ne sont pas
  le bilan de la comparaison actuelle. Leur difference
  avec les 9 divergences reste a expliquer.
- Une divergence technique ne constitue pas a elle seule
  une decision humaine manquante ou une correction approuvee.
- Les decisions necessitant confirmation humaine restent
  ouvertes. Aucun label officiel n'a ete remplace.
- SHA-256 registre : 497CF0E1023540C51EC47E86C782B709696EC1C51A3E3369C988481CEDFAC80A
- SHA-256 corpus humain 540 : 965DBE80FABD724258CE7417CE233296C6A2BB459D4CDD36A12A6B3CB1DA83C5
- SHA-256 corpus A1 600 : 5741A6E84459772DE84930C5493786DFB5F065E0F50EE43026F64F22D81443FF
- Les propositions 0054, 0066 et 0462 ne sont pas
  considérées comme validées.

## Reproductibilité et limites

- Six empreintes SHA-256 vérifiées dans l'audit S3.
- Hashes à actualiser uniquement après approbation.
- Source primaire P266/P267 non vérifiée directement.
- Redistribution publique non autorisée à ce stade.
- Respecter les droits propres à chaque corpus source.
- Validation scientifique collective encore nécessaire.

---

**Document de base :** `docs/data_card_v1.1_silver_nli_v6_proposition.md` (proposition en attente de validation collective).

## Clarifications par rapport a la v1.1

Les formulations suivantes precisent les passages correspondants de la Data Card v1.1 :

- **Arbitrages :** Les 31 désaccords initiaux disposent de décisions documentées dans un registre de travail ; leur validation humaine finale reste à confirmer.
- **Cas P0289 :** Pour `tarc-forum-0289`, le corpus consolidé contient un texte lisible et le label OPINION ; le fichier historique contient encore #NOM? et sa correction directe n'est pas établie. Une reconfirmation humaine reste nécessaire.
- **Accord humain :** La consolidation Bronze de 100 annotations humaines est documentée, avec 31 désaccords documentés (validation finale à confirmer) et un Cohen's Kappa initial rapporté de 0,3481.

---


## Actualisation — Validation Achref du 20 novembre 2026

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

## Réconciliation des partitions A1 600

**Statut :** audit technique documenté ; validation
scientifique collective encore nécessaire.

La comparaison R3-07 confirme que les partitions Silver A1
(train 420, validation 90, test 90) correspondent exactement
au corpus historique A1 600 pour les identifiants, les textes
et les labels.

| Partition | Différences avec l'historique | Différences avec le corpus humain final |
|---|---:|---:|
| Train (420) | 0 | 137 |
| Validation (90) | 0 | 29 |
| Test (90) | 0 | 33 |
| **Total (600)** | **0** | **199** |

Les deux corpus contiennent les mêmes 600 identifiants
et les mêmes textes, mais 199 labels diffèrent.

- Corpus historique :
  `corpus_a1_600_consolide_prive.jsonl`
- SHA-256 historique :
  `5741A6E84459772DE84930C5493786DFB5F065E0F50EE43026F64F22D81443FF`
- Corpus humain final :
  `corpus_a1_600_humain_final_prive.jsonl`
- SHA-256 de la version humaine finale :
  `EA1BE0FB16D35611B6CD753FB6DA02CF299DA1E1E4D4E88F55C5284EB2549200`

Cette correspondance explique les divergences techniques
précédemment observées dans les partitions Silver.

Elle ne prouve pas l'origine du processus de création
des partitions ni la validation scientifique des changements
de labels.

**Précaution :** ne pas présenter les évaluations
effectuées avec les anciens labels comme des évaluations
sur les nouveaux labels sans nouvelle validation.

Aucun corpus, label ou split historique n'a été modifié.
