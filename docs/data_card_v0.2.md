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

## 3. Corpus A1 — 600 phrases

**Fichier de référence audité :** `data/annotations/corpus_a1_600_humain_final_prive.jsonl`

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

**Fichier de référence audité :** `data/annotations/nli_corpus_300_consolide_v4_prive.jsonl`

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

| Indicateur | Résultat |
|---|---:|
| Phrases comparées | 100 |
| Accords | 69 |
| Désaccords | 31 |
| Accord observé | 69 % |
| Cohen's Kappa | ≈ 0,34 |

Le Kappa mesure l'accord corrigé du hasard. Sa valeur indique que les divergences d'interprétation doivent être examinées.

Les 31 désaccords font l'objet d'une relecture humaine dans la Pull Request #18.

Les labels proposés pour l'arbitrage ne sont pas considérés comme définitifs avant validation humaine.

## 6. Guide d'annotation

**Document :** `docs/annotation_guide_v1.1.md`

Le guide définit les trois catégories, les règles de décision, les cas ambigus, la double annotation et la méthode de calcul de Cohen's Kappa.

La version 1.1 reste une proposition en attente de validation par l'équipe.

## 7. Contrôles techniques

Les deux corpus ont été audités en lecture seule.

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

Le corpus pilote historique utilise notamment TArC et Tunifact.

Les données peuvent comprendre des extraits originaux et des reformulations. Leur distinction doit rester explicite.

La provenance, les URL, les dates, les documents sources et les modalités d'annotation doivent être vérifiés sur les corpus étendus.

Aucune provenance non vérifiée ne doit être inventée.

## 9. Licences et confidentialité

Les conditions de réutilisation de TArC et Tunifact doivent être vérifiées séparément.

La licence CC BY-NC-SA 4.0 associée à TArC impose notamment des conditions d'attribution et de réutilisation.

Aucun droit général de redistribution des contenus Tunifact n'est présumé.

Les fichiers identifiés comme privés ne doivent pas être publiés intégralement avant vérification des droits et autorisation de l'équipe.

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