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
- `extract_claims` ne filtre pas les opinions : la décision de les écarter n'est pas encore prise
  au niveau de l'équipe (l'information reste disponible dans la sortie détaillée).

## Sortie détaillée et contrat JSON

`extract_claims_detailed(doc) -> list[ExtractedClaim]` renvoie, pour chaque phrase candidate
(au moins 4 mots), les champs du contrat plus des champs **internes au Lot B** :

| Champ | Sens |
|-------|------|
| `resolved_text` | phrase rendue autonome par la coréférence (« Il a annoncé… » → « Le ministre a annoncé… ») |
| `resolution_log` | remplacements effectués (« Il → Le ministre ») |
| `source`, `time`, `location` | source de l'information : « selon l'INS » → `l'INS`, incise (« …, a déclaré le ministre » → `le ministre`), sinon locuteur d'un verbe de parole + complétive (antécédent si c'est un pronom résolu) ; temps (« en 2024 ») et lieu (« fi Gafsa ») retirés de l'objet, avec leur préposition |
| `modality`, `certainty` | label de `types.MODALITY_LABELS` et certitude dans [0, 1] |
| `is_opinion`, `confidence` | phrase non factuelle (opinion, question, souhait) et confiance |
| `is_claim` (propriété) | affirmation vérifiable : ni opinion, ni question, ni souhait, ni hypothèse |
| `parser`, `triggers` | parseur utilisé (`spacy-fr`, `stanza-ar`, `rules`) et indices déclencheurs |

`extract_claims(doc)` = `[c.to_claim() for c in extract_claims_detailed(doc)]`.

Contrat JSON (pour travailler sans les autres lots) — `io_contract.py` :
- entrée : une ligne JSON par document, au format `asdict(Document)`
  (`{"raw_text", "text", "lang", "script"}`), validée par `document_from_json` ;
- sortie : `{"claims": [...]}` par document, au format `Claim` (contrat) ou `ExtractedClaim` (`--detailed`).

```bash
python -m linguistic_analysis.io_contract tests/fixtures/linguistic_analysis/mock_documents.jsonl sortie.jsonl
python -m linguistic_analysis.io_contract tests/fixtures/linguistic_analysis/mock_documents.jsonl sortie.jsonl --detailed
```

Documents simulés : `tests/fixtures/linguistic_analysis/mock_documents.jsonl`, générés par
`make_mock_documents.py` à partir de la normalisation du Lot A2.

## Démonstration

```bash
python -m linguistic_analysis.demo "Je pense que le gouvernement devrait agir plus vite."
python -m linguistic_analysis.demo            # exemples FR / AR / tunisien
python -m linguistic_analysis.demo --rules "…"  # sans spaCy / Stanza ; --json pour la sortie brute
```

Affiche, phrase par phrase, l'affirmation vérifiable ou non, l'opinion, la modalité et la certitude,
le triplet et ses compléments (source, temps, lieu), la phrase résolue par coréférence et les indices déclencheurs. Contrairement à
`pipeline.py`, les phrases non vérifiables sont affichées (elles ne passent pas par le filtre du Lot C).

## Évaluation

Jeu annoté : `tests/fixtures/linguistic_analysis/eval_30.jsonl` (guide : `docs/lot-b_guide_annotation.md`).

```bash
python -m linguistic_analysis.evaluate --rules --errors   # règles seules (conditions de la CI)
python -m linguistic_analysis.evaluate --errors           # avec spaCy / Stanza
```

Résultats dans `evaluation/results/` ; analyse d'erreurs : `docs/lot-b_analyse_erreurs_bronze.md` ;
expériences `EXP-B-001` (Bronze), `EXP-B-002` (compléments hors objet), `EXP-B-003` (lexique
verbal du mode règles) et `EXP-B-004` (source du discours rapporté, complément du participe)
dans `experiments.md`.

## Installation

Les dépendances `spacy` et `stanza` figurent déjà dans `requirements.txt`. Les modèles se téléchargent à part :

```bash
pip install -r requirements.txt            # ou : pip install spacy stanza
python -m spacy download fr_core_news_md
python -c "import stanza; stanza.download('ar', processors='tokenize,mwt,pos,lemma,depparse')"
```

Stanza stocke ses modèles dans son cache utilisateur, hors dépôt : sous Windows
`%LOCALAPPDATA%\StanfordNLP\stanza\Cache\<version>\resources`. Le dossier exact s'obtient avec
`python -c "import stanza.resources.common as c; print(c.DEFAULT_MODEL_DIR)"` et peut être changé
via la variable d'environnement `STANZA_RESOURCES_DIR`.

**Sans ces bibliothèques ou modèles, le module fonctionne quand même** : `preprocessing.get_parser`
renvoie `None` et l'analyse bascule sur les règles. C'est le mode utilisé par la CI, qui n'installe
que `requirements-dev.txt`.

## Structure

