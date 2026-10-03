# `linguistic_analysis/` — Lot B : Analyse linguistique

**Responsable : Membre 3 · Branche : `lot-b-linguistic`**

## Rôle
Identifier dans un document normalisé les **affirmations candidates** et les analyser :
- segmentation en phrases ;
- **POS** et **analyse en dépendances** (spaCy pour le FR, Stanza pour l'arabe) ;
- distinction **fait / opinion** ;
- extraction **Sujet–Prédicat–Objet** (SPO) ;
- **modalité** : assertif, rapporté (« selon… », « aurait… »), conditionnel, hypothétique, opinion, interrogatif, souhait ;
- **coréférence** pour rendre chaque affirmation autonome (« Il a annoncé… » → « Le ministre X a annoncé… ») ;
- règles linguistiques (entités, chiffres, dates) comme indices de vérifiabilité.

## Entrées / sorties
- Entrée : `common.schemas.Document` (sortie du Lot A2).
- Sortie : `list[common.schemas.Claim]` avec `text`, `span`, `subject`, `predicate`, `obj`, `modality`.
- Point d'entrée : `linguistic_analysis.claim_extraction.extract_claims(doc) -> list[Claim]`.
- Le score de vérifiabilité (`checkworthiness`) est ensuite calculé par le Lot C.
- Les informations supplémentaires (texte résolu, certitude, confiance, parseur) sont portées par
  `types.ExtractedClaim`, interne au module ; `ExtractedClaim.to_claim()` projette vers le contrat partagé.

## Installation

Les dépendances `spacy` et `stanza` figurent déjà dans `requirements.txt`. Les modèles se téléchargent à part :

```bash
pip install -r requirements.txt            # ou : pip install spacy stanza
python -m spacy download fr_core_news_md
python -c "import stanza; stanza.download('ar', processors='tokenize,mwt,pos,lemma,depparse')"
```

Stanza stocke ses modèles dans `~/stanza_resources` (hors dépôt, environ 600 Mo avec PyTorch).

**Sans ces bibliothèques ou modèles, le module fonctionne quand même** : `preprocessing.get_parser`
renvoie `None` et l'analyse bascule sur les règles. C'est le mode utilisé par la CI, qui n'installe
que `requirements-dev.txt`.

## Structure

| Fichier | Contenu |
|---------|---------|
| `claim_extraction.py` | Point d'entrée `extract_claims`, segmentation, sélection des candidats |
| `types.py` | `ExtractedClaim`, `MODALITY_LABELS`, adaptateur `to_claim()` |
| `preprocessing.py` | Chargement paresseux et mis en cache des pipelines spaCy / Stanza (`get_parser`) |
| `factuality.py` | Fait vs opinion (lexiques + patrons syntaxiques) |
| `spo.py` | Extraction SPO sur l'arbre de dépendances, repli positionnel |
| `modality.py` | Modalité et score de certitude |
| `coreference.py` | Résolution de coréférence par règles |
| `io_contract.py` | (Dé)sérialisation JSON du contrat d'entrée/sortie |
| `resources/` | Lexiques FR / AR / TN (verbes d'opinion, marqueurs de modalité…) |

Tests : `tests/test_linguistic_analysis.py`, données dans `tests/fixtures/linguistic_analysis/`.

## Choix techniques
- **FR** : spaCy `fr_core_news_md` (bon compromis taille / qualité des dépendances, morphologie
  disponible pour le conditionnel et l'accord).
- **AR (MSA)** : Stanza, entraîné sur l'Universal Dependencies arabe (PADT), avec un étiquetage UD
  cohérent avec celui du français, ce qui permet de partager les règles SPO.
- **Tunisien** : aucun parseur mature. Règles lexicales et positionnelles, en lettres arabes et en arabizi.
- **Chargement paresseux** : aucun import de spaCy/Stanza à l'import du module ; chaque pipeline est
  chargé une fois (`functools.lru_cache`) au premier appel.

## Conventions
- Les `span` sont des positions de caractères dans `Document.text`.
- Les tests nécessitant spaCy ou Stanza sont marqués `@pytest.mark.slow` (ignorés en CI).
- Comparer règles vs. modèles et consigner les résultats (précision/rappel de l'extraction) dans `experiments.md`.
