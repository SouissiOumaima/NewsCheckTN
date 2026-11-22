"""Lot D — Gold, EXP-D-017 : LLM-juge local, validé par son accord avec l'annotation humaine.

Protocole : `docs/lot-d_protocole_gold.md`, sections 4 et 6.

Plan fixé avant la mesure :
- juge : `qwen2.5:3b-instruct` (Ollama, local), différent de Falcon ; prompt versionné
  `rag_llm/prompts/juge_v<N>.txt` ; température 0 ; graine 42 ; JSON imposé ;
- unités : les 30 verdicts de Falcon (graine 42) d'EXP-D-018, avec les mêmes passages que ceux
  montrés aux annotatrices (fichier `lot-d_annotation_hadil_dev.csv`) ;
- partage du dev (graine 42) en deux moitiés de 15 verdicts : `mise_au_point` (le prompt peut y
  être modifié, chaque version est un nouveau fichier) puis `mesure` (une seule fois, prompt
  inchangé) ;
- trois étiquettes : `pertinence` (par passage cité), `invente`, `fidelite` ;
- accord : kappa de Cohen et accord brut, IC 95 % du kappa par bootstrap (10 000 tirages,
  graine 42) ; si une étiquette n'a qu'une seule valeur chez l'humain et le juge, le kappa n'est pas
  défini et l'étiquette est déclarée **non validable** sur ce jeu ;
- validation : une étiquette est validée si kappa ≥ 0.60 sur la moitié `mesure` ;
- en plus : accord entre les deux annotations humaines (Hadil, Wiem) sur leurs verdicts communs.

Usage : `rag_llm/exp_d_017_juge.ps1 -Part mise_au_point` puis, une seule fois,
`-Part mesure`. Sorties non versionnées dans `evaluation/results/`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
from datetime import date
from pathlib import Path

from rag_llm import llm_verdict as lv
from rag_llm.evaluate_retrieval import RESULTS_DIR, ROOT
from rag_llm.silver_verdict import CachedGenerator

EXP_ID = "EXP-D-017"
PROMPTS = Path(__file__).resolve().parent / "prompts"
P = ["P1", "P2", "P3", "P4", "P5"]
LABELS = {
    "pertinence": ("pertinent", "non_pertinent"),
    "invente": ("oui", "non"),
    "fidelite": ("fidele", "infidele"),
}
SPLIT_SEED = 42
JUDGE_SEED = 42
KEYS_PLACEHOLDER = "{{CLES}}"
YES_NO = {"oui": True, "non": False}
KAPPA_MIN = 0.60
REPLICATIONS = 10_000
HUMAN_HADIL = RESULTS_DIR / "lot-d_annotation_hadil_dev_annote.csv"
HUMAN_WIEM = RESULTS_DIR / "lot-d_annotation_wiem_dev_annote.csv"


# ---------------------------------------------------------------------------
# Lecture des annotations
# ---------------------------------------------------------------------------


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def cited(row: dict) -> list[str]:
    return [c.strip() for c in (row.get("citations") or "").split(",") if c.strip() in P]


def human_labels(row: dict) -> dict[tuple[str, str], str]:
    """{(claim_id, étiquette[:passage]) : valeur} pour une ligne annotée."""
    cid, out = row["claim_id"], {}
    for p in cited(row):
        if row.get(f"pertinence_{p}"):
            out[(cid, f"pertinence:{p}")] = row[f"pertinence_{p}"].strip()
    for lab in ("invente", "fidelite"):
        if row.get(lab):
            out[(cid, lab)] = row[lab].strip()
    return out


def split_halves(claim_ids: list[str], seed: int = SPLIT_SEED) -> dict[str, list[str]]:
    ids = sorted(claim_ids)
    random.Random(seed).shuffle(ids)
    half = len(ids) // 2
    return {"mise_au_point": sorted(ids[:half]), "mesure": sorted(ids[half:])}


# ---------------------------------------------------------------------------
# Juge
# ---------------------------------------------------------------------------


def build_messages(row: dict, system_prompt: str) -> list[dict]:
    cits = cited(row)
    lines = [
        f"Affirmation : {row['affirmation']}",
        f"Verdict du système : {row['verdict']}",
        f"Explication du système : {row.get('explication') or '(aucune)'}",
        "Passages :",
    ]
    for p in P:
        if row.get(p):
            mark = " (CITÉ)" if p in cits else ""
            lines.append(f"{p}{mark} : {row[p]}")
    lines.append(f"Passages cités : {', '.join(cits) if cits else 'aucun'}")
    if KEYS_PLACEHOLDER in system_prompt:  # prompt v2 et suivants : clés attendues explicites
        system_prompt = system_prompt.replace(
            KEYS_PLACEHOLDER, expected_keys_template(row, system_prompt)
        )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "\n".join(lines)},
    ]


def expected_keys_template(row: dict, system_prompt: str = "") -> str:
    """Gabarit JSON des clés attendues pour ce verdict (format plat, prompts v2 et v3)."""
    keys = {"raison": "...", "sens_explication": "confirmee | contredite | insuffisante"}
    keys.update({f"pertinence_{p}": "oui | non" for p in cited(row)})
    if '"faits_absents"' in system_prompt:  # v3 : le code applique la règle de fidélité
        keys["faits_absents"] = ["..."]
    else:
        keys.update({"fait_invente": "oui | non", "verdict_fidele": "oui | non"})
    return json.dumps(keys, ensure_ascii=False)


# Prompt v3 : le juge lit le sens de l'explication et liste les faits absents ; la règle du guide
# (section 4) est appliquée par le code : fidèle = verdict cohérent avec ce sens
# ET aucun fait absent.
SENS_FOR_VERDICT = {
    "vrai": {"confirmee"},
    "faux": {"contredite"},
    "preuves_insuffisantes": {"insuffisante"},
    "trompeur": {"confirmee", "contredite"},  # en partie vrai, en partie faux
}


def parse_judge(raw: str, row: dict) -> tuple[dict[tuple[str, str], str], str | None]:
    """Étiquettes du juge ; erreur si la sortie n'est pas exploitable."""
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        return {}, "json_absent"
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}, "json_invalide"
    if not isinstance(data, dict):
        return {}, "json_invalide"
    cid, out = row["claim_id"], {}
    if "faits_absents" in data:  # prompt v3 : règle appliquée par le code
        for p in cited(row):
            v = YES_NO.get(str(data.get(f"pertinence_{p}", "")).strip().lower())
            if v is not None:
                out[(cid, f"pertinence:{p}")] = "pertinent" if v else "non_pertinent"
        absent = data.get("faits_absents")
        sens = str(data.get("sens_explication", "")).strip().lower().replace("é", "e")
        if isinstance(absent, list):
            absent = [a for a in absent if str(a).strip() and str(a).strip() != "..."]
            out[(cid, "invente")] = "oui" if absent else "non"
            if sens in {"confirmee", "contredite", "insuffisante"}:
                ok = sens in SENS_FOR_VERDICT.get(row["verdict"], set()) and not absent
                out[(cid, "fidelite")] = "fidele" if ok else "infidele"
        expected = len(cited(row)) + 2
        return out, None if len(out) == expected else "etiquettes_manquantes"
    if "verdict_fidele" in data or "fait_invente" in data:  # format plat (prompt v2)
        for p in cited(row):
            v = YES_NO.get(str(data.get(f"pertinence_{p}", "")).strip().lower())
            if v is not None:
                out[(cid, f"pertinence:{p}")] = "pertinent" if v else "non_pertinent"
        v = YES_NO.get(str(data.get("fait_invente", "")).strip().lower())
        if v is not None:
            out[(cid, "invente")] = "oui" if v else "non"
        v = YES_NO.get(str(data.get("verdict_fidele", "")).strip().lower())
        if v is not None:
            out[(cid, "fidelite")] = "fidele" if v else "infidele"
        expected = len(cited(row)) + 2
        return out, None if len(out) == expected else "etiquettes_manquantes"
    pert = data.get("pertinence") or {}
    if not isinstance(pert, dict):
        pert = {}
    for p in cited(row):
        v = str(pert.get(p, "")).strip().lower().replace(" ", "_")
        if v in LABELS["pertinence"]:
            out[(cid, f"pertinence:{p}")] = v
    for lab in ("invente", "fidelite"):
        v = str(data.get(lab, "")).strip().lower().replace("è", "e")
        if v in LABELS[lab]:
            out[(cid, lab)] = v
    expected = len(cited(row)) + 2
    return out, None if len(out) == expected else "etiquettes_manquantes"


