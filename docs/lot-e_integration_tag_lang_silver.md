# Lot E — utilisation de tag_lang pour le bilan Silver

L'outil de PR #22 prépare des métadonnées pour l'évaluation hors ligne. Il ne
remplace pas normalize dans l'API et ne nécessite aucune modification du pipeline.

## Utilisation locale

Sur une copie de travail privée autorisée :

```powershell
python -X utf8 -m normalization.tag_lang data/interim/lot_c/nli/jeu.jsonl --fields claim evidence
git check-ignore -- data/interim/lot_c/nli/jeu_lang.jsonl
```

Adapter les noms de champs au fichier réel : le CSV d'erreurs utilise notamment
`affirmation` et `preuve`, et non `claim` et `evidence`.
Le CSV accepté ici utilise la virgule. Ne pas appliquer directement la commande
à un CSV séparé par des points-virgules sans conversion locale explicite.
L'outil refuse une sortie existante et des colonnes langue/écriture déjà présentes.
Ne pas supprimer ces colonnes si elles proviennent d'une annotation humaine.

## Interprétation dans le tableau de bord

- Distinguer `claim_lang` et `evidence_lang` pour les paires de langues différentes.
- Les champs ajoutés sont des prédictions A2, pas une référence humaine.
- Conserver la langue de référence disponible ; documenter la source utilisée
  pour grouper chaque tableau. Ne pas remplacer les groupes officiels d'EXP-C-011
  par de nouvelles prédictions sans présenter séparément cette analyse.
- Afficher les effectifs, la version du corpus et la métrique pour chaque groupe.
  Les valeurs unk restent un groupe explicite.
- Ne pas fabriquer de score TN quand le corpus évalué n'a pas de paire tunisienne.

La sortie dans data/ n'est pas automatiquement hors Git : vérifier les règles
effectives. Ne publier que les agrégats autorisés, sans texte ni commentaire privé.
Cette vérification technique ne clôture pas l'intégration Silver : les modèles C,
le retrieval dense/hybride et le verdict LLM D restent des composants distincts.