| Fichier | Contenu |
|---------|---------|
| `claim_extraction.py` | Points d'entrée `extract_claims` et `extract_claims_detailed` |
| `types.py` | `ExtractedClaim`, `MODALITY_LABELS`, adaptateur `to_claim()`, propriété `is_claim` |
| `preprocessing.py` | Chargement paresseux et mis en cache des pipelines spaCy / Stanza (`get_parser`) |
| `factuality.py` | Fait vs opinion (lexiques + patrons syntaxiques) |
| `spo.py` | Extraction SPO sur l'arbre de dépendances, repli positionnel |
| `modality.py` | Modalité et score de certitude |
| `coreference.py` | Résolution de coréférence par règles |
| `io_contract.py` | (Dé)sérialisation JSON du contrat d'entrée/sortie, ligne de commande |
| `evaluate.py` | Évaluation sur le jeu annoté, export des résultats et des erreurs |
| `resources/` | Lexiques : `tn_lexicon.json` (étiquetage par règles), `opinion_<langue>.txt`, `modality_<langue>.json`, `speech_verbs.txt`, `adjuncts.json` (marqueurs de source, noms de temps, lieux), `verbs.json` (lexique verbal du mode règles) |

Tests : `tests/test_linguistic_analysis.py`, données dans `tests/fixtures/linguistic_analysis/`.

## Choix techniques
- **FR** : spaCy `fr_core_news_md` (bon compromis taille / qualité des dépendances, morphologie
  disponible pour le conditionnel et l'accord).
- **AR (MSA)** : Stanza, entraîné sur l'Universal Dependencies arabe (PADT), avec un étiquetage UD
  cohérent avec celui du français, ce qui permet de partager les règles SPO.
- **Tunisien** : aucun parseur mature. Règles lexicales et positionnelles, en lettres arabes et en arabizi.
- **Verbes sans parseur** (`resources/verbs.json`, `preprocessing.verb_lexicon`) : formes générées
  à partir de lemmes français en -er et de verbes de l'arabe standard au passé (passé, présent,
  futur ; و / ف collés retirés), plus des formes listées (irrégulières, auxiliaires, modaux,
  tunisien). Le ش / ch final de la négation ما…ش est retiré à la recherche. Un mot précédé d'un
  déterminant n'est pas un verbe (« la baisse »). Modal + infinitif forment le prédicat.
  Verbe arabe en tête : sujet jusqu'à une préposition, un nombre ou un complément si le verbe
  est intransitif (« ارتفع », « تراجع ») ; sinon chaîne d'annexion (« وزير الصحه ») et adjectifs
  de relation (« الوطنيه »). Avec un verbe intransitif, le complément d'un participe défini reste
  dans le sujet (« عدد السياح الوافدين على تونس »), sauf si la préposition est suivie d'un nombre.
  Limites : verbes absents de la liste, noms homographes d'un verbe (« سجل », « تراجع » en tête
  de phrase), participe reconnu à sa seule forme (noms de même forme : « الشارع »).
- **Chargement paresseux** : aucun import de spaCy/Stanza à l'import du module ; chaque pipeline est
  chargé une fois (`functools.lru_cache`) au premier appel.
- **Coréférence** : règles uniquement, sans bibliothèque externe. Seul le pronom sujet de la
  proposition principale (il/elle/ils/elles, هو/هي/هم, howa/hiya/houma) est remplacé par le sujet
  compatible le plus récent des deux phrases précédentes ; sans candidat sûr, la phrase est laissée
  inchangée. Le résultat est dans `ExtractedClaim.resolved_text` (avec `resolution_log`) ;
  `Claim.text` reste la phrase d'origine. La bibliothèque `coreferee` (extension spaCy) sera
  évaluée au palier Silver ; les pronoms affixes arabes (ـه، ـها، ـهم) restent à traiter.
- **Compléments hors objet** : la source, le temps et le lieu sont repérés par un lexique
  (`resources/adjuncts.json`), identique dans les deux modes : avec arbre, un tel complément n'est
  jamais choisi comme objet ; dans tous les cas, il est retiré de la fin de l'objet. Garde-fous :
  un nombre en tête (« 100 jours », « 2024 voitures ») reste dans l'objet, une année doit être
  précédée d'une préposition, un lieu doit figurer dans la liste (gouvernorats et villes de
  Tunisie). La complétive d'un verbe de parole reste entière. Limites : lieux absents de la liste
  (« au palais de Carthage »), préposition arabe collée (« بصفاقس »), compléments en milieu d'objet.
- **Source du discours rapporté** : « selon X » → X ; incise finale après une virgule
  (auxiliaire facultatif + verbe de parole + groupe nominal ; avec spaCy, `parataxis` dont la tête
  est un verbe de parole) → son groupe nominal, retiré de l'objet, modalité `rapporté` ; verbe de
  parole + complétive → le sujet. « حسب ما أفاد به X » → X. Sujet absent (« 9alou elli … ») :
  pas de source. Non mesuré sur `eval_30` (pas de source dans le gold) : tests ciblés seulement.

## Conventions
- Les `span` sont des positions de caractères dans `Document.text`.
- Les tests nécessitant spaCy ou Stanza sont marqués `@pytest.mark.slow` (ignorés en CI).
- Comparer règles vs. modèles et consigner les résultats (précision/rappel de l'extraction) dans `experiments.md`.
