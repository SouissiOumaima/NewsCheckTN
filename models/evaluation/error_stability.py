"""Compte, pour chaque phrase du test, le nombre de seeds XLM-R qui échouent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows_by_id: dict[str, dict] = {}
    for path in args.predictions:
        seed = path.parent.name.replace("model1_", "").replace("seed", "") or path.stem
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            entry = rows_by_id.setdefault(row["id"], {"id": row["id"], "text": row["text"], "label": row["label"], "lang": row.get("lang", "unk"), "wrong_seeds": []})
            if not row["correct"]:
                entry["wrong_seeds"].append(seed)
    result = []
    for entry in rows_by_id.values():
        entry["n_wrong_seeds"] = len(entry["wrong_seeds"])
        if entry["n_wrong_seeds"]:
            result.append(entry)
    result.sort(key=lambda item: (-item["n_wrong_seeds"], item["id"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in result), encoding="utf-8")
    stable = sum(row["n_wrong_seeds"] == len(args.predictions) for row in result)
    print(json.dumps({"n_error_examples": len(result), "stable_errors_all_seeds": stable, "n_seeds": len(args.predictions)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
