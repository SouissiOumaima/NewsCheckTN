# Carte de modèle — identification de langue du Lot A2

Composant : `normalization/normalize.py` (`normalize(text) -> Document`, champs `lang` et `script`),
avec `normalization/langid.py`. Deux parties : une règle à lexique pour les lettres arabes, un modèle
appris pour les lettres latines sans chiffre d'arabizi. Journal : EXP-A2-001 à EXP-A2-009.

## 1. Règle à lexique (tunisien en lettres arabes)

| Élément | Valeur |
| --- | --- |
| Tâche | arabe standard (`ar`) ou tunisien (`tn`) pour un texte en lettres arabes |
| Méthode | au moins une marque tunisienne et au moins 2 % des mots ; négation « ما … ش » |
| Lexique | 78 marques (`resources/tn_markers.txt`), tirées de TSAC et absentes de UD Arabic-PADT train |
| Reproduire | `python -m normalization.lexicon candidates` puis `press` (EXP-A2-004) |

## 2. Modèle arabizi (lettres latines sans chiffre)

| Élément | Valeur |
| --- | --- |
| Tâche | tunisien en arabizi (`tn`) ou français (`fr`), quand la règle à chiffres ne conclut pas |
| Modèle | régression logistique, n-grammes de caractères 1 à 4 par mot (présence), `min_df` 5, `C` 0.5, classes équilibrées, graine 13 |
| Fichier | `resources/arabizi_ngrams.json` : les 20 000 poids les plus forts (315 Ko), lus en Python pur |
| Décision | score ≥ 5.0, au moins 2 mots de 2 lettres ; mots neutres retirés avant le calcul (`resources/neutral_latin_words.txt`) |
| Données d'entraînement | voir `DATA_CARD.md` : arabizi (Tunizi + lignes de TSAC à chiffres d'arabizi), 66 241 textes ; français (UD French-GSD train découpé à la longueur des commentaires), 35 194 morceaux ; 57 textes « arabizi » écartés car jugés français au premier passage |
| Seuil | choisi sur le français `dev` pour n'y classer aucun texte arabizi ; aucun seuil ne l'atteint depuis EXP-A2-006 (1 texte anglais sur 2 941), 5.0 gardé par repli |
| Reproduire | `python -m normalization.train_langid` ; vérifié par `test_arabizi_model_is_regenerable` (test lent) |

## 3. Évaluation

| Mesure | Jeu | Résultat |
| --- | --- | --- |
| Langue, macro-F1 | eval_30 (34 phrases du Lot B) | 0,94 ; tunisien : précision 1,00, rappel 12/14 |
| Français classé arabizi | UD French-GSD test (416), consulté une seule fois | 0 |
| Presse arabe classée tunisien | UD Arabic-PADT dev + test (1 589) | 0 |
| Tunisien en lettres arabes retrouvé | échantillon TSAC de référence (77 `t`) | 41 (0,53) ; arabe standard 23/23 |
| Lettres latines | échantillon TSAC de référence (70 `t`, 16 `f`) | `t` 65/70, `f` 12/16 |
| Arabizi mis de côté retrouvé | 7 360 textes | 6 687 (optimiste : Tunizi contient du français mal étiqueté) |
| Bascules dues à un nom de lieu | 2 912 phrases × 7 ajouts | 0 |

Analyse de 45 erreurs : `docs/lot-a2_analyse_erreurs.md` (EXP-A2-009).

## 4. Usage prévu et limites

- Prévu : choisir l'analyseur ou le modèle selon la langue (lots B, C), ventiler les résultats par langue (lot E).
- Hors périmètre : autres dialectes arabes, anglais (classé selon sa ressemblance au français), textes d'un seul mot.
- Limites connues : rappel du tunisien en lettres arabes de 0,53 (lexique limité, variantes, affixes, négation contractée) ; un mot seul d'arabizi tout en majuscules n'est pas reconnu ; un verbe standard en « ش » hors liste déclenche une fausse négation ; « bravo + nom » reste fragile ; textes mêlant français et tunisien mal représentés.
- Éthique : les données d'entraînement sont des commentaires publics, parfois injurieux ; le fichier de poids ne contient que des fragments de 1 à 4 lettres, aucun texte entier.
