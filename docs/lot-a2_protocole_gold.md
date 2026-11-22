# Lot A2 — Protocole Gold : robustesse, baseline externe, fuites et mesure unique

**Responsable : Abd Elmouhib Souri (Membre 2, Lot A2) · Version 1 · 2026-11-22**

Ce fichier est écrit et commité **avant toute mesure du Gold**. Une mesure faite avant ce commit
ne compte pas. Pendant les mesures du Gold, aucune règle, aucun lexique et aucun seuil du Lot A2
n'est modifié : une correction éventuelle devient une nouvelle expérience, déclarée comme telle
dans `experiments.md` et remesurée.

## 1. Système mesuré

| Élément | Valeur (fixée) |
|---|---|
| Identification de langue et d'écriture | `detect_language`, `detect_script` (`normalization/normalize.py`), comportement identique au commit `c95b9b4` |
| Normalisation | `normalize()`, même commit |
| Modèle tunisien | cascade lexique → MARBERTv2 d'EXP-A2-015, figée : lr 2e-5, 4 époques, seuil 0.30 ; **non intégrée** à `normalize.py` (protocole du modèle tunisien, §4) |
| Graine | 20261122 (perturbations et bootstrap) |
| Intervalles | bootstrap percentile, 1 000 tirages, IC à 95 % |

## 2. Questions

1. **Robustesse (INV)** : l'étiquette de langue reste-t-elle la même quand on modifie la surface
   d'un texte sans en changer le sens ?
2. **Baseline externe** : que donne un identifiant de langue générique (fastText lid.176) face
   aux règles du Lot A2 ?
3. **Fuites** : des textes du test gelé figurent-ils déjà dans l'entraînement ou le dev ?
4. **Accord humain** : les deux annotateurs s'accordent-ils sur la langue du test gelé ?
5. **Question de recherche** (protocole du modèle tunisien) : la cascade relève-t-elle le rappel
   du tunisien en lettres arabes sans perdre en précision, sur le test gelé ?

## 3. Statut réel au 2026-11-22 (avant toute mesure)

