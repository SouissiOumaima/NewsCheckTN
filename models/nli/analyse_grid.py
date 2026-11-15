"""Grille Silver NLI (EXP-C-011) : moyenne et écart-type de la val par lr et par époque, et choix
par la règle fixée le 2026-11-14 (marge 0.03 : époque la plus ancienne, puis lr le plus petit).
Lit seulement les journaux de val (copies de train_log.json écrites par models/nli/run_grid.ps1
dans models/checkpoints/grid_v3/) ; jamais le test. Usage, depuis la racine du dépôt :
    python models/nli/analyse_grid.py main|ablation
"""

import json
import statistics
import sys
from pathlib import Path

MARGIN = 0.03
GRID_DIR = Path(__file__).resolve().parents[2] / "models" / "checkpoints" / "grid_v3"


def load_val_log(path: Path) -> dict:
    """Journal de train.py : refuse tout fichier qui contiendrait une mesure du test."""
    log = json.loads(path.read_text(encoding="utf-8"))
    keys = set(log) | {k for h in log["history"] for k in h}
    if any("test" in k.lower() for k in keys):
        raise ValueError(f"{path.name} contient une clé de test : refusé")
    return log


which = sys.argv[1] if len(sys.argv) > 1 else "main"
runs: dict[float, dict[int, list[float]]] = {}
seeds: dict[float, list[int]] = {}
for f in sorted(GRID_DIR.glob(f"{which}_lr*_seed*.json")):
    log = load_val_log(f)
    lr = log["learning_rate"]
    seeds.setdefault(lr, []).append(log["seed"])
    for h in log["history"]:
        runs.setdefault(lr, {}).setdefault(h["epoch"], []).append(h["val_macro_f1"])

if not runs:
    sys.exit(f"aucun journal {which}_*.json dans {GRID_DIR}")

epochs = sorted({e for per in runs.values() for e in per})
print(f"Grille {which} — val v3 (33 paires), macro-F1 moyenne ± écart-type sur les graines\n")
print("| lr | graines | " + " | ".join(f"ép. {e}" for e in epochs) + " |")
print("|---|---|" + "---|" * len(epochs))
cells = []
for lr in sorted(runs):
    row = []
    for e in epochs:
        v = runs[lr].get(e, [])
        if not v:
            row.append("—")
            continue
        m = statistics.mean(v)
        s = statistics.stdev(v) if len(v) > 1 else 0.0
        row.append(f"{m:.3f} ± {s:.3f}")
        cells.append({"lr": lr, "epoch": e, "mean": m, "n": len(v)})
    print(f"| {lr:g} | {','.join(map(str, sorted(seeds[lr])))} | " + " | ".join(row) + " |")

complete = [c for c in cells if c["n"] == 3]
if len(complete) < len(cells):
    print("\nattention : certaines cases n'ont pas 3 graines ; choix fait sur les cases complètes")
best = max(complete, key=lambda c: c["mean"])
equiv = [c for c in complete if best["mean"] - c["mean"] < MARGIN]
chosen = min(equiv, key=lambda c: (c["epoch"], c["lr"]))
print(f"\nmeilleure moyenne : lr {best['lr']:g}, époque {best['epoch']} ({best['mean']:.3f})")
print(f"équivalentes (écart < {MARGIN}) : {len(equiv)} configuration(s)")
print(
    f"CHOIX PAR LA RÈGLE : lr {chosen['lr']:g}, époque {chosen['epoch']} "
    f"(moyenne {chosen['mean']:.3f})"
    + ("  → époque 0 = modèle sans affinage" if chosen["epoch"] == 0 else "")
)
