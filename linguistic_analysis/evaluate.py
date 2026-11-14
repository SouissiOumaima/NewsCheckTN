"""Lot B — Évaluation sur un jeu annoté (`eval_30.jsonl` par défaut, `eval_100.jsonl` ensuite).

Métriques, globales, par groupe langue/script (`fr-latin`, `ar-arabic`, `tn-arabic`,
`tn-arabizi`, `tn-mixed`) et par phénomène (champ `phenomena`), chacune avec son effectif :
- détection d'affirmation : exactitude et macro-F1 (`evaluation.metrics`) ;
- modalité : exactitude ;
- triplets SPO (phrases `is_claim = true` du gold) : correspondance exacte et partielle
  (F1 de recouvrement de tokens), par rôle ;
- coréférence : exactitude de `resolved_text` sur les phrases annotées.

Les chaînes sont comparées sous forme repliée (minuscules, arabe normalisé), comme le texte
produit par la normalisation du Lot A2 ; les annotations restent lisibles.

Le fichier est validé avant l'évaluation (`validate_eval_set`). Intervalles de confiance :
bootstrap percentile sur les phrases (`BOOTSTRAP_RESAMPLES` tirages, graine `BOOTSTRAP_SEED`,
niveau `CONFIDENCE`) ; comparaison des deux modes par bootstrap apparié (mêmes tirages de
phrases pour les deux modes). Verrou du jeu : empreinte SHA-256 comparée à celle notée dans
`docs/lot-b_protocole_eval_100.md` (section 7).

Usage (depuis la racine du dépôt) :
    python -m linguistic_analysis.evaluate            # parseurs disponibles (spaCy / Stanza)
    python -m linguistic_analysis.evaluate --rules    # règles seules, comme en CI
    python -m linguistic_analysis.evaluate --errors   # + export des erreurs (analyse d'erreurs)
    python -m linguistic_analysis.evaluate --compare  # règles vs parseurs, bootstrap apparié
    python -m linguistic_analysis.evaluate --eval-set <fichier> --check-lock  # jeu verrouillé
    python -m linguistic_analysis.evaluate --eval-set <fichier> --sha256      # empreinte seule
    python -m linguistic_analysis.evaluate --rules --exp-id EXP-B-012         # autre expérience
`--exp-id` (format `EXP-B-NNN`, défaut `EXP_ID`) est l'identifiant écrit dans les résultats, les
erreurs et la comparaison, et affiché dans le résumé ; il ne change pas le nom des fichiers.
Le résultat est écrit dans `evaluation/results/lot-b_extraction_<mode>_<AAAAMMJJ>.json`
(format de `evaluation/README.md` ; `_<jeu>` est ajouté avant la date pour un autre jeu
qu'`eval_30`), les erreurs dans `lot-b_erreurs_<mode>_<AAAAMMJJ>.json`, la comparaison dans
`lot-b_comparaison_<jeu>_<AAAAMMJJ>.json`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from evaluation.metrics import macro_f1
from linguistic_analysis import modality, preprocessing
from linguistic_analysis.claim_extraction import extract_claims_detailed
from linguistic_analysis.preprocessing import fold
from linguistic_analysis.types import MODALITY_LABELS
from normalization.normalize import normalize

ROOT = Path(__file__).resolve().parents[1]
EVAL_SET = ROOT / "tests" / "fixtures" / "linguistic_analysis" / "eval_30.jsonl"
RESULTS_DIR = ROOT / "evaluation" / "results"
EXP_ID = "EXP-B-005"
_EXP_ID_FORMAT = re.compile(r"EXP-B-[0-9]{3}")  # chiffres ASCII seulement
PROTOCOL = ROOT / "docs" / "lot-b_protocole_eval_100.md"
ROLES = ("subject", "predicate", "obj")
_TOKEN = re.compile(r"\w+|[^\w\s]")

# Format des jeux annotés (guide d'annotation, protocole eval_100 section 5).
LANGS = frozenset({"fr", "ar", "tn"})
SCRIPTS = frozenset({"latin", "arabic", "arabizi", "mixed"})
GROUPS = frozenset({"fr-latin", "ar-arabic", "tn-arabic", "tn-arabizi", "tn-mixed"})
PHENOMENA = frozenset({
    "fait_chiffré", "opinion", "question", "souhait", "hypothétique", "rapporté", "source_citée",
    "conditionnel_journalistique", "futur_intention", "passif", "copule", "phrase_nominale",
    "ordre_vso", "négation", "négation_tn", "complément_temps", "complément_lieu", "coréférence",
    "coréférence_affixe", "coordination", "code_switching",
})
ORIGIN_TYPES = frozenset({"article", "fact-check", "réseau_social", "rédigée"})
ITEM_KEYS = frozenset({"id", "lang", "script", "text", "context", "phenomena", "gold", "origin",
                       "known_hard"})
GOLD_REQUIRED = ("is_claim", "subject", "predicate", "obj", "modality")
GOLD_KEYS = frozenset({*GOLD_REQUIRED, "resolved_text"})
_PLACEHOLDER = re.compile(r"<[^<>]*>")

# Bootstrap : graine fixe (date de mise en place), 1000 tirages, intervalle percentile à 95 %.
BOOTSTRAP_SEED = 20261015
BOOTSTRAP_RESAMPLES = 1000
CONFIDENCE = 0.95
SMALL_CELL = 5  # effectif en dessous duquel une cellule est signalée « * » dans le résumé
SCALAR_METRICS = (
    "is_claim_accuracy", "is_claim_macro_f1", "modality_accuracy",
    *(f"spo_exact.{role}" for role in ROLES), *(f"spo_partial.{role}" for role in ROLES),
    "spo_all_exact", "coref_accuracy",
)


def load_eval_set(path: Path = EVAL_SET) -> list[dict]:
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ---------------------------------------------------------------------------
# Validation du fichier et verrou
# ---------------------------------------------------------------------------


def _placeholders(value) -> list[str]:
    """Valeurs de gabarit (« <phrase française> ») restées dans une ligne, à toute profondeur."""
    if isinstance(value, str):
        return _PLACEHOLDER.findall(value)
    if isinstance(value, dict):
        return [p for v in value.values() for p in _placeholders(v)]
    if isinstance(value, list):
        return [p for v in value for p in _placeholders(v)]
    return []


def _item_problems(item: dict) -> list[str]:
    problems = []
    if not isinstance(item, dict):
        return ["ligne qui n'est pas un objet JSON"]
    unknown = sorted(set(item) - ITEM_KEYS)
    if unknown:
        problems.append(f"clés inconnues {unknown} (gabarit : supprimer « _commentaire »)")
    for key in ("id", "lang", "script", "text"):
        if not isinstance(item.get(key), str) or not item.get(key, "").strip():
            problems.append(f"« {key} » manquant ou vide")
    if item.get("lang") not in LANGS:
        problems.append(f"langue {item.get('lang')!r} hors de {sorted(LANGS)}")
    if item.get("script") not in SCRIPTS:
        problems.append(f"écriture {item.get('script')!r} hors de {sorted(SCRIPTS)}")
    elif item.get("lang") in LANGS and group_of(item) not in GROUPS:
        problems.append(f"groupe {group_of(item)!r} hors de {sorted(GROUPS)}")
    phenomena = item.get("phenomena")
    if not isinstance(phenomena, list) or not phenomena:
        problems.append("« phenomena » doit être une liste non vide")
    else:
        unknown_ph = sorted(set(phenomena) - PHENOMENA)
        if unknown_ph:
            problems.append(f"phénomènes inconnus {unknown_ph}")
    gold = item.get("gold")
    if not isinstance(gold, dict):
        problems.append("« gold » manquant")
    else:
        missing = [k for k in GOLD_REQUIRED if k not in gold]
        if missing:
            problems.append(f"gold : champs manquants {missing}")
        if sorted(set(gold) - GOLD_KEYS):
            problems.append(f"gold : clés inconnues {sorted(set(gold) - GOLD_KEYS)}")
        if "is_claim" in gold and not isinstance(gold["is_claim"], bool):
            problems.append("gold.is_claim doit être true ou false")
        if "modality" in gold and gold["modality"] not in MODALITY_LABELS:
            problems.append(f"gold.modality {gold['modality']!r} inconnue")
        for role in ROLES:
            if role in gold and not (gold[role] is None or isinstance(gold[role], str)):
                problems.append(f"gold.{role} doit être une chaîne ou null")
        if isinstance(phenomena, list) and "coréférence" in phenomena:
            if not item.get("context") or not gold.get("resolved_text"):
                problems.append("coréférence : « context » et gold.resolved_text obligatoires")
    origin = item.get("origin")
    if origin is not None and (
        not isinstance(origin, dict) or origin.get("type") not in ORIGIN_TYPES
    ):
        problems.append(f"origin.type hors de {sorted(ORIGIN_TYPES)}")
    placeholders = _placeholders(item)
    if placeholders:
        problems.append(f"valeurs de gabarit non remplacées : {placeholders[:3]}")
    return problems


def validate_eval_set(items: list[dict]) -> list[str]:
    """Problèmes de format du jeu (liste vide si le fichier est valide).

    Vérifie, ligne par ligne : clés connues, champs obligatoires, langue / écriture / groupe
    autorisés, phénomènes de la liste, labels de modalité, `context` et `resolved_text` pour la
    coréférence, `origin.type`, absence de valeur de gabarit (« <…> ») ; et l'unicité des `id`.
    """
    problems = []
    seen: dict[str, int] = {}
    for number, item in enumerate(items, start=1):
        label = f"ligne {number}" + (f" ({item.get('id')})" if isinstance(item, dict) else "")
        problems += [f"{label} : {p}" for p in _item_problems(item)]
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            if item["id"] in seen:
                problems.append(f"{label} : id en double (déjà ligne {seen[item['id']]})")
            seen.setdefault(item["id"], number)
    return problems


def counts_summary(items: list[dict]) -> str:
    """Effectifs d'un jeu valide (groupes, affirmations, modalités, phénomènes), à comparer aux
    minimums du protocole ; n'exécute pas le système."""
    groups = Counter(group_of(it) for it in items)
    modalities = Counter(it["gold"]["modality"] for it in items)
    phenomena = Counter(ph for it in items for ph in it["phenomena"])
    real = sum(1 for it in items if it.get("origin", {}).get("type") not in (None, "rédigée"))
    claims = sum(it["gold"]["is_claim"] for it in items)
    lines = [
        f"Jeu valide : {len(items)} phrases, {claims} affirmations "
        f"({claims / len(items):.0%}), {real} phrases réelles",
        "Groupes : " + ", ".join(f"{g} {groups.get(g, 0)}" for g in sorted(GROUPS)),
        "Modalités : " + ", ".join(f"{m} {modalities.get(m, 0)}" for m in MODALITY_LABELS),
        "Phénomènes : " + ", ".join(f"{p} {phenomena.get(p, 0)}" for p in sorted(PHENOMENA)),
    ]
    return "\n".join(lines)


