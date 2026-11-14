# Carte de modèle — extraction d'affirmations du Lot B

Composant : `linguistic_analysis/claim_extraction.py`
(`extract_claims(doc: Document) -> list[Claim]`, version détaillée `extract_claims_detailed`).
Système à règles et lexiques, avec analyseurs syntaxiques facultatifs. Aucun apprentissage, aucun
poids appris. Journal : EXP-B-001 à EXP-B-009.

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

### Deux modes

| Mode | Analyse | Usage |
| --- | --- | --- |
| règles | règles et lexiques seulement, pour toutes les langues | CI, environnement sans modèle (`evaluate --rules`) |
| parseurs | spaCy `fr_core_news_md` (français), Stanza `ar` (arabe standard) ; règles pour le tunisien et les langues inconnues | défaut si les modèles sont installés |

Les modèles spaCy et Stanza sont chargés paresseusement. S'ils manquent, le mode règles prend le
relais.

## 3. Données de mise au point

| Jeu | Contenu | Rôle |
| --- | --- | --- |
| eval_30 (`tests/fixtures/linguistic_analysis/eval_30.jsonl`) | 34 phrases, 5 groupes (`fr-latin`, `ar-arabic`, `tn-arabic`, `tn-arabizi`, `tn-mixed`), gold complet (affirmation, modalité, triplet sur 22 phrases, coréférence sur 3) | jeu de développement : les règles ont été réglées dessus (EXP-B-001 à EXP-B-006) |
| Pilote du Lot A1 (P01–P60) | 60 textes annotés par deux personnes (label, modalité ; pas de triplet) ; langue selon le Lot A2 : fr 26, ar 15, tn-arabizi 19 | première mesure (EXP-B-008, EXP-B-009) ; a aussi servi à choisir des corrections : ce n'est plus un jeu de test. Fichiers hors dépôt |

Le jeu de test neuf, à geler avant toute mesure, sera mesuré dans EXP-B-010
(`docs/lot-b_protocole_eval_100.md`).

## 4. Résultats

Bootstrap percentile 95 %, graine 20261015, 1000 tirages ; différences appariées : graine 42,
2000 tirages.

| Mesure | Jeu | Règles | Parseurs | Baseline |
| --- | --- | --- | --- | --- |
| Détection, exactitude | eval_30 (34) | 1.000 | 1.000 | 0.647 (« tout = affirmation ») |
| Modalité, exactitude | eval_30 (34) | 1.000 | 1.000 | 0.412 (classe majoritaire) |
| Triplet exact | eval_30 (22) | 0.909 (20/22) | 0.864 (19/22) | 0.000 (positions) |
| Coréférence exacte | eval_30 (3) | 3/3 | 3/3 | — |
| Détection, macro-F1 | pilote, gold A (60) | 0.519 [0.394 ; 0.644] | 0.519 | 0.348 |
| Détection, macro-F1 | pilote, gold B (60) | 0.635 [0.477 ; 0.773] | 0.635 | 0.406 |
| Détection, macro-F1 | pilote, accord de label (47) | 0.619 [0.439 ; 0.769] | 0.619 | 0.397 |
| Détection, rappel | pilote, chaque gold | 1.000 | 1.000 | 1.000 |
| Modalité, exactitude | pilote, gold A / gold B | 0.567 / 0.467 | 0.600 / 0.500 | 0.533 / 0.433 |
| Modalité, macro-F1 | pilote, accord de modalité (35) | 0.363 | 0.404 | 0.136 |

- Extracteur − baseline, en macro-F1 de détection : +0.17 à +0.23, avec un IC apparié qui exclut 0
  contre chaque gold.
- En macro-F1 de modalité : IC qui exclut 0 contre les trois gold en mode parseurs, contre A
  seulement en mode règles.
- Ablation (EXP-B-009, `python -m linguistic_analysis.ablation`) :
  - les règles de factualité portent la détection sur eval_30 (−0.324 sans elles) ;
  - les verbes de parole portent le triplet (−5/22) ;
  - la coréférence n'agit que sur `resolved_text`.

## 5. Usage prévu

- Prévu : extraire les affirmations vérifiables de textes de presse et de commentaires en français,
  arabe standard et tunisien, pour le tri du Lot C et la recherche de preuves du Lot D.
- Hors périmètre : vérité des affirmations ; autres dialectes arabes ; anglais ; textes d'un seul
  mot.

## 6. Limitations

- **Pas de parseur pour le tunisien ni pour l'arabizi** : ces textes passent toujours par les règles,
  dans les deux modes. Sur le pilote, le groupe tn-arabizi est le plus faible (détection 0.263 et
  0.368 en exactitude).
- **Scores eval_30 optimistes** : les règles ont été réglées sur ce jeu. Les 1.000 en détection et
  en modalité ne se généralisent pas (pilote : 0.617 / 0.767 et 0.567 / 0.467).
- **Pilote non adjugé** : les deux annotations divergent (kappa label 0.615, modalité 0.390). Les
  mesures sont données contre chaque annotateur et sur les textes où ils s'accordent. Aucune n'est
  un gold définitif. Le pilote a aussi servi à la mise au point.
- **Coréférence mesurée sur 3 phrases** seulement (eval_30). Aucun gold de coréférence sur le
  pilote.
- **« Titre / corps » non traité** : un article est vu comme une suite de phrases. Un titre sans
  ponctuation peut être fusionné avec la première phrase du corps, et aucun lien titre → corps
  n'est fait.
- **Lexiques de modalité possiblement sur-ajustés à eval_30** : sur le pilote, les retirer améliore
  la modalité (+0.06 à +0.08 de macro-F1 sur l'accord), alors qu'ils servent sur eval_30. À
  vérifier sur le jeu de test neuf avant toute retouche.
- **Unité phrase contre unité texte** : l'annotation du pilote est faite par texte. La mesure
  agrège les phrases (un texte est une affirmation si l'une de ses phrases l'est), ce qui favorise
  le rappel au détriment de la précision.
- **Classe AUTRE** (salutations, demandes, récits personnels) : sans équivalent direct dans
  `is_claim`, c'est la première source de faux positifs.
- **Éthique** : les lexiques contiennent des mots isolés, aucun texte d'annotation. Les données
  annotées restent hors dépôt.
