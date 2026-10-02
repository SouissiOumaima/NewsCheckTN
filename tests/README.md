# `tests/` — Tests automatisés (pytest)

Un fichier par lot ; chacun maintient le sien :

| Fichier | Lot |
|---------|-----|
| `test_data.py` | A1 |
| `test_normalization.py` | A2 |
| `test_linguistic_analysis.py` | B |
| `test_models.py` | C |
| `test_rag_llm.py` | D |
| `test_api.py`, `test_evaluation.py` | E |

Lancer : `pytest` (depuis la racine). La CI les exécute sur chaque PR.

## Conventions
- Les tests doivent être **rapides** et **ne pas télécharger de modèle** : les tests nécessitant un modèle
  lourd sont marqués `@pytest.mark.slow` et ignorés en CI, ou utilisent un faux modèle (mock).
- Tester au minimum que chaque point d'entrée respecte son contrat (types et champs de `common/schemas.py`).
