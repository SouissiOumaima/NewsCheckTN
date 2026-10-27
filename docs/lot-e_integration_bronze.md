# Lot E — Intégration Bronze et contrat de démo

## Chemin exécuté

`POST /bronze/check` est la route de démonstration Bronze. Elle utilise uniquement
les composants classiques : normalisation A2, extraction par règles B, retrieval
BM25 D, NLI lexical C et verdict à gabarit D. Elle ne passe ni par un encodeur
dense, ni par un LLM, ni par le filtre Model 1 entraîné.

| Étape | Entrée / sortie | Responsable | Preuve visible |
|---|---|---|---|
| Normalisation | texte → `Document` | A2 | langue, écriture, texte normalisé |
| Extraction | `Document` → candidats / `Claim` assertif | B | nombre de segments, sujet/prédicat/objet |
| Recherche | `Claim` → top-k `Evidence` | D | identifiant, source, score BM25, texte |
| Position | preuve + claim → supports/refutes/neutral | C | position et confiance par passage |
| Verdict | positions → `Verdict` | D | label, explication, citations, abstention |

Le champ `timings_ms` contient la durée mesurée sur la machine qui exécute
l'API. Il ne s'agit pas d'un benchmark matériel : il permet de rendre la
latence observable pendant la revue.

## Gestion sûre des cas non vérifiables

- Question, souhait, hypothèse ou opinion : aucune affirmation assertive n'est
  retenue ; les étapes aval sont arrêtées et l'interface affiche **Filtré**.
- Aucune preuve suffisamment pertinente : verdict `preuves_insuffisantes` et
  abstention explicite.
- Citation : un verdict non abstenu doit citer seulement un `doc_id` renvoyé
  par le retrieval ; l'audit contrôle cette propriété.

## Reproduire l'audit E2E

```powershell
python -m evaluation.integration_audit
python -m pytest tests/test_api.py tests/test_evaluation.py -q
```

Le jeu versionné `data/annotations/bronze_fr_integration_eval.jsonl` couvre
une confirmation, une contradiction numérique, une absence de preuve et une
opinion. Il est un **contrôle d'intégration de quatre cas**, pas un test
statistique représentatif. Les métriques de performance des composants restent
dans les expériences des lots B, C et D.

## Checklist orale

- Lancer `uvicorn api.main:app --reload`, puis ouvrir `/app/bronze.html`.
- Montrer successivement un exemple vrai, le chômage à 25 %, l'aéroport 2026,
  puis une opinion.
- Vérifier que la latence, la source et le comportement d'abstention sont bien
  affichés.
- Ne pas présenter le résultat de quatre cas comme une performance générale.
