# NewsCheck TN

**Détection d'affirmations vérifiables et vérification assistée — français, arabe standard et dialecte tunisien.**

Projet d'équipe (6 membres) du module NLP — ESPRIM.

---

## 1. Objectif

À partir d'un texte ou d'un article (FR / AR / tunisien en lettres arabes ou en arabizi), le système :

1. **normalise** le texte et identifie la langue ;
2. **extrait** les affirmations factuelles vérifiables ;
3. **retrouve des preuves** dans un corpus (RAG hybride BM25 + dense, re-ranking) ;
4. **détermine la position** de chaque preuve (NLI : soutient / contredit / neutre) ;
5. **génère un verdict argumenté** par LLM avec **citations obligatoires**, **niveau d'incertitude** et **abstention** si les preuves sont insuffisantes.

Le tout est exposé via une **API FastAPI**, une **interface web** et un **tableau de bord d'évaluation**.

## 2. Architecture

```
 texte brut (FR / AR / TN)
        │
        ▼
 ┌──────────────────┐   normalization/        Lot A2
 │ Normalisation +  │   normalize()
 │ identif. langue  │
 └────────┬─────────┘
          ▼
 ┌──────────────────┐   linguistic_analysis/  Lot B
 │ Extraction des   │   extract_claims()       (SPO, modalité, coréférence)
 │ affirmations     │
 └────────┬─────────┘
          ▼
 ┌──────────────────┐   models/               Lot C
 │ Check-worthiness │   filter_checkworthy()   (TF-IDF, XLM-R, AraBERT, LoRA)
 └────────┬─────────┘
          ▼
 ┌──────────────────┐   rag_llm/retrieval/    Lot D   ◄── data/ (corpus de preuves, Lot A1)
 │ Retrieval hybride│   retrieve()
 └────────┬─────────┘
          ▼
 ┌──────────────────┐   models/nli/           Lot C
 │ NLI (stance)     │   predict_stances()
 └────────┬─────────┘
          ▼
 ┌──────────────────┐   rag_llm/              Lot D
 │ Verdict LLM      │   generate_verdict()     (citations, incertitude, abstention)
 └────────┬─────────┘
          ▼
   pipeline.py  →  api/ (FastAPI)  →  frontend/  +  evaluation/      Lot E
```

Les structures échangées entre étapes (`Document`, `Claim`, `Evidence`, `StanceResult`, `Verdict`)
sont définies **une seule fois** dans [`common/schemas.py`](common/schemas.py). Détails : [`docs/architecture.md`](docs/architecture.md).

## 3. Organisation de l'équipe

| Lot | Membre | Dossier(s) | Branche | Rôle |
|-----|--------|-----------|---------|------|
| A1 | Membre 1 | `data/` | `lot-a1-data` | Corpus, preuves, annotations, data cards |
| A2 | Membre 2 | `normalization/` | `lot-a2-normalization` | Normalisation FR/AR/TN, arabizi, langue, perplexité |
| B  | Membre 3 | `linguistic_analysis/` | `lot-b-linguistic` | POS, dépendances, SPO, modalité, coréférence |
| C  | Membre 4 | `models/` | `lot-c-models` | Baselines, fine-tuning XLM-R/AraBERT + LoRA, NLI |
| D  | Membre 5 | `rag_llm/` | `lot-d-rag` | Retrieval hybride, re-ranking, prompting, abstention, fidélité |
| E  | toute l'équipe (base : Membre 5) | `api/`, `frontend/`, `evaluation/`, `pipeline.py`, `common/` | `lot-e-*` | Intégration, API, plateforme, dashboard, CI, rapport |

Dossiers partagés : `docs/`, `notebooks/` (un sous-dossier par lot), `tests/` (un fichier par lot), `experiments.md`.

## 4. Arborescence

```
NewsCheckTN/
├── .github/               # template de PR + CI (lint + tests)
├── common/                # contrats de données partagés (schemas.py)
├── data/                  # [A1] scrapers, corpus, annotations, data cards
├── normalization/         # [A2] normalisation, langue, arabizi
├── linguistic_analysis/   # [B]  extraction d'affirmations, SPO, modalité
├── models/                # [C]  baselines, encodeurs, NLI
├── rag_llm/               # [D]  retrieval, prompts, verdict
├── api/                   # [E]  FastAPI
├── frontend/              # [E]  interface web
├── evaluation/            # [E]  métriques communes + tableau de bord
├── notebooks/             # exploration, un sous-dossier par lot
├── docs/                  # architecture, rapport, guides
├── tests/                 # tests pytest, un fichier par lot
├── pipeline.py            # enchaînement bout-en-bout
├── experiments.md         # journal d'expériences (obligatoire)
├── requirements.txt       # dépendances complètes
├── requirements-dev.txt   # dépendances légères (dev + CI)
└── pyproject.toml         # config pytest + ruff
```

Chaque dossier contient un `README.md` décrivant son rôle, ses entrées/sorties et ses conventions.

## 5. Installation et lancement

```bash
git clone https://github.com/SouissiOumaima/NewsCheckTN.git
cd NewsCheckTN
python -m venv .venv
# Windows : .venv\Scripts\activate      Linux/macOS : source .venv/bin/activate

pip install -r requirements-dev.txt   # suffisant pour lancer l'API et les tests
pip install -r requirements.txt       # dépendances complètes (torch, transformers, spaCy...)
cp .env.example .env                  # puis compléter
```

| Action | Commande |
|--------|----------|
| Pipeline en ligne de commande | `python pipeline.py "Le chômage en Tunisie est de 16,4 % en 2023."` |
| API (doc sur http://localhost:8000/docs) | `uvicorn api.main:app --reload` |
| Frontend | ouvrir `frontend/index.html` dans le navigateur (API lancée) |
| Tableau de bord | `streamlit run evaluation/dashboard/app.py` |
| Tests | `pytest` |
| Lint | `ruff check .` |

> Toutes les commandes se lancent **depuis la racine du dépôt**.

## 6. Contribuer

Voir [`CONTRIBUTING.md`](CONTRIBUTING.md) : une branche par lot, PR vers `main`, CI verte et une relecture obligatoires.
Toute expérience (entraînement, évaluation, essai de prompt) est consignée dans [`experiments.md`](experiments.md).

## 7. État actuel

Squelette fonctionnel : chaque étape est un **stub** marqué `TODO(Lot X)` qui renvoie un résultat valide,
pour que le pipeline, l'API et les tests tournent dès le premier jour. Chaque lot remplace son stub
par sa vraie implémentation **sans changer la signature** de sa fonction d'entrée.
