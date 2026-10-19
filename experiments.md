# Journal d'expériences — NewsCheck TN

Ce journal est **exigé par le cahier des charges du module**. Chaque expérience (entraînement,
évaluation, essai de prompt, configuration de retrieval, choix de normalisation…) y est consignée,
**y compris les échecs**. Les entrées sont ajoutées **en haut** de la section *Entrées* (plus récente d'abord).

## Format d'une entrée

```markdown
### EXP-<lot>-<NNN> — <titre court>
- **Date** : AAAA-MM-JJ
- **Auteur / Lot** : Membre X / Lot Y
- **Objectif / hypothèse** : ce qu'on cherche à vérifier
- **Données** : jeu(x) utilisé(s), version, split (train/dev/test), taille, langues
- **Méthode / configuration** : modèle, hyperparamètres, prompt, graine aléatoire
- **Code** : commit `abc1234`, fichier / notebook
- **Résultats** : métriques (par langue si possible : FR / AR / TN)
- **Analyse** : interprétation, erreurs typiques
- **Décision / suite** : retenu / abandonné / à creuser
```

Numérotation : `EXP-A1-001`, `EXP-A2-001`, `EXP-B-001`, `EXP-C-001`, `EXP-D-001`, `EXP-E-001`…

## Tableau récapitulatif

| ID | Date | Lot | Tâche | Configuration | Métrique principale | Résultat | Décision |
|----|------|-----|-------|---------------|---------------------|----------|----------|
| EXP-E-001 | 2026-10-02 | E | Squelette pipeline | stubs | — | pipeline + API OK | base de départ |
| EXP-B-001 | 2026-10-04 | B | Extraction d'affirmations (SPO, modalité, coréférence) | règles ; règles + spaCy FR / Stanza AR | modalité ; triplet SPO exact | modalité 1.00 ; SPO 0.46 (règles et parseurs) | Bronze retenu ; Silver : objets, lexique verbal |
| EXP-A2-001 | 2026-10-06 | A2 | Normalisation + identification de langue et de script | règles : stub vs v1 | exactitude langue (eval_30) ; cas FR ciblés | 0.82 (stub = v1) ; cas ciblés 0/5 → 5/5 | v1 retenue ; suite : classifieur TN |
| EXP-A2-002 | 2026-10-07 | A2 | Tunisien en lettres arabes | règle : lexique de 78 marques + négation | langue TN sur eval_30 ; rappel TN sur échantillon annoté | 8/14 → 12/14 ; 41/78, standard 15/15 | règle retenue comme référence ; suite : classifieur |
| EXP-A2-003 | 2026-10-07 | A2 | Arabizi sans chiffre (français ou tunisien ?) | régression logistique sur n-grammes de caractères 1-4 ; seuil 5.0 | fausses alertes sur français de test ; rappel TN sur échantillon annoté | 0/416 ; 0/67 → 61/67 (FR 12/16) | modèle retenu ; suite : biais de sujet « tunisiens », règle du seuil |
| EXP-A2-004 | 2026-10-19 | A2 | Reproductibilité : échantillons annotés et lexique | `normalization.annotation`, `normalization.lexicon` | tirage refait ; lexique retrouvé ; fausses alertes sur la presse | 100/100 et 100/100 ; 55/78 (+ 23 variantes) ; 0/1 589 | tout est refaisable ; suite : kappa, presse d'une autre source |
| EXP-A2-005 | 2026-10-19 | A2 | Biais de sujet : noms de lieux tunisiens | 8 lieux ajoutés aux mots neutres ; modèle inchangé | bascules français → arabizi ; arabizi perdu par le pipeline | 22 → 0 ; 13 sur 7 363, dont 8 en réalité français | liste élargie retenue ; suite : réentraîner, retirer le français des corpus arabizi |

## Entrées

### EXP-A2-005 — Biais de sujet : noms de lieux tunisiens rendus neutres
- **Date** : 2026-10-19
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : mesurer, puis corriger, le biais vu dans EXP-A2-003 (« les quatorze
  meilleurs clubs tunisiens » : score 3.33). Hypothèse : un nom de lieu s'écrit pareil dans une
  phrase française et dans un commentaire en arabizi ; l'ignorer supprime les bascules sans perte
  notable d'arabizi.
- **Données** :
  - (a) test de bascule : les 2 912 textes français `dev` d'EXP-A2-003 (phrases entières et leurs
    5 premiers mots, sans doublon), auxquels on ajoute un seul groupe de mots parmi 7 : « en Tunisie »,
    « selon les Tunisiens », « à Tunis », « à Sfax », « à Kairouan », « selon Kaïs Saïed », « en Tunisie
    et à Sfax » (20 384 variantes). Seul l'ajout change : toute bascule lui est due ;
  - (b) français `dev` (2 912) et `test` (416) ; (c) les 7 363 textes arabizi mis de côté
    d'EXP-A2-003 ; (d) l'échantillon annoté en lettres latines (67 `t`, 16 `f`).
