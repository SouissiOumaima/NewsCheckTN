# Carte de modèle — extraction d'affirmations du Lot B

Composant : `linguistic_analysis/claim_extraction.py`
(`extract_claims(doc: Document) -> list[Claim]`, version détaillée `extract_claims_detailed`).
Système à règles et lexiques, avec analyseurs syntaxiques facultatifs. Aucun apprentissage, aucun
poids appris. Journal : EXP-B-001 à EXP-B-011, EXP-B-013 et EXP-B-014 (EXP-B-012 est réservé à
eval_100). **Système gelé** au commit `1826244` : aucune
modification du code ni des lexiques depuis (voir `experiments.md`, « Gel du système du Lot B
pour EXP-B-010 »). Résultat de référence actuel : **EXP-B-010** (540 textes synthétiques jamais vus ;
voir §3 et §6.1). Mesure de référence à venir sur textes réels : eval_100.

## 1. Rôle, entrées et sorties

| Élément | Valeur |
| --- | --- |
| Tâche | découper un document en phrases et, pour chaque phrase candidate (4 mots ou plus), dire si c'est une affirmation vérifiable, donner sa modalité, son triplet sujet / prédicat / objet et sa version résolue par coréférence |
| Entrée | `common.schemas.Document` produit par le Lot A2 (`text` normalisé, `lang` ∈ `fr` / `ar` / `tn`, `script`) |
| Sortie | `list[Claim]` : `text`, `lang`, `span`, `subject`, `predicate`, `obj`, `modality` ; champs internes dans `ExtractedClaim` (`is_opinion`, `certainty`, `resolved_text`, `source`, `time`, `location`, `triggers`, `parser`) |
| Affirmation | `is_claim = not is_opinion and modality ∉ {interrogatif, souhait, hypothétique, opinion}` |
| Consommateurs | Lot C (`filter_checkworthy`, utilise `text` et `modality == "assertif"`), Lot D (`retrieve`), API `POST /extract` |

## 2. Composants

| Composant | Fichier | Rôle |
| --- | --- | --- |
| Prétraitement | `preprocessing.py` | phrases, jetons ; analyseur choisi selon la langue |
| Factualité | `factuality.py`, `resources/opinion_<langue>.txt` | opinion, question, souhait contre indices factuels (nombre, date, entité) |
| Modalité | `modality.py`, `resources/modality_<langue>.json` | label de modalité et score de certitude |
| Triplet | `spo.py`, `resources/verbs.json`, `speech_verbs.txt`, `adjuncts.json` | sujet, prédicat, objet ; source, temps et lieu hors de l'objet |
| Coréférence | `coreference.py` | pronom sujet remplacé par son antécédent (`resolved_text`) |

### Les 7 modalités

Un seul label par phrase, selon cette priorité (guide `docs/lot-b_guide_annotation.md` §4) :
`interrogatif` > `souhait` > `hypothétique` > `conditionnel` > `rapporté` > `opinion` > `assertif`.
`assertif` est le label par défaut. Une phrase `rapporté` ou `conditionnel` reste une affirmation.

### Règles ajoutées avant le gel

Elles ont été choisies sur le pilote, à partir de l'analyse des faux positifs. Elles ajoutent des
entrées de lexique dans `opinion_<langue>.txt` et une condition dans `factuality.py`.

| Règle | Effet | Garde-fou |
| --- | --- | --- |
| R1 Salutation conventionnelle → `souhait` (validée par le Lot A1) | « Bonjour à tous » seul n'est plus une affirmation | seulement en tête de phrase et sans aucun indice factuel (nombre, date, entité) |
| R2 Formule de politesse ou requête → `souhait` | « merci d'avance », « svp » : la phrase demande, elle n'affirme rien | aucun |
| R4 Appréciation à la 1re personne → `opinion` | « j'aime », « je déteste » | verbe compté seulement à la 1re personne ; « préférer » exclu |

### Deux modes

| Mode | Analyse | Usage |
| --- | --- | --- |
| règles | règles et lexiques seulement, pour toutes les langues | CI, environnement sans modèle (`evaluate --rules`) |
| parseurs | spaCy `fr_core_news_md` (français), Stanza `ar` (arabe standard) ; règles pour le tunisien et les langues inconnues | défaut si les modèles sont installés |

