"""Lot B — Robustesse (critère « INV ») de l'extracteur gelé : perturbations à sens conservé.

Mesure seulement : aucune règle n'est modifiée à partir de ces résultats.

Entrée (hors dépôt) : fichier tabulé du format de `evaluate_double` (`id`, `texte`, `label`,
`modalite` ; colonnes facultatives `langue` et `script`, langue déclarée par le jeu).

Perturbations (une par texte et par type ; graine 20261015, un générateur par type,
`random.Random("20261015-<type>")`). Un texte auquel un type ne s'applique pas (perturbation
impossible ou sans effet) est exclu pour ce type :
- P1 casse : lettres latines en minuscules ;
- P2 ponctuation : catégories Unicode P* retirées, sauf apostrophe / tiret entre deux lettres et
  séparateur décimal entre deux chiffres ;
- P3 faute : une lettre supprimée ou doublée dans un mot alphabétique de 4 lettres ou plus ;
- P4 élongation : lettre latine répétée 3 fois ; dans un mot arabe, tatweel après une lettre
  qui se lie à la suivante ;
- P5 diacritiques : diacritiques arabes retirés (texte sans diacritique : exclu) ;
- P6 arabizi (textes tn-arabizi et tn-mixte) : chiffre → lettre (7→h, 9→q, 3→a, 5→kh), ou
  kh→5, q→9 ;
- P7 fin : « !! » ou un émoji ajouté en fin de texte.
L'empreinte SHA-256 de l'ensemble des perturbations est calculée (contrôle de reproductibilité,
option `--expect-perturbations-sha256`).

Mesures, en mode règles et en mode parseurs (prédiction de `evaluate_double.predict_text`) :
- taux de changement de `is_claim` et de `modality` (prédiction perturbée ≠ d'origine), IC
  bootstrap (graine 20261015, 1000 tirages) ;
- macro-F1 de détection et exactitude de modalité contre le gold, avant / après, différence
  appariée (graine 42, 2000 tirages) ;
- taux de changement de la langue détectée par le Lot A2 ;
- ventilation par groupe de langue ; un groupe de moins de 15 textes est signalé ;
- couples (texte, type) instables, causes (catégories d'indices seulement) et 10 cas maximaux ;
- décomposition de P2 sur les textes qui contenaient un point d'interrogation : (a) un mot
  interrogatif des lexiques `[questions]` reste présent après perturbation, (b) aucun.

Sorties (identifiants, labels et chiffres ; aucun texte) : `inv_resultats.json`,
`inv_resultats.md`, `p2_decompose.csv`.

Usage (depuis la racine du dépôt ; dossier de sortie hors du dépôt) :
    python -X utf8 notebooks/lot_b_linguistic/mesures/inv_robustesse.py --gold <test.tsv> \\
        --out-dir <dossier> [--expect-perturbations-sha256 <empreinte>]
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import json
import random
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from linguistic_analysis import evaluate, modality, preprocessing  # noqa: E402
from linguistic_analysis import evaluate_double as ed  # noqa: E402
from linguistic_analysis.claim_extraction import extract_claims_detailed  # noqa: E402
from linguistic_analysis.factuality import find_marker, load_lexicon, match_text  # noqa: E402
from normalization.normalize import normalize  # noqa: E402

SEED = 20261015
CI_RESAMPLES = 1000
PAIRED_SEED, PAIRED_RESAMPLES = 42, 2000
MIN_GROUP = 15
GROUPS = ("fr", "ar", "tn-arabe", "tn-arabizi", "tn-mixte")
TYPES = ("P1_casse", "P2_ponctuation", "P3_faute", "P4_elongation", "P5_diacritiques",
         "P6_arabizi", "P7_fin_emoji")
QUESTION_MARKS = ("?", "؟")

AR_LETTER = re.compile(r"[ء-ي]")
DIACRITICS = re.compile(r"[ً-ْٰ]")
LATIN_LETTER = re.compile(r"[A-Za-zÀ-ɏ]")
TATWEEL = "ـ"
# lettres arabes qui ne se lient pas à la suivante : pas de tatweel après elles
NON_CONNECTING = set("اأإآدذرزوؤة"
                     "ىء")
WORD = re.compile(r"\S+")
ARABIZI_DIGITS = {"7": "h", "9": "q", "3": "a", "5": "kh"}
END_MARKS = (" !!", " \U0001F642")


def declared_group(row: dict) -> str:
    lang, script = row["langue"].strip(), row["script"].strip()
    if lang in ("fr", "ar"):
        return lang
    return {"arabic": "tn-arabe", "arabizi": "tn-arabizi", "mixed": "tn-mixte"}[script]


# ---------------------------------------------------------------------------
# Perturbations : chacune renvoie le texte perturbé ou None (non applicable)
# ---------------------------------------------------------------------------


def p1_casse(text: str, rng: random.Random) -> str | None:
    if not LATIN_LETTER.search(text):
        return None
    out = "".join(c.lower() if LATIN_LETTER.match(c) else c for c in text)
    return out if out != text else None


def p2_ponctuation(text: str, rng: random.Random) -> str | None:
    out = []
    for i, c in enumerate(text):
        if unicodedata.category(c).startswith("P"):
            prev, nxt = text[i - 1:i], text[i + 1:i + 2]
            if c in "'’-" and prev.isalpha() and nxt.isalpha():
                out.append(c)
                continue
            if c in ".," and prev.isdigit() and nxt.isdigit():
                out.append(c)
                continue
            out.append(" " if prev.isalnum() and nxt.isalnum() else "")
            continue
        out.append(c)
    res = re.sub(r"[ \t]{2,}", " ", "".join(out)).strip()
    return res if res != text.strip() else None


def _alpha_words(text: str, min_len: int = 4) -> list[tuple[int, int]]:
    """Positions des mots entièrement alphabétiques (sans chiffre), ponctuation de bord retirée."""
    cands = []
    for m in WORD.finditer(text):
        core = m.group().strip(".,;:!?«»\"()[]'’…،؟؛")
        if len(core) >= min_len and core.isalpha():
            start = m.start() + m.group().index(core)
            cands.append((start, start + len(core)))
    return cands


def p3_faute(text: str, rng: random.Random) -> str | None:
    cands = _alpha_words(text)
    if not cands:
        return None
    s, e = rng.choice(cands)
    i = rng.randrange(s, e)
    if rng.random() < 0.5:
        return text[:i] + text[i + 1:]       # lettre supprimée
    return text[:i] + text[i] + text[i:]     # lettre doublée


def p4_elongation(text: str, rng: random.Random) -> str | None:
    cands = _alpha_words(text, min_len=2)
    if not cands:
        return None
    s, e = rng.choice(cands)
    if AR_LETTER.search(text[s:e]):
        pos = [i for i in range(s, e - 1) if text[i] not in NON_CONNECTING]
        if not pos:
            return None
        i = rng.choice(pos)
        return text[:i + 1] + TATWEEL + text[i + 1:]
    i = rng.randrange(s, e)
    return text[:i] + text[i] * 3 + text[i + 1:]


def p5_diacritiques(text: str, rng: random.Random) -> str | None:
    if not AR_LETTER.search(text) or not DIACRITICS.search(text):
        return None
    return DIACRITICS.sub("", text)


def p6_arabizi(text: str, rng: random.Random, group: str) -> str | None:
    if group not in ("tn-arabizi", "tn-mixte"):
        return None
    cands = []
    for m in WORD.finditer(text):
        w = m.group()
        if not LATIN_LETTER.search(w):
            continue
        cands += [(m.start() + j, 1, ARABIZI_DIGITS[c]) for j, c in enumerate(w)
                  if c in ARABIZI_DIGITS]
        cands += [(m.start() + j, 2, "5") for j in range(len(w) - 1) if w[j:j + 2].lower() == "kh"]
        cands += [(m.start() + j, 1, "9") for j, c in enumerate(w) if c.lower() == "q"]
    if not cands:
        return None
    i, n, new = rng.choice(cands)
    return text[:i] + new + text[i + n:]


def p7_fin(text: str, rng: random.Random) -> str | None:
    return text.rstrip() + rng.choice(END_MARKS)


_SIMPLE = {"P1_casse": p1_casse, "P2_ponctuation": p2_ponctuation, "P3_faute": p3_faute,
           "P4_elongation": p4_elongation, "P5_diacritiques": p5_diacritiques,
           "P7_fin_emoji": p7_fin}


def perturb(kind: str, text: str, rng: random.Random, group: str) -> str | None:
    out = p6_arabizi(text, rng, group) if kind == "P6_arabizi" else _SIMPLE[kind](text, rng)
    return out if out is not None and out != text else None


def perturb_all(texts: dict[str, str], groups: dict[str, str],
                seed: int = SEED) -> dict[tuple[str, str], str]:
    """Toutes les perturbations : {(type, id) : texte perturbé}."""
    out = {}
    for kind in TYPES:
        rng = random.Random(f"{seed}-{kind}")
        for i in sorted(texts):
            res = perturb(kind, texts[i], rng, groups[i])
            if res is not None:
                out[(kind, i)] = res
    return out


def perturbations_sha256(perturbed: dict[tuple[str, str], str]) -> str:
    payload = json.dumps(sorted([k, i, t] for (k, i), t in perturbed.items()), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Système : même décision que evaluate_double.predict_text, plus des indices de cause
# ---------------------------------------------------------------------------


def predict(text: str) -> dict:
    doc = normalize(text)
    claims = extract_claims_detailed(doc)
    sentences = preprocessing.analyze(doc)
    claim = next((c for c in claims if c.is_claim), None)
    if claim is not None:
        label = claim.modality
    elif claims:
        label = claims[0].modality
    else:
        label = modality.detect_modality(sentences[0])[0]
    chosen = claim or (claims[0] if claims else None)
    triggers = chosen.triggers if chosen else modality.detect_modality(sentences[0])[2]
    return {"is_claim": claim is not None, "modality": label, "lang": doc.lang.value,
            "n_sentences": len(sentences), "n_candidates": len(claims),
            # catégorie seulement (`opinion:…` → `opinion`) : aucun mot du texte en sortie
            "trigger_cats": sorted({t.split(":", 1)[0] for t in triggers})}


def run_mode(texts: dict[str, str], mode: str) -> dict[str, dict]:
    ctx = evaluate.rules_only() if mode == "regles" else contextlib.nullcontext()
    with ctx:
        return {k: predict(t) for k, t in texts.items()}


# ---------------------------------------------------------------------------
# Mesures
# ---------------------------------------------------------------------------


def rate_ci(flags: list[bool]) -> dict:
    n = len(flags)
    if not n:
        return {"n": 0, "count": 0, "rate": None, "ci": None}
    ci = ed.ci(SEED, CI_RESAMPLES, n, lambda idx: sum(flags[i] for i in idx) / n)
    return {"n": n, "count": sum(flags), "rate": sum(flags) / n, "ci": ci}


def paired_diff(metric, gold: list, after: list, before: list) -> dict | None:
    if not gold:
        return None
    r = ed.paired_vs_baseline(PAIRED_SEED, PAIRED_RESAMPLES, metric, gold, after, before)
    lo, hi = r["ci"]
    return {"before": r["baseline"], "after": r["systeme"], "diff": r["difference"],
            "ci": [lo, hi], "contains_zero": lo <= 0 <= hi}


def block(ids: list[str], gold_claim: dict, gold_mod: dict, orig: dict, pert: dict) -> dict:
    gc, gm = [gold_claim[i] for i in ids], [gold_mod[i] for i in ids]
    bc, ac = [orig[i]["is_claim"] for i in ids], [pert[i]["is_claim"] for i in ids]
    bm, am = [orig[i]["modality"] for i in ids], [pert[i]["modality"] for i in ids]
    return {
        "n": len(ids), "interpretable": len(ids) >= MIN_GROUP,
        "change_is_claim": rate_ci([b != a for b, a in zip(bc, ac, strict=True)]),
        "change_modality": rate_ci([b != a for b, a in zip(bm, am, strict=True)]),
        "change_lang_a2": rate_ci([orig[i]["lang"] != pert[i]["lang"] for i in ids]),
        "detection_macro_f1": paired_diff(ed.detection_macro_f1, gc, ac, bc),
        "modality_accuracy": paired_diff(ed.accuracy, gm, am, bm),
    }


def cause(o: dict, p: dict) -> str:
    if o["lang"] != p["lang"]:
        return "langue détectée par A2 changée"
    if o["n_candidates"] != p["n_candidates"] or o["n_sentences"] != p["n_sentences"]:
        return "segmentation / nombre de candidates changé"
    lost = set(o["trigger_cats"]) - set(p["trigger_cats"])
    new = set(p["trigger_cats"]) - set(o["trigger_cats"])
    if lost and not new:
        return "marqueur non reconnu après perturbation"
    if new and not lost:
        return "marqueur nouveau après perturbation"
    if lost or new:
        return "marqueurs différents"
    return "autre (mêmes catégories d'indices)"


def question_entries() -> list[str]:
    """Mots interrogatifs des lexiques gelés (sections `[questions]` fr, ar, tn)."""
    return [e for code in ("fr", "ar", "tn") for e in load_lexicon(code).get("questions", ())]


def interrogative_word(text: str, entries: list[str]) -> tuple[bool, bool]:
    """(mot interrogatif présent n'importe où, présent en tête) dans le texte normalisé."""
    folded = match_text(normalize(text).text)
    return (find_marker(folded, entries) is not None,
            find_marker(folded, entries, anchored=True) is not None)


def run(gold_path: Path, modes: tuple[str, ...] = ed.MODES) -> tuple[dict, list[list]]:
    """Mesure complète ; renvoie (résultats, lignes du CSV de décomposition de P2)."""
    items, problems = ed.read_annotation(gold_path)
    if problems:
        raise ValueError("gold invalide : " + " ; ".join(problems[:5]))
    with Path(gold_path).open(encoding="utf-8-sig", newline="") as f:
        rows = {r["id"].strip(): r for r in csv.DictReader(f, delimiter="\t")}
    text = {it["id"]: it["text"] for it in items}
    gold_claim = {it["id"]: it["gold"]["is_claim"] for it in items}
    gold_mod = {it["id"]: it["gold"]["modality"] for it in items}
    group = {i: declared_group(rows[i]) for i in text}

    perturbed = perturb_all(text, group)
    applicable = {k: sorted(i for kk, i in perturbed if kk == k) for k in TYPES}
    p2_q = [i for i in applicable["P2_ponctuation"]
            if any(q in text[i] for q in QUESTION_MARKS)]
    entries = question_entries()
    p2_class = {}
    for i in p2_q:
        anywhere, head = interrogative_word(perturbed[("P2_ponctuation", i)], entries)
        p2_class[i] = ("a" if anywhere else "b", head)

    out = {"gold_sha256": hashlib.sha256(Path(gold_path).read_bytes()).hexdigest(),
           "n": len(text), "seed": SEED, "ci_resamples": CI_RESAMPLES,
           "paired": [PAIRED_SEED, PAIRED_RESAMPLES],
           "perturbed_sha256": perturbations_sha256(perturbed),
           "applicable": {k: {"n": len(v), "by_group": dict(Counter(group[i] for i in v))}
                          for k, v in applicable.items()},
           "lexique_questions": len(entries), "modes": {}, "p2_decompose": {}}
    unstable: Counter = Counter()
    details: dict = {}
    p2_preds: dict = {}
    for mode in modes:
        orig = run_mode(text, mode)
        pert_all = run_mode({f"{k}|{i}": t for (k, i), t in perturbed.items()}, mode)
        all_ids = sorted(text)
        res = {"origine": {
            "detection_macro_f1": ed.detection_macro_f1([gold_claim[i] for i in all_ids],
                                                        [orig[i]["is_claim"] for i in all_ids]),
            "modality_accuracy": ed.accuracy([gold_mod[i] for i in all_ids],
                                             [orig[i]["modality"] for i in all_ids])},
            "types": {}}
        for kind in TYPES:
            ids = applicable[kind]
            pert = {i: pert_all[f"{kind}|{i}"] for i in ids}
            res["types"][kind] = {"global": block(ids, gold_claim, gold_mod, orig, pert)}
            for g in GROUPS:
                res["types"][kind][g] = block([i for i in ids if group[i] == g],
                                              gold_claim, gold_mod, orig, pert)
            for i in ids:
                o, p = orig[i], pert[i]
                score = 2 * (o["is_claim"] != p["is_claim"]) + (o["modality"] != p["modality"])
                if score:
                    unstable[(i, kind)] += score
                    details.setdefault((i, kind), {})[mode] = {
                        "is_claim": [o["is_claim"], p["is_claim"]],
                        "modality": [o["modality"], p["modality"]],
                        "lang_a2": [o["lang"], p["lang"]], "cause": cause(o, p),
                        "triggers_avant": o["trigger_cats"], "triggers_apres": p["trigger_cats"],
                        "candidates": [o["n_candidates"], p["n_candidates"]]}
        p2_preds[mode] = {i: (orig[i], pert_all[f"P2_ponctuation|{i}"]) for i in p2_q}
        out["p2_decompose"][mode] = {
            sub: block([i for i in p2_q if p2_class[i][0] == sub], gold_claim, gold_mod,
                       orig, {i: pert_all[f"P2_ponctuation|{i}"] for i in p2_q})
            for sub in ("a", "b")}
        out["modes"][mode] = res
    top = sorted(unstable.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    out["top10"] = [{"id": i, "type": k, "group": group[i], "score": s,
                     "gold": [gold_claim[i], gold_mod[i]], "modes": details[(i, k)]}
                    for (i, k), s in top]
    out["unstable_cases"] = len(unstable)
    out["max_score_cases"] = sum(1 for s in unstable.values() if s == 3 * len(modes))
    out["cause_counts"] = {m: dict(Counter(d[m]["cause"] for d in details.values() if m in d))
                           for m in modes}
    out["p2_questions"] = {"n": len(p2_q), "a": sum(c[0] == "a" for c in p2_class.values()),
                           "a_mot_en_tete": sum(c[1] for c in p2_class.values() if c[0] == "a"),
                           "by_group": {sub: dict(Counter(group[i] for i in p2_q
                                                          if p2_class[i][0] == sub))
                                        for sub in ("a", "b")}}
    csv_rows = [["id", "groupe", "a_b", "mot_interrogatif_en_tete", "gold_is_claim",
                 "gold_modalite"]
                + [f"{m}_{f}_{w}" for m in modes for f in ("is_claim", "modalite")
                   for w in ("avant", "apres")]]
    for i in p2_q:
        row = [i, group[i], p2_class[i][0], p2_class[i][1], gold_claim[i], gold_mod[i]]
        for m in modes:
            o, p = p2_preds[m][i]
            row += [o["is_claim"], p["is_claim"], o["modality"], p["modality"]]
        csv_rows.append(row)
    return out, csv_rows


# ---------------------------------------------------------------------------
# Tableaux
# ---------------------------------------------------------------------------


def _pct(x: dict | None) -> str:
    if not x or x["rate"] is None:
        return "-"
    lo, hi = x["ci"]
    return f"{100 * x['rate']:.1f} % [{100 * lo:.1f} ; {100 * hi:.1f}]"


def _diff(x: dict | None) -> str:
    if x is None:
        return "-"
    flag = "" if x["contains_zero"] else " **≠0**"
    return (f"{x['before']:.3f} → {x['after']:.3f} ({x['diff']:+.3f} "
            f"[{x['ci'][0]:+.3f} ; {x['ci'][1]:+.3f}]){flag}")


def to_markdown(d: dict) -> str:
    out = ["### Effectifs (textes perturbés par type)", "",
           "| Type | n | " + " | ".join(GROUPS) + " |", "|---|---|" + "---|" * len(GROUPS)]
    for k, v in d["applicable"].items():
        out.append(f"| {k} | {v['n']} | "
                   + " | ".join(str(v["by_group"].get(g, 0)) for g in GROUPS) + " |")
    for mode, res in d["modes"].items():
        o = res["origine"]
        out += ["", f"### Mode {mode} — origine : macro-F1 {o['detection_macro_f1']:.3f}, "
                    f"modalité {o['modality_accuracy']:.3f}", "",
                "| Type | n | Δ is_claim | Δ modality | Δ langue A2 | macro-F1 détection | "
                "exactitude modalité |", "|---|---|---|---|---|---|---|"]
        for k, t in res["types"].items():
            b = t["global"]
            out.append(f"| {k} | {b['n']} | {_pct(b['change_is_claim'])} | "
                       f"{_pct(b['change_modality'])} | {_pct(b['change_lang_a2'])} | "
                       f"{_diff(b['detection_macro_f1'])} | {_diff(b['modality_accuracy'])} |")
        out += ["", f"### Mode {mode} — par groupe (changement is_claim / modality ; Δ macro-F1) ;"
                    " ⚠ = n < 15", "",
                "| Type | " + " | ".join(GROUPS) + " |", "|---|" + "---|" * len(GROUPS)]
        for k, t in res["types"].items():
            cells = []
            for g in GROUPS:
                b = t[g]
                if not b["n"]:
                    cells.append("—")
                    continue
                warn = " ⚠" if not b["interpretable"] else ""
                x = b["detection_macro_f1"]
                flag = "" if x["contains_zero"] else " **≠0**"
                cells.append(f"n={b['n']}{warn} : {100 * b['change_is_claim']['rate']:.1f} / "
                             f"{100 * b['change_modality']['rate']:.1f} % ; {x['diff']:+.3f} "
                             f"[{x['ci'][0]:+.3f} ; {x['ci'][1]:+.3f}]{flag}")
            out.append(f"| {k} | " + " | ".join(cells) + " |")
    q = d["p2_questions"]
    out += ["", f"### P2 décomposé ({q['n']} textes avec point d'interrogation ; "
                f"(a) {q['a']}, dont {q['a_mot_en_tete']} avec le mot en tête)", "",
            "| Mode | Groupe | n | changement is_claim | changement modality | Δ macro-F1 |",
            "|---|---|---|---|---|---|"]
    for mode, subs in d["p2_decompose"].items():
        for sub, b in subs.items():
            if not b["n"]:
                continue
            ci_c, ci_m = b["change_is_claim"], b["change_modality"]
            if b["interpretable"]:
                cells = [_pct(ci_c), _pct(ci_m), _diff(b["detection_macro_f1"])]
            else:  # moins de 15 textes : comptes bruts, non interprétable
                cells = [f"{ci_c['count']} / {b['n']} ⚠", f"{ci_m['count']} / {b['n']} ⚠",
                         "non interprétable"]
            out.append(f"| {mode} | ({sub}) | {b['n']} | " + " | ".join(cells) + " |")
    out += ["", f"### Cas instables : {d['unstable_cases']} couples (texte, type) ; "
                f"{d['max_score_cases']} au score maximal (10 premiers par identifiant)", "",
            "| id | groupe | type | mode | is_claim | modality | langue A2 | cause |",
            "|---|---|---|---|---|---|---|---|"]
    for c in d["top10"]:
        for mode, x in c["modes"].items():
            out.append(f"| {c['id']} | {c['group']} | {c['type']} | {mode} | "
                       f"{x['is_claim'][0]} → {x['is_claim'][1]} | "
                       f"{x['modality'][0]} → {x['modality'][1]} | "
                       f"{x['lang_a2'][0]} → {x['lang_a2'][1]} | {x['cause']} |")
    out += ["", "### Causes (tous les couples instables)", ""]
    for mode, cc in d["cause_counts"].items():
        out.append(f"- {mode} : " + " ; ".join(f"{k} {v}" for k, v in
                                                sorted(cc.items(), key=lambda kv: -kv[1])))
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Robustesse INV de l'extracteur du Lot B.")
    ap.add_argument("--gold", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--modes", nargs="+", choices=ed.MODES, default=list(ed.MODES))
    ap.add_argument("--expect-gold-sha256", help="refuse la mesure si l'empreinte du gold diffère")
    ap.add_argument("--expect-perturbations-sha256",
                    help="refuse la mesure si l'empreinte des perturbations diffère "
                         "(préfixe admis)")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not ed.outside_repo(args.out_dir):
        ap.exit(2, "Le dossier de sortie doit être hors du dépôt.\n")
    if args.expect_gold_sha256:
        actual = hashlib.sha256(args.gold.read_bytes()).hexdigest()
        if actual != args.expect_gold_sha256.lower():
            ap.exit(2, f"Empreinte du gold inattendue : {actual}\n")
    if args.expect_perturbations_sha256:
        items, _ = ed.read_annotation(args.gold)
        with args.gold.open(encoding="utf-8-sig", newline="") as f:
            rows = {r["id"].strip(): r for r in csv.DictReader(f, delimiter="\t")}
        texts = {it["id"]: it["text"] for it in items}
        sha = perturbations_sha256(perturb_all(texts, {i: declared_group(rows[i])
                                                       for i in texts}))
        if not sha.startswith(args.expect_perturbations_sha256.lower()):
            ap.exit(2, f"Empreinte des perturbations inattendue : {sha}\n")
        print(f"Empreinte des perturbations conforme : {sha}")
    out, csv_rows = run(args.gold, tuple(args.modes))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "inv_resultats.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.out_dir / "inv_resultats.md").write_text(to_markdown(out), encoding="utf-8")
    with (args.out_dir / "p2_decompose.csv").open("w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(csv_rows)
    print(to_markdown(out))


if __name__ == "__main__":
    main()