class LockError(ValueError):
    """Le jeu d'évaluation ne correspond pas à l'empreinte enregistrée."""


def sha256_file(path: Path) -> str:
    """Empreinte SHA-256 du fichier, fins de ligne ramenées à LF avant le calcul : git stocke
    le fichier en LF (`.gitattributes`), une copie de travail Windows en CRLF donne la même
    empreinte."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def recorded_sha256(protocol: Path = PROTOCOL) -> str | None:
    """Dernière empreinte notée dans la section 7 du protocole, ou None."""
    text = Path(protocol).read_text(encoding="utf-8")
    section = re.split(r"^## 7\b", text, flags=re.MULTILINE)
    if len(section) < 2:
        return None
    hashes = re.findall(r"\b[0-9a-fA-F]{64}\b", section[1])
    return hashes[-1].lower() if hashes else None


def check_lock(path: Path, protocol: Path = PROTOCOL) -> str:
    """Vérifie que le jeu est celui qui a été verrouillé ; renvoie son empreinte.

    Lève `LockError` si aucune empreinte n'est enregistrée ou si elle diffère.
    """
    expected = recorded_sha256(protocol)
    actual = sha256_file(path)
    if expected is None:
        raise LockError(
            f"aucune empreinte SHA-256 enregistrée dans {Path(protocol).name} (section 7)"
        )
    if actual != expected:
        raise LockError(
            f"{Path(path).name} a changé depuis son verrouillage : SHA-256 {actual} "
            f"≠ {expected} (protocole, section 7)"
        )
    return actual


def group_of(item: dict) -> str:
    return f"{item['lang']}-{item['script']}"


def _norm(value: str | None) -> str | None:
    if value is None:
        return None
    return fold(value).replace("’", "'").strip(" .,;:!?؟،")


def exact_match(gold: str | None, pred: str | None) -> bool:
    return _norm(gold) == _norm(pred)


def token_f1(gold: str | None, pred: str | None) -> float:
    """F1 de recouvrement de tokens (1.0 si les deux sont absents)."""
    if gold is None or pred is None:
        return float(gold is None and pred is None)
    g, p = _TOKEN.findall(_norm(gold) or ""), _TOKEN.findall(_norm(pred) or "")
    common = sum(min(g.count(t), p.count(t)) for t in set(g))
    if not g or not p or common == 0:
        return 0.0
    precision, recall = common / len(p), common / len(g)
    return 2 * precision * recall / (precision + recall)


@contextmanager
def rules_only():
    """Force l'analyse par règles (comme en CI), quels que soient les modèles installés."""
    original = preprocessing.get_parser
    preprocessing.get_parser = lambda lang: None
    try:
        yield
    finally:
        preprocessing.get_parser = original


