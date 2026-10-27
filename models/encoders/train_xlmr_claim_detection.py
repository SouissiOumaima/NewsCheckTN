"""Fine-tuning XLM-R + LoRA pour le Model 1 du Lot C.

Exécuter sur Colab/Kaggle avec GPU, une fois par seed :
    python -m models.encoders.train_xlmr_claim_detection \
      --input data/processed/claim_detection_600.jsonl \
      --split-file data/splits/claim_detection_multiclass_600_seed42.json \
      --seed 42 --output-dir models/checkpoints/claim_detection_xlmr_lora_seed42
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

LABELS = ("AFFIRMATION", "OPINION", "AUTRE")
LABEL_TO_ID = {label: index for index, label in enumerate(LABELS)}


def read_rows(path: Path) -> list[dict]:
    rows = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if any(row.get("label") not in LABEL_TO_ID for row in rows):
        raise ValueError("Le dataset contient un label Model 1 invalide.")
    return rows


def split_rows(
    rows: list[dict], test_ids: set[str], seed: int
) -> tuple[list[dict], list[dict], list[dict]]:
    """Conserve le test gelé puis crée validation depuis le seul entraînement."""
    from sklearn.model_selection import train_test_split

    test = [row for row in rows if row["id"] in test_ids]
    remaining = [row for row in rows if row["id"] not in test_ids]
    train, validation = train_test_split(
        remaining, test_size=0.15, random_state=seed, stratify=[row["label"] for row in remaining]
    )
    return train, validation, test


def main() -> None:
    parser = argparse.ArgumentParser(description="XLM-R + LoRA, Model 1")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--split-file", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--text-mode", choices=("raw", "normalized"), default="raw")
    args = parser.parse_args()

    try:
        import numpy as np
        import torch
        from datasets import Dataset
        from peft import LoraConfig, TaskType, get_peft_model
        from sklearn.metrics import f1_score
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            DataCollatorWithPadding,
            Trainer,
            TrainingArguments,
            set_seed,
        )
    except ImportError as error:
        raise SystemExit(
            "Installer requirements.txt dans un environnement GPU (Colab/Kaggle)."
        ) from error

    set_seed(args.seed)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    rows = read_rows(args.input)
    frozen = json.loads(args.split_file.read_text(encoding="utf-8"))
    train_rows, validation_rows, test_rows = split_rows(rows, set(frozen["test_ids"]), args.seed)

    tokenizer = AutoTokenizer.from_pretrained("FacebookAI/xlm-roberta-base")

    if args.text_mode == "normalized":
        from normalization.normalize import normalize

        def model_text(row: dict) -> str:
            return normalize(row["text"]).text
    else:

        def model_text(row: dict) -> str:
            return row["text"]

    def make_dataset(items: list[dict]) -> Dataset:
        dataset = Dataset.from_dict(
            {
                "text": [model_text(row) for row in items],
                "labels": [LABEL_TO_ID[row["label"]] for row in items],
            }
        )
        return dataset.map(
            lambda batch: tokenizer(batch["text"], truncation=True, max_length=256), batched=True
        )

    train_set, validation_set, test_set = map(
        make_dataset, (train_rows, validation_rows, test_rows)
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        "FacebookAI/xlm-roberta-base",
        num_labels=len(LABELS),
        id2label=dict(enumerate(LABELS)),
        label2id=LABEL_TO_ID,
    )
    model = get_peft_model(
        model,
        LoraConfig(
            task_type=TaskType.SEQ_CLS,
            r=8,
            lora_alpha=16,
            lora_dropout=0.1,
            target_modules=["query", "value"],
        ),
    )

    def metrics(prediction):
        predicted = prediction.predictions.argmax(axis=-1)
        return {
            "macro_f1": f1_score(
                prediction.label_ids,
                predicted,
                labels=list(range(len(LABELS))),
                average="macro",
                zero_division=0,
            )
        }

    training = TrainingArguments(
        output_dir=str(args.output_dir),
        learning_rate=2e-4,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        logging_steps=10,
        report_to="none",
        seed=args.seed,
    )
    trainer = Trainer(
        model=model,
        args=training,
        train_dataset=train_set,
        eval_dataset=validation_set,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=metrics,
    )
    started = time.perf_counter()
    trainer.train()
    training_seconds = time.perf_counter() - started
    test_metrics = trainer.evaluate(test_set, metric_key_prefix="test")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(args.output_dir))
    run_info = {
        **test_metrics,
        "seed": args.seed,
        "text_mode": args.text_mode,
        "n_train": len(train_rows),
        "n_validation": len(validation_rows),
        "n_test": len(test_rows),
        "training_seconds": training_seconds,
        "device": str(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"),
        "torch_version": torch.__version__,
    }
    (args.output_dir / "test_metrics.json").write_text(
        json.dumps(run_info, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(test_metrics, indent=2))


if __name__ == "__main__":
    main()
