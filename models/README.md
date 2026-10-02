# `models/` — Lot C : Modèles appris

**Responsable : Membre 4 · Branche : `lot-c-models`**

## Rôle
1. **Détection d'affirmations vérifiables** (check-worthiness, classification binaire) :
   - baselines : TF-IDF + régression logistique / SVM, FastText ;
   - encodeurs fine-tunés : XLM-R, AraBERT (et variantes dialectales), avec **LoRA** (PEFT).
2. **NLI / stance** : position d'une preuve vis-à-vis d'une affirmation (soutient / contredit / neutre).

## Entrées / sorties
| Point d'entrée | Entrée | Sortie |
|----------------|--------|--------|
| `models.claim_detector.filter_checkworthy` | `list[Claim]` (Lot B) | `list[Claim]` filtrés, `checkworthiness` renseigné |
| `models.nli.stance.predict_stances` | `Claim`, `list[Evidence]` (Lot D) | `list[StanceResult]` |

Données d'entraînement : `data/processed/checkworthy_*.jsonl` et `data/processed/nli_*.jsonl` (Lot A1).

## Organisation
| Dossier / fichier | Contenu |
|-------------------|---------|
| `baselines/` | TF-IDF, FastText (`train_tfidf.py`, `train_fasttext.py`) |
| `encoders/` | Fine-tuning XLM-R / AraBERT + LoRA (`train_encoder.py`, configs) |
| `nli/` | Modèle de stance (`stance.py` = inférence, `train_nli.py`) |
| `claim_detector.py` | Inférence check-worthiness utilisée par le pipeline |
| `checkpoints/` | Poids entraînés — **non versionné** |

## Conventions
- Nom de checkpoint : `<tâche>_<modèle>_<AAAAMMJJ>` (ex. `checkworthy_xlmr-lora-r8_20261115`).
- Les poids sont partagés via Hugging Face Hub ou le drive de l'équipe ; le lien va dans ce README.
- Chaque script d'entraînement accepte `--seed`, `--output_dir` et enregistre ses hyperparamètres en JSON à côté du checkpoint.
- Rapporter les résultats **par langue** (FR / AR / TN) sur le split `test` commun et les consigner dans `experiments.md`.
- `import torch` / `transformers` **à l'intérieur** des fonctions ou via un chargement paresseux (CI légère).
