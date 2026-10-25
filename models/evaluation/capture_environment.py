"""Enregistre les versions, le GPU et l'environnement d'une exécution Model 1."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
from pathlib import Path


def version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        import torch
        gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except ImportError:
        torch, gpu = None, None
    report = {
        "python": platform.python_version(), "platform": platform.platform(), "gpu": gpu,
        "packages": {name: version(name) for name in ("torch", "transformers", "peft", "accelerate", "datasets", "sentence-transformers", "scikit-learn", "numpy")},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
