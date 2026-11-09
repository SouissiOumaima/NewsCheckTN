# NewsCheck TN — Data Card

**Version :** 0.2 — Proposition Bronze
**Date :** 07/11/2026
**Projet :** NewsCheck TN
**Lot :** A1 — Données et annotations
**Statut :** Validation structurelle réalisée ; validation scientifique et arbitrage humain en cours.

## 1. Présentation

NewsCheck TN constitue un corpus multilingue pour l'analyse d'énoncés potentiellement vérifiables et l'inférence en langage naturel (NLI).

Les livrables documentés comprennent :

- Un corpus A1 de 600 phrases.
- Un corpus de 300 paires NLI.
- Un guide d'annotation v1.1.
- Une double annotation indépendante de 100 phrases.
- Une procédure d'arbitrage des désaccords.

Les annotations AFFIRMATION, OPINION et AUTRE ne déterminent pas la véracité des informations.

## 2. Corpus pilote historique

Le pilote initial comprend 60 phrases :

| Source | Nombre |
|---|---:|
| TArC | 30 |
| Tunifact | 30 |
| **Total** | **60** |

Distribution historique : 48 AFFIRMATION, 7 OPINION et 5 AUTRE.

Ces chiffres concernent uniquement le pilote initial et ne doivent pas être confondus avec les statistiques du corpus étendu.
### Provenance et statut de TunSwitch

Le dépôt contient un lot de préparation de **22 phrases candidates issues de TunSwitch**, en tunisien écrit en caractères arabes.

Les correspondances textuelles ont été vérifiées dans le fichier source local `TO_text.txt`. Le suivi de ces candidates est documenté dans `data/deliverables/equipe_a1_preparation/README.md` et `manifest_a1.json`.

**Statut de validation :**

- Provenance textuelle : correspondances vérifiées dans la source locale.
- Licence et conditions d'utilisation : à confirmer.
- Autorisation de redistribution : à confirmer.
- Admissibilité et intégration dans les jeux d'évaluation : à valider.

Ces 22 candidates ne doivent pas être présentées comme intégrées au corpus A1 final ou à `eval_100` sans vérification supplémentaire. Aucune redistribution des textes sources ne doit être effectuée avant confirmation des droits applicables.

## 3. Corpus A1 — 600 phrases

**Fichier de référence audité :** corpus A1 de 600 phrases, conservé dans un espace de travail privé hors dépôt.

### Distribution des labels

| Label | Nombre | Pourcentage |
|---|---:|---:|
| AFFIRMATION | 127 | 21,2 % |
| OPINION | 203 | 33,8 % |
| AUTRE | 270 | 45,0 % |
| **Total** | **600** | **100 %** |

### Distribution linguistique

| Langue | Nombre | Pourcentage |
|---|---:|---:|
| Tunisien (tn) | 565 | 94,2 % |
| Français (fr) | 20 | 3,3 % |
| Arabe (ar) | 15 | 2,5 % |

Le corpus présente une forte concentration de textes tunisiens. La répartition entre écritures arabe, latine et Arabizi reste à auditer à partir des métadonnées appropriées.

## 4. Corpus NLI — 300 paires

**Fichier de référence audité :** corpus NLI consolidé de 300 paires, conservé dans un espace de travail privé hors dépôt.

### Relations NLI

| Relation | Nombre | Pourcentage |
|---|---:|---:|
| supports | 152 | 50,7 % |
| refutes | 83 | 27,7 % |
| neutral | 65 | 21,7 % |
| **Total** | **300** | **100 %** |

### Distribution linguistique

| Langue | Claims | Evidences |
|---|---:|---:|
| Français | 112 | 107 |
| Arabe | 188 | 193 |
| **Total** | **300** | **300** |

La validité sémantique des relations NLI nécessite une vérification distincte de la validation structurelle.

## 5. Double annotation et accord humain

Une double annotation indépendante a été réalisée sur 100 phrases communes par Ghofran et Achref.

### 5.1. Accord inter-annotateurs initial

| Indicateur | Résultat |
|---|---:|
| Phrases comparées | 100 |
| Accords | 69 |
| Désaccords | 31 |
| Accord observé | 69 % |
| Cohen's Kappa | ≈ 0,3481 |

Le coefficient de Cohen's Kappa mesure l'accord entre les deux annotateurs en tenant compte de l'accord attendu par hasard. Le calcul repose exclusivement sur les annotations initiales, avant toute relecture ou décision d'arbitrage.

