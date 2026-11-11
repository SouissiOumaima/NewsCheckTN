# Convention de relecture A1 — proposition pour PR #18

Cette convention distingue les labels de classification et l'avis sur une
proposition d'arbitrage. Elle n'établit aucun label final.

| Champ | Contenu |
| --- | --- |
| `label_ghofran` | Annotation initiale de Ghofran, conservée |
| `label_achref` | Annotation initiale d'Achref, conservée |
| `decision_achref` | Label de relecture déjà renseigné ; ne pas remplacer par un avis |
| `avis_achref` | `ACCEPTER`, `REFUSER` ou `A_DISCUTER` après examen de la proposition identifiée |

## Signification des avis

- `ACCEPTER` : accord avec le label proposé dans la version de travail examinée.
- `REFUSER` : désaccord ; préciser le motif et le label alternatif dans le fichier privé.
- `A_DISCUTER` : contexte insuffisant ou règle à arbitrer ; préciser le point litigieux dans le fichier privé.
- Une cellule vide signifie que l'avis n'est pas encore renseigné.

Les 31 avis restent vides tant que la dernière version des propositions de
Ghofran n'est pas fournie et rapprochée par `id`. Ne pas déduire un avis à partir
du seul label de relecture : un même label peut accompagner une réserve de contexte.

Les propositions, leur version et les commentaires `commentaire_achref` sont
conservés dans l'espace privé autorisé. Aucun texte source, label proposé privé
ou commentaire libre n'est réintroduit dans le CSV minimisé du dépôt.
Le dernier retour de Ghofran confirme que les labels finaux seront validés
collectivement après relecture. Les conserver séparément des avis et des
annotations initiales dans le fichier d'arbitrage privé.

L'ajout de cette colonne ne règle pas le statut des anciens commits contenant
les textes. La procédure de régularisation reste à définir avec l'équipe et
l'encadrant ; aucune réécriture de l'historique n'est effectuée ici.
