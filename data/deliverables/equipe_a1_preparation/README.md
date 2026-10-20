# NewsCheck TN - Livraison A1 (preparation interne)

## Statut

Preparation interne. Les droits de redistribution restent a confirmer
avec l'encadrant avant tout partage des textes concernes.

## Fichiers references

### Pilote A1 - 60 phrases
- Chemin : data/annotations/pilote_60_provenance_a_valider.jsonl
- 30 extraits TArC
- 15 extraits Tunifact
- 15 reformulations Tunifact
- 45 correspondances textuelles verifiees dans les sources locales
- Aucun label d'annotation

### TArC - 30 phrases
- Chemin : data/annotations/tarc_30_provenance_a_valider.jsonl
- Ces 30 phrases sont deja presentes dans le pilote A1
- Provenance textuelle verifiee dans forum.tab
- Quatre cas de classification linguistique a confirmer

### TunSwitch - 22 phrases
- Chemin : data/annotations/tunswitch_22_sans_labels_a_valider.jsonl
- Correspondances textuelles verifiees dans TO_text.txt
- 22 candidates en tunisien ecrit en caracteres arabes
- Quatre observations linguistiques a revoir
- Licence, contexte et admissibilite a confirmer

## Regles importantes

- Ne pas compter les 30 phrases TArC deux fois.
- Ne pas presenter les reformulations comme des citations originales.
- Ne pas inclure les annotations privees d'Oumaima.
- Ne pas modifier les IDs ou les textes sources.
- Ne pas integrer automatiquement ces phrases dans eval_100.
- Verifier les licences avant redistribution.

## Documents de suivi

- manifest_a1.json
- data/annotations/tarc_revue_groupes_propositions.csv
- data/annotations/tunswitch_revue_linguistique.csv

## Travaux restants

1. Confirmer les licences et conditions de partage.
2. Valider les cas linguistiques douteux.
3. Finaliser les annotations independantes.
4. Selectionner et valider les donnees pour eval_100.