def predict(item: dict) -> dict:
    """Sortie du Lot B pour la phrase cible (dernière phrase du document, après le contexte)."""
    raw = f"{item['context']} {item['text']}" if item.get("context") else item["text"]
    doc = normalize(raw)
    sentences = preprocessing.analyze(doc)
    target = sentences[-1]
    claim = next((c for c in extract_claims_detailed(doc) if c.span[0] >= target.start), None)
    if claim is None:  # phrase trop courte pour être une affirmation candidate
        label = modality.detect_modality(target)[0]
        return {"is_claim": False, "modality": label, "subject": None, "predicate": None,
                "obj": None, "resolved_text": target.text, "parser": target.parser,
                "triggers": [], "resolution_log": []}
    return {
        "is_claim": claim.is_claim,
        "modality": claim.modality,
        "subject": claim.subject,
        "predicate": claim.predicate,
        "obj": claim.obj,
        "resolved_text": claim.resolved_text,
        "parser": claim.parser,
        "triggers": claim.triggers,
        "resolution_log": claim.resolution_log,
    }


def _metrics(records: list[dict]) -> dict:
    gold_claim = ["claim" if r["gold"]["is_claim"] else "non" for r in records]
    pred_claim = ["claim" if r["pred"]["is_claim"] else "non" for r in records]
    claims = [r for r in records if r["gold"]["is_claim"]]
    coref = [r for r in records if r["gold"].get("resolved_text")]
    out = {
        "n": len(records),
        "is_claim_accuracy": _mean(g == p for g, p in zip(gold_claim, pred_claim, strict=True)),
        "is_claim_macro_f1": round(macro_f1(gold_claim, pred_claim), 3) if records else None,
        "modality_accuracy": _mean(r["gold"]["modality"] == r["pred"]["modality"] for r in records),
        "spo_n": len(claims),
        "spo_exact": {
            role: _mean(exact_match(r["gold"][role], r["pred"][role]) for r in claims)
            for role in ROLES
        },
        "spo_partial": {
            role: _mean(token_f1(r["gold"][role], r["pred"][role]) for r in claims)
            for role in ROLES
        },
        "spo_all_exact": _mean(
            all(exact_match(r["gold"][role], r["pred"][role]) for role in ROLES) for r in claims
        ),
        "coref_n": len(coref),
        "coref_accuracy": _mean(
            exact_match(r["gold"]["resolved_text"], r["pred"]["resolved_text"]) for r in coref
        ),
    }
    return out


