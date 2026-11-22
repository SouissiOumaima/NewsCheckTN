# Carte de modèle — identification de langue du Lot A2

Composant : `normalization/normalize.py` (`normalize(text) -> Document`, champs `lang` et `script`),
avec `normalization/langid.py`. Deux parties : une règle à lexique pour les lettres arabes, un modèle
appris pour les lettres latines sans chiffre d'arabizi. Journal : EXP-A2-001 à EXP-A2-020.

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
- Limites connues : rappel du tunisien en lettres arabes de 0,53 sur le dev (échantillon TSAC de référence, EXP-A2-009) et de 0,392 sur le test gelé (règles seules, EXP-A2-020) (lexique limité, variantes, affixes, négation contractée) ; un mot seul d'arabizi tout en majuscules n'est pas reconnu ; un verbe standard en « ش » hors liste déclenche une fausse négation ; « bravo + nom » reste fragile ; textes mêlant français et tunisien mal représentés.
- Éthique : les données d'entraînement sont des commentaires publics, parfois injurieux ; le fichier de poids ne contient que des fragments de 1 à 4 lettres, aucun texte entier.

## 5. Palier Gold : limites (EXP-A2-016 à 020)

Protocole : `docs/lot-a2_protocole_gold.md`. Le composant décrit ici reste celui des sections 1 et 2 (règles et modèle arabizi), sans changement de comportement.

- **Arabizi identifié, pas converti** : `arabizi_to_arabic` renvoie le texte inchangé. Aucun jeu de référence de translittération n'existe, une table ne pourrait donc pas être mesurée. Conséquence pour le Lot D : la recherche BM25 n'a pas de forme arabe de l'arabizi à comparer.
- **Cascade MARBERTv2 non intégrée** : mesurée une seule fois sur le test gelé (EXP-A2-020), elle porte le rappel du tunisien en lettres arabes à 0.90 (règles : 0.39) avec une précision de 0.95, mais deux des quatre critères fixés avant ne sont pas atteints (fausses alertes sur la presse, baisse sur eval_30). Elle ne figure donc pas dans `normalize()`, qui reste en bibliothèque standard. Le rappel du tunisien en lettres arabes du composant reste celui des règles.
- **Fausses alertes sur la presse** : elles concernent la cascade (8.4 % sur 300 phrases de presse neuve), pas les règles (0/300 sur la même presse).
- **Dev vu pendant la mise au point** : la robustesse (EXP-A2-016 : 1 bascule sur 1 314 textes perturbés) et la comparaison à fastText lid.176 (EXP-A2-017 : macro-F1 0.628 / 0.831 contre 0.185 / 0.250) sont mesurées sur ce dev ; elles sont optimistes et ne valent pas généralisation.
- **Annotation** : la référence du test gelé vient d'un seul annotateur (accord humain non mesuré, EXP-A2-019) ; les résultats de la cascade sont indicatifs.
