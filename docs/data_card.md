
# NewsCheck TN — Data Card

**Version :** 0.1 — Pilote
**Projet :** NewsCheck TN
**Lot :** A1 — Données et annotations
**Statut :** Pilote validé techniquement, en attente de revue qualitative

## 1. Présentation

NewsCheck TN est un projet de constitution d'un corpus
multilingue destiné à l'analyse d'énoncés et à la
vérification d'informations.

Le Lot A1 prépare :
- 600 phrases annotées
- 300 paires NLI
- Un guide d'annotation
- Une Data Card
- 100 candidats multilingues documentés pour le Lot B

## 2. Corpus pilote

Le pilote contient 60 phrases réparties entre deux sources.

| Source | Nombre |
|---|---:|
| TArC | 30 |
| Tunifact | 30 |
| Total | 60 |

Fichiers :
- data/annotations/tarc_review_30.jsonl
- data/annotations/tunifact_review_30.jsonl

## 3. Distribution des annotations

| Catégorie | Nombre |
|---|---:|
| AFFIRMATION | 48 |
| OPINION | 7 |
| AUTRE | 5 |
| Total | 60 |

Les catégories décrivent la nature des énoncés,
pas leur véracité.

## 4. Groupes linguistiques

| Groupe | Nombre |
|---|---:|
| fr-latin | 20 |
| ar-arabic | 15 |
| tn-mixed | 19 |
| tn-arabizi | 6 |
| Total | 60 |

La distribution est déséquilibrée et ne représente
pas l'ensemble des usages linguistiques tunisiens.

## 5. Sources

### TArC
Corpus de textes tunisiens utilisés pour le pilote.

### Tunifact
Articles de vérification des faits en français et en arabe.

Articles utilisés :
- 698 : migration
- 937 : intempéries et coupures électriques
- 890 : services financiers
- 613 : santé et vaccination
- 797 : éducation et baccalauréat

## 6. Origine des textes

Le pilote comprend :
- Des phrases extraites de sources originales
- Des phrases reformulées à partir d'articles Tunifact

Ces deux types doivent être distingués avant
l'exploitation ou la redistribution.

Le champ `source` indique certaines reformulations,
mais le champ `text_origin` devra être harmonisé
dans une version ultérieure.

## 7. Processus d'annotation

Chaque phrase reçoit une catégorie :

- AFFIRMATION
- OPINION
- AUTRE

Les décisions suivent :
docs/annotation_guide.md

La validation automatique est réalisée avec :
tools/validate_pilot.py

## 8. Contrôles techniques

Résultats du pilote :

- 60 phrases
- 0 doublon d'identifiant
- 0 phrase sans annotation
- Validation automatique réussie

Ces résultats ne prouvent pas la fidélité des textes
aux sources ni l'accord entre annotateurs.

## 9. Licences et redistribution

Les conditions de réutilisation de TArC et Tunifact
doivent être vérifiées séparément.

La licence CC BY-NC-SA 4.0 associée à TArC
nécessite notamment le respect des conditions
d'attribution et de partage.

Aucune licence de redistribution des contenus Tunifact
n'est considérée comme acquise à ce stade.

Le corpus ne doit pas être publié intégralement
avant vérification des droits applicables.

## 10. Limites

- Échantillon pilote de petite taille
- Surreprésentation d'AFFIRMATION
- Diversité thématique encore limitée
- Reformulations et extraits originaux mélangés
- Certaines dates de publication manquantes
- Absence de double annotation indépendante
- Qualité sémantique non encore évaluée

## 11. Prochaines étapes

1. Réaliser une revue qualitative des 60 phrases.
2. Harmoniser les métadonnées.
3. Étendre le corpus à 600 phrases.
4. Préparer 300 paires NLI.
5. Documenter 100 candidats pour le Lot B.
6. Vérifier les licences avant diffusion.
