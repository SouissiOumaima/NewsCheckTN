# Guide de contribution — NewsCheck TN

## 1. Branches

| Branche | Rôle | Qui pousse dessus |
|---------|------|-------------------|
| `main` | Version stable, toujours fonctionnelle (CI verte) | Personne directement : **uniquement via PR** |
| `lot-a1-data` | Lot A1 — corpus, preuves, annotations | Membre 1 |
| `lot-a2-normalization` | Lot A2 — normalisation & multilinguisme | Membre 2 |
| `lot-b-linguistic` | Lot B — analyse linguistique | Membre 3 |
| `lot-c-models` | Lot C — modèles appris | Membre 4 |
| `lot-d-rag` | Lot D — RAG & LLM | Membre 5 |
| `lot-e-*` (ex. `lot-e-plateforme`) | Lot E — intégration, API, plateforme (partagé) | toute l'équipe |

Pour une tâche plus large, on peut créer une sous-branche à partir de sa branche de lot,
préfixée par le lot : `lot-c-models/xlmr-lora`, `lot-d-rag/bm25`… puis la fusionner dans la branche de lot.

## 2. Flux de travail quotidien

```bash
# Première fois
git clone https://github.com/SouissiOumaima/NewsCheckTN.git
cd NewsCheckTN
git switch lot-b-linguistic          # votre branche de lot

# Avant de commencer à travailler : récupérer les nouveautés de main
git fetch origin
git merge origin/main                # (ou git rebase origin/main si vous êtes seul sur la branche)

# Travailler, puis
pytest && ruff check .
git add <fichiers>
git commit -m "feat(lot-b): extraction SPO avec spaCy"
git push origin lot-b-linguistic
```

Puis ouvrir une **Pull Request** `lot-xxx → main` sur GitHub.

## 3. Règles de Pull Request

1. **Petites PR fréquentes** (idéalement au moins une par semaine et par lot) plutôt qu'une énorme PR en fin de projet.
2. La **CI doit être verte** (lint + tests).
3. **Au moins 1 relecture** d'un autre membre ; **2 relectures** (dont un membre du lot concerné) si la PR touche
   `common/schemas.py`, `pipeline.py`, `api/`, `requirements*.txt` ou `.github/`.
4. Remplir le template de PR (ce qui change, comment tester, ligne ajoutée dans `experiments.md`).
5. Fusion par **"Squash and merge"** pour garder un historique de `main` lisible.
6. Après fusion, chacun fait `git merge origin/main` dans sa branche de lot.

> Recommandé (admin du repo) : *Settings → Branches → Add rule* sur `main` :
> "Require a pull request before merging", "Require approvals (1)", "Require status checks to pass (CI)".

## 4. Périmètre de chaque lot (éviter les conflits)

- Chaque membre ne modifie **que son dossier**, son sous-dossier `notebooks/lot_xxx/` et son fichier `tests/test_<module>.py`.
- Les **fonctions d'entrée** appelées par `pipeline.py` gardent leur **signature** :

| Lot | Fonction d'entrée | Signature |
|-----|-------------------|-----------|
| A1 | `data.loaders.load_evidence_corpus` | `() -> list[Evidence]` |
| A2 | `normalization.normalize.normalize` | `(text: str) -> Document` |
| B  | `linguistic_analysis.claim_extraction.extract_claims` | `(doc: Document) -> list[Claim]` |
| C  | `models.claim_detector.filter_checkworthy` | `(claims: list[Claim]) -> list[Claim]` |
| C  | `models.nli.stance.predict_stances` | `(claim, evidences) -> list[StanceResult]` |
| D  | `rag_llm.retrieval.hybrid.retrieve` | `(claim, corpus, k) -> list[Evidence]` |
| D  | `rag_llm.verdict.generate_verdict` | `(claim, stances) -> Verdict` |

- Besoin d'un nouveau champ dans un schéma partagé ? → PR dédiée sur `common/schemas.py`, prévenir l'équipe.
- Besoin d'une nouvelle dépendance ? → l'ajouter dans `requirements.txt` dans une PR, avec justification.
  Les imports lourds (`torch`, `transformers`, `spacy`...) se font **à l'intérieur des fonctions** ou derrière
  un chargement paresseux, pour que l'API et la CI restent rapides.

## 5. Conventions

**Messages de commit** (style *Conventional Commits*) : `type(lot-x): description`
- types : `feat`, `fix`, `data`, `exp` (expérience), `docs`, `test`, `refactor`, `chore`
- ex. : `data(lot-a1): ajout scraper Tunisia Check`, `exp(lot-c): XLM-R + LoRA r=8`

**Code Python**
- Python ≥ 3.10, formaté/linté avec `ruff` (longueur de ligne 100).
- Noms de fichiers/fonctions en `snake_case`, classes en `PascalCase`.
- Les stubs restants sont marqués `# TODO(Lot X): ...` — chercher `TODO(Lot` pour voir le travail restant.
- Docstrings et commentaires en français.

**Données et modèles**
- **Jamais** de corpus brut, de checkpoint, d'index ou de clé API dans git (voir `.gitignore`).
- Les gros fichiers se partagent via le drive de l'équipe / Hugging Face Hub ; le lien et la procédure
  de téléchargement sont documentés dans le README du dossier concerné.
- Les secrets vont dans `.env` (jamais commité), modèle dans `.env.example`.

**Notebooks**
- Dans `notebooks/lot_xxx/`, nommés `NN_auteur_sujet.ipynb` (ex. `01_m4_baseline_tfidf.ipynb`).
- Vider les sorties volumineuses avant commit. Le code réutilisable migre dans le module du lot.

## 6. Journal d'expériences

Toute expérience (entraînement, évaluation, prompt, configuration de retrieval) ajoute **une entrée**
dans `experiments.md` selon le format indiqué en tête de fichier. C'est exigé par le cahier des charges.