- **Méthode / configuration** : 8 formes ajoutées à `resources/neutral_latin_words.txt` : `tunisie`,
  `tunisien`, `tunisiens`, `tunisiene`, `tunisienes`, `tunis`, `sfax`, `kairouan` (lettres doublées
  écrites une fois, comme le reste de la liste). Modèle inchangé, entraîné avec l'ancienne liste de
  18 mots : les mots neutres sont retirés au moment de la lecture. Ordre suivi : essai de la nouvelle
  liste en mémoire, comparé à l'ancienne sur les mêmes jeux ; lecture un par un des textes arabizi
  perdus, avec la décision du pipeline complet (`normalize(...).script`) ; puis seulement, modification
  du fichier.
- **Code** : commit `d7d31b1` : `normalization/resources/neutral_latin_words.txt` ; 3 tests ajoutés
  à `tests/test_normalization.py`.
- **Résultats** :
  - (a) bascules : avant, 22 sur 20 384 (par ajout : 4, 1, 8, 2, 2, 0, 5), dont 19 sur des textes de
    5 mots ou moins ; après, 0 ;
  - (b) français : 0/2 912 et 0/416 avant comme après ;
  - (c) arabizi retrouvé par le modèle seul : 6 715 → 6 701. Des 14 textes perdus, 1 est rattrapé par
    la règle à chiffres du pipeline. Lecture des 13 autres : 8 sont écrits en français (« vive la
    tunisie libre », « voyage en tunisie c bien »…), 1 n'a aucun mot de langue (un nom de personne et
    un nom de pays), 4 sont vraiment tunisiens, tous de 2 à 4 mots (« sfax maaak »…) ;
  - (d) échantillon annoté : inchangé, t 61/67, f 4/16 ;
  - tests : 415 réussis, aucun échec ; `ruff check .` sans remarque.
- **Analyse** : l'hypothèse tient. La « perte » est surtout un gain : 8 des 13 textes étaient du
  français rangé avec l'arabizi dans les corpus. Conséquence : le score « arabizi retrouvé »
  d'EXP-A2-003 (0.91) est faussé par ces erreurs d'étiquette, et une partie de ses « erreurs » sont des
  réponses justes. Le vrai coût est de 4 commentaires tunisiens très courts. Limites : le test de
  bascule est artificiel (lieux ajoutés en fin de phrase) ; la liste est fermée : d'autres lieux
  (Sousse, Gabès…) et les noms de personnes ne sont pas couverts ; « selon Kaïs Saïed » ne fait pas
  basculer ce modèle, mais un modèle d'essai plus permissif (seuil 2.0) y était sensible ; le modèle
  n'a pas été réentraîné avec la nouvelle liste.
- **Décision / suite** : liste élargie retenue. Suite : réentraîner avec la nouvelle liste et
  remesurer ; retirer le français des corpus arabizi, puis mesurer le rappel sur de l'arabizi vérifié
  à la main ; traiter les textes très courts.

### EXP-A2-004 — Reproductibilité : échantillons annotés et lexique des marques
- **Date** : 2026-10-19
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : rendre refaisables, par le code du dépôt, les étapes d'EXP-A2-002 et
  EXP-A2-003 faites jusque-là hors dépôt : tirage des deux échantillons annotés, copie vierge pour un
  second annotateur, kappa, extraction du lexique tunisien, contrôle sur la presse. Hypothèse : refaites
  ainsi, elles redonnent exactement les mêmes fichiers et les mêmes chiffres.
