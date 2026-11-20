# Lot B — Analyse d'erreurs, palier Silver (test gelé d'EXP-B-010)

- Jeu : lignes P061 à P600 du jeu de 600 phrases du Lot A1 (540 textes, hors dépôt), SHA-256
  `5514039a5ad44c3b9a1416ef7dd82525aa708b28b78d603281da4693064f9a6b`, vérifié avant le tirage.
- Système : extracteur gelé (`1826244`), mode règles, unité texte, mêmes conventions
  qu'EXP-B-010 (AFFIRMATION → affirmation ; OPINION et AUTRE → non-affirmation).
- Aucun texte n'est reproduit ici : seulement des identifiants.
- Le système n'a pas été modifié après cette analyse. Les corrections ci-dessous sont des pistes. Toute
  correction appliquée rendra une nouvelle mesure sur ce jeu optimiste (« 2ᵉ passage »).

## 1. Tirage

- Erreurs disponibles (mode règles) :
  - 116 erreurs de détection (54 OPINION et 58 AUTRE prédits affirmation, 4 AFFIRMATION manquées) ;
  - 144 erreurs de modalité.
- Erreurs par groupe de langue déclaré par le jeu (détection / modalité) : fr 33 / 35, ar 26 / 34,
  tn-arabe 22 / 27, tn-arabizi 29 / 40, tn-mixte 6 / 8.
- **40 erreurs tirées**, graine 20261015 :
  - 20 en détection, puis 20 en modalité ;
  - 4 par groupe de langue dans chaque cas ;
  - dans chaque groupe, les identifiants sont triés, mélangés avec le même générateur, puis les 4
    premiers sont pris ;
  - un texte déjà tiré en détection est exclu du tirage de modalité.
- Script et sortie hors dépôt (`eval100-work/exp_b010/tirage_erreurs_silver.py`,
  `erreurs_silver_tirage.json`, SHA-256 `3c05b52e32b5024a3e6a05dbe511e26a9aceef6680e5fea0e29237b5fced590a`).

## 2. Catégories

Ce sont les catégories du palier Bronze (`docs/lot-b_analyse_erreurs_bronze.md`), précisées par une
sous-catégorie. Une seule catégorie nouvelle a été ajoutée, **E9** : aucune catégorie existante ne
couvre un texte non affirmatif sans aucun indice linguistique.

| Code | Catégorie |
|------|-----------|
| E1 | segmentation / tokenisation (ici : seuil de longueur des phrases candidates) |
| E3 | lexique ou règle incomplets (marqueur d'opinion, de souhait, d'hypothèse, verbe de parole) |
| E5 | modalité mal priorisée ou mal ciblée |
| E7 | effet du traitement amont (identification de langue) |
| E8 | ambiguïté réelle, annotation discutable ou désaccord avec la définition du guide |
| E9 | **nouvelle** : texte AUTRE sans marqueur (récit personnel, fait privé) pris pour une affirmation |

Le critère E7 a été testé. Le Lot A2 classe 5 des 8 textes tn-arabe tirés comme arabe standard
(P506, P523, P556, P557, P559). Avec la langue forcée à `tn`, la sortie de ces 5 textes ne change
pas : **aucune erreur n'est classée E7** dans ce tirage.

## 3. Tableau

