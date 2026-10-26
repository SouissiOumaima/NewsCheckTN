# Guide d'annotation — langue d'un texte en lettres arabes (Lot A2)

## Objet
Dire, pour un texte écrit en lettres arabes, s'il est en **tunisien** (`t`), en **arabe standard** (`a`)
ou **indécidable** (`x`). L'étiquette sert au Lot B à choisir son analyseur : elle décrit la langue
de la phrase, pas la nationalité de son auteur. Un Tunisien qui écrit en arabe standard donne un `a`.

## Règle de décision (dans cet ordre)
1. Texte illisible, non arabe, formule figée ou trop courte pour décider : `x`.
2. Au moins une forme qui n'est pas de l'arabe standard : `t`. Un seul mot suffit.
3. Sinon : `a` (la phrase pourrait paraître telle quelle dans un journal).

En cas de doute réel : `x`. Un doute honnête vaut mieux qu'une étiquette forcée.

## Marques qui justifient `t`
- Lexique : `برشا`, `ياسر`, `باش`, `موش`, `مش`, `ديما`, `توا`, `قداش`, `علاش`, `كيفاش`, `شنوة`, `باهي`, `متاع`, `محلاها`, `ماسط`.
- Négation collée au verbe en ـش : `معجبنيش`, `ما شفتش`, `ماعادش`.
- Relatif `اللي`, `الي`, `لي` à la place de `الذي` / `التي`.
- Pronom en ـو à la place de ـه : `قلبو`, `منو`, `عندو`.
- Verbe à la 1re personne du singulier en نـ : `نحب`, `نقول`, `نتفرج`.
- Particules : `راك`, `راهم`, `هاذي`, `هذوا`, `هالـ`.

## Ce qui n'est PAS une marque
- Une faute d'orthographe en arabe standard : `حقيقتا`.
- Un mot étranger : `برافو`, `لوك`.
- Les lettres étirées, les emojis, la ponctuation répétée.
- Un mot familier commun à plusieurs pays arabes, s'il est seul : `فلوس`, `زبالة` (exception
  décidée pour `حلو` / `حلوة` : voir « Cas tranchés lors de l'adjudication »).
- Une insulte ou un nom propre : on les met de côté et on décide avec les autres mots. Ce n'est
  jamais une raison de mettre `x`.
- Un mot étranger écrit en lettres arabes (`لوك`, `برافو`, `ساكس`) : mis de côté de la même façon.

## Cas tranchés lors de la première passe
- Phrase standard contenant un seul mot dialectal : `t`.
- Phrase standard avec `الي` pour `الذي` : `t` (ce mot fait échouer l'analyseur standard, cf. EXP-B-001, E7).
- Arabe standard avec fautes d'orthographe : `a`.
- Formule religieuse figée seule (« ما شاء الله ») : `x`. Un vœu rédigé en arabe standard
  (« بالتوفيق والنجاح… ») : `a`.

## Cas tranchés lors de l'adjudication (2026-10-26)
- Phrase standard qui se termine par `معاك` ou `معاه` : `a` (cette forme seule ne suffit pas).
- `حلو` / `حلوة` (« beau », « bonne idée ») : compté comme marque tunisienne, bien qu'il soit
  employé dans d'autres pays arabes. Décision à confirmer sur un échantillon plus grand.
- Seuil proposé « moins de 3 mots arabes après retrait des noms propres, des insultes et des mots
  étrangers → `x` » : discuté, non retenu pour l'instant.

## Procédure
- Fichier TSV, une ligne par texte : étiquette, tabulation, texte. On ne modifie que l'étiquette.
- Deux annotateurs, chacun seul, sans se concerter et sans voir les étiquettes de l'autre.
- Accord mesuré par le kappa de Cohen sur les trois classes, puis discussion des désaccords.

## Première passe (2026-10-07)
- Données : 100 commentaires de TSAC (Facebook, licence LGPL-3.0), en lettres arabes, 3 mots ou plus,
  doublons retirés, tirage aléatoire de graine 13. Le fichier n'est pas versionné (`data/interim/`).
- Les comptages, le kappa et les décisions ligne par ligne sont dans `experiments.md`
  (EXP-A2-002, 007 et 009). Ils ne figurent pas ici, pour ne pas influencer un futur annotateur.

## Textes en lettres latines (ajout du 2026-10-07)

Même principe que pour les lettres arabes : l'étiquette décrit la langue de la phrase, pas
l'origine de son auteur.

| Étiquette | Sens |
|-----------|------|
| `t` | tunisien écrit en lettres latines (arabizi), avec ou sans chiffres |
| `f` | français |
| `x` | indécidable : les deux langues dans la même phrase, ou aucun mot qui permette de trancher |

Fichier : `data/interim/langid/tsac_latin_sample.tsv` (100 commentaires TSAC en lettres latines sans
chiffre d'arabizi, 3 mots ou plus, graine 13). Comptages et kappa : `experiments.md`.

Cas décidés :

- « bravo » suivi d'un prénom ou d'un nom, sans autre mot : `f`. Le seul mot de langue est français ;
  un nom propre ne dit rien de la langue de la phrase.
- français et tunisien dans la même phrase (« c pas possible mamstou ») : `x`.
- Les mots passe-partout (bravo, merci, ok, super, normal…) ne suffisent pas à décider : on regarde
  les autres mots de la phrase.
- Lettres étirées, majuscules, émoticônes et ponctuation n'entrent pas en compte.

Cas tranchés lors de l'adjudication (2026-10-26) :

- Un mot français isolé ou un emprunt courant (« patron », « flop », « point », « mais ») dans une
  phrase tunisienne ne la rend pas mélangée : `t`. `x` seulement si au moins deux mots français
  se suivent.
- Les insultes sont mises de côté : elles ne changent pas la langue de la phrase.
- « bravo + nom » reste `f`, mais ces lignes sont comptées à part dans les mesures (cas fragile :
  presque aucun mot de langue).

Cas encore ouvert :

- Les phrases mêlées restent `x`, donc hors mesure : prévoir une étiquette ou un jeu à part pour
  mesurer ce cas, fréquent dans les textes réels.
