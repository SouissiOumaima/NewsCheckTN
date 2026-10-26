# Lot A2 — Tableaux de la revue Bronze

Normalisation, identification de langue et perplexité. Tous les chiffres viennent de
`experiments.md` (EXP-A2-003, 004, 008, 010, 011) et se refont depuis le dépôt :
`python -X utf8 -m normalization.review` et `python -X utf8 -m normalization.perplexity`.

**Jeux** : *test* = `eval_30.jsonl` (34 phrases, jamais utilisé pour écrire les règles du Lot A2,
gelé au commit `85fb77d`, 2026-10-20) ; *dev* = références TSAC adjudiquées (EXP-A2-009), qui ont
servi à la mise au point ; tests de fausses alertes = PADT `test` et UD French-GSD `test`.
Empreintes SHA-256 : EXP-A2-011.

## Tableau 1 — Résultats par composant

| Composant | Lot | Méthode Bronze | Baseline triviale | Métrique | Score baseline | Score Bronze | N test |
|---|---|---|---|---|---|---|---|
| Identification de langue (fr / ar / tn) | A2 | règles d'alphabet + lexique de 78 marques + n-grammes de caractères (arabizi) | classe majoritaire | macro-F1 (↑) | 0.19 | **0.94** | 34 (eval_30) |
| Identification de langue | A2 | idem | alphabet seul (comportement d'avant le Lot A2) | macro-F1 (↑) | 0.50 | **0.94** | 34 |
| Identification de langue — dev lettres arabes | A2 | idem | classe majoritaire | macro-F1 (↑) | 0.43 | 0.63 | 100 (dev) |
| Identification de langue — dev lettres latines | A2 | idem | classe majoritaire | macro-F1 (↑) | 0.45 | 0.83 | 86 (dev) |
| Tunisien : fausses alertes sur la presse | A2 | lexique de marques | « toujours tunisien » | presse classée `tn` (↓) | 100 % | **0 %** | 680 (PADT test) |
| Arabizi : fausses alertes sur le français | A2 | n-grammes de caractères, seuil 5.0 réglé sur dev | « toujours arabizi » | français classé arabizi (↓) | 100 % | **0 %** | 416 (UD test) |
| Perplexité — lettres arabes | A2 | n-grammes de caractères (ordre 4), seuil = 95e centile dev | aléatoire | AUC bruit « lettres » (↑) | 0.50 | **0.999** | 569 (test) |
| Perplexité — lettres latines | A2 | idem | aléatoire | AUC bruit « lettres » (↑) | 0.50 | **0.996** | 1 000 (test) |
| Normaliseur | A2 | règles (formes de présentation, chiffres, lettres étirées) | copie de la source | textes aux nombres conservés (↑) | 29/29 | **29/29** | 220 |
| Normaliseur | A2 | idem | copie de la source | réduction du vocabulaire (↑) | 0 % | 1.9 % | 220 |

Composants déterministes : un seul passage sur le test. Les réglages (seuil 5.0, seuil de
perplexité, choix des marques) sont faits sur `train` / `dev`, jamais sur le test.

## Tableau 2 — Résultats par langue / script

Identification de langue, F1 par classe (rappel entre parenthèses).

| Composant | Jeu | FR | AR | Tunisien (arabe) | Tunisien (arabizi) | EN |
|---|---|---|---|---|---|---|
| Identification de langue | test eval_30 | 0.95 (10/10) | 0.95 (10/10) | 4/5 bien classées | 5/5 bien classées | hors périmètre |
| Identification de langue | dev TSAC | 0.73 (0.75) | 0.56 (1.00) | 0.69 (0.53) | 0.94 (0.93) | hors périmètre |
| Perplexité (bruit repéré, lettres au hasard) | test | 99.3 % (modèle « lettres latines », FR et arabizi confondus) | 99.6 % (modèle « lettres arabes », AR et TN confondus) | idem AR | idem FR | — |
| Perplexité (fausses alertes sur texte propre) | test | 5.3 % | 4.7 % | idem AR | idem FR | — |
| Perplexité (bruit d'encodage repéré) | test | 12.3 % (AUC 0.53) | 100 % | idem AR | idem FR | — |

Sur eval_30, les 4 phrases mixtes FR / TN : 3/4 bien classées `tn`. La perplexité a un modèle par
alphabet, pas par langue : ses chiffres valent pour toutes les langues d'un même alphabet.

## Tableau 3 — Analyse d'erreurs

Identification de langue, jeux de dev, 45 erreurs. Détail ligne par ligne :
`docs/lot-a2_analyse_erreurs.md` ; CSV (entrée, sortie, référence, catégorie) :
`data/interim/langid/bronze_erreurs.csv`, non versionné car il contient des textes du corpus.

| Composant | Catégorie d'erreur | Nombre (sur 45) | Exemple court | Piste de correction |
|---|---|---|---|---|
| Identification de langue | Lexique incomplet (mot absent, variante d'orthographe) | 13 | `توحشتك`, `ماصط` | Agrandir le lexique, comparer après pliage orthographique ; remesurer la presse |
| Identification de langue | Morphologie dialectale (affixe collé, négation contractée, construction) | 11 | `يتفرجو`, `معجبكش` | Retirer les affixes avant la comparaison ; élargir la règle de négation |
| Identification de langue | Texte trop court ou sous le seuil | 9 | 2 à 3 mots | Limite assumée : prix du seuil prudent (0 français classé arabizi) |
| Identification de langue | Effet d'une règle choisie | 7 | `ياسر` (aussi prénom) ; « bravo + nom » | Compromis documenté ; compter « bravo + nom » à part |
| Identification de langue | Étiquette de référence discutable | 5 | `حلو`, `معاه` en fin de phrase | Revoir avec la seconde annotatrice |

Toutes les erreurs en lettres arabes vont dans le même sens : du tunisien pris pour de l'arabe
standard. La règle privilégie la précision (aucune phrase de presse classée tunisienne).

## Limites à dire

- Le test est petit (34 phrases, dont 5 en tunisien lettres arabes) et annoté par une seule personne.
- Les scores du dev sont optimistes : ce jeu a servi à la mise au point.
- La perplexité ne repère presque pas l'encodage abîmé en arabizi (AUC 0.53).
- Suite prévue : échantillon TSAC neuf, jamais vu, annoté par deux personnes.