| Catégorie | Nombre | Identifiants | Cause | Lot responsable | Correction envisageable (non appliquée) |
|---|---|---|---|---|---|
| E3 — opinion sans marqueur | 7 | P231, P333, P344, P436, P445 (détection) ; P332, P337 (modalité) | jugement évaluatif, superlatif ou généralisation sans marqueur à la 1re personne ni mot du lexique d'opinion | B | marqueurs évaluatifs (adjectif évaluatif + intensifieur, superlatif) ; à mesurer sur un autre jeu, risque de faux négatifs sur les faits chiffrés |
| E3 — hypothèse non reconnue | 7 | P254, P257, P556, P599 (détection) ; P145, P551, P598 (modalité) | la règle française ne couvre que « si » + imparfait ; « si » + présent ou futur n'est pas couvert ; « si » en texte mixte non couvert ; conditionnel tunisien en lettres arabes absent du lexique `tn` | B | étendre la règle « si » au présent et au futur ; ajouter la particule conditionnelle tunisienne en lettres arabes, limitée à la tête de proposition (forme polysémique) |
| E3 — souhait non reconnu | 6 | P160, P595 (détection) ; P088, P359, P464, P465 (modalité) | formules de vœu, de félicitation ou d'encouragement absentes (R1 ne couvre que les salutations, R2 que la politesse et les requêtes) | B | lexique de formules de vœu par langue, avec le garde-fou de R1 (aucun indice factuel) |
| E3 — rapporté sans verbe de parole connu | 5 | P085, P196, P518, P523, P580 (modalité) | « confirmer » et « démentir » absents de `speech_verbs.txt` ; en tunisien : « entendre que » et verbe de parole au singulier non reconnus | B | ajouter les verbes de confirmation ou de démenti (FR) et les formes tunisiennes au singulier et à la 1re personne |
| E5 — indice trouvé mais non décisif | 3 | P434, P587 (détection) ; P427 (modalité) | P434, P587 : un intensifieur est détecté (`opinion:intensifieur`), mais il ne suffit pas à classer en opinion. P427 : la particule conditionnelle tunisienne, ici au sens « seulement », passe avant le verbe de parole → `hypothétique` au lieu de `rapporté` | B | intensifieur + adjectif évaluatif → opinion ; particule conditionnelle comptée seulement en tête de proposition |
| E8 — désaccord avec le guide ou annotation discutable | 7 | P219, P327 (détection) ; P265, P373, P481, P557, P600 (modalité) | P219, P327 : gold AFFIRMATION avec modalité `opinion`, marqués « doute » (« je crois que » + fait chiffré). Les 5 autres : salutation seule annotée `assertif`, alors que R1 (validée par le Lot A1) donne `souhait` | A1 (guide) et B | trancher dans le guide la modalité d'une salutation seule et le cas « je crois que » + fait vérifiable ; ne pas changer le système avant |
| E9 — AUTRE sans marqueur pris pour affirmation (nouvelle) | 4 | P371, P483, P559, P560 (détection) | récit personnel ou fait privé, de forme assertive : la définition de `is_claim` du Lot B ne l'exclut pas | C (filtrage `filter_checkworthy`) ; B pour la documentation | laisser le tri au Model 1 du Lot C (rôle prévu au contrat) ; au plus, un indice « 1re personne + fait privé » transmis au Lot C, sans changer `is_claim` |
| E1 — phrase sous le seuil de longueur | 1 | P506 (détection) | texte de 3 mots, sous le seuil de 4 mots des phrases candidates (`MIN_TOKENS`) : aucune candidate → affirmation manquée (P359, classé E3, est aussi concerné) | B | seuil abaissé à 3 mots si la phrase contient un verbe conjugué ; à mesurer (risque de faux positifs) |
| **Total** | **40** | 20 détection, 20 modalité | | | |

## 4. Répartition par groupe de langue (déclaré par le jeu)

| Groupe | E1 | E3 | E5 | E8 | E9 | Total |
|---|---|---|---|---|---|---|
| fr | 0 | 6 | 0 | 2 | 0 | 8 |
| ar | 0 | 5 | 0 | 2 | 1 | 8 |
| tn-arabe | 1 | 4 | 0 | 1 | 2 | 8 |
| tn-arabizi | 0 | 4 | 2 | 1 | 1 | 8 |
| tn-mixte | 0 | 6 | 1 | 1 | 0 | 8 |

## 5. Lecture

- **E3 domine (25 sur 40)** : opinion, hypothèse, souhait et rapporté, à parts proches. C'est le
  défaut `assertif` déjà vu en EXP-B-009 et EXP-B-010 : sans marqueur connu, toute phrase est
  assertive.
- **E8 (7 sur 40)** : la convention sur les salutations est appliquée de deux façons. R1, validée par
  le Lot A1, donne `souhait`, alors que le gold de ce jeu donne `assertif`. Une partie des
  « erreurs » de modalité vient donc du guide, pas du système.
- **E9 (4 sur 40)** : les textes AUTRE sans marqueur relèvent du tri du Lot C. Le contrat prévoit
  que le Lot B propose des candidates et que le Lot C filtre.
- **Aucune erreur E7** dans ce tirage, alors que le Lot A2 classe 41 des 81 textes tn-arabe comme
  arabe standard (EXP-B-010). Les règles du Lot B donnent ici la même sortie quelle que soit la
  langue.
- Limites :
  - 40 erreurs sur 260, tirées à effectif égal par groupe : les proportions ci-dessus ne
    représentent pas la population des erreurs ;
  - classement fait par une seule personne ;
  - un seul annotateur pour le gold.