- **Données** (corpus bruts non versionnés, dans `data/raw/langid/`) : TSAC (LGPL-3.0) ; UD Arabic-PADT
  (CC BY-NC-SA 3.0, `git clone --depth 1`), presse en arabe standard : `train` (6 075 phrases) pour
  choisir les mots, `dev` (909) et `test` (680) pour le contrôle seulement ; les deux échantillons
  annotés d'EXP-A2-002 (lettres arabes) et d'EXP-A2-003 (lettres latines).
- **Méthode / configuration** : déterministe (graine 13 pour les tirages).
  - `python -m normalization.annotation sample arabic|latin --check` : refait le tirage et compare,
    ligne par ligne, aux fichiers déjà annotés ; `blank`, `count` et `kappa` remplacent les scripts
    collés dans le terminal ;
  - `python -m normalization.lexicon candidates` : mots présents dans au moins 12 commentaires TSAC en
    lettres arabes (hors échantillons annotés) et dans aucune phrase de PADT `train`, comptés en
    textes et sous la forme repliée que lit la règle ;
  - `python -m normalization.lexicon press` : décision du pipeline complet (`normalize(...).lang`) sur
    PADT `dev` et `test`.
- **Code** : commits `e001a7d` (`normalization/annotation.py`) et `04314d3`
  (`normalization/lexicon.py`) ; 7 tests ajoutés à `tests/test_normalization.py`.
- **Résultats** :
  - tirages refaits : lettres arabes 100/100 lignes identiques, lettres latines 100/100 ; comptage de
    l'échantillon en lettres latines : 67 `t`, 16 `f`, 17 `x` ;
  - lexique : 6 899 commentaires TSAC, 351 candidats ; 55 des 78 marques en font partie ; les 23
    autres sont des variantes ajoutées à la main (`متاعو`, `ماهوش`…), trop rares pour le seuil de
    12 textes, et toutes absentes de la presse ;
  - presse : 0 phrase classée tunisien sur 909 (`dev`) et 0 sur 680 (`test`) ; aucune des 78 marques
    n'y apparaît, même une seule fois ;
  - tests : 412 réussis, aucun échec ; `ruff check .` sans remarque. Résultats identiques sur deux
    machines (Windows et Linux).
- **Analyse** : l'hypothèse tient. Un point appris en route : une graine fixe ne suffit pas à rendre un
  tirage reproductible. Avec le code actuel, qui compte aussi les lettres arabes « déjà dessinées »
  (anciens codes Unicode), 17 textes de plus entraient dans la liste des candidats, et le tirage en
  lettres arabes ne redonnait plus aucune des 100 lignes. Le module compte donc les lettres comme au
  premier tirage. Limites : le contrôle sur la presse utilise le même corpus que la sélection des
  mots (PADT `train` d'un côté, `dev` et `test` de l'autre) : le 0/1 589 est optimiste et ne dit rien
  d'une autre presse, par exemple tunisienne en arabe standard ; le tri manuel des 351 candidats
  n'est pas consigné mot par mot.
- **Décision / suite** : outils retenus ; les prochaines expériences du lot passeront par eux. Suite :
  kappa dès le retour du second annotateur (`python -m normalization.annotation kappa …`) ; contrôle
  sur une presse d'une autre source ; puis les faiblesses d'EXP-A2-003 (biais de sujet, règle du seuil).

### EXP-A2-003 — Arabizi sans chiffre : modèle à n-grammes de caractères
- **Date** : 2026-10-07
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : séparer le français du tunisien écrit en lettres latines sans chiffre
  d'arabizi (« barcha », « mahlek »), que les règles classaient toujours `fr`. Hypothèse : les suites
  de 1 à 4 lettres suffisent à distinguer les deux langues, sans dictionnaire ni gros modèle.
