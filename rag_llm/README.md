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
| `retrieval/hybrid.py` | Point d'entrée du retrieval (BM25 seul pour l'instant, index mis en cache) |
| `retrieval/text.py` | Prétraitement pour la recherche : normalisation « agressive », tokens, mots vides |
| `retrieval/bm25.py` | BM25 Okapi en Python pur (aucune dépendance, testable en CI) |
| `retrieval/dense.py`, `retrieval/rerank.py` | Composants (à créer, S4–S5) |
| `evaluate_retrieval.py` | Recall@k, Hit@k, MRR par langue/script → `evaluation/results/` |
| `prompts/` | Gabarits de prompt versionnés : `<tâche>_<langue>_v<N>.txt` |
| `verdict.py` | Appel LLM, parsing JSON, vérification des citations, abstention |
| `faithfulness.py` | Grille de fidélité (à créer) |
| `index/` | Index BM25/FAISS construits — **non versionné** |

## Conventions
- Configuration (modèle d'embedding, LLM, clés) via `.env` — **jamais de clé dans le code**.
- Toute nouvelle version de prompt = nouveau fichier (`_v2`, `_v3`…), l'ancien est conservé pour comparer.
- Script de construction d'index reproductible : `python -m rag_llm.retrieval.build_index`.
- Métriques à consigner dans `experiments.md` : Recall@k, MRR, taux d'abstention, score de fidélité, citations invalides.

## État d'avancement
| Semaine | Tâche | État |
|---------|-------|------|
| S1 | BM25 baseline + évaluation (EXP-D-001) | ✅ fait, sur jeu de dev **fictif** |
| S2 | Verdict minimal par règles | stub existant (`verdict.py`) |
| S3 | Verdict par gabarit + règle d'abstention v1 | à faire |
| S4 | Retrieval dense multilingue | à faire |
| S5 | Hybride BM25 + dense (RRF) + re-ranking | à faire |

## Évaluer le retrieval
```bash
python -m rag_llm.evaluate_retrieval                     # jeu de dev fictif (tests/fixtures/rag_llm/)
python -m rag_llm.evaluate_retrieval --corpus data/processed/evidence_corpus.jsonl \
    --claims <paires_annotees>.jsonl --exp-id EXP-D-00N --split dev
```
Format des affirmations : `{"claim_id", "text", "lang": "fr|ar|tn", "script", "gold_doc_ids": [...]}`.

## Points ouverts avec les autres lots
- **A1** : ajouter `lang` (et idéalement `script`) à `Evidence` dans `common/schemas.py` — le champ
  existe déjà dans `evidence_corpus.jsonl` mais est perdu au chargement. Utile pour ventiler les
  métriques et pour le retrieval croisé FR ↔ AR.
- **A2** : translittération arabizi (`arabizi_to_arabic`) — sans elle, BM25 échoue sur l'arabizi.
- **B** : exposer `resolved_text` (coréférence résolue) dans `Claim` : meilleure requête que `text`.