| Élément | État |
|---|---|
| Test gelé (300 textes, annotateur 1) | **0 / 300** annotés |
| Test gelé (300 textes, annotatrice 2) | **0 / 300** annotés |
| Textes communs du kappa (160, annotatrice 2) | **0 / 160** annotés |
| Entraînement (800 textes, annotateur 1) | 800 / 800 annotés |
| Cascade MARBERTv2 | validation croisée seulement (EXP-A2-015) ; entraînement final non fait |
| EXP-A2-014 (PR #28) et EXP-A2-015 (PR #31) | non fusionnées sur `main` |
| Translittération arabizi → arabe | stub (§10) |

## 4. Jeux de données et usages autorisés

| Jeu | Effectif, empreinte | Usage autorisé dans le Gold |
|---|---|---|
| Dev lettres arabes (`tsac_arabic_sample_reference.tsv`, EXP-A2-009) | 100 (77 `t`, 23 `a`), SHA-256 `a59f3d27…` | INV, fastText, fuites |
| Dev lettres latines (`tsac_latin_sample_reference.tsv`, EXP-A2-009) | 86 (70 `t`, 16 `f`), SHA-256 `1703f003…` | INV, fastText, fuites |
| Entraînement du modèle tunisien | 800, SHA-256 de la liste ordonnée `5b4f40b9…` | fuites (empreintes) ; entraînement final |
| Test gelé | 300, SHA-256 de la liste ordonnée `a579a57d…` | fuites (empreintes seulement) ; **mesure unique** (§9) |
| eval_30 (Lot B, commit `85fb77d`) | 34, SHA-256 `1d0bcfaa…` | fuites (empreintes) ; non-régression unique, à la fin |
| Presse neuve (Leipzig `ara_news`, règle du §9) | 300 phrases, empreintes consignées avant la mesure | fausses alertes, unique, à la fin |

Règles communes :
- les empreintes complètes sont celles d'EXP-A2-011 et du protocole du modèle tunisien ; chaque
  script vérifie l'empreinte de ses fichiers et **refuse de tourner** si elle ne correspond pas ;
- les scripts qui lisent des données sont lancés par le responsable du lot ; ils n'affichent que
  des effectifs, des scores et des empreintes, jamais le contenu d'une ligne ; en cas d'erreur,
  seulement le numéro de ligne et le type d'exception ;
- aucune sortie contenant du texte n'est versionnée.

## 5. EXP-A2-016 — Robustesse INV (dev seulement)

Perturbations (fixées maintenant, une à la fois, tirage déterministe avec la graine) :

| Code | Perturbation | S'applique à |
|---|---|---|
| P1 | tout en minuscules | lettres latines |
| P2 | tout en majuscules | lettres latines |
| P3 | une lettre d'un mot répétée 3 fois (élongation) | tous |
| P4 | tatweel inséré dans un mot | lettres arabes |
| P5 | diacritiques ajoutés à des lettres | lettres arabes |
| P6 | formes de présentation (ligature lam-alef, forme NFKC inverse) | lettres arabes contenant « لا » |
| P7 | émoji ajouté en fin de texte | tous |
| P8 | URL ajoutée en fin de texte | tous |
| P9 | ponctuation répétée (« !!! ») ajoutée | tous |
| P10 | espaces multiples et espace insécable | tous |

Un texte n'est compté pour une perturbation que si elle le modifie (effectif applicable rapporté).

Mesures :
- **taux de bascule** : part des textes dont `detect_language` change après perturbation, par
  perturbation et par écriture, avec IC ;
- exactitude et macro-F1 avant / après contre les références, écart apparié avec IC ;
- deux invariants sans étiquette : idempotence (`normalize(normalize(x)) == normalize(x)`) et
  cohérence (`detect_language(x) == detect_language(normalize(x))`) ;
- baselines : « alphabet seul » (EXP-A2-011) et fastText (§6), mêmes perturbations.

**Règle de décision (fixée avant toute mesure)** : par perturbation et par écriture, sur
l'intervalle de Wilson à 95 % du taux de bascule :
- **indéterminé** si l'effectif applicable est inférieur à 30 ;
- **robuste** si la borne haute de l'intervalle est ≤ 0.05 ;
- **fragile** si la borne basse de l'intervalle est > 0.02 ;
- sinon **indéterminé**.

Attendu écrit avant mesure : P2 risque d'être fragile (limite connue, test `xfail` « mot seul
tout en majuscules »). Aucun résultat n'entraîne de correction dans le Gold.

## 6. EXP-A2-017 — Baseline externe : fastText lid.176 (dev seulement)

- Modèle : `lid.176.bin` (fastText, 176 langues, CC BY-SA 3.0), dans `models/checkpoints/`, non
  versionné ; son SHA-256 est consigné au téléchargement ; import seulement dans le module de
  baseline, jamais dans `normalize()`.
- Correspondance des étiquettes pour le score (fixée maintenant) : `ar`, `arz` → `ar` ; `fr` →
  `fr` ; toute autre étiquette → `autre` (comptée comme erreur). lid.176 n'a pas d'étiquette
  tunisienne : son rappel `tn` est nul par construction. C'est le constat attendu : un
  identifiant générique ne voit pas le tunisien.
- Chiffre informatif séparé, hors score : part des textes de référence `t` que lid.176 étiquette
  `arz` (arabe égyptien), par écriture.
- Mesures : exactitude et macro-F1 sur chaque dev ; écart apparié règles − fastText avec IC ;
  taux de bascule sous les perturbations du §5.
- **Limite de temps** : 1 h pour l'installation. Si `fasttext-wheel` ne s'installe pas sous
  Windows avec Python 3.10, EXP-A2-017 est rapportée « non réalisée », avec la raison, et aucune
  autre baseline n'est improvisée.

## 7. EXP-A2-018 — Audit des fuites par empreintes

- Deux empreintes par texte : SHA-256 du texte brut sans espaces de bord, et SHA-256 de
  `" ".join(normalize(texte).split())`.
- Jeux : test gelé, entraînement, dev lettres arabes, dev lettres latines, eval_30.
- Résultats : doublons internes de chaque jeu, et intersection de chaque paire de jeux, en
  **effectifs seulement**. Les numéros de ligne concernés restent dans un fichier local, hors dépôt.
- **Règle de décision (fixée maintenant)** : si le test gelé partage au moins un texte avec
  l'entraînement ou le dev, ces textes sont retirés du test **avant** la mesure, par un avenant
  daté au protocole du modèle tunisien (§5), et l'effectif final est rapporté.