Les modèles spaCy et Stanza sont chargés paresseusement. S'ils manquent, le mode règles prend le
relais.

## 3. Données (mise au point, test gelé, exploratoire)

| Jeu | Contenu | Rôle |
| --- | --- | --- |
| eval_30 (`tests/fixtures/linguistic_analysis/eval_30.jsonl`) | 34 phrases, 5 groupes (`fr-latin`, `ar-arabic`, `tn-arabic`, `tn-arabizi`, `tn-mixed`), gold complet (affirmation, modalité, triplet sur 22 phrases, coréférence sur 3) | jeu de développement : les règles ont été réglées dessus (EXP-B-001 à EXP-B-006) |
| Pilote du Lot A1 (P01–P60) | 60 textes annotés par deux personnes (label, modalité ; pas de triplet) ; langue selon le Lot A2 : fr 26, ar 15, tn-arabizi 19 | première mesure (EXP-B-008, EXP-B-009) ; a aussi servi à choisir des corrections : ce n'est plus un jeu de test. Fichiers hors dépôt |

| Jeu | Contenu | Rôle |
| --- | --- | --- |
| Test P061–P600 | 540 textes synthétiques générés par un modèle de langue par catégorie (blocs consécutifs), annotés à la main par un seul annotateur (Lot C) ; protocole de génération à documenter par le Lot C (label, modalité ; pas de triplet ni de coréférence) ; langue déclarée : fr 140, ar 135, tn-arabizi 135, tn-arabe 81, tn-mixte 49 ; SHA-256 `5514039a…4f9a6b` noté avant la mesure | **test gelé** d'EXP-B-010 : jamais utilisé pour écrire ni régler les règles. Fichier hors dépôt |
| silver_40 du Lot A1 (livraison provisoire) | 40 textes (TArC 30, Tunifact 10), deux annotations, 10 triplets dont 3 avec réserve, 1 coréférence | mesure exploratoire EXP-B-011 ; 5 textes déjà dans le pilote. Fichiers hors dépôt |

## 4. Résultats

### 4.1 Référence : test gelé P061–P600 (EXP-B-010)

Textes synthétiques (voir §3) : scores probablement optimistes (§6.1).
Système gelé (`1826244`), unité texte, un annotateur. Bootstrap percentile 95 %, graine 20261015,
1000 tirages ; extracteur − baseline : apparié, graine 42, 2000 tirages. Commande dans
`experiments.md` (EXP-B-010).

| Mesure (540 textes) | Règles [IC 95 %] | Parseurs | Baseline |
| --- | --- | --- | --- |
| Détection, exactitude | 0.785 [0.750 ; 0.820] | 0.789 | 0.526 (« tout = affirmation ») |
| Détection, précision | 0.714 [0.670 ; 0.757] | 0.718 | 0.526 |
| Détection, rappel | 0.986 [0.972 ; 0.997] | 0.986 | 1.000 |
| Détection, macro-F1 | 0.771 [0.733 ; 0.806] | 0.775 | 0.345 |
| Modalité, exactitude | 0.733 [0.696 ; 0.769] | 0.731 | 0.385 (« tout = assertif ») |
| Modalité, macro-F1 | 0.734 [0.690 ; 0.772] | 0.729 | 0.079 |

- **Extracteur − baseline (règles)** : détection +0.426 [+0.391 ; +0.460] ; modalité +0.655
  [+0.613 ; +0.691].
- **Parseurs − règles** : aucune différence établie (détection +0.004 [−0.004 ; +0.013]).
- **Par langue déclarée** (règles ; macro-F1 de détection / exactitude de modalité) : fr 0.731 /
  0.750 ; ar 0.794 / 0.748 ; tn-arabe 0.713 / 0.667 ; tn-arabizi 0.780 / 0.704 ; tn-mixte
  0.868 / 0.837.
- **Erreurs** : 116 en détection (54 OPINION et 58 AUTRE prédits affirmation, 4 affirmations
  manquées) et 144 en modalité. 40 erreurs sont classées dans `docs/lot-b_analyse_erreurs_silver.md`.

