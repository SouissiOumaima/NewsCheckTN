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