def _mean(values) -> float | None:
    values = [float(v) for v in values]
    return round(sum(values) / len(values), 3) if values else None


def _get(metrics: dict, path: str) -> float | None:
    for part in path.split("."):
        metrics = metrics[part]
    return metrics


def _interval(values: list[float], confidence: float) -> tuple[float, float] | None:
    """Intervalle percentile (bornes incluses) d'une distribution bootstrap."""
    if not values:
        return None
    ordered = sorted(values)
    alpha = (1 - confidence) / 2
    last = len(ordered) - 1
    return ordered[math.floor(alpha * last)], ordered[math.ceil((1 - alpha) * last)]


def bootstrap_ci(
    records: list[dict],
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
    confidence: float = CONFIDENCE,
) -> dict[str, dict]:
    """Intervalle de confiance de chaque métrique de `SCALAR_METRICS`, par bootstrap percentile.

    `records` : dicts avec `gold` et `pred` (phrases). Chaque tirage rééchantillonne les phrases
    avec remise ; une métrique sans phrase concernée dans un tirage (ex. coréférence) n'y compte
    pas (`valid` = nombre de tirages utilisés).
    """
    rng = random.Random(seed)
    samples: dict[str, list[float]] = {path: [] for path in SCALAR_METRICS}
    n = len(records)
    for _ in range(resamples if n else 0):
        drawn = _metrics([records[rng.randrange(n)] for _ in range(n)])
        for path in SCALAR_METRICS:
            value = _get(drawn, path)
            if value is not None:
                samples[path].append(value)
    out = {}
    for path, values in samples.items():
        interval = _interval(values, confidence)
        out[path] = {
            "low": interval[0] if interval else None,
            "high": interval[1] if interval else None,
            "valid": len(values),
        }
    return out


