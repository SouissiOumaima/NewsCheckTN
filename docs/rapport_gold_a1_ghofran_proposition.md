# NewsCheck TN — Rapport scientifique Gold A1 (proposition)

**Responsable :** Ghofran Maaoui
**Date :** 21 novembre 2026
**Statut :** Brouillon scientifique — non valide collectivement

## 1. Resume executif

Ce rapport consolide les audits Gold A1 de couverture linguistique,
de robustesse et de separation des donnees NLI.

Les controles effectues indiquent :
- aucune fuite exacte detectee entre les partitions NLI ;
- une separation par article conforme aux identifiants reconstruits ;
- aucune paire explicitement etiquetee tunisienne dans le corpus NLI V6 ;
- aucune paire francais-vers-arabe dans le test officiel.

Ces constats ne constituent pas une mesure de performance des modeles.

## 2. Corpus et protocole

- Corpus NLI V6 : 300 paires.
- Train : 174 paires.
- Validation : 33 paires.
- Test : 56 paires.
- Brouillons exclus : 37 paires.
- Split : NLI V3, seed 42.
- SHA-256 corpus NLI V6 prive (300 paires) : `FBB13F118F4A2F3B604C86BA1729295BED5A6BEA4A7EDBF80262CF15835B7B29`.
- SHA-256 split NLI V3, seed 42 : `59582EB759DF4CD9E15F7A17D1DF7E85DFAE411717A111D52D536FC1C6C3552C`.
- SHA-256 corpus NLI V3 utilise pour la comparaison des labels : `5FA857BE810D568E6266641EADE1C0FFFE805E804D6E4A989BA0CA5B5CFC1099`.

Le split officiel est conserve sans modification.

## 3. Couverture linguistique

| Langues claim/evidence | Train | Validation | Test | Exclus |
|---|---:|---:|---:|---:|
| ar/ar | 117 | 3 | 31 | 37 |
| fr/fr | 54 | 28 | 25 | 0 |
| fr/ar | 3 | 2 | 0 | 0 |
| Total | 174 | 33 | 56 | 37 |

Aucune paire n'est explicitement etiquetee tunisienne dans V6.
Une etiquette `ar` ne permet toutefois pas d'exclure la presence
de dialecte tunisien non identifie.

Le test ne permet pas d'estimer une performance specifique au
transfert fr/ar ni au tunisien.

## 4. Distribution des labels du test

| Langues | supports | refutes | neutral | Total |
|---|---:|---:|---:|---:|
| ar/ar | 13 | 13 | 5 | 31 |
| fr/fr | 10 | 6 | 9 | 25 |
| Total | 23 | 19 | 14 | 56 |

Les trois classes sont presentes dans les deux groupes,
mais les effectifs restent faibles pour des conclusions fines.

## 5. Audit des fuites exactes

Aucun chevauchement entre train, validation et test pour :
- `claim_id` ;
- `evidence_id` ;
- texte normalise des claims ;
- texte normalise des evidences.

Des repetitions internes aux partitions existent.
L'independance statistique des paires n'est donc pas garantie.

Les paraphrases et recouvrements semantiques n'ont pas ete exclus
par ces controles exacts.

### 5.1. Protocole d'audit reproductible

Script : `scripts/audit_gold_a1_nli_v6.py` (ajoute dans la
presente PR ; commit `10057bc093f85492d739a409a1aa72a9f2505958`).

Fonctions de reference : `models/nli/data.py`, commit
`2795077df6cce466bec14be24adde89ee2e3e0e8`.

Normalisation exacte du Lot C :
`re.sub(r"\s+", " ", text).strip().lower()`.

Cette normalisation reduit les espaces, supprime les espaces
exterieurs et applique les minuscules. Elle n'applique pas NFKC.

Les controles sont realises par intersection d'ensembles
entre train, validation et test, pour chaque variable.

