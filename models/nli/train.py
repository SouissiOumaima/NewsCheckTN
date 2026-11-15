"""Lot C — Model 2 : affinage (fine-tuning) du NLI sur le corpus du Lot A1.

On part du modèle de la baseline (mDeBERTa-v3 xnli, déjà entraîné au NLI) et on continue
l'entraînement sur la partie `train`. La partie `val` choisit la meilleure époque ; l'époque 0
(le modèle sans affinage) est aussi candidate : si l'affinage n'aide pas sur `val`, on garde la
baseline. Le `test` n'est jamais regardé ici.

    python -m models.nli.train --version v3 --seed 42
    python -m models.nli.train --version v3 --seed 42 --lr 2e-5 --epochs 6 --no-save   # grille
    python -m models.nli.train --version v3 --seed 42 --base-model microsoft/mdeberta-v3-base

Écrit dans models/checkpoints/<run_name>/ (non versionné) le modèle gardé et `train_log.json`
(hyperparamètres, macro-F1 de validation par époque, durée, matériel). Avec `--no-save`, seul le
journal est écrit. Ensuite : `NLI_MODEL=<ce dossier> python -m models.nli.evaluate ...`.

Matériel : sur carte graphique, calcul en bfloat16 si elle le permet ; poids et optimiseur
toujours en float32 (le modèle de base est stocké en float16 : on force le float32 au chargement).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import time
from contextlib import nullcontext
from pathlib import Path

from models.nli import stance
from models.nli.data import LABELS, OUT_DIR, ROOT, load_pairs
from models.nli.evaluate import metrics

CHECKPOINTS = ROOT / "models" / "checkpoints"
# Ablation : même architecture, sans pré-entraînement XNLI (tête à 3 classes neuve).
ABLATION_MODEL = "microsoft/mdeberta-v3-base"

# Hyperparamètres par défaut (petit jeu : peu d'époques, pas d'apprentissage élevé)
EPOCHS = 4
LEARNING_RATE = 1e-5
BATCH_SIZE = 4  # paires par passage (6 Go de mémoire graphique)
GRAD_ACCUM = 2  # gradients cumulés sur 2 passages : lot effectif de 8
WEIGHT_DECAY = 0.01
WARMUP_SHARE = 0.1

# Nos labels → noms de classes du modèle NLI
TO_MODEL = {"supports": "entailment", "refutes": "contradiction", "neutral": "neutral"}
# Ordre des classes du modèle xnli de base, réutilisé pour la tête neuve de l'ablation
NLI_ID2LABEL = {0: "entailment", 1: "neutral", 2: "contradiction"}


def needs_new_head(model_label2id: dict[str, int]) -> bool:
    """Vrai pour un encodeur brut (classes LABEL_0, LABEL_1…) : tête NLI à créer."""
    lower = {name.lower() for name in model_label2id}
    return not set(TO_MODEL.values()) <= lower


def label_ids(model_label2id: dict[str, int]) -> dict[str, int]:
    """Nos labels → indices de sortie du modèle (lus dans sa configuration)."""
    lower = {name.lower(): i for name, i in model_label2id.items()}
    missing = sorted(set(TO_MODEL.values()) - set(lower))
    if missing:
        raise ValueError(f"classes NLI absentes de la configuration du modèle : {missing}")
    return {lab: lower[TO_MODEL[lab]] for lab in LABELS}


def run_name(base_model: str, version: str, lr: float, epochs: int, seed: int) -> str:
    """Nom du dossier d'une exécution (une configuration = un dossier, rien n'est écrasé)."""
    if base_model == stance.DEFAULT_MODEL:
        tag = "mdeberta-ft"
    else:
        tag = re.sub(r"[^a-z0-9._-]+", "-", Path(base_model).name.lower()) + "-ft"
    return f"nli_{tag}_{version}_lr{lr:g}_e{epochs}_seed{seed}"


def best_epoch(history: list[dict]) -> dict:
    """Meilleure époque sur la validation (macro-F1) ; à égalité, la plus ancienne."""
    return max(history, key=lambda h: (round(h["val_macro_f1"], 6), -h["epoch"]))


def set_seed(seed: int) -> None:
    """Graine et calculs déterministes (à appeler avant toute opération sur la carte graphique)."""
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True, warn_only=True)


def _encode(tokenizer, batch: list[dict], device):
    return tokenizer(
        [p["evidence"] for p in batch],
        [p["claim"] for p in batch],
        truncation="only_first",  # on coupe la preuve, jamais l'affirmation
        max_length=stance.MAX_LENGTH,
        padding=True,
        return_tensors="pt",
    ).to(device)


def _predict(model, tokenizer, pairs: list[dict], id2ours: dict[int, str], device) -> list[str]:
    """Prédictions en float32 (comme l'évaluation finale)."""
    import torch

    model.eval()
    preds: list[str] = []
    for start in range(0, len(pairs), stance.BATCH_SIZE):
        batch = pairs[start : start + stance.BATCH_SIZE]
        with torch.no_grad():
            logits = model(**_encode(tokenizer, batch, device)).logits
        preds.extend(id2ours[int(i)] for i in logits.argmax(dim=-1).tolist())
    return preds


def train(
    version: str,
    seed: int,
    base_model: str = stance.DEFAULT_MODEL,
    epochs: int = EPOCHS,
    lr: float = LEARNING_RATE,
    batch_size: int = BATCH_SIZE,
    grad_accum: int = GRAD_ACCUM,
    freeze_embeddings: bool = True,
    keep_epoch: int | None = None,
    save: bool = True,
) -> Path:
    import torch
    import transformers
    from transformers import (
        AutoConfig,
        AutoModelForSequenceClassification,
        AutoTokenizer,
        get_linear_schedule_with_warmup,
    )

    if keep_epoch is not None and not 0 <= keep_epoch <= epochs:
        raise ValueError(f"--keep-epoch {keep_epoch} hors de [0, {epochs}]")
    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_bf16 = device.type == "cuda" and torch.cuda.is_bf16_supported()

    def amp():
        return torch.autocast("cuda", dtype=torch.bfloat16) if use_bf16 else nullcontext()

    train_pairs = load_pairs(OUT_DIR / f"nli_{version}_train.jsonl")
    val_pairs = load_pairs(OUT_DIR / f"nli_{version}_val.jsonl")

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    extra = {}
    if needs_new_head(AutoConfig.from_pretrained(base_model).label2id):
        extra = {
            "num_labels": 3,
            "id2label": NLI_ID2LABEL,
            "label2id": {v: k for k, v in NLI_ID2LABEL.items()},
        }
    model = AutoModelForSequenceClassification.from_pretrained(
        base_model, dtype=torch.float32, **extra
    ).to(device)
    if freeze_embeddings:
        model.get_input_embeddings().weight.requires_grad_(False)
    ours2id = label_ids(model.config.label2id)
    id2ours = {i: lab for lab, i in ours2id.items()}
    trainable = [p for p in model.parameters() if p.requires_grad]

    out = CHECKPOINTS / run_name(base_model, version, lr, epochs, seed)
    out.mkdir(parents=True, exist_ok=True)
    val_gold = [p["label"] for p in val_pairs]
    kept: dict = {}

    def validate(epoch: int) -> dict:
        pred = _predict(model, tokenizer, val_pairs, id2ours, device)
        m = metrics(val_gold, pred)
        print(f"  époque {epoch} : val macro-F1 {m['macro_f1']:.3f}  accuracy {m['accuracy']:.3f}")
        h = {"epoch": epoch, "val_macro_f1": m["macro_f1"], "val_accuracy": m["accuracy"]}
        return h | {"_pred": pred}

    def keep(h: dict) -> None:
        """Époque gardée : prédictions de val notées, modèle écrit sur disque si demandé."""
        kept.clear()
        kept.update(h)
        if save:
            model.save_pretrained(out)
            tokenizer.save_pretrained(out)

    history = [validate(0)]  # époque 0 = baseline sans affinage
    if keep_epoch in (None, 0):
        keep(history[0])

    micro_per_epoch = (len(train_pairs) + batch_size - 1) // batch_size
    total = ((micro_per_epoch + grad_accum - 1) // grad_accum) * epochs
    optim = torch.optim.AdamW(trainable, lr=lr, weight_decay=WEIGHT_DECAY)
    sched = get_linear_schedule_with_warmup(optim, int(WARMUP_SHARE * total), total)
    rng = random.Random(seed)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
    start = time.time()

    for epoch in range(1, epochs + 1):
        model.train()
        order = list(range(len(train_pairs)))
        rng.shuffle(order)
        loss_sum = 0.0
        for step, s in enumerate(range(0, len(order), batch_size), start=1):
            batch = [train_pairs[i] for i in order[s : s + batch_size]]
            labels = torch.tensor([ours2id[p["label"]] for p in batch], device=device)
            with amp():
                loss = model(**_encode(tokenizer, batch, device), labels=labels).loss
            (loss / grad_accum).backward()
            loss_sum += loss.item() * len(batch)
            if step % grad_accum == 0 or step == micro_per_epoch:
                torch.nn.utils.clip_grad_norm_(trainable, 1.0)
                optim.step()
                sched.step()
                optim.zero_grad()
        h = validate(epoch)
        h["train_loss"] = round(loss_sum / len(train_pairs), 4)
        history.append(h)
        if keep_epoch == epoch or (keep_epoch is None and best_epoch(history) is h):
            keep(h)

    log = {
        "base_model": base_model,
        "corpus_version": version,
        "seed": seed,
        "device": str(device),
        "gpu": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
        "precision": "bf16-autocast" if use_bf16 else "fp32",
        "peak_gpu_memory_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2)
        if device.type == "cuda"
        else None,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "epochs": epochs,
        "learning_rate": lr,
        "batch_size": batch_size,
        "grad_accum": grad_accum,
        "effective_batch_size": batch_size * grad_accum,
        "freeze_embeddings": freeze_embeddings,
        "new_head": bool(extra),
        "weight_decay": WEIGHT_DECAY,
        "warmup_share": WARMUP_SHARE,
        "max_length": stance.MAX_LENGTH,
        "train_pairs": len(train_pairs),
        "val_pairs": len(val_pairs),
        "history": [{k: v for k, v in h.items() if k != "_pred"} for h in history],
        "selection": "meilleure époque sur val" if keep_epoch is None else "époque fixée",
        "kept_epoch": kept["epoch"],
        "kept_val_macro_f1": kept["val_macro_f1"],
        "kept_val_predictions": dict(
            zip([p["pair_id"] for p in val_pairs], kept["_pred"], strict=True)
        ),
        "model_saved": save,
        "training_seconds": round(time.time() - start, 1),
    }
    (out / "train_log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(
        f"époque gardée : {kept['epoch']} (val macro-F1 {kept['val_macro_f1']:.3f}) -> {out}"
        + ("" if save else "  (journal seulement)")
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--base-model", default=stance.DEFAULT_MODEL)
    ap.add_argument("--epochs", type=int, default=EPOCHS)
    ap.add_argument("--lr", type=float, default=LEARNING_RATE)
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    ap.add_argument("--grad-accum", type=int, default=GRAD_ACCUM)
    ap.add_argument("--freeze-embeddings", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--keep-epoch", type=int, default=None, help="époque fixée par la grille")
    ap.add_argument("--no-save", action="store_true", help="journal seulement, sans les poids")
    args = ap.parse_args()
    train(
        args.version,
        args.seed,
        base_model=args.base_model,
        epochs=args.epochs,
        lr=args.lr,
        batch_size=args.batch_size,
        grad_accum=args.grad_accum,
        freeze_embeddings=args.freeze_embeddings,
        keep_epoch=args.keep_epoch,
        save=not args.no_save,
    )


if __name__ == "__main__":
    main()