def paired_bootstrap(
    items_a: list[dict],
    items_b: list[dict],
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
    confidence: float = CONFIDENCE,
) -> dict[str, dict]:
    """Comparaison appariée de deux sorties sur les mêmes phrases (B − A, par métrique).

    Les deux listes doivent contenir les mêmes `id` (même ordre après tri). Chaque tirage
    utilise les mêmes phrases pour A et B. `contains_zero` : l'intervalle de la différence
    contient 0, la différence n'est donc pas établie à ce niveau de confiance.
    """
    a = sorted(items_a, key=lambda r: r["id"])
    b = sorted(items_b, key=lambda r: r["id"])
    if [r["id"] for r in a] != [r["id"] for r in b]:
        raise ValueError("comparaison appariée : phrases différentes dans les deux sorties")
    observed_a, observed_b = _metrics(a), _metrics(b)
    rng = random.Random(seed)
    diffs: dict[str, list[float]] = {path: [] for path in SCALAR_METRICS}
    n = len(a)
    for _ in range(resamples if n else 0):
        indices = [rng.randrange(n) for _ in range(n)]
        drawn_a = _metrics([a[i] for i in indices])
        drawn_b = _metrics([b[i] for i in indices])
        for path in SCALAR_METRICS:
            va, vb = _get(drawn_a, path), _get(drawn_b, path)
            if va is not None and vb is not None:
                diffs[path].append(vb - va)
    out = {}
    for path in SCALAR_METRICS:
        va, vb = _get(observed_a, path), _get(observed_b, path)
        interval = _interval(diffs[path], confidence)
        out[path] = {
            "a": va,
            "b": vb,
            "diff": None if va is None or vb is None else round(vb - va, 3),
            "diff_mean": _mean(diffs[path]),
            "low": round(interval[0], 3) if interval else None,
            "high": round(interval[1], 3) if interval else None,
            "contains_zero": None if interval is None else interval[0] <= 0 <= interval[1],
            "valid": len(diffs[path]),
        }
    return out