- Limite : seuls les doublons exacts sont repérés, pas les quasi-doublons.

## 8. EXP-A2-019 — Accord entre annotateurs et adjudication

- Jeux : 160 textes communs (lignes 1 à 160 de l'entraînement) et test gelé (300).
- Annotation : chacun seul, sans assistance, sans voir les étiquettes de l'autre ni aucune
  proposition de LLM (avenant 1 du protocole du modèle tunisien) ; étiquettes `t`, `a`, `f`, `x`.
- Mesures : kappa de Cohen avec IC, accord brut, matrice de confusion entre annotateurs.
- Adjudication : le script ne liste que les numéros de ligne en désaccord. Les décisions sont
  prises par les deux annotateurs en séance, une règle écrite par décision (comme EXP-A2-009),
  jamais par un outil ni par un LLM. Le SHA-256 du fichier de référence adjugé est consigné dans
  EXP-A2-019 avant la mesure du §9.
- **Règle si l'annotatrice 2 manque** : si la seconde annotation du test n'est pas complète au
  moment de la mesure :
  - aucun kappa n'est rapporté pour le test ; la mention est « **accord humain non mesuré** » ;
  - la référence est l'annotation de l'annotateur 1 seul ; c'est un écart au protocole du
    modèle tunisien (§2 : « annoté par deux personnes, adjugé »), écrit en avenant daté **avant**
    la mesure (avenant 2) ;
  - le résultat est qualifié d'**indicatif** : on ne conclut pas « critères atteints » ou « non
    atteints » au sens du protocole ;
  - si seuls les 160 textes communs sont doublement annotés, leur kappa est rapporté, et le test
    reste signalé comme annoté par une seule personne.

## 9. EXP-A2-020 — Mesure unique sur le test gelé

Préconditions, toutes nécessaires :
1. ce protocole est commité ;
2. EXP-A2-018 est faite, et les retraits éventuels sont déclarés ;
3. la référence du test est adjugée (ou §8 appliqué), et son SHA-256 est consigné ;
4. la cascade est entraînée **une seule fois** sur les 800 textes, configuration figée
   (EXP-A2-015), avec 3 graines (1, 2, 3 ; avenant 2 du protocole du modèle tunisien) ; les
   prédictions sur le test sont écrites dans un fichier dont le SHA-256 est consigné avant tout
   calcul de score.

Presse neuve (règle fixée maintenant, avant tout téléchargement) :
- corpus Leipzig `ara_news` de l'année la plus récente disponible au téléchargement, différente
  de 2022 (2022 a servi au réglage Silver), en version 10K ; si plusieurs fichiers existent pour
  cette année, on prend `ara_news_<année>_10K` ;
- tirage de 300 phrases avec la graine 42 ;
- l'année retenue, l'URL et le SHA-256 de l'archive et de l'échantillon sont consignés dans
  EXP-A2-020 **avant** la mesure ;
- si aucune année autre que 2022 n'est disponible, EXP-A2-020 rapporte le critère « fausses
  alertes » comme **non mesuré**.

Le script de mesure :
- refuse de tourner si l'empreinte de la liste ordonnée du test (`a579a57d…`), de la référence
  ou des prédictions ne correspond pas ;
- n'a aucune option pour changer le seuil, le modèle ou les jeux ;
- calcule les quatre critères du protocole du modèle tunisien (§4), recopiés sans changement :
  rappel `tn` ≥ 0.70 ; précision `tn` ≥ 0.90 ; ≤ 1 % de fausses alertes sur la presse neuve ;
  aucune baisse du macro-F1 sur eval_30 (0.94) ;
- rapporte, sur le même test, la baseline « lexique seul » et la moyenne ± écart-type sur les
  3 graines, avec un IC bootstrap par graine ; les critères sont jugés sur la moyenne.

Une seule exécution. Toute relance est déclarée comme 2e passage. Même si les critères sont
atteints, l'intégration de la cascade dans `normalize.py` ne fait pas partie de ce Gold (règle de
la bibliothèque standard) : elle relève d'un module facultatif et d'une décision séparée.

