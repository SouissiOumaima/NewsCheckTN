# `api/` — Lot E : API FastAPI

**Partagé par toute l'équipe (pas de Membre 6) · Chaque lot maintient ses routes · Relecture : 2 membres**

## Rôle
Exposer le pipeline et chacune de ses étapes via HTTP, pour le frontend et pour tester chaque lot isolément.

## Lancer
```bash
uvicorn api.main:app --reload     # depuis la racine du repo
```
Documentation interactive : http://localhost:8000/docs

## Routes
| Méthode | Route | Lot | Entrée (JSON) | Sortie |
|---------|-------|-----|---------------|--------|
| GET  | `/health` | E | — | `{"status": "ok"}` |
| POST | `/normalize` | A2 | `{"text"}` | `Document` |
| POST | `/extract` | B + C | `{"text"}` | `{"claims": [Claim]}` |
| POST | `/retrieve` | D | `{"claim", "lang", "k"}` | `{"evidence": [Evidence]}` |
| POST | `/nli` | C | `{"claim", "evidence", "lang"}` | `StanceResult` |
| POST | `/verdict` | D | `{"claim", "lang", "k"}` | `Verdict` |
| POST | `/check` | tous | `{"text"}` | `{"verdicts": [Verdict]}` |
| POST | `/verdict/detail` | D | `{"claim", "lang", "k", "nli": "lot-c"\|"regles"}` | `{"corpus_size", "nli", "evidences": [Evidence + rank, stance, confidence], "verdict"}` |
| GET  | `/corpus/stats` | A1 | — | `{"size", "by_source", "sample"}` |
| GET  | `/results` | tous | — | `{"results": [...]}` : fichiers de `evaluation/results/`, allégés |
| GET  | `/app/` | E | — | pages de la plateforme (`frontend/`) |

Le corpus de preuves est lu dans `data/processed/evidence_corpus.jsonl`, ou dans le fichier indiqué par
la variable d'environnement `EVIDENCE_CORPUS` (voir `frontend/README.md`).

## Conventions
- L'API ne contient **aucune logique métier** : elle appelle les points d'entrée des lots.
- Les modèles de requête sont des classes Pydantic dans `main.py` (ou `schemas.py` si le fichier grossit) ;
  les réponses sérialisent les dataclasses de `common/schemas.py`.
- Toute nouvelle route a un test dans `tests/test_api.py`.