Pour permettre la reproduction du résultat, il reste à joindre les marges par annotateur, la matrice de confusion, les valeurs Po et Pe, le script de calcul ainsi que la version ou l'empreinte des 100 enregistrements alignés, dans un espace autorisé.

Le Lot E signale 12 cas nécessitant une discussion selon le retour qui lui a été communiqué. La comparaison locale des 31 propositions avec les décisions de relecture d'Achref identifie, quant à elle, 7 divergences. Ces deux chiffres correspondent à des suivis dont les périmètres doivent être rapprochés avant toute conclusion.

Aucun label d'arbitrage final n'est considéré comme validé à ce stade.

### 5.2. Relecture des 31 désaccords

Les 31 désaccords initiaux ont fait l'objet d'une relecture humaine documentée dans le cadre de la Pull Request #18.

| Indicateur | Résultat |
|---|---:|
| Cas soumis à relecture | 31 |
| Concordances entre propositions et décisions d'Achref | 24 |
| Divergences restantes | 7 |
| Taux de concordance après relecture | 77,42 % |

**Origine et méthode de calcul des résultats 24/7 :**

Les résultats ont été recalculés localement à partir de deux sources :

- Le fichier privé de propositions de relecture, conservé hors dépôt public, contenant les colonnes `id` et `label_propose`.
- Le fichier sans textes `data/annotations/a1_relecture_achref_31_sans_textes.csv` de la PR #18, contenant notamment `id` et `decision_achref`.

Les deux jeux de données ont été associés par l'identifiant `id`, sans utiliser l'ordre des lignes.

Pour chacun des 31 identifiants, nous avons comparé `label_propose` à `decision_achref` après suppression des espaces en début et fin de valeur.

- **Concordance :** les deux labels sont identiques.
- **Divergence :** les deux labels sont différents.

Le recalcul effectué sur les 31 décisions donne 24 concordances et 7 divergences, soit un taux de concordance de 77,42 %.

Cette vérification est reproductible dans un environnement autorisé disposant des deux sources. Le CSV public seul ne permet pas de reproduire le résultat 24/7, car il ne contient pas `label_propose`.

Les décisions d'Achref sont des décisions de relecture et ne constituent pas un arbitrage final.

Ce taux représente uniquement la concordance entre les propositions de relecture et les décisions d'Achref. Il ne constitue ni un nouveau Kappa ni une mesure d'accord inter-annotateurs indépendante.

### 5.3. Arbitrage final

Les sept cas divergents nécessitent une validation humaine complémentaire, notamment pour les phrases mixtes, les référents ambigus et les propositions dont le caractère factuel dépend du contexte.

Les 24 cas concordants ne sont pas non plus considérés comme définitivement arbitrés tant que la procédure de validation n'est pas achevée.

Les annotations originales sont conservées séparément des propositions, des décisions de relecture et des futurs labels finaux.

**Statut : arbitrage final en attente de validation par l'équipe.**

## 6. Guide d'annotation

**Document :** `docs/annotation_guide_v1.1.md`

Le guide définit les trois catégories, les règles de décision, les cas ambigus, la double annotation et la méthode de calcul de Cohen's Kappa.

La version 1.1 reste une proposition en attente de validation par l'équipe.

## 7. Contrôles techniques

Les résultats ci-dessous sont rapportés par le Lot A1 pour son audit en lecture
seule du 07/11/2026. Les deux fichiers privés de référence ne sont pas présents
dans cette branche ; la relecture technique du Lot E ne reproduit donc pas cet audit.
Pour permettre sa reproduction dans un espace autorisé, joindre un manifeste
avec version ou empreinte SHA-256 des fichiers, schémas et champs contrôlés,
commande ou script utilisé et rapport de sortie, sans exposer les données privées.

| Contrôle | A1 | NLI |
|---|---:|---:|
| Enregistrements | 600 | 300 |
| JSON invalides | 0 | 0 |
| Identifiants dupliqués | 0 | 0 |
| Champs requis manquants | 0 | 0 |
| Labels non autorisés | 0 | 0 |
| Codes linguistiques non autorisés | 0 | 0 |

Ces résultats portent sur les contrôles exécutés le 07/11/2026.

Ils ne constituent pas une validation complète des contenus, des sources ou des relations sémantiques.

## 8. Sources et traçabilité

### 8.1. Origine des données

Le corpus pilote historique utilise notamment TArC et Tunifact.