| Variable | Uniques train/val/test | Repetitions internes train/val/test | Chevauchements inter-partitions |
|---|---|---|---|
| claim_id | 151 / 25 / 47 | 23 / 8 / 9 | 0 |
| evidence_id | 166 / 32 / 56 | 8 / 1 / 0 | 0 |
| claim normalise | 151 / 25 / 47 | 23 / 8 / 9 | 0 |
| evidence normalisee | 157 / 23 / 48 | 17 / 10 / 8 | 0 |
| article_id reconstruit | 30 / 8 / 10 | 144 / 25 / 46 | 0 |

Commande de reproduction, depuis la racine du depot :

```powershell
python -B scripts/audit_gold_a1_nli_v6.py `
  --v6 "CHEMIN_LOCAL_PRIVE_V6.jsonl" `
  --v3 "CHEMIN_LOCAL_PRIVE_V3.jsonl" `
  --split "data/splits/nli_v3_by_article_seed42.json"
```

Remplacer les deux chemins prives par les copies locales correspondant
aux SHA-256 documentes. Le script ne publie aucune paire privee.
Execution locale de controle : `status=PASS`, code retour 0.

Les effectifs de repetitions sont des nombres de lignes
supplementaires par rapport aux valeurs distinctes ; ils
ne representent pas des paires de doublons independantes.

## 6. Separation par article

| Partition | Articles distincts |
|---|---:|
| Train | 30 |
| Validation | 8 |
| Test | 10 |

- Chevauchement d'identifiants d'article entre partitions : 0.
- Articles reserves au Lot D presents dans le test : 6/6.
- Articles reserves au Lot D dans train/validation : 0.

Les identifiants ont ete reconstruits ; aucun `article_id`
explicite n'etait renseigne dans les 263 paires actives.

La fonction `article_id()` du Lot C applique, dans cet ordre :
1. `article_id` explicite s'il existe (0/300 dans V6) ;
2. regex `tunifact-(\d+)` dans `evidence_id` (259/300) ;
3. regex `tunifact\.org/articles/(\d+)` dans `remarque` (3/300) ;
4. premiere URL presente dans `remarque`, sans slash final
   et en minuscules (38/300) ;
5. identifiant `inconnu:` de secours (0/300).

Ces comptes couvrent les 300 paires, y compris les 37 brouillons.
La reconstruction permet de grouper les sources, mais ne certifie
pas l'existence en ligne ou la validite editoriale des articles.

## 7. Provenance et identifiants reconstruits

Sur les 300 paires, brouillons exclus compris :
- Tunifact via `evidence_id` : 259 ;
- Tunifact via `remarque` : 3 ;
- URL via `remarque` : 38 ;
- identifiant de secours `inconnu:` : 0.

Pour les 38 paires utilisant une URL :
- 11 URL distinctes ;
- un domaine distinct ;
- aucun chemin vide ;
- les 38 URL possedent au moins deux segments de chemin.

La structure des URL ne prouve pas la validite de leur provenance
ni leur correspondance reelle a des articles distincts.

## 8. Limites scientifiques

- Absence de sous-ensemble tunisien explicitement annote en NLI.
- Absence de paires fr/ar dans le test.
- Faible taille des sous-groupes linguistiques.
- Repetitions internes de claims et d'evidences.
- Provenance des articles non verifiee manuellement de bout en bout.
- Absence de test de similarite semantique inter-partitions.
- Aucune performance de modele mesuree dans ce rapport.

### 8.1. Risques de raccourcis linguistiques A1

Les audits anterieurs du corpus humain A1 de 540 elements
ont mis en evidence des caracteristiques de longueur et
de ponctuation susceptibles d'etre correlees aux labels.

Ces associations constituent un risque de raccourcis
statistiques pour la detection des affirmations.
Elles ne prouvent pas qu'un modele utilise ces raccourcis.

Recommandation : evaluer separement les textes courts,
les textes fortement ponctues et les sous-groupes
linguistiques, avec des effectifs documentes.

### 8.2. Historique des labels et reproductibilite

La reconciliation des deux versions historiques du
corpus A1 de 600 elements a identifie 199 differences
de labels entre la version historique et la version finale.

Les identifiants et textes correspondants doivent etre
maintenus dans leur contexte de version.

Les evaluations effectuees avec les anciennes etiquettes
ne doivent pas etre attribuees automatiquement aux
etiquettes finales.

Aucun corpus ni split n'est modifie par ce constat.

### 8.3. Versions NLI V3/V6 et experience EXP-C-011

La comparaison par `pair_id` des deux corpus NLI de 300 paires
montre 300 identifiants communs, 0 difference de claim,
0 difference d'evidence et 0 difference de langue.

Un seul label change entre V3 et V6 :
- partition validation : `neutral` (V3) vers `refutes` (V6) ;
- train : 0 changement ;
- test : 0 changement ;
- brouillons exclus : 0 changement.

Les labels du test sont identiques dans les deux versions :
23 `supports`, 19 `refutes` et 14 `neutral`.

L'experience Silver `EXP-C-011` du Lot C documente une
evaluation sur les donnees V3, avec split V3 seed 42.
Reference : `models/nli/measure_test.py`, commit `01074c9`.

La copie intermediaire privee V3 du Lot C n'a pas ete retrouvee
lors de ce controle. Les performances documentees de
`EXP-C-011` ne sont pas attribuees au corpus V6.
Aucune nouvelle evaluation de modele sur V6 n'est revendiquee.

Cette difference NLI V3/V6 est distincte des 199 differences
historiques mentionnees plus haut pour le corpus A1 de 600 textes.

## 9. Recommandations pour les lots C/D

1. Conserver les partitions gelees pour les evaluations officielles.
2. Rapporter les performances par langue et par classe lorsqu'elles
   sont effectivement mesurees, avec les effectifs correspondants.
3. Ne pas presenter le test actuel comme une evaluation du tunisien
   ou du transfert fr/ar.
4. Prevoir un jeu tunisien distinct, annote et valide, pour tester
   ces capacites sans contaminer le test existant.
5. Verifier manuellement la provenance des articles avant toute
   affirmation plus forte sur l'absence de fuite.
6. Documenter les repetitions internes et la taille des groupes
   lors de l'interpretation des resultats.

7. Evaluer les risques de raccourcis statistiques
   associes aux textes courts et fortement ponctues.
   Rapporter les performances par sous-groupe lorsque
   des predictions de modele seront disponibles.

8. Tracer la version des labels A1 utilisee pour chaque
   evaluation. Les 199 differences entre corpus historique
   et final interdisent de transposer automatiquement
   les resultats d'une version vers une autre.

9. Accompagner les metriques des effectifs et, lorsque
   possible, d'intervalles d'incertitude tenant compte
   du regroupement par article. Ne pas surestimer
   les conclusions sur de petits sous-groupes.

10. Verifier la provenance et la correspondance
    article par article des 11 URL distinctes
    utilisees dans la reconstruction des identifiants.
    Ne pas publier les donnees privees.


## 10. Statut et references

Document de travail Gold A1, non approuve et non gele.

References documentaires Silver :
- [rapport_silver_a1_ghofran_2026-11-20_nli_v6_proposition.md](https://github.com/SouissiOumaima/NewsCheckTN/blob/07d05e5/docs/rapport_silver_a1_ghofran_2026-11-20_nli_v6_proposition.md)
- [data_card_v1.2_silver_consolidee_proposition.md](https://github.com/SouissiOumaima/NewsCheckTN/blob/d1eb551/docs/data_card_v1.2_silver_consolidee_proposition.md)
- [manifeste_reproductibilite_silver_a1_v1.1_proposition.md](https://github.com/SouissiOumaima/NewsCheckTN/blob/d1eb551/docs/manifeste_reproductibilite_silver_a1_v1.1_proposition.md)

Les arbitrages Silver A1 `0066` et `0071` restent soumis
a validation collective.

Les resultats Gold sont des audits de donnees et de protocole :
ils ne remplacent pas une evaluation experimentale des modeles.
