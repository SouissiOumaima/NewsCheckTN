# `linguistic_analysis/` — Lot B : Analyse linguistique

**Responsable : Membre 3 · Branche : `lot-b-linguistic`**

## Rôle
Identifier dans un document normalisé les **affirmations candidates** et les analyser :
- segmentation en phrases ;
- **POS** et **analyse en dépendances** (spaCy pour le FR, Stanza pour l'arabe) ;
- extraction **Sujet–Prédicat–Objet** (SPO) ;
- **modalité** : assertif, conditionnel, rapporté (« selon… », « aurait… »), interrogatif, opinion ;
- **coréférence** pour rendre chaque affirmation autonome (« Il a annoncé… » → « Le ministre X a annoncé… ») ;
- règles linguistiques (entités, chiffres, dates) comme indices de vérifiabilité.

## Entrées / sorties
- Entrée : `common.schemas.Document` (sortie du Lot A2).
- Sortie : `list[common.schemas.Claim]` avec `text`, `span`, `subject`, `predicate`, `obj`, `modality`.
- Point d'entrée : `linguistic_analysis.claim_extraction.extract_claims(doc) -> list[Claim]`.
- Le score de vérifiabilité (`checkworthiness`) est ensuite calculé par le Lot C.

## Organisation suggérée
| Fichier | Contenu |
|---------|---------|
| `claim_extraction.py` | Point d'entrée, segmentation, sélection des candidats |
| `parsing.py` | Chargement paresseux des pipelines spaCy / Stanza par langue |
| `spo.py` | Extraction SPO sur l'arbre de dépendances |
| `modality.py` | Règles de modalité |
| `coreference.py` | Résolution de coréférence |
| `rules/` | Lexiques de déclencheurs (verbes de parole, marqueurs d'opinion…) |

## Conventions
- Les modèles spaCy/Stanza sont chargés **une seule fois** et **à la demande** (pas à l'import du module).
- Les `span` sont des positions de caractères dans `Document.text`.
- Comparer règles vs. modèles et consigner les résultats (précision/rappel de l'extraction) dans `experiments.md`.