- **Données** (corpus bruts non versionnés, dans `data/raw/langid/`) :
  - arabizi : Tunizi (Zenodo, CC BY 4.0) et lignes de TSAC (LGPL-3.0) reconnues par la règle à
    chiffres ; après dédoublonnage, 66 272 textes pour apprendre, 7 363 mis de côté (10 %, graine 13) ;
  - français : UD French-GSD (CC BY-SA 4.0) ; `train` découpé en 35 356 morceaux de la longueur des
    commentaires, `dev` pour choisir le seuil, `test` (416 phrases) consulté une seule fois, à la fin ;
  - (c) 100 commentaires TSAC en lettres latines sans chiffre d'arabizi (3 mots ou plus, graine 13),
    annotés `t` / `f` / `x` par un annotateur : 67 `t`, 16 `f`, 17 `x`. Jamais appris, mais ils ont
    servi à repérer le défaut du mot « bravo » : jeu de mise au point, pas jeu de test.
- **Méthode / configuration** : `python -m normalization.train_langid` (scikit-learn 1.7.2, graine 13).
  Présence, mot par mot, des n-grammes de 1 à 4 caractères (ignorés s'ils sont vus dans moins de
  5 textes) ; régression logistique (C = 0.5, classes équilibrées). Deux passages : le premier sert à
  retirer les textes « arabizi » jugés nettement français (score < -2.0 : 60 textes), le second donne
  le modèle. Les 20 000 poids les plus forts sont exportés dans `resources/arabizi_ngrams.json`
  (315 Ko) ; à l'usage, score = somme des poids des n-grammes présents, en Python pur (ni les tests
  ni la CI n'ont besoin de scikit-learn). Seuil : le plus petit de la grille 0 à 5 sans aucune fausse
  alerte sur le français `dev` ; valeur retenue 5.0, borne haute de la grille. Garde-fous : 18 mots
  neutres ignorés (`resources/neutral_latin_words.txt` : « bravo », « merci »…) et aucune décision
  en dessous de 2 mots.
- **Code** : commit `6113840` : `normalization/train_langid.py`, `normalization/langid.py` ; dans
  `normalization/normalize.py`, `detect_script` interroge le modèle quand les règles répondent `latin`.
- **Résultats** :
  - français `test`, jamais consulté avant : 0 phrase classée arabizi sur 416 ;
  - arabizi mis de côté : 6 715 retrouvés sur 7 363 (0.91) ;
  - grille des seuils (score seul, 2 941 textes français `dev`) : à 2.0, 97.3 % d'arabizi retrouvé et
    2 textes français classés arabizi ; à 4.0, 93.9 % et 1 ; à 5.0, 91.4 % et 0 ;
  - (c) avant → après, 83 lignes décidées : TN 0/67 → 61/67 ; FR 16/16 → 12/16 ; exactitude
    0.19 → 0.88 ; moyenne par classe 0.50 → 0.83. Les chiffres « avant » sont connus d'avance :
    l'échantillon a été tiré parmi les textes que les règles classaient `fr` ;
  - eval_30 (langue) : inchangé, FR 10/10, AR 10/10, TN 12/14 ; échantillon en lettres arabes
    d'EXP-A2-002 : inchangé, AR 15/15, TN 41/78 ;
  - tests : 405 réussis, aucun échec ; `ruff check .` sans remarque.