### 4.2 Exploratoire : silver_40 (EXP-B-011)

Ces chiffres ne remplacent pas EXP-B-010. Les effectifs sont trop petits pour une conclusion par
langue, et l'indépendance de la seconde annotation n'est pas garantie.

| Mesure | N | Règles | Parseurs |
| --- | --- | --- | --- |
| Kappa label (3 classes) entre annotateurs | 38 | 0.660 [0.434 ; 0.858] | — |
| Détection, macro-F1 (gold Ghofrane) | 40 | 0.394 (baseline 0.200) | identique |
| Détection, macro-F1, TArC seul | 30 | 0.167 (24 textes sur 30 prédits affirmation) | identique |
| Modalité, exactitude (gold Achraf) | 38 | 0.395 | — |
| Triplet exact, sans réserve | 7 | 1/7 | 2/7 |
| Coréférence (avec réserve) | 1 | 0/1 | 0/1 |

### 4.3 Jeux de mise au point (eval_30, pilote)

Règles R1, R2 et R4 comprises. Bootstrap percentile 95 %, graine 20261015,
1000 tirages ; différences appariées : graine 42, 2000 tirages. Entre parenthèses : la valeur avant
les règles R1, R2 et R4 (EXP-B-009).

**Ces règles ont été choisies sur le pilote : les chiffres du pilote sont optimistes.**

| Mesure | Jeu | Règles | Parseurs | Baseline |
| --- | --- | --- | --- | --- |
| Détection, exactitude | eval_30 (34) | 1.000 | 1.000 | 0.647 (« tout = affirmation ») |
| Modalité, exactitude | eval_30 (34) | 1.000 | 1.000 | 0.412 (classe majoritaire) |
| Triplet exact | eval_30 (22) | 0.909 (20/22) | 0.864 (19/22) | 0.000 (positions) |
| Coréférence exacte | eval_30 (3) | 3/3 | 3/3 | — |
| Détection, macro-F1 | pilote, gold A (60) | 0.603 [0.475 ; 0.722] (0.519) | 0.603 | 0.348 |
| Détection, macro-F1 | pilote, gold B (60) | 0.737 [0.594 ; 0.860] (0.635) | 0.737 | 0.406 |
| Détection, macro-F1 | pilote, accord de label (47) | 0.741 [0.580 ; 0.881] (0.619) | 0.741 | 0.397 |
| Détection, exactitude | pilote, accord de label (47) | 0.809 (0.745) | 0.809 | 0.660 |
| Détection, rappel | pilote, chaque gold | 1.000 | 1.000 | 1.000 |
| Modalité, exactitude | pilote, gold A / gold B | 0.600 / 0.450 (0.567 / 0.467) | 0.633 / 0.483 | 0.533 / 0.433 |
| Modalité, macro-F1 | pilote, accord de modalité (35) | 0.408 (0.363) | 0.449 | 0.136 |

- **Extracteur − baseline, macro-F1 de détection** : +0.255 [+0.126 ; +0.369] (A),
  +0.331 [+0.179 ; +0.445] (B), +0.344 [+0.174 ; +0.472] (accord).
- **Macro-F1 de modalité** : l'IC exclut 0 contre les trois gold en mode parseurs. En mode règles,
  il exclut 0 contre A et sur l'accord, mais pas contre B : +0.119 [−0.003 ; +0.232].
- **Ablation** (`python -m linguistic_analysis.ablation`) :
  - les règles de factualité portent la détection : −0.324 sur eval_30, −0.115 et −0.141 de
    macro-F1 sur le pilote ;
  - les verbes de parole portent le triplet (−5/22) ;
  - la coréférence n'agit que sur `resolved_text`.

## 5. Usage prévu

- Prévu : extraire les affirmations vérifiables de textes de presse et de commentaires en français,
  arabe standard et tunisien, pour le tri du Lot C et la recherche de preuves du Lot D.
- Hors périmètre : vérité des affirmations ; autres dialectes arabes ; anglais ; textes d'un seul
  mot.

## 6. Limitations

Cinq dimensions. Les chiffres viennent d'EXP-B-010 (test gelé), sauf mention contraire.