class JudgeGenerator(lv.OpenAICompatibleGenerator):
    """Même client qu'au verdict (Ollama), avec une température de 0."""

    def generate(self, messages: list[dict], seed: int) -> str:
        saved = lv.TEMPERATURE
        lv.TEMPERATURE = 0.0
        try:
            return super().generate(messages, seed)
        finally:
            lv.TEMPERATURE = saved


def run_judge(rows: list[dict], generator, system_prompt: str) -> list[dict]:
    out = []
    for row in rows:
        raw = generator.generate(build_messages(row, system_prompt), JUDGE_SEED)
        labels, error = parse_judge(raw, row)
        out.append({"claim_id": row["claim_id"], "labels": labels, "error": error, "raw": raw})
    return out


def printable(judged: list[dict]) -> list[dict]:
    """Détail par verdict, clés lisibles pour le fichier JSON."""
    return [{**j, "labels": {k[1]: v for k, v in j["labels"].items()}} for j in judged]


# ---------------------------------------------------------------------------
# Accord
# ---------------------------------------------------------------------------


def cohen_kappa(a: list[str], b: list[str]) -> float | None:
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b, strict=True)) / n
    cats = set(a) | set(b)
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    if pe >= 1.0:
        return None  # une seule valeur partout : kappa non défini
    return (po - pe) / (1 - pe)