- **Analyse** : l'hypothèse tient : sans dictionnaire, le modèle retrouve 9 textes tunisiens sur 10 et
  ne déclenche aucune fausse alerte sur le français de presse. Les 12 textes `dev` les mieux notés
  « arabizi », relus un par un, et les erreurs de (c) montrent quatre faiblesses :
  1. le seuil tient à un seul texte : « can you feel it a » (score 4.79), fragment anglais du corpus
     français. Sans lui, 4.0 suffisait (93.9 % retrouvés au lieu de 91.4 %) ;
  2. biais de sujet : « les quatorze meilleurs clubs tunisiens » obtient 3.33, porté par `tun`, `tuni`.
     Tunizi parle souvent de la Tunisie, et les affirmations à vérifier aussi : c'est le principal
     risque pour le pipeline ;
  3. noms propres : 3 des 4 erreurs FR → TN de (c) sont « bravo » accompagné d'un nom tunisien
     (« bravo » est ignoré, il ne reste que le nom) ; côté `dev`, « billie holiday », « baník okd »,
     « keating » montent de 1.1 à 1.8. La 4e erreur de (c) (ligne 43) est une annotation discutable ;
  4. français familier et textes courts : ` ca `, ` c `, `tu ` comptent pour l'arabizi, car Tunizi
     contient du français familier (le nettoyage n'en retire que 60) ; ce registre est presque absent
     des mesures (« chauchard tu es une bête » : 0.62). Les 6 erreurs TN → FR de (c) ont 1 à 3 mots.
  Limites : (c) a servi à la mise au point et n'a que 16 lignes `f`, surtout des « bravo + nom » ;
  un seul annotateur ; ni français familier ni phrase mêlant les deux langues dans les mesures
  (`mx-4` d'eval_30 reste `fr`).
- **Décision / suite** : modèle retenu, seuil 5.0 inchangé pour l'instant, la règle à chiffres passant
  toujours en premier. Suite (EXP-A2-004) : rendre reproductibles tirages, kappa et lexique ; revoir
  la règle du seuil (un texte anglais ne devrait pas la décider) ; apprendre aussi du français qui
  parle de la Tunisie et du français familier ; double annotation de (c) ; échantillon neuf pour un
  vrai test.

### EXP-A2-002 — Tunisien en lettres arabes : règle à lexique de marques
- **Date** : 2026-10-07
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : reconnaître le tunisien écrit en lettres arabes (point E7 d'EXP-B-001),
  jusque-là toujours classé `ar`. Hypothèse : quelques dizaines de mots-outils suffisent pour une règle
  sans fausse alerte, qui servira de référence à tout classifieur.
- **Données** : (a) `tests/fixtures/linguistic_analysis/eval_30.jsonl` du Lot B (34 phrases), non
  utilisé pour construire la règle ; (b) 100 commentaires TSAC en lettres arabes (3 mots ou plus,
  graine 13), annotés `t` / `a` / `x` par un annotateur selon `docs/lot-a2_guide_annotation.md` :
  78 `t`, 15 `a`, 7 `x`. Cet échantillon a servi à écrire le guide et à choisir les mots : c'est un
  jeu de mise au point, pas un jeu de test. Corpus brut non versionné (TSAC, licence LGPL-3.0).
- **Méthode / configuration** : règle déterministe, sans graine (`normalization/langid.py`) : 78 formes
  dans `resources/tn_markers.txt`, plus la négation en ما…ش (collée ou en deux mots, hors verbes
  standard en ش). Texte déclaré dialectal s'il contient au moins un mot du lexique et au moins 2 % de
  mots dialectaux. Lexique : mots fréquents dans TSAC et absents d'un corpus de presse en arabe
  standard (UD Arabic-PADT), puis tri manuel ; formes ambiguës exclues (`الي`, `لي`, `ياسر`, `شنوا`).
  Cette extraction a été faite hors dépôt : à rendre reproductible (EXP-A2-003).
- **Code** : commit `9810bcd`, `normalization/langid.py` ; `normalization/evaluate.py` lit maintenant
  aussi les fichiers d'annotation `.tsv`.
- **Résultats** :
  - (a) eval_30, avant (`e2fdbe7`) → après : FR 10/10 → 10/10 ; AR 10/10 → 10/10 ; TN 8/14 → 12/14 ;
    exactitude 0.82 → 0.94 ; moyenne par classe 0.86 → 0.95. Script inchangé (0.88).
  - (b) échantillon annoté, 93 lignes décidées : AR 15/15 ; TN 41/78 (0.53) ; moyenne par classe 0.76.
    L'ancien code classait tout texte en lettres arabes en `ar`.
  - Tests : 385 réussis, aucun échec ; `ruff check .` sans remarque.
- **Analyse** : règle sûre (aucune des 25 phrases standard de (a) et (b) n'est classée tunisien) mais
  rappel partiel : un lexique ne voit ni la morphologie (pronom en ـو, négation sans ما, verbes en نـ)
  ni le vocabulaire ouvert. Erreurs restantes sur (a) : `tn-a3` (aucun mot du lexique) et `mx-4`
  (arabizi sans chiffre). Effet de bord : la fixture `mock_documents.jsonl` du Lot B a été régénérée
  par son propre script (1 ligne, `ar` → `tn`). Limites : 15 lignes standard seulement dans (b) ; un
  seul annotateur ; (b) a servi à la mise au point, donc son score est optimiste ; `ديما` et `راني`
  sont aussi des prénoms.
- **Décision / suite** : règle retenue comme référence. Suite : double annotation et kappa sur (b) ;
  contrôle des fausses alertes sur la presse et essai d'un classifieur à n-grammes de caractères, à
  rendre reproductibles (EXP-A2-003) ; échantillon neuf pour un vrai test.

### EXP-A2-001 — Normalisation v1 et identification de langue par règles
- **Date** : 2026-10-06
- **Auteur / Lot** : Membre 2 / Lot A2
- **Objectif / hypothèse** : remplacer le stub de normalisation ; vérifier que la détection d'arabizi
  ne classe plus en tunisien le français contenant un chiffre collé à une lettre (G20, A320, 5G),
  sans dégrader le reste.
- **Données** : (a) `tests/fixtures/linguistic_analysis/eval_30.jsonl`, 34 phrases annotées par le
  Lot B (10 FR, 10 arabe standard, 5 tunisien en lettres arabes, 5 arabizi, 4 mixtes), un annotateur,
  étiquettes `lang` et `script` ; (b) 5 phrases françaises ciblées, rédigées pour reproduire le défaut
  (`test_french_with_digits_is_not_arabizi`). Pas de split : aucune donnée d'apprentissage.
- **Méthode / configuration** : règles déterministes (pas de graine). Stub = `normalize.py` de
  `fe99c66` ; v1 = `6a3d92d`. v1 : mot arabizi sous conditions (au moins 2 lettres, chiffre isolé
  parmi 2-3-5-6-7-9, pas tout en majuscules, pas une unité), seuil de 5 % des mots latins, script
  décidé à la majorité (80 %), liens et adresses ignorés ; chiffres arabes convertis, nombres, sigles
  et liens jamais modifiés.
- **Code** : commit `6a3d92d`, `normalization/normalize.py`, `tests/test_normalization.py` ;
  `normalization/evaluate.py` (`python -m normalization.evaluate --errors`).
- **Résultats** :
  - (a) eval_30, identiques pour le stub et la v1. Langue : FR 10/10, AR 10/10, TN 8/14 (0.57) ;
    exactitude 0.82, moyenne par classe 0.86. Script : arabic 15/15, arabizi 5/5, latin 10/10,
    mixed 0/4 ; exactitude 0.88, moyenne par classe 0.75.
  - (b) phrases ciblées : stub 0/5 (classées arabizi), v1 5/5.
  - Tests du lot : stub 55 réussis / 15 échecs ; v1 70 réussis, 2 échecs attendus (xfail).
    Projet entier avec la v1 : 370 réussis, aucun échec ; `ruff check .` sans remarque.
- **Analyse** : eval_30 ne contient aucune phrase française avec un chiffre collé à une lettre : il ne
  distingue pas les deux versions, d'où le jeu (b). Les 9 erreurs restantes sur eval_30 : 5 phrases
  tunisiennes en lettres arabes classées `ar` (l'alphabet seul ne suffit pas) ; 1 arabizi sans chiffre
  classé `fr` (`mx-4`) ; 4 `mixed`, où le Lot B entend « mélange de langues FR/TN en lettres latines »
  et le code « mélange d'alphabets » : définition à fixer. La v1 conserve ة → ه et ى → ي du stub, qui
  gênent l'analyse syntaxique (EXP-B-001, E7). Limites : jeu petit, un seul annotateur ; les phrases
  (b) ont été rédigées en connaissant les règles : elles prouvent la correction du défaut, pas une
  performance générale.
- **Décision / suite** : v1 retenue. À discuter avec les Lots B et D : texte léger (orthographe
  conservée) dans `Document.text` et repli séparé pour la recherche ; sens de `script = mixed`.
  Suite : classifieur de langue (n-grammes de caractères) pour le tunisien en lettres arabes et
  l'arabizi sans chiffres ; jeu d'évaluation A2 de phrases réelles.

### EXP-B-001 — Extracteur à règles, palier Bronze
- **Date** : 2026-10-04
- **Auteur / Lot** : Membre 3 / Lot B
- **Objectif / hypothèse** : mesurer l'extracteur du Lot B (affirmation vérifiable, modalité, triplet
  sujet-prédicat-objet, coréférence) dans les 3 langues / écritures, avec et sans parseur.
- **Données** : `tests/fixtures/linguistic_analysis/eval_30.jsonl`, 34 phrases rédigées pour
  l'évaluation (10 FR, 10 arabe standard, 5 tunisien en lettres arabes, 5 arabizi, 4 mixtes FR/TN),
  22 affirmations, 3 cas de coréférence ; annotation simple (un annotateur) selon
  `docs/lot-b_guide_annotation.md`, cas difficiles déclarés avant exécution.
- **Méthode / configuration** : règles (lexiques FR / AR / TN, patrons positionnels) ; mode « parseurs » :
  spaCy 3.8 `fr_core_news_md` et Stanza 1.15 `ar` (UD), repli sur les règles pour le tunisien ;
  texte normalisé par `normalization.normalize` ; comparaison sur formes repliées. Déterministe (pas de graine).
- **Code** : 1ᵉʳ passage = code de `26a6064` avec le jeu et le script d'évaluation (commités ensuite
  dans `3c0c382`) ; 2ᵉ passage = `3c0c382` (après corrections) ; `linguistic_analysis/evaluate.py`
  (`--rules`, `--errors`).
- **Résultats** :
  - 1ᵉʳ passage — règles : détection 0.97, modalité 0.97, triplet exact 0.41, coréférence 0.67 ;
    parseurs : détection 0.97, modalité 1.00, triplet 0.46, coréférence 1.00.
  - 2ᵉ passage — règles : détection 1.00 (macro-F1 1.00), modalité 1.00, sujet / prédicat / objet
    0.59 / 0.68 / 0.64, triplet 0.46, coréférence 0.67 ; parseurs : détection 1.00, modalité 1.00,
    0.91 / 0.86 / 0.50, triplet 0.46, coréférence 1.00.
  - Triplet exact par groupe (règles / parseurs) : FR 0.50 / 0.50 ; AR 0.29 / 0.43 ;
    TN lettres arabes 0.50 / 0.00 ; arabizi 0.67 / 0.67 ; mixte 0.50 / 0.50.
- **Analyse** : `docs/lot-b_analyse_erreurs_bronze.md`. Sans parseur, erreurs dominées par le lexique
  verbal (13/25, surtout arabe standard) ; avec parseur, par le choix de l'objet (compléments de temps,
  sources) et des arbres faux (12/16). Deux erreurs liées au traitement amont (tā' marbūṭa, tunisien
  analysé comme arabe standard). Les 3 corrections entre les passages ont été faites en voyant le jeu :
  scores du 2ᵉ passage optimistes ; jeu petit et annoté par une seule personne.
- **Décision / suite** : palier Bronze retenu. Silver : règle d'objet (temps / lieu / source), lexique
  verbal et morphologie du mode règles, jeu d'environ 100 phrases en partie issues d'articles réels avec
  double annotation ; points amont à discuter avec le Lot A2.

### EXP-E-001 — Squelette du pipeline bout-en-bout
- **Date** : 2026-10-02
- **Auteur / Lot** : Lot E
- **Objectif / hypothèse** : disposer d'un pipeline exécutable de bout en bout avec des stubs par lot.
- **Données** : échantillon de 2 passages intégré à `data/loaders.py`.
- **Méthode / configuration** : heuristiques simples (regex, recouvrement lexical), NLI neutre.
- **Code** : commit initial, `pipeline.py`
- **Résultats** : 22 tests passent ; le pipeline s'abstient (attendu, NLI non implémentée).
- **Analyse** : —
- **Décision / suite** : chaque lot remplace son stub.
