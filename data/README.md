# `data/` — Lot A1 : Corpus, preuves, annotations

**Responsable : Membre 1 · Branche : `lot-a1-data`**

## Rôle
Collecter et préparer toutes les données du projet :
- articles de **fact-checkers** (vérifications publiées avec leur verdict) en FR / AR / tunisien ;
- **corpus de preuves** dans lequel le Lot D cherchera (sources officielles, presse, INS…) ;
- **jeux annotés** : check-worthiness (Lot C), paires affirmation/preuve pour la NLI (Lot C), verdicts de référence (évaluation) ;
- **data cards** documentant chaque jeu de données.

## Organisation

| Dossier | Contenu | Versionné ? |
|---------|---------|-------------|
| `collect/` | Scrapers / scripts de collecte, **un fichier par source** (`<source>_scraper.py`) | oui |
| `raw/` | Données brutes telles que collectées (HTML, JSON) | **non** (`.gitignore`) |
| `interim/` | Données nettoyées intermédiaires | **non** |
| `processed/` | Jeux finaux prêts à l'emploi (`.jsonl`) | oui si < 5 Mo, sinon lien de téléchargement |
| `annotations/` | Guide d'annotation, fichiers annotés, accord inter-annotateurs | oui |
| `data_cards/` | Une data card par jeu (`<nom_du_jeu>.md`) | oui |
| `loaders.py` | Fonctions de chargement utilisées par le reste du pipeline | oui |

## Sorties attendues (contrat avec les autres lots)

Tous les jeux finaux sont en **JSON Lines UTF-8** (une ligne = un exemple) :

- `processed/evidence_corpus.jsonl` (→ Lot D)
  `{"doc_id", "text", "source", "url", "date": "AAAA-MM-JJ", "lang": "fr|ar|tn"}`
- `processed/checkworthy_{train,dev,test}.jsonl` (→ Lot C)
  `{"id", "text", "lang", "label": 0|1}`
- `processed/nli_{train,dev,test}.jsonl` (→ Lot C)
  `{"id", "claim", "evidence", "lang", "label": "supports|refutes|neutral"}`
- `processed/factchecks.jsonl` (→ évaluation Lot E)
  `{"id", "claim", "verdict", "evidence_ids": [...], "source_url", "lang"}`

Point d'entrée : `data.loaders.load_evidence_corpus() -> list[Evidence]`.

## Conventions
- Nommage : `<tâche>_<split>.jsonl`, `<source>_scraper.py`, data card `<nom_du_jeu>.md`.
- Splits **fixés une fois pour toutes** (graine documentée) et partagés par toute l'équipe.
- Respecter les conditions d'utilisation des sites (robots.txt, délai entre requêtes) ; ne pas versionner de contenu protégé.
- Chaque data card indique : source, licence, date de collecte, taille, répartition par langue et par label, biais connus.
