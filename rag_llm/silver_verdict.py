"""Lot D — Palier Silver : verdict par LLM contraint, 3 graines, ablations, bootstrap (EXP-D-009).

Systèmes comparés sur les mêmes affirmations, avec la recherche retenue au Silver (EXP-D-008 :
hybride BM25 + e5-base, top 5) et les positions du NLI du Lot C (`NLI_BACKEND`, enregistré) :
- `gabarit + NLI`   : verdict par règles du Bronze (baseline apprise = aucune, déterministe) ;
- `LLM`             : prompt contrôlé v1 (`rag_llm.llm_verdict`), **configuration principale**,
                      fixée avant la mesure du test, 3 graines (13, 42, 2026) ;
- ablations (graine 42) : indices NLI ajoutés au prompt ; 3 puis 1 seul passage ; recherche BM25 ;
- baselines triviales : classe majoritaire du dev, toujours s'abstenir.

Métriques (comme EXP-D-007) : exactitude, macro-F1 (4 labels), couverture, précision sélective,
abstention justifiée, citations invalides ; en plus pour le LLM : part de sorties valides et
raisons de rejet. Moyenne ± écart-type sur les 3 graines. Bootstrap apparié (10 000 tirages,
graine 42) du LLM (graine 42) contre le gabarit, en exactitude et en macro-F1.

Ordre conseillé : d'abord le dev (vérifier le format des sorties), puis **une seule fois** le test.
    python -X utf8 -m rag_llm.silver_verdict                       # dev seulement
    python -X utf8 -m rag_llm.silver_verdict --splits test         # test gelé
    python -X utf8 -m rag_llm.silver_verdict --limit 3             # essai rapide
Les générations sont mises en cache (`evaluation/results/lot-d_llm_cache.jsonl`) : une exécution
interrompue (Colab) reprend là où elle s'est arrêtée. Sortie :
`evaluation/results/lot-d_silver_verdict_<split>_<AAAAMMJJ>.json` (non versionné).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import statistics
from collections import Counter, defaultdict
from datetime import date

from common.schemas import Claim, Lang
from data.loaders import load_evidence_corpus
from evaluation.metrics import macro_f1
from rag_llm import llm_verdict as lv
from rag_llm.bronze_report import DEV_CLAIMS, NEI, verdict_baseline
from rag_llm.evaluate_retrieval import RESULTS_DIR, ROOT, load_claims
from rag_llm.evaluate_verdict import compute_metrics
from rag_llm.freeze_test import check as check_freeze
from rag_llm.retrieval import hybrid
from rag_llm.silver_retrieval import LANGS, SPLITS, lang_family, paired_bootstrap
from rag_llm.verdict import generate_verdict_with_reason

K = 5
SEEDS = (13, 42, 2026)
MAIN_SEED = 42
REPLICATIONS = 10_000
CACHE = RESULTS_DIR / "lot-d_llm_cache.jsonl"

# (nom, k, montrer les indices NLI, méthode de recherche ou None = celle du Silver, graines)
LLM_SYSTEMS = [
    ("LLM", K, False, None, SEEDS),
    ("ablation : LLM + indices NLI", K, True, None, (MAIN_SEED,)),
    ("ablation : LLM avec 3 passages", 3, False, None, (MAIN_SEED,)),
    ("ablation : LLM avec 1 passage", 1, False, None, (MAIN_SEED,)),
    ("ablation : LLM, recherche BM25", K, False, "bm25", (MAIN_SEED,)),
]


# ---------------------------------------------------------------------------
# Cache des générations
# ---------------------------------------------------------------------------


class CachedGenerator:
    """Enveloppe un moteur : une même requête (prompt, graine, modèle) n'est générée qu'une fois."""

    def __init__(self, generator, path=CACHE) -> None:
        self.inner, self.path, self.name = generator, path, generator.name
        self.hits = self.misses = 0
        self._cache: dict[str, str] = {}
        if path is not None and path.exists():
            with path.open(encoding="utf-8") as f:
                for line in filter(str.strip, f):
                    row = json.loads(line)
                    self._cache[row["key"]] = row["output"]

    def _key(self, messages: list[dict], seed: int) -> str:
        blob = json.dumps([self.name, seed, messages], ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    def generate(self, messages: list[dict], seed: int) -> str:
        key = self._key(messages, seed)
        if key in self._cache:
            self.hits += 1
            return self._cache[key]
        self.misses += 1
        output = self.inner.generate(messages, seed)
        self._cache[key] = output
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"key": key, "output": output}, ensure_ascii=False) + "\n")
        return output


# ---------------------------------------------------------------------------
# Préparation : recherche et positions NLI, une fois par affirmation
# ---------------------------------------------------------------------------


def prepare(corpus, claims: list[dict], method: str, predict_stances) -> dict:
    """Top 5 et positions NLI pour chaque affirmation (réutilisés par tous les systèmes)."""
    out = {}
    for c in claims:
        claim = Claim(text=c["text"], lang=Lang(c["lang"]))
        evidences = hybrid.retrieve(claim, corpus, k=K, method=method)
        out[c["claim_id"]] = (claim, evidences, predict_stances(claim, evidences))
    return out


def _row(c: dict, verdict, evidences, **extra) -> dict:
    retrieved = {e.doc_id for e in evidences}
    return {
        "claim_id": c["claim_id"],
        "lang": lang_family(c),
        "group": f"{c['lang']}-{c.get('script', '?')}",
        "gold": c["gold_label"],
        "pred": verdict.label.value,
        "abstained": verdict.abstained,
        "citations": verdict.citations,
        "invalid_citations": [d for d in verdict.citations if d not in retrieved],
        **extra,
    }


def run_template(claims, prepared, method: str) -> list[dict]:
    threshold = hybrid.min_relevance_score(method)
    rows = []
    for c in claims:
        claim, evidences, stances = prepared[c["claim_id"]]
        verdict, reason = generate_verdict_with_reason(claim, stances, min_score=threshold)
        rows.append(_row(c, verdict, evidences, reason=reason))
    return rows


def run_llm(claims, prepared, generator, k: int, show_nli: bool, seed: int, method: str):
    threshold = hybrid.min_relevance_score(method)
    rows = []
    for c in claims:
        claim, evidences, stances = prepared[c["claim_id"]]
        evidences, stances = evidences[:k], stances[:k]
        res = lv.llm_verdict(
            claim,
            evidences,
            generator,
            seed=seed,
            stances=stances,
            show_nli=show_nli,
            min_score=threshold,
        )
        rows.append(
            _row(
                c,
                res.verdict,
                evidences,
                valid=res.valid,
                error=res.error,
                fallback=res.fallback,
                seed=seed,
                raw=res.raw,
                explanation=res.verdict.explanation,
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Métriques et statistiques
# ---------------------------------------------------------------------------


def metrics(rows: list[dict]) -> dict:
    out = compute_metrics(rows)
    if rows and "valid" in rows[0]:
        out["valid_outputs"] = round(sum(r["valid"] for r in rows) / len(rows), 3)
        out["rejections"] = dict(Counter(r["error"] for r in rows if r["error"]))
    by_lang = defaultdict(list)
    for r in rows:
        by_lang[r["lang"]].append(r)
    out["by_lang"] = {g: compute_metrics(by_lang[g]) for g in LANGS if g in by_lang}
    return out


def seed_summary(per_seed: dict[int, dict]) -> dict:
    out = {}
    for m in ("accuracy", "macro_f1", "coverage", "valid_outputs"):
        vals = [s[m] for s in per_seed.values() if s.get(m) is not None]
        if vals:
            sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
            out[m] = {"mean": round(statistics.mean(vals), 3), "std": round(sd, 3)}
    return out


def paired_bootstrap_macro_f1(
    gold: list[str],
    base: list[str],
    cand: list[str],
    replications: int = REPLICATIONS,
    seed: int = 42,
) -> dict:
    n = len(gold)
    rng = random.Random(seed)
    diffs = []
    for _ in range(replications):
        idx = [rng.randrange(n) for _ in range(n)]
        g = [gold[i] for i in idx]
        diffs.append(macro_f1(g, [cand[i] for i in idx]) - macro_f1(g, [base[i] for i in idx]))
    diffs.sort()
    return {
        "diff": round(macro_f1(gold, cand) - macro_f1(gold, base), 3),
        "ci95": [
            round(diffs[int(0.025 * replications)], 3),
            round(diffs[int(0.975 * replications) - 1], 3),
        ],
        "p_one_sided": round(sum(d <= 0 for d in diffs) / replications, 4),
        "n": n,
        "replications": replications,
        "seed": seed,
    }


def compare(base_rows: list[dict], cand_rows: list[dict]) -> dict:
    gold = [r["gold"] for r in base_rows]
    correct = lambda rows: [float(r["pred"] == r["gold"]) for r in rows]  # noqa: E731
    return {
        "accuracy": paired_bootstrap(correct(base_rows), correct(cand_rows), REPLICATIONS),
        "macro_f1": paired_bootstrap_macro_f1(
            gold, [r["pred"] for r in base_rows], [r["pred"] for r in cand_rows]
        ),
    }


# ---------------------------------------------------------------------------
# Évaluation d'un jeu
# ---------------------------------------------------------------------------


def evaluate_split(corpus, claims, generator, predict_stances, method: str = "hybrid") -> dict:
    prepared = {method: prepare(corpus, claims, method, predict_stances)}
    for *_, other, _ in LLM_SYSTEMS:
        if other and other not in prepared:
            prepared[other] = prepare(corpus, claims, other, predict_stances)

    template = run_template(claims, prepared[method], method)
    systems = {"gabarit + NLI": {"metrics": metrics(template), "per_claim": template}}
    for name, k, show_nli, other, seeds in LLM_SYSTEMS:
        m = other or method
        per_seed_rows = {
            s: run_llm(claims, prepared[m], generator, k, show_nli, s, m) for s in seeds
        }
        per_seed = {s: metrics(rows) for s, rows in per_seed_rows.items()}
        main_rows = per_seed_rows.get(MAIN_SEED) or next(iter(per_seed_rows.values()))
        systems[name] = {
            "metrics": per_seed.get(MAIN_SEED) or next(iter(per_seed.values())),
            "per_seed": per_seed,
            "seeds": seed_summary(per_seed) if len(seeds) > 1 else None,
            "per_claim": main_rows,
            "bootstrap_vs_gabarit": compare(template, main_rows),
        }
    majority = Counter(c["gold_label"] for c in load_claims(DEV_CLAIMS)).most_common(1)[0][0]
    baselines = {
        f"majorité ({majority})": verdict_baseline(claims, majority),
        "toujours abstention": verdict_baseline(claims, NEI),
    }
    return {"systems": systems, "baselines": baselines}


def print_split(name: str, res: dict) -> None:
    print(f"\n=== {name.upper()}")
    print(
        f"{'système':<34}{'exact.':>8}{'m-F1':>7}{'couv.':>7}{'sél.':>7}{'valid.':>8}"
        + "".join(f"{g:>7}" for g in LANGS)
        + "   (exactitude par langue)"
    )
    for sys_name, s in res["systems"].items():
        m = s["metrics"]
        sel = m.get("selective_accuracy")
        langs = "".join(f"{m['by_lang'].get(g, {}).get('accuracy', '-'):>7}" for g in LANGS)
        print(
            f"{sys_name:<34}{m['accuracy']:>8}{m['macro_f1']:>7}{m['coverage']:>7}"
            f"{str(sel):>7}{str(m.get('valid_outputs', '-')):>8}{langs}"
        )
    for b, m in res["baselines"].items():
        print(f"{b:<34}{m['accuracy']:>8}{m['macro_f1']:>7}{m['coverage']:>7}")
    main = res["systems"]["LLM"]
    if main.get("seeds"):
        s = main["seeds"]
        print(
            "LLM, 3 graines (moyenne ± écart-type) : "
            + ", ".join(f"{k} {v['mean']} ± {v['std']}" for k, v in s.items())
        )
    print("Bootstrap apparié contre le gabarit (différence, IC 95 %, p unilatéral) :")
    for sys_name, s in res["systems"].items():
        if "bootstrap_vs_gabarit" in s:
            a, f = s["bootstrap_vs_gabarit"]["accuracy"], s["bootstrap_vs_gabarit"]["macro_f1"]
            print(
                f"  {sys_name:<32} exact. {a['diff']:+.3f} {a['ci95']} p={a['p_one_sided']}"
                f" | m-F1 {f['diff']:+.3f} {f['ci95']} p={f['p_one_sided']}"
            )
    rejected = {
        n: s["metrics"].get("rejections")
        for n, s in res["systems"].items()
        if s["metrics"].get("rejections")
    }
    if rejected:
        print(f"Sorties rejetées (raison : nombre) : {rejected}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--splits", nargs="+", default=["dev"], choices=list(SPLITS))
    p.add_argument("--retrieval", default="hybrid", choices=hybrid.METHODS)
    p.add_argument("--model", default=None, help="LLM (défaut : LLM_MODEL ou Qwen2.5-7B-Instruct)")
    p.add_argument("--limit", type=int, default=None, help="essai rapide sur N affirmations")
    args = p.parse_args()

    if "test" in args.splits:
        problems = check_freeze()
        if problems:
            raise SystemExit("Test gelé modifié : " + "; ".join(problems))

    from models.nli.stance import backend_info, predict_stances

    generator = lv.get_generator()
    if args.model:
        generator.name = args.model
    generator = CachedGenerator(generator)
    payload = {
        "exp_id": "EXP-D-009",
        "date": date.today().isoformat(),
        "llm": generator.name,
        "prompt_version": lv.PROMPT_VERSION,
        "prompt_sha": lv.prompt_fingerprint(),
        "temperature": lv.TEMPERATURE,
        "top_p": lv.TOP_P,
        "seeds": SEEDS,
        "retrieval": args.retrieval,
        "nli": backend_info(),
        "limit": args.limit,
        "reasoning_effort": os.getenv("LLM_REASONING_EFFORT"),
    }
    for split in args.splits:
        corpus_path, claims_path = SPLITS[split]
        corpus, claims = load_evidence_corpus(corpus_path), load_claims(claims_path)
        claims = claims[: args.limit] if args.limit else claims
        res = evaluate_split(corpus, claims, generator, predict_stances, args.retrieval)
        print_split(
            f"{split} — {len(claims)} affirmations, LLM {generator.name}, "
            f"NLI {payload['nli'].get('backend')}",
            res,
        )
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out = RESULTS_DIR / f"lot-d_silver_verdict_{split}_{date.today():%Y%m%d}.json"
        out.write_text(
            json.dumps(
                {
                    **payload,
                    "split": split,
                    "api_dropped": getattr(generator.inner, "dropped", []),
                    **res,
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        print(f"Résultats : {out.relative_to(ROOT)}")
    print(f"Cache : {generator.hits} réutilisées, {generator.misses} générées")


if __name__ == "__main__":
    main()
