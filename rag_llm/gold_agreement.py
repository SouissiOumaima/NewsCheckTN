"""Lot D — Gold, EXP-D-017 (suite) : accord entre annotateurs humains, et du juge avec chacun.

Protocole : `docs/lot-d_protocole_gold.md`, section 4 (accord humain-humain) et section 6.

Plan fixé avant le calcul :
- annotations humaines lues dans `evaluation/results/lot-d_annotation_<nom>_dev_annote.csv`
  (`hadil` = référence : 30 verdicts ; les autres : les 10 mêmes verdicts tirés avec la graine 42) ;
- juge : sorties déjà enregistrées du juge retenu (Qwen2.5-3B, prompt v2) sur les deux moitiés
  (`lot-d_juge_mise_au_point_juge_v2_*.json` et `lot-d_juge_mesure_juge_v2_*.json`) ;
  **aucun nouveau lancement du juge** ;
- pour chaque paire (annotateur, annotateur) et (juge, annotateur) : kappa de Cohen, accord brut
  et IC 95 % par bootstrap, par étiquette, sur les verdicts communs ;
- descriptif : aucune décision n'est changée (la validation du juge reste celle de la moitié
  « mesure » contre la référence).

Usage : `python -X utf8 -m rag_llm.gold_agreement`
"""

from __future__ import annotations

import json
import re
from itertools import combinations
from pathlib import Path

from rag_llm.evaluate_retrieval import RESULTS_DIR, ROOT
from rag_llm.gold_judge import LABELS, agreement, human_labels, read_csv

PATTERN = re.compile(r"lot-d_annotation_([a-z]+)_dev_annote\.csv$")
JUDGE_GLOB = "lot-d_juge_{part}_juge_v2_2*.json"  # 3B (sans suffixe de modèle)


def load_humans(results_dir: Path = RESULTS_DIR) -> dict[str, dict]:
    humans = {}
    for f in sorted(results_dir.glob("lot-d_annotation_*_dev_annote.csv")):
        m = PATTERN.search(f.name)
        if not m:
            continue
        labels = {}
        for r in read_csv(f):
            labels.update(human_labels(r))
        humans[m.group(1)] = labels
    return humans


def load_judge(results_dir: Path = RESULTS_DIR) -> dict:
    labels = {}
    for part in ("mise_au_point", "mesure"):
        files = sorted(results_dir.glob(JUDGE_GLOB.format(part=part)))
        if not files:
            raise SystemExit(f"Sorties du juge absentes : {JUDGE_GLOB.format(part=part)}")
        for item in json.loads(files[-1].read_text(encoding="utf-8"))["per_item"]:
            for key, v in item["labels"].items():
                labels[(item["claim_id"], key)] = v
    return labels


def pairwise(annotators: dict[str, dict]) -> dict[str, dict]:
    out = {}
    for a, b in combinations(annotators, 2):
        out[f"{a} / {b}"] = {lab: agreement(annotators[a], annotators[b], lab) for lab in LABELS}
    return out


def main() -> None:
    humans = load_humans()
    if "hadil" not in humans or len(humans) < 2:
        raise SystemExit(f"Il faut la référence et au moins une autre annotation : {list(humans)}")
    annotators = {**humans, "juge": load_judge()}
    res = pairwise(annotators)

    print(f"Annotateurs : {', '.join(humans)} + juge (Qwen2.5-3B, prompt v2)\n")
    print(f"{'paire':<20}{'étiquette':<12}{'n':>4}{'accord':>8}{'kappa':>8}  IC95")
    for pair, per_label in res.items():
        for lab, a in per_label.items():
            print(
                f"{pair:<20}{lab:<12}{a['n']:>4}{str(a['raw']):>8}{str(a['kappa']):>8}"
                f"  {a.get('ci95', '-')}"
            )
    out = RESULTS_DIR / "lot-d_accord_annotateurs_dev.json"
    out.write_text(
        json.dumps({"annotators": list(annotators), "pairs": res}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nRésultats : {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