Si EXP-A2-020 n'est pas exécutée avant la validation Gold, elle est rapportée comme non réalisée
à la date du Gold, sans résultat partiel.

## 10. Limite : translittération arabizi → lettres arabes

`arabizi_to_arabic` renvoie le texte inchangé. Il n'existe aucun jeu de référence de
translittération : une table écrite d'ici le Gold ne pourrait pas être mesurée, elle n'est donc
pas implémentée. L'arabizi reste **identifié** comme du tunisien (eval_30 : 5 / 5 ; dev lettres
latines : F1 `tn` 0.94, EXP-A2-011), mais pas converti. Conséquence pour le Lot D : la recherche
BM25 sur l'arabizi n'a pas de forme arabe à comparer (`rag_llm/README.md`). Perspective : un jeu
de paires arabizi / arabe annoté par deux personnes, puis une table mesurée.

## 11. Limites connues avant mesure

- INV et fastText sont mesurés sur le dev, qui a servi à la mise au point : leurs chiffres ne
  valent pas pour une généralisation.
- Effectifs petits (100 et 86), donc IC larges.
- Avec 100 textes et aucune bascule, la borne haute de Wilson vaut environ 0.037 : la règle
  « robuste » est atteignable ; avec 86 textes, environ 0.043.
- INV porte sur les règles, pas sur la cascade (aucun modèle n'est chargé localement).
- Les perturbations sont synthétiques.
- Le test vient de TSAC, comme les marques du lexique (protocole du modèle tunisien, §2).
- Les biais par source ou par sujet ne sont pas mesurés dans ce Gold (seulement par écriture et
  par langue) ; le biais des noms de lieux est traité dans EXP-A2-005.

## 12. Ordre et identifiants

| Étape | Jeu | Identifiant réservé |
|---|---|---|
| Robustesse INV | dev | EXP-A2-016 |
| Baseline fastText lid.176 | dev | EXP-A2-017 |
| Audit des fuites | tous (empreintes) | EXP-A2-018 |
| Accord et adjudication | 160 communs + test | EXP-A2-019 |
| Mesure unique de la cascade | test gelé, presse neuve, eval_30 | EXP-A2-020 |

EXP-A2-014 (PR #28) et EXP-A2-015 (PR #31) sont déjà prises. Chaque identifiant reçoit son
entrée dans `experiments.md`, même si le résultat est négatif ou si l'étape n'est pas réalisée.

## 13. Interdits

- Régler quoi que ce soit (règle, lexique, seuil, modèle, perturbation) sur le test gelé ou
  sur eval_30.
- Relancer la mesure du §9 sans la déclarer comme 2e passage.
- Faire adjuger ou annoter par un outil ou un LLM.
- Versionner un texte, une annotation, une sortie contenant du texte ou un poids de modèle.
- Intégrer MARBERTv2 dans `normalize()`.

## 14. Incidents

**2026-11-22, vers 9 h 35 — tentative d'affichage d'une ligne du test gelé.**
Lors d'un comptage des étiquettes, un script exécuté par l'assistant de code a chargé en mémoire
le fichier local `data/interim/langid/model_tn/test_frozen_300_annotateur1.tsv` et a tenté
d'afficher sa première ligne (fichier sans en-tête : la ligne contenait un texte du test).
L'affichage a échoué avant toute écriture (UnicodeEncodeError de la console Windows) : la sortie
ne contient que la trace d'erreur et des positions de caractères, aucun texte. Les fichiers
`test_frozen_300_annotateur2.tsv`, `train_160_annotateur2.tsv` et `train_800_annotateur1.tsv`
ont été lus localement par des scripts qui n'affichaient que des effectifs.

Impact : aucun texte du test n'a été affiché ni transmis. Aucune règle, aucun seuil ni aucun
choix de modèle n'en dépend, et aucun modèle du Lot A2 n'a lu ces fichiers. Le test gelé est
conservé tel quel (300 textes, empreinte inchangée).

Mesures prises le même jour : interdiction de lecture de `data/` et des fichiers d'annotation pour
l'outil ; scripts sur données lancés uniquement par le responsable du lot, avec des sorties
limitées aux effectifs, aux scores et aux empreintes, y compris en cas d'erreur ; option
d'entraînement du compte désactivée. L'incident a été signalé à l'équipe le 22/11.
