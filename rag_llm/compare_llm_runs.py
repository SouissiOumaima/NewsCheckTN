"""Lot D — EXP-D-012 : comparer deux fichiers de verdict LLM (Tiny Aya contre Aya Expanse 8B).

Question : Tiny Aya (3,35 Md de paramètres, CohereLabs/tiny-aya-global), assez petit pour un
portable (GPU de 4 Go), perd-il beaucoup par rapport à Aya Expanse 8B (EXP-D-010) ?

Plan fixé AVANT la mesure (rien n'est réglé) :
- même protocole qu'EXP-D-010 : `rag_llm.silver_verdict --main-only`, prompt v1, température 0.3,
  top-p 0.9, 4 bits sur GPU, recherche hybride top 5, NLI Bronze pour le gabarit de repli,
  graines 13, 42 et 2026 ; dev d'abord (sorties valides), puis test gelé une seule fois ;
- système principal : `tiny-aya-global` (généraliste, suit les consignes) ; secondaire :
  `tiny-aya-earth` (spécialiste Afrique et Asie de l'Ouest, donc l'arabe), mêmes réglages ;
- comparaison appariée sur la graine 42 (bootstrap 10 000 tirages, graine 42), exactitude et
  macro-F1, référence = Aya Expanse 8B d'EXP-D-010 ;
- règle de décision pour la démo locale : Tiny Aya peut remplacer Aya 8B dans l'interface si
  (1) ses sorties valides sur le test (graine 42) sont ≥ 0,90 et (2) l'écart d'exactitude
  « Aya 8B meilleur » n'est pas significatif (p unilatéral ≥ 0,05). Avec 21 affirmations, ce
  test a peu de puissance : « non significatif » ne prouve pas l'équivalence, et l'écart observé
  est toujours affiché. Le système officiel du Silver reste Aya 8B.

    python -X utf8 -m rag_llm.compare_llm_runs --ref <aya-8b.json> --cand <tiny-aya.json>
Les fichiers sont ceux de `evaluation/results/` (non versionnés) ; seuls des identifiants et des
labels sont affichés.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_llm import silver_verdict as sv

MIN_VALID = 0.90
ALPHA = 0.05


def load(path: Path, system: str = "LLM") -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if system not in data.get("systems", {}):
        raise SystemExit(f"{path} : pas de système {system!r} ({list(data.get('systems', {}))})")
    return data


def aligned(ref_rows: list[dict], cand_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Mêmes affirmations, dans le même ordre (sinon arrêt)."""
    by_id = {r["claim_id"]: r for r in cand_rows}
    if set(by_id) != {r["claim_id"] for r in ref_rows}:
        raise SystemExit("Les deux fichiers ne portent pas sur les mêmes affirmations.")
    cand = [by_id[r["claim_id"]] for r in ref_rows]
    if any(a["gold"] != b["gold"] for a, b in zip(ref_rows, cand, strict=True)):
        raise SystemExit("Labels attendus différents : fichiers incompatibles.")
    return ref_rows, cand


def protocol_differences(ref: dict, cand: dict) -> list[str]:
    keys = ("prompt_version", "prompt_sha", "temperature", "top_p", "retrieval", "seeds")
    return [k for k in keys if ref.get(k) != cand.get(k)]


def decide(cand_metrics: dict, p_ref_better: float) -> dict:
    valid = cand_metrics.get("valid_outputs")
    ok_valid = valid is not None and valid >= MIN_VALID
    ok_gap = p_ref_better >= ALPHA
    return {
        "valid_outputs": valid,
        "valid_ok": ok_valid,
        "p_ref_better": p_ref_better,
        "gap_ok": ok_gap,
        "demo_locale_autorisee": ok_valid and ok_gap,
    }


def compare_runs(ref: dict, cand: dict, system: str = "LLM") -> dict:
    ref_rows, cand_rows = aligned(
        ref["systems"][system]["per_claim"], cand["systems"][system]["per_claim"]
    )
    cand_vs_ref = sv.compare(ref_rows, cand_rows)  # différence = candidat − référence
    ref_vs_cand = sv.compare(cand_rows, ref_rows)  # p : la référence est-elle meilleure ?
    changed = [
        {"claim_id": a["claim_id"], "lang": a["lang"], "gold": a["gold"],
         "ref": a["pred"], "cand": b["pred"]}
        for a, b in zip(ref_rows, cand_rows, strict=True)
        if a["pred"] != b["pred"]
    ]  # fmt: skip
    cand_metrics = sv.metrics(cand_rows)
    return {
        "ref_llm": ref.get("llm"),
        "cand_llm": cand.get("llm"),
        "protocol_differences": protocol_differences(ref, cand),
        "ref": {"metrics": sv.metrics(ref_rows), "seeds": ref["systems"][system].get("seeds")},
        "cand": {"metrics": cand_metrics, "seeds": cand["systems"][system].get("seeds")},
        "cand_minus_ref": cand_vs_ref,
        "p_ref_better": {
            "accuracy": ref_vs_cand["accuracy"]["p_one_sided"],
            "macro_f1": ref_vs_cand["macro_f1"]["p_one_sided"],
        },
        "changed": changed,
        "decision": decide(cand_metrics, ref_vs_cand["accuracy"]["p_one_sided"]),
    }


def print_report(r: dict) -> None:
    print(f"Référence : {r['ref_llm']}\nCandidat  : {r['cand_llm']}")
    if r["protocol_differences"]:
        print("⚠️ Protocole différent sur :", ", ".join(r["protocol_differences"]))
    for who in ("ref", "cand"):
        m, s = r[who]["metrics"], r[who]["seeds"]
        print(
            f"\n{who:<5} graine 42 : exact. {m['accuracy']} | m-F1 {m['macro_f1']} | couv. "
            f"{m['coverage']} | valides {m.get('valid_outputs')} | par langue "
            f"{ {g: v.get('accuracy') for g, v in m['by_lang'].items()} }"
        )
        if s:
            print(f"      3 graines : {s}")
    for key in ("accuracy", "macro_f1"):
        c = r["cand_minus_ref"][key]
        print(
            f"\n{key} candidat − référence : {c['diff']:+.3f} IC95 {c['ci95']} "
            f"| p (référence meilleure) = {r['p_ref_better'][key]}"
        )
    print(f"\nVerdicts différents ({len(r['changed'])}) :")
    for x in r["changed"]:
        print(f"  {x['claim_id']:<8} ({x['lang']}) or {x['gold']:<22} {x['ref']} → {x['cand']}")
    d = r["decision"]
    print(
        f"\nRègle fixée avant la mesure : valides ≥ {MIN_VALID} ({d['valid_outputs']}) et "
        f"p ≥ {ALPHA} ({d['p_ref_better']}) → démo locale autorisée : "
        f"{'OUI' if d['demo_locale_autorisee'] else 'NON'}"
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--ref", required=True, type=Path, help="fichier d'Aya Expanse 8B (EXP-D-010)")
    p.add_argument("--cand", required=True, type=Path, help="fichier de Tiny Aya")
    p.add_argument("--system", default="LLM")
    args = p.parse_args()
    report = compare_runs(load(args.ref, args.system), load(args.cand, args.system), args.system)
    print_report(report)
    out = args.cand.with_name(args.cand.stem + "_vs_ref.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRésultats : {out}")


if __name__ == "__main__":
    main()