def agreement(
    ref: dict[tuple[str, str], str], other: dict[tuple[str, str], str], label: str
) -> dict:
    keys = sorted(k for k in ref if k in other and k[1].split(":")[0] == label)
    a, b = [ref[k] for k in keys], [other[k] for k in keys]
    n = len(keys)
    if not n:
        return {"n": 0, "kappa": None, "raw": None}
    kappa = cohen_kappa(a, b)
    out = {
        "n": n,
        "raw": round(sum(x == y for x, y in zip(a, b, strict=True)) / n, 3),
        "kappa": None if kappa is None else round(kappa, 3),
        "ref_counts": {v: a.count(v) for v in sorted(set(a))},
        "other_counts": {v: b.count(v) for v in sorted(set(b))},
        "disagreements": [
            k[0] + ("" if ":" not in k[1] else " " + k[1].split(":")[1])
            for k, x, y in zip(keys, a, b, strict=True)
            if x != y
        ],
    }
    if kappa is not None:
        rng, ks = random.Random(42), []
        for _ in range(REPLICATIONS):
            idx = [rng.randrange(n) for _ in range(n)]
            k = cohen_kappa([a[i] for i in idx], [b[i] for i in idx])
            if k is not None:
                ks.append(k)
        ks.sort()
        if ks:
            out["ci95"] = [
                round(ks[int(0.025 * len(ks))], 3),
                round(ks[int(0.975 * len(ks)) - 1], 3),
            ]
    return out


def validate(per_label: dict[str, dict]) -> dict[str, str]:
    verdicts = {}
    for label, agr in per_label.items():
        if agr["kappa"] is None:
            verdicts[label] = "non validable (kappa non défini)"
        else:
            verdicts[label] = "validée" if agr["kappa"] >= KAPPA_MIN else "non validée"
    return verdicts


# ---------------------------------------------------------------------------
# Exécution
# ---------------------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--part", required=True, choices=["mise_au_point", "mesure"])
    p.add_argument("--prompt", default="juge_v1", help="nom du fichier de prompt (sans .txt)")
    p.add_argument("--human", type=Path, default=HUMAN_HADIL)
    p.add_argument("--human2", type=Path, default=HUMAN_WIEM)
    args = p.parse_args()

    system_prompt = (PROMPTS / f"{args.prompt}.txt").read_text(encoding="utf-8")
    human_rows = read_csv(args.human)
    halves = split_halves([r["claim_id"] for r in human_rows])
    part_ids = set(halves[args.part])
    rows = [r for r in human_rows if r["claim_id"] in part_ids]

    human = {}
    for r in rows:
        human.update(human_labels(r))

    generator = CachedGenerator(JudgeGenerator())
    judged = run_judge(rows, generator, system_prompt)
    judge = {}
    for j in judged:
        judge.update(j["labels"])

    per_label = {lab: agreement(human, judge, lab) for lab in LABELS}
    result = {
        "exp_id": EXP_ID,
        "date": date.today().isoformat(),
        "part": args.part,
        "claim_ids": sorted(part_ids),
        "judge": generator.name,
        "prompt": args.prompt,
        "prompt_sha": hashlib.sha256(system_prompt.encode()).hexdigest()[:16],
        "temperature": 0.0,
        "seed": JUDGE_SEED,
        "human_file": str(args.human.name),
        "judge_errors": {j["claim_id"]: j["error"] for j in judged if j["error"]},
        "agreement_judge_human": per_label,
        "validation": validate(per_label) if args.part == "mesure" else None,
        "per_item": printable(judged),
    }
    if args.human2.exists():
        h2 = {}
        for r in read_csv(args.human2):
            h2.update(human_labels(r))
        all_h1 = {}
        for r in human_rows:
            all_h1.update(human_labels(r))
        result["agreement_human_human"] = {lab: agreement(all_h1, h2, lab) for lab in LABELS}

    print(
        f"\n{EXP_ID} — juge {generator.name}, prompt {args.prompt}, moitié « {args.part} »"
        f" ({len(rows)} verdicts)"
    )
    print(f"{'étiquette':<12}{'n':>4}{'accord':>8}{'kappa':>8}  IC95          humain / juge")
    for lab, a in per_label.items():
        print(
            f"{lab:<12}{a['n']:>4}{str(a['raw']):>8}{str(a['kappa']):>8}  "
            f"{str(a.get('ci95', '-')):<14}{a.get('ref_counts')} / {a.get('other_counts')}"
        )
    if result["judge_errors"]:
        print("Sorties du juge inexploitables :", result["judge_errors"])
    if result["validation"]:
        print("Validation (kappa ≥ 0.60) :", result["validation"])
    if "agreement_human_human" in result:
        print(
            "Accord Hadil / Wiem :",
            {k: (v["n"], v["raw"], v["kappa"]) for k, v in result["agreement_human_human"].items()},
        )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"lot-d_juge_{args.part}_{args.prompt}_{date.today():%Y%m%d}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Résultats : {out.relative_to(ROOT)}")
    print(f"Cache : {generator.hits} réutilisées, {generator.misses} générées")


if __name__ == "__main__":
    main()
