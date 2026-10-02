# `api/` — Lot E : API FastAPI

**Responsable : Membre 6 · Branche : `lot-e-integration`**

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

## Conventions
- L'API ne contient **aucune logique métier** : elle appelle les points d'entrée des lots.
- Les modèles de requête sont des classes Pydantic dans `main.py` (ou `schemas.py` si le fichier grossit) ;
  les réponses sérialisent les dataclasses de `common/schemas.py`.
- Toute nouvelle route a un test dans `tests/test_api.py`.