def evaluate(
    items: list[dict],
    *,
    rules: bool = False,
    split: str = EVAL_SET.stem,
    bootstrap: int = 0,
    seed: int = BOOTSTRAP_SEED,
    exp_id: str = EXP_ID,
) -> dict:
    """Évalue le Lot B sur `items` ; renvoie le document de résultats (métriques + prédictions).

    `bootstrap` > 0 : ajoute les intervalles de confiance (global et par groupe) sous la clé
    `bootstrap` ; 0 (défaut de la fonction) les omet, la ligne de commande les calcule.
    `exp_id` : identifiant d'expérience écrit dans le résultat (`EXP_ID` par défaut).
    """
    if rules:
        with rules_only():
            records = [{"item": it, "gold": it["gold"], "pred": predict(it)} for it in items]
    else:
        records = [{"item": it, "gold": it["gold"], "pred": predict(it)} for it in items]

    parsers = sorted({r["pred"]["parser"] for r in records})
    by_group: dict[str, list[dict]] = defaultdict(list)
    by_phenomenon: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_group[group_of(r["item"])].append(r)
        for phenomenon in r["item"].get("phenomena", []):
            by_phenomenon[phenomenon].append(r)
    metrics = _metrics(records)
    metrics["by_lang"] = {group: _metrics(rs) for group, rs in sorted(by_group.items())}
    metrics["by_phenomenon"] = {ph: _metrics(rs) for ph, rs in sorted(by_phenomenon.items())}
    results = {
        "exp_id": exp_id,
        "lot": "B",
        "task": "extraction-affirmations",
        "model": "regles" if rules else "parseurs",
        "parsers_used": parsers,
        "split": split,
        "date": date.today().isoformat(),
        "metrics": metrics,
        "items": [
            {
                "id": r["item"]["id"],
                "group": group_of(r["item"]),
                "phenomena": r["item"].get("phenomena", []),
                "gold": r["gold"],
                "pred": r["pred"],
            }
            for r in records
        ],
    }
    if bootstrap > 0:
        settings = {"resamples": bootstrap, "seed": seed}
        results["bootstrap"] = {
            "seed": seed,
            "resamples": bootstrap,
            "confidence": CONFIDENCE,
            "global": bootstrap_ci(records, **settings),
            "by_lang": {g: bootstrap_ci(rs, **settings) for g, rs in sorted(by_group.items())},
        }
    return results


def _stem(results: dict) -> str:
    split = results.get("split", EVAL_SET.stem)
    suffix = "" if split == EVAL_SET.stem else f"_{split}"
    return f"{results['model']}{suffix}_{results['date'].replace('-', '')}"


