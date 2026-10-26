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
- Un mot familier commun à tout le monde arabe, s'il est seul : `فلوس`, `حلو`, `زبالة`.
- Une insulte ou un nom propre.

## Cas tranchés lors de la première passe
- Phrase standard contenant un seul mot dialectal : `t`.
- Phrase standard avec `الي` pour `الذي` : `t` (ce mot fait échouer l'analyseur standard, cf. EXP-B-001, E7).
- Arabe standard avec fautes d'orthographe : `a`.
- Vœu ou formule religieuse seule : `x`.

## Cas ouverts, à trancher après la double annotation
- Phrase standard qui se termine par `معاك` ou `معاه` : la règle 2 donnerait `t`.
- Phrases où les deux lectures de la première passe diffèrent : lignes 12, 20, 33, 71, 86.

## Procédure
- Fichier TSV, une ligne par texte : étiquette, tabulation, texte. On ne modifie que l'étiquette.
- Deux annotateurs, chacun seul, sans se concerter et sans voir les étiquettes de l'autre.
- Accord mesuré par le kappa de Cohen sur les trois classes, puis discussion des désaccords.

## Première passe (2026-10-07)
- Données : 100 commentaires de TSAC (Facebook, licence LGPL-3.0), en lettres arabes, 3 mots ou plus,
  doublons retirés, tirage aléatoire de graine 13. Le fichier n'est pas versionné (`data/interim/`).
- Un annotateur, Membre 2. Lecture sans règle écrite : 91 `t`, 9 `a`, 0 `x`.
  Après application de la règle ci-dessus : **78 `t`, 15 `a`, 7 `x`**.
- Conclusion : environ une ligne sur cinq n'est pas clairement du tunisien. TSAC ne peut pas servir
  tel quel d'exemples de tunisien.

## Textes en lettres latines (ajout du 2026-10-07)

Même principe que pour les lettres arabes : l'étiquette décrit la langue de la phrase, pas
l'origine de son auteur.

| Étiquette | Sens |
|-----------|------|
| `t` | tunisien écrit en lettres latines (arabizi), avec ou sans chiffres |
| `f` | français |
| `x` | indécidable : les deux langues dans la même phrase, ou aucun mot qui permette de trancher |

Fichier : `data/interim/langid/tsac_latin_sample.tsv` (100 commentaires TSAC en lettres latines sans
chiffre d'arabizi, 3 mots ou plus, graine 13). Premier passage, un annotateur : 67 `t`, 16 `f`, 17 `x`.

Cas décidés :

- « bravo » suivi d'un prénom ou d'un nom, sans autre mot : `f`. Le seul mot de langue est français ;
  un nom propre ne dit rien de la langue de la phrase.
- français et tunisien dans la même phrase (« c pas possible mamstou ») : `x`.
- Les mots passe-partout (bravo, merci, ok, super, normal…) ne suffisent pas à décider : on regarde
  les autres mots de la phrase.
- Lettres étirées, majuscules, émoticônes et ponctuation n'entrent pas en compte.

Cas ouverts, à discuter avec le second annotateur :

- « bravo + nom » en `f` : choix cohérent, mais ces lignes ne contiennent presque pas de français.
  Les compter à part dans les mesures.
- Ligne 43 : annotée `f`, alors que son dernier mot est une forme tunisienne (`t` ?).
- Les phrases mêlées restent `x`, donc hors mesure : prévoir une étiquette ou un jeu à part pour
  mesurer ce cas, fréquent dans les textes réels.
