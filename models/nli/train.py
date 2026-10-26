"""Lot C — Model 2 : affinage (fine-tuning) du NLI sur le corpus du Lot A1.

On part du modèle de la baseline (mDeBERTa-v3 xnli, déjà entraîné au NLI) et on continue
l'entraînement sur la partie `train`. La partie `val` choisit la meilleure époque ; l'époque 0
(le modèle sans affinage) est aussi candidate : si l'affinage n'aide pas sur `val`, on garde la
baseline. Le `test` n'est jamais regardé ici.

    python -m models.nli.train --version v3 --seed 42
    python -m models.nli.train --version v3 --seed 123
    python -m models.nli.train --version v3 --seed 2026

Écrit le meilleur modèle dans models/checkpoints/nli_mdeberta-ft_<version>_seed<graine>/
(non versionné) avec `train_log.json` (hyperparamètres, macro-F1 de validation par époque,
durée). Ensuite : `NLI_MODEL=<ce dossier> python -m models.nli.evaluate ...`.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

from models.nli import stance
from models.nli.data import LABELS, OUT_DIR, ROOT, load_pairs
from models.nli.evaluate import metrics

CHECKPOINTS = ROOT / "models" / "checkpoints"

# Hyperparamètres par défaut (petit jeu : peu d'époques, pas d'apprentissage élevé)
EPOCHS = 4
LEARNING_RATE = 1e-5
BATCH_SIZE = 8
WEIGHT_DECAY = 0.01
WARMUP_SHARE = 0.1

# Nos labels → noms de classes du modèle NLI
TO_MODEL = {"supports": "entailment", "refutes": "contradiction", "neutral": "neutral"}


def label_ids(model_label2id: dict[str, int]) -> dict[str, int]:
    """Nos labels → indices de sortie du modèle (lus dans sa configuration)."""
    lower = {name.lower(): i for name, i in model_label2id.items()}
    return {lab: lower[TO_MODEL[lab]] for lab in LABELS}


def best_epoch(history: list[dict]) -> dict:
    """Meilleure époque sur la validation (macro-F1) ; à égalité, la plus ancienne."""
    return max(history, key=lambda h: (round(h["val_macro_f1"], 6), -h["epoch"]))


def set_seed(seed: int) -> None:
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def _predict(model, tokenizer, pairs: list[dict], id2ours: dict[int, str], device) -> list[str]:
    import torch

    model.eval()
    preds: list[str] = []
    for start in range(0, len(pairs), stance.BATCH_SIZE):
        batch = pairs[start : start + stance.BATCH_SIZE]
        enc = tokenizer(
            [p["evidence"] for p in batch],
            [p["claim"] for p in batch],
            truncation="only_first",
            max_length=stance.MAX_LENGTH,
            padding=True,
            return_tensors="pt",
        ).to(device)
        with torch.no_grad():
            logits = model(**enc).logits
        # on ne garde que nos 3 classes (toutes présentes dans un modèle NLI à 3 sorties)
        preds.extend(id2ours[int(i)] for i in logits.argmax(dim=-1).tolist())
    return preds


def train(
    version: str,
    seed: int,
    base_model: str = stance.DEFAULT_MODEL,
    epochs: int = EPOCHS,
    lr: float = LEARNING_RATE,
    batch_size: int = BATCH_SIZE,
) -> Path:
    import torch
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        get_linear_schedule_with_warmup,
    )

    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_pairs = load_pairs(OUT_DIR / f"nli_{version}_train.jsonl")
    val_pairs = load_pairs(OUT_DIR / f"nli_{version}_val.jsonl")

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForSequenceClassification.from_pretrained(base_model).to(device)
    ours2id = label_ids(model.config.label2id)
    id2ours = {i: lab for lab, i in ours2id.items()}

    out = CHECKPOINTS / f"nli_mdeberta-ft_{version}_seed{seed}"
    out.mkdir(parents=True, exist_ok=True)
    val_gold = [p["label"] for p in val_pairs]

    def validate(epoch: int) -> dict:
        m = metrics(val_gold, _predict(model, tokenizer, val_pairs, id2ours, device))
        print(f"  époque {epoch} : val macro-F1 {m['macro_f1']:.3f}  accuracy {m['accuracy']:.3f}")
        return {"epoch": epoch, "val_macro_f1": m["macro_f1"], "val_accuracy": m["accuracy"]}

    history = [validate(0)]  # époque 0 = baseline sans affinage
    best = history[0]
    model.save_pretrained(out)
    tokenizer.save_pretrained(out)

    steps_per_epoch = (len(train_pairs) + batch_size - 1) // batch_size
    total = steps_per_epoch * epochs
    optim = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=WEIGHT_DECAY)
    sched = get_linear_schedule_with_warmup(optim, int(WARMUP_SHARE * total), total)
    rng = random.Random(seed)
    start = time.time()

    for epoch in range(1, epochs + 1):
        model.train()
        order = list(range(len(train_pairs)))
        rng.shuffle(order)
        loss_sum = 0.0
        for s in range(0, len(order), batch_size):
            batch = [train_pairs[i] for i in order[s : s + batch_size]]
            enc = tokenizer(
                [p["evidence"] for p in batch],
                [p["claim"] for p in batch],
                truncation="only_first",
                max_length=stance.MAX_LENGTH,
                padding=True,
                return_tensors="pt",
            ).to(device)
            labels = torch.tensor([ours2id[p["label"]] for p in batch], device=device)
            loss = model(**enc, labels=labels).loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optim.step()
            sched.step()
            optim.zero_grad()
            loss_sum += loss.item() * len(batch)
        h = validate(epoch)
        h["train_loss"] = round(loss_sum / len(train_pairs), 4)
        history.append(h)
        if best_epoch(history) is h:  # nouvelle meilleure époque : on la garde sur disque
            best = h
            model.save_pretrained(out)
            tokenizer.save_pretrained(out)

    log = {
        "base_model": base_model,
        "corpus_version": version,
        "seed": seed,
        "device": str(device),
        "epochs": epochs,
        "learning_rate": lr,
        "batch_size": batch_size,
        "weight_decay": WEIGHT_DECAY,
        "warmup_share": WARMUP_SHARE,
        "max_length": stance.MAX_LENGTH,
        "train_pairs": len(train_pairs),
        "val_pairs": len(val_pairs),
        "history": history,
        "best_epoch": best["epoch"],
        "training_seconds": round(time.time() - start, 1),
    }
    (out / "train_log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(f"meilleure époque : {best['epoch']} (val macro-F1 {best['val_macro_f1']:.3f}) -> {out}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--version", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--epochs", type=int, default=EPOCHS)
    ap.add_argument("--lr", type=float, default=LEARNING_RATE)
    args = ap.parse_args()
    train(args.version, args.seed, epochs=args.epochs, lr=args.lr)


if __name__ == "__main__":
    main()