Les corpus étendus peuvent comprendre des extraits originaux et des reformulations. Cette distinction doit être conservée dans les métadonnées lorsque l'information est disponible.

La provenance, les URL, les dates, les documents sources et les modalités d'annotation doivent être vérifiés avant toute affirmation de traçabilité complète.

### 8.2. Traçabilité des preuves NLI

Le corpus NLI comprend 300 paires claim–evidence, réparties entre les relations `supports`, `refutes` et `neutral`.

La validation structurelle des 300 enregistrements ne garantit pas que chaque preuve soit correctement reliée à un document source.

La vérification de la traçabilité doit notamment examiner :

- La présence des identifiants de preuves.
- La correspondance entre identifiants et contenus.
- La disponibilité des documents sources.
- La distinction entre preuves originales et reformulations.
- La cohérence entre chaque claim, sa preuve et sa relation NLI.

Une absence de correspondance documentaire stricte ne démontre pas, à elle seule, qu'une preuve est incorrecte ou inexistante.

### 8.3. Limites et validation

L'audit structurel a été réalisé séparément de l'évaluation scientifique des preuves.

La traçabilité documentaire complète et la validité sémantique des relations NLI restent à confirmer.

Aucune provenance non vérifiée ne doit être inventée.

**Statut : validation structurelle réalisée ; audit de provenance et validation sémantique en cours.**

## 9. Licences et confidentialité

### 9.1. Licences et droits de réutilisation

Les conditions de réutilisation de TArC et Tunifact doivent être vérifiées séparément.

La mention de la licence CC BY-NC-SA 4.0 pour TArC doit être confirmée sur la version exacte du corpus utilisée.

Si cette licence est applicable, elle impose notamment des obligations d'attribution, des restrictions d'utilisation commerciale et des conditions de partage des adaptations.

La référence officielle de la licence et les conditions de réutilisation doivent être documentées avant validation.

Aucun droit général de redistribution des contenus Tunifact n'est présumé.

Les droits applicables aux extraits originaux et aux reformulations doivent être examinés avant toute diffusion.

### 9.2. Protection des données d'annotation

Les fichiers d'annotation peuvent contenir des textes bruts, des commentaires humains et des informations de provenance dont la diffusion nécessite une vérification préalable.

Le fait qu'un fichier soit autorisé par `.gitignore` ou qu'il soit de petite taille ne constitue pas une autorisation de publication.

Les fichiers portant le suffixe `_prive` doivent être considérés comme non destinés à une diffusion publique tant que leur statut n'a pas été clarifié.

### 9.3. Partage et versionnement

Avant de publier un jeu d'annotations, l'équipe doit vérifier les droits de redistribution, les risques de divulgation et la nécessité de partager les textes complets.

Une version minimale contenant uniquement les identifiants et les labels peut être envisagée, sous réserve d'une validation de l'équipe. Les identifiants eux-mêmes peuvent permettre de retrouver les textes d'origine.

La suppression d'un fichier d'une branche Git ne garantit pas son effacement de l'historique.

### 9.4. Validation

La décision concernant la diffusion des données d'annotation privées relève de l'équipe NewsCheck TN.

**Statut : politique de partage des données privées en attente de validation collective.**

## 10. Limites

- Déséquilibre des classes dans le corpus A1.
- Forte prédominance du tunisien dans les 600 phrases.
- Répartition des écritures à documenter.
- Déséquilibre des relations NLI.
- Accord inter-annotateurs perfectible.
- Arbitrage des 31 désaccords non terminé.
- Validation sémantique NLI à confirmer.
- Provenance et licences à auditer.
- Doublons textuels, quasi-doublons et fuites entre ensembles non encore vérifiés dans cet audit.

## 11. Prochaines étapes

1. Finaliser l'arbitrage humain avec Achref.
2. Actualiser les annotations finales après validation.
3. Auditer les métadonnées et la provenance des 600 phrases.
4. Contrôler les doublons textuels et les quasi-doublons.
5. Vérifier les relations sémantiques et les preuves des 300 paires NLI.
6. Contrôler les splits et l'absence de fuite de données.
7. Vérifier les licences et les restrictions de diffusion.
8. Soumettre la Data Card v0.2 à la validation de l'équipe.

## 12. Historique des versions

- **v0.1 :** documentation du pilote historique de 60 phrases.
- **v0.2 — 07/11/2026 :** intégration des statistiques des corpus A1 et NLI, des résultats de double annotation et des contrôles structurels. Proposition non encore validée par l'équipe.
