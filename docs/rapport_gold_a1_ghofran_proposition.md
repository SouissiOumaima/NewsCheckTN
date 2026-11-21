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
- Verification SHA-256 du split et du corpus : conforme aux references auditees.

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
- [data_card_v1.2_silver_consolidee_proposition.md](https://github.com/SouissiOumaima/NewsCheckTN/blob/07d05e5/docs/data_card_v1.2_silver_consolidee_proposition.md)
- [manifeste_reproductibilite_silver_a1_v1.1_proposition.md](https://github.com/SouissiOumaima/NewsCheckTN/blob/07d05e5/docs/manifeste_reproductibilite_silver_a1_v1.1_proposition.md)

Les arbitrages Silver A1 `0066` et `0071` restent soumis
a validation collective.

Les resultats Gold sont des audits de donnees et de protocole :
ils ne remplacent pas une evaluation experimentale des modeles.
