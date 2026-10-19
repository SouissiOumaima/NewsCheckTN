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
| `retrieval/hybrid.py` | Point d'entrée du retrieval : `bm25` / `dense` / `hybrid` (fusion RRF), choisi par `RETRIEVAL_METHOD` |
| `retrieval/text.py` | Prétraitement pour la recherche : normalisation « agressive », tokens, mots vides |
| `retrieval/bm25.py` | BM25 Okapi en Python pur (aucune dépendance, testable en CI) |
| `retrieval/dense.py` | Recherche dense : encodeur sentence-transformers (import paresseux), cosinus, cache disque |
| `retrieval/rerank.py` | Re-ranking cross-encoder (à créer, S5) |
| `evaluate_retrieval.py` | Recall@k, Hit@k, MRR par langue/script → `evaluation/results/` |
| `prompts/` | Gabarits de prompt versionnés : `<tâche>_<langue>_v<N>.txt` |
| `verdict.py` | Verdict par gabarit (FR / AR) + politique d'abstention v1 ; LLM en S6 |
| `baseline_stance.py` | NLI par règles (nombres, démentis), même signature que le Lot C ; repli pour la démo |
| `evaluate_verdict.py` | Évaluation bout-en-bout : exactitude, couverture, précision sélective, abstention |
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
| S2 | Baseline NLI par règles (`baseline_stance.py`) | ✅ fait (EXP-D-002) |
| S3 | Verdict par gabarit + politique d'abstention v1 | ✅ fait (EXP-D-002) |
| S4 | Retrieval dense multilingue + fusion RRF (EXP-D-003) | ✅ fait : hybride e5-base, Recall@5 0.67 → 0.94 |
| S5 | Re-ranking cross-encoder | à faire |

## Choisir la méthode de retrieval
`RETRIEVAL_METHOD` dans `.env` : `bm25` (défaut, aucun modèle), `dense` ou `hybrid`.
`dense` et `hybrid` demandent `pip install sentence-transformers` ; le modèle (`EMBEDDING_MODEL`)
est téléchargé au premier appel, et les vecteurs du corpus sont mis en cache dans `rag_llm/index/`.
La CI reste en `bm25` ; les tests du dense utilisent un faux encodeur bilingue.

Mesures réelles : `notebooks/lot_d_rag/01_m5_dense_retrieval.ipynb` (Colab).

## Évaluer le retrieval
```bash
python -m rag_llm.evaluate_retrieval                     # jeu de dev fictif (tests/fixtures/rag_llm/)
python -m rag_llm.evaluate_retrieval --method all        # compare bm25, dense, hybrid
python -m rag_llm.evaluate_retrieval --corpus data/processed/evidence_corpus.jsonl \
    --claims <paires_annotees>.jsonl --exp-id EXP-D-00N --split dev
```
Format des affirmations : `{"claim_id", "text", "lang": "fr|ar|tn", "script", "gold_doc_ids": [...]}`.

## Politique d'abstention v1 (`verdict.py`)
Le système répond `preuves_insuffisantes` si : **A1** aucune preuve retrouvée ; **A2** aucune preuve
de score ≥ seuil de la méthode (`hybrid.min_relevance_score` : BM25 ≥ 1.0, cosinus ≥ 0.4 ;
en hybride, filtrage avant fusion) ; **A3** aucune preuve décisive (soutient/contredit avec
confiance ≥ `MIN_CONFIDENCE` = 0.6) ; **A4** preuves décisives contradictoires (écart < 0.25).
Sinon : `vrai` ou `faux`, avec jusqu'à 3 citations recopiées mot pour mot et une incertitude ≥ 0.1.

```bash
python -m rag_llm.evaluate_verdict                  # NLI par règles
python -m rag_llm.evaluate_verdict --stance lot-c   # NLI du Lot C (stub : toujours neutre)
```

## Points ouverts avec les autres lots
- **A1** : ajouter `lang` (et idéalement `script`) à `Evidence` dans `common/schemas.py` — le champ
  existe déjà dans `evidence_corpus.jsonl` mais est perdu au chargement. Utile pour ventiler les
  métriques et pour le retrieval croisé FR ↔ AR.
- **A2** : translittération arabizi (`arabizi_to_arabic`) — sans elle, BM25 échoue sur l'arabizi.
- **E** : ajouter `abstention_reason` à `Verdict` (pour l'instant fourni par
  `generate_verdict_with_reason`) ; pour la démo Bronze, `rag_llm.baseline_stance.predict_stances`
  peut remplacer le stub NLI du Lot C (même signature).
- **C** : tant que le NLI renvoie toujours « neutre », le pipeline s'abstient sur tout.
- **B** : exposer `resolved_text` (coréférence résolue) dans `Claim` : meilleure requête que `text`.
