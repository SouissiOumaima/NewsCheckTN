# `rag_llm/` — Lot D : RAG & LLM

**Responsable : Membre 5 · Branche : `lot-d-rag`**

## Rôle
1. **Retrieval hybride** : BM25 (lexical) + recherche dense (sentence-transformers multilingue + FAISS), fusion (RRF), puis **re-ranking** (cross-encoder).
2. **Génération du verdict** par LLM avec **prompting contraint** :
   - réponse fondée **uniquement** sur les preuves fournies ;
   - **citations obligatoires** (`[doc_id]`) et vérifiées ;
   - **niveau d'incertitude** ;
   - **abstention** (`preuves_insuffisantes`) si les preuves ne permettent pas de conclure.
3. **Grille de fidélité** : chaque affirmation du verdict est-elle soutenue par une preuve citée ?

## Entrées / sorties
| Point d'entrée | Entrée | Sortie |
|----------------|--------|--------|
| `rag_llm.retrieval.hybrid.retrieve` | `Claim`, corpus `list[Evidence]` (Lot A1), `k` | `list[Evidence]` triées par `score` |
| `rag_llm.verdict.generate_verdict` | `Claim`, `list[StanceResult]` (Lot C) | `Verdict` |

## Organisation
| Dossier / fichier | Contenu |
|-------------------|---------|
| `retrieval/hybrid.py` | Point d'entrée du retrieval |
| `retrieval/bm25.py`, `retrieval/dense.py`, `retrieval/rerank.py` | Composants (à créer) |
| `prompts/` | Gabarits de prompt versionnés : `<tâche>_<langue>_v<N>.txt` |
| `verdict.py` | Appel LLM, parsing JSON, vérification des citations, abstention |
| `faithfulness.py` | Grille de fidélité (à créer) |
| `index/` | Index BM25/FAISS construits — **non versionné** |

## Conventions
- Configuration (modèle d'embedding, LLM, clés) via `.env` — **jamais de clé dans le code**.
- Toute nouvelle version de prompt = nouveau fichier (`_v2`, `_v3`…), l'ancien est conservé pour comparer.
- Script de construction d'index reproductible : `python -m rag_llm.retrieval.build_index`.
- Métriques à consigner dans `experiments.md` : Recall@k, MRR, taux d'abstention, score de fidélité, citations invalides.