### 6.1 Données
- **Test P061–P600 synthétique** : 540 textes synthétiques générés par un modèle de langue par catégorie (blocs consécutifs), annotés à la main par un seul annotateur (Lot C) ; protocole de génération à documenter par le Lot C. Les scores mesurés sur ces données sont
  **probablement optimistes**. Sur le pilote P01–P60, textes fournis par le Lot A1 (dont des
  phrases Tunifact attestées) ; provenance de chaque texte non certifiée : la macro-F1 de
  détection y est de 0.52 à 0.64 (EXP-B-009, avant les règles R1, R2 et R4). eval_100 (textes
  réels) reste la mesure de référence à venir.
- **Un seul annotateur sur le test** : pas de kappa ni de gold adjugé. 47 textes sur 540 sont
  marqués « doute » ; sur ces textes, le macro-F1 de détection tombe à 0.668 (0.780 sur les 493
  autres).
- **Même annotateur** que le gold A du pilote.
- **P061–P600 a servi à entraîner le Model 1 du Lot C** : 428 de ces 540 textes sont dans son
  entraînement, et 112 dans son test gelé (120 identifiants). Une comparaison équitable avec le
  Model 1 ne peut porter que sur ces 112 textes.
- **Jeux de mise au point optimistes** : eval_30 (34 phrases, 1.000 en détection et en modalité)
  et le pilote P01–P60 (kappa 0.615, modalité 0.390) ont servi à régler les règles, dont R1, R2
  et R4.
- **Désaccord guide / gold** : une salutation seule est annotée `assertif` dans le test, alors que
  R1 donne `souhait`. Cela touche 5 des 40 erreurs analysées (catégorie E8).

### 6.2 Langues
- **Le tunisien en lettres arabes est le groupe le plus faible** : macro-F1 de détection 0.713,
  exactitude de modalité 0.667, macro-F1 de modalité 0.573 (81 textes), contre 0.731 à 0.868 pour
  les autres groupes.
- Le Lot A2 classe 41 de ces 81 textes comme arabe standard. Dans les 5 cas vérifiés de l'analyse
  d'erreurs, forcer la langue `tn` ne change pas la sortie.
- **Pas de parseur pour le tunisien ni pour l'arabizi** : ces textes passent toujours par les
  règles. Les parseurs n'apportent rien de mesurable sur le test (+0.004 [−0.004 ; +0.013]).
- **Langue par document** : une seule langue par `Document`. Le code-switching dans la phrase
  n'est pas modélisé.

### 6.3 Phénomènes linguistiques
- **Défaut `assertif`** : une phrase sans marqueur connu est assertive. Sur le test : opinion →
  assertif 55/84, souhait → assertif 30/47, rapporté → assertif 33/92, hypothétique → assertif
  17/39. Sur les 40 erreurs analysées, 25 viennent d'un lexique ou d'une règle incomplets (E3).
- **Hypothèse** : la règle française ne couvre que « si » + imparfait (7 erreurs analysées sur 40).
- **Futur** : il n'a pas de label propre. L'indice de futur est détecté, mais la phrase reste
  `assertif` (exemples P145, P254). Le futur n'est pas mesuré séparément.
- **Négation** : elle n'est mesurée que sur eval_30 (3 phrases, jeu de mise au point). Sa portée
  n'est pas mesurée sur le test.
- **Phrases complexes** (coordination, relatives, apposition) : non traitées. Une phrase donne au
  plus un triplet.
- **Triplet et coréférence mesurés sur peu de cas** : triplet exact 20/22 sur eval_30 (mise au
  point), 1/7 en règles et 2/7 en parseurs sur silver_40 ; coréférence 3/3 sur eval_30 et 0/1 sur
  silver_40. Aucun gold de triplet ni de coréférence sur le test.
- **Seuil de 4 mots** : un texte plus court n'a aucune phrase candidate (affirmation manquée,
  P506).
- **« Titre / corps » non traité** : un titre sans ponctuation peut être fusionné avec la première
  phrase du corps.

