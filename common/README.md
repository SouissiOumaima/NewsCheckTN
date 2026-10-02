# `common/` — Contrats de données partagés

**Propriétaire : Lot E · Modifications : PR relue par les lots concernés**

`schemas.py` définit les structures échangées entre les étapes du pipeline :

| Classe | Produite par | Consommée par |
|--------|--------------|---------------|
| `Document` | A2 (normalisation) | B |
| `Claim` | B (extraction) + C (score) | C, D, API |
| `Evidence` | A1 (corpus) / D (retrieval) | C (NLI), D |
| `StanceResult` | C (NLI) | D |
| `Verdict` | D (LLM) | API, frontend, évaluation |

Énumérations : `Lang` (`fr`, `ar`, `tn`, `unk`), `Stance` (`supports`, `refutes`, `neutral`),
`Label` (`vrai`, `faux`, `trompeur`, `preuves_insuffisantes`).

Règles : ajouter un champ **avec une valeur par défaut** pour ne casser personne ; ne jamais renommer
ou supprimer un champ sans accord de l'équipe.