def write_results(results: dict, out_dir: Path = RESULTS_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = Path(out_dir) / f"lot-b_extraction_{_stem(results)}.json"
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def find_errors(results: dict) -> list[dict]:
    """Une entrée par (phrase, champ) en erreur, avec le contexte utile à l'analyse.

    Champs examinés : `is_claim` et `modality` (toutes les phrases), `subject` / `predicate` /
    `obj` (phrases `is_claim = true` du gold), `resolved_text` (phrases annotées).
    """
    errors = []
    for it in results["items"]:
        gold, pred = it["gold"], it["pred"]
        fields = ["is_claim", "modality"]
        if gold["is_claim"]:
            fields += list(ROLES)
        if gold.get("resolved_text"):
            fields.append("resolved_text")
        for field in fields:
            if field in ("is_claim", "modality"):
                wrong = gold[field] != pred[field]
            else:
                wrong = not exact_match(gold[field], pred[field])
            if wrong:
                errors.append({
                    "id": it["id"],
                    "group": it["group"],
                    "field": field,
                    "gold": gold[field],
                    "pred": pred[field],
                    "parser": pred["parser"],
                    "triggers": pred["triggers"],
                    "resolution_log": pred["resolution_log"],
                })
    return errors


def write_errors(results: dict, errors: list[dict], out_dir: Path = RESULTS_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = Path(out_dir) / f"lot-b_erreurs_{_stem(results)}.json"
    payload = {"exp_id": results["exp_id"], "model": results["model"], "errors": errors}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _rows(header: str, rows: list[tuple[str, dict]]) -> list[str]:
    """Tableau de scores ; n = phrases, nS = affirmations (SPO), nC = coréférence ;
    « * » = effectif inférieur à SMALL_CELL (score peu fiable)."""
    lines = [
        f"{header:<28}{'n':>4}  {'claim':>6} {'mod.':>6}  "
        f"{'nS':>3} {'S':>5} {'P':>5} {'O':>5}  {'SPO':>5}  {'nC':>3} {'coref':>5}"
    ]
    for name, g in rows:
        exact = g["spo_exact"]
        flag = "*" if g["n"] < SMALL_CELL else " "
        spo_flag = "*" if 0 < g["spo_n"] < SMALL_CELL else " "
        lines.append(
            f"{name:<28}{g['n']:>3}{flag}  "
            f"{_fmt(g['is_claim_accuracy'])} {_fmt(g['modality_accuracy'])}  "
            f"{g['spo_n']:>2}{spo_flag} {_fmt(exact['subject'], 5)} {_fmt(exact['predicate'], 5)} "
            f"{_fmt(exact['obj'], 5)}  {_fmt(g['spo_all_exact'], 5)}  "
            f"{g['coref_n']:>3} {_fmt(g['coref_accuracy'], 5)}"
        )
    return lines


def _summary(results: dict) -> str:
    m = results["metrics"]
    parsers = ", ".join(results["parsers_used"])
    lines = [f"{results['exp_id']} — mode {results['model']} ({parsers}) — jeu {results['split']}"]
    lines += _rows("groupe", [("global", m), *m["by_lang"].items()])
    lines.append(f"coréférence : {_fmt(m['coref_accuracy'])} sur {m['coref_n']} phrases")
    if m.get("by_phenomenon"):
        lines.append("")
        lines += _rows("phénomène", list(m["by_phenomenon"].items()))
    if "bootstrap" in results:
        b = results["bootstrap"]
        lines.append("")
        lines.append(
            f"IC {round(b['confidence'] * 100)} % (bootstrap, {b['resamples']} tirages, "
            f"graine {b['seed']}) — global :"
        )
        for path in SCALAR_METRICS:
            ci = b["global"][path]
            lines.append(
                f"  {path:<22}{_fmt(_get(m, path))}  [{_fmt(ci['low'], 4)} ; {_fmt(ci['high'], 4)}]"
            )
    lines.append("* : effectif < " + str(SMALL_CELL) + ", score peu fiable")
    return "\n".join(lines)


def compare_summary(comparison: dict) -> str:
    lines = [
        f"Comparaison appariée règles (A) / parseurs (B) — jeu {comparison['split']}, "
        f"{comparison['resamples']} tirages, graine {comparison['seed']}, "
        f"IC {round(comparison['confidence'] * 100)} %",
        f"{'métrique':<22}{'règles':>7}{'pars.':>7}{'B−A':>7}   {'IC de B−A':<17} conclusion",
    ]
    for path, c in comparison["metrics"].items():
        if c["diff"] is None:
            lines.append(f"{path:<22}{'-':>7}{'-':>7}{'-':>7}   {'-':<17} non calculable")
            continue
        verdict = (
            "IC contient 0 : différence non établie" if c["contains_zero"]
            else ("parseurs meilleurs" if c["diff"] > 0 else "règles meilleures")
        )
        interval = f"[{c['low']:+.2f} ; {c['high']:+.2f}]"
        lines.append(
            f"{path:<22}{_fmt(c['a'], 7)}{_fmt(c['b'], 7)}{c['diff']:>+7.2f}   "
            f"{interval:<17} {verdict}"
        )
    return "\n".join(lines)


def _fmt(value: float | None, width: int = 6) -> str:
    return f"{'-':>{width}}" if value is None else f"{value:>{width}.2f}"


def exp_id_arg(value: str) -> str:
    """Valide l'option `--exp-id` : format `EXP-B-NNN` (trois chiffres)."""
    if not _EXP_ID_FORMAT.fullmatch(value):
        raise argparse.ArgumentTypeError(
            f"identifiant d'expérience invalide : {value!r} (format attendu : EXP-B-NNN, "
            "trois chiffres, par exemple EXP-B-012)"
        )
    return value


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Évaluation du Lot B sur le jeu annoté.")
    parser.add_argument("--rules", action="store_true", help="règles seules (comme en CI)")
    parser.add_argument("--exp-id", type=exp_id_arg, default=EXP_ID,
                        help=f"identifiant d'expérience, format EXP-B-NNN (défaut {EXP_ID})")
    parser.add_argument("--eval-set", type=Path, default=EVAL_SET)
    parser.add_argument("--out-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--errors", action="store_true", help="exporte aussi les erreurs")
    parser.add_argument("--compare", action="store_true",
                        help="évalue les deux modes et les compare (bootstrap apparié)")
    parser.add_argument("--bootstrap", type=int, default=BOOTSTRAP_RESAMPLES,
                        help=f"tirages bootstrap (0 = sans IC ; défaut {BOOTSTRAP_RESAMPLES})")
    parser.add_argument("--seed", type=int, default=BOOTSTRAP_SEED,
                        help=f"graine du bootstrap (défaut {BOOTSTRAP_SEED})")
    parser.add_argument("--check-lock", action="store_true",
                        help="refuse d'évaluer si l'empreinte du jeu diffère de celle du protocole")
    parser.add_argument("--protocol", type=Path, default=PROTOCOL,
                        help="protocole contenant l'empreinte de référence (section 7)")
    parser.add_argument("--sha256", action="store_true",
                        help="affiche l'empreinte SHA-256 du jeu et s'arrête")
    parser.add_argument("--validate", action="store_true",
                        help="valide le fichier et affiche ses effectifs, sans exécuter le système")
    args = parser.parse_args(argv)
    # Console Windows : forcer l'UTF-8 pour afficher l'arabe sans erreur d'encodage.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.sha256:
        print(f"{sha256_file(args.eval_set)}  {args.eval_set}")
        return
    if args.check_lock:
        try:
            print(f"Verrou OK : SHA-256 {check_lock(args.eval_set, args.protocol)}")
        except LockError as e:
            parser.exit(2, f"Évaluation refusée : {e}\n")
    items = load_eval_set(args.eval_set)
    problems = validate_eval_set(items)
    if problems:
        listing = "\n".join(f"  {p}" for p in problems)
        parser.exit(2, f"Jeu d'évaluation invalide :\n{listing}\n")
    if args.validate:
        print(counts_summary(items))
        return
    settings = {"split": args.eval_set.stem, "bootstrap": args.bootstrap, "seed": args.seed,
                "exp_id": args.exp_id}
    if args.compare:
        _compare(items, args, settings)
        return
    results = evaluate(items, rules=args.rules, **settings)
    path = write_results(results, args.out_dir)
    print(_summary(results))
    print(f"-> {path}")
    if args.errors:
        errors = find_errors(results)
        print(f"{len(errors)} erreur(s) -> {write_errors(results, errors, args.out_dir)}")
        for e in errors:
            print(f"  {e['id']:<6} {e['group']:<11} {e['field']:<13} [{e['parser']}] "
                  f"attendu={e['gold']!r} produit={e['pred']!r}")


def _compare(items: list[dict], args: argparse.Namespace, settings: dict) -> None:
    runs = {mode: evaluate(items, rules=mode == "regles", **settings)
            for mode in ("regles", "parseurs")}
    for results in runs.values():
        print(_summary(results))
        print(f"-> {write_results(results, args.out_dir)}")
        print()
    resamples = args.bootstrap or BOOTSTRAP_RESAMPLES
    comparison = {
        "exp_id": settings["exp_id"],
        "split": settings["split"],
        "date": date.today().isoformat(),
        "a": "regles",
        "b": "parseurs",
        "parsers_used": runs["parseurs"]["parsers_used"],
        "seed": args.seed,
        "resamples": resamples,
        "confidence": CONFIDENCE,
        "metrics": paired_bootstrap(
            runs["regles"]["items"], runs["parseurs"]["items"], resamples=resamples, seed=args.seed
        ),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stamp = comparison["date"].replace("-", "")
    path = Path(args.out_dir) / f"lot-b_comparaison_{settings['split']}_{stamp}.json"
    path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    print(compare_summary(comparison))
    print(f"-> {path}")


if __name__ == "__main__":
    main()