### 6.4 Robustesse et biais
- **Robustesse aux perturbations de surface (INV, EXP-B-014)** : 7 perturbations à sens conservé
  sur le test gelé, une par texte et par type (graine 20261015). Δ macro-F1 de détection, mode
  règles [IC 95 %] :
  - casse (155 textes) et diacritiques (9) : aucun changement ;
  - faute de frappe (534) : −0.019 [−0.034 ; −0.006], 1.9 % de décisions changées ;
  - élongation (532) : −0.007 [−0.018 ; +0.001], non établi ;
  - variantes arabizi (146) : +0.000 [−0.023 ; +0.023] ; la langue du Lot A2 change pour 11.6 %
    de ces textes ;
  - « !! » ou émoji en fin de texte (540) : −0.016 [−0.030 ; −0.004] ;
  - **ponctuation retirée (341) : −0.137 [−0.178 ; −0.097]**, 12.0 % de décisions changées.
    Sur les 50 questions, celles qui gardent un mot interrogatif du lexique ne changent pas (0 sur
    10, effectif non interprétable) ; les autres changent presque toutes (39 sur 40). **La
    reconnaissance des questions repose presque entièrement sur le point d'interrogation ; le
    lexique interrogatif ne compte que 6 entrées ; limite de couverture, non corrigée (système
    gelé).** Le mode parseurs donne des chiffres très proches.
- **Comparaison avec le Model 1 du Lot C (EXP-B-013)**, sur les 112 textes de son test gelé
  présents dans P061–P600 : macro-F1 binaire 0.803 [0.725 ; 0.874] contre 0.825 [0.742 ; 0.893]
  pour le TF-IDF ; différence −0.023 [−0.124 ; +0.076], **non établie**, ni par langue.
  Contre XLM-R + LoRA du Lot C (3 graines, moyenne ± écart-type) :
  - global : XLM-R 0.851 ± 0.015 contre Lot B 0.803, écart **non établi** ;
  - tunisien (60 textes) : XLM-R 0.816 ± 0.030 contre Lot B 0.707, écart **non établi** ;
  - seul écart établi : **tunisien en lettres arabes**, Lot B 0.542 contre XLM-R 0.907 (n = 18,
    établi pour 3 graines sur 3). À lire avec prudence : 18 textes seulement, et 6 sous-groupes
    de langue comparés.
  - XLM-R est entraîné sur 428 autres textes de P061–P600 (même source synthétique), ce qui
    l'avantage.
- **Biais par source et par sujet : non mesurés.** Un seul indice : sur silver_40, les textes de
  forum TArC donnent 24 affirmations prédites sur 30, alors que le gold n'en compte aucune
  (macro-F1 de détection 0.167). Sur Tunifact, la détection vaut 1.000, mais ce jeu ne contient
  que des affirmations. Le comportement dépend donc fortement du genre de texte.
- **Pas de calibration** : `certainty` et `confidence` sont des scores heuristiques, non calibrés
  (ECE non mesurée).

### 6.5 Usage
- **Décision L5 (répartition des rôles)** : le Model 1 du Lot C écarte AUTRE et OPINION ; le Lot B
  fournit l'extraction et la modalité, opinion comprise. La classe (Lot C) et la modalité (Lot B)
  sont des annotations distinctes.
- **Le Lot B ne filtre pas la classe AUTRE.** `is_claim` ne sépare que les opinions, questions,
  souhaits et hypothèses. Les récits personnels et les faits privés de forme assertive restent des
  candidates : 58 AUTRE sur 175 sont prédits affirmation, et 4 des 40 erreurs analysées sont dans
  ce cas (E9). Le tri de vérifiabilité est le **rôle du Lot C** (`filter_checkworthy`). Le Lot B
  favorise le rappel : 0.986 sur le test.
- **Salutation suivie d'une affirmation dans la même phrase (R1)** : sans indice factuel, la phrase
  reçoit `souhait` et l'affirmation est perdue. Exemple inventé : « Bonjour à tous, les prix du
  pain ont encore augmenté ».
- **Requête polie (R2)** : une demande d'information polie sans point d'interrogation reçoit
  `souhait` au lieu d'`interrogatif`. La détection reste juste.
- **Hors périmètre** : la vérité des affirmations, les autres dialectes arabes, l'anglais.
- **Éthique** : les lexiques contiennent des mots isolés, aucun texte d'annotation. Les données
  annotées restent hors dépôt.
