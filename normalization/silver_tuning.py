"""Lot A2 — Silver : réglage du lexique tunisien en lettres arabes (EXP-A2-012, EXP-A2-013).

Usage (depuis la racine du dépôt) :
    python -X utf8 -m normalization.silver_tuning tune              # EXP-A2-012 (inchangé)
    python -X utf8 -m normalization.silver_tuning tune --leipzig    # EXP-A2-013
    python -X utf8 -m normalization.silver_tuning final --min-texts 8 --max-leipzig 0

Protocole (aucun réglage sur un jeu de test) :
- dev en lettres arabes (tsac_arabic_sample_reference.tsv) coupé en deux moitiés FIXES selon
  l'empreinte SHA-256 de chaque texte : « reglage » sert à choisir, « mesure » à mesurer ;
- presse : PADT dev pour régler (fausses alertes), PADT test seulement à la fin ;
- eval_30 : seulement à la fin, pour vérifier l'absence de régression.

Leviers :
- seuil MIN_TEXTS du lexique (12 = lexique actuel ; 8, 6, 4 = mots plus rares ajoutés) ;
- retrait d'un préfixe / suffixe avant comparaison (langid.affix_variants) ;
- EXP-A2-013 : un mot candidat n'est ajouté que s'il apparaît dans au plus N phrases d'une
  grande référence d'arabe standard (Leipzig, News 2022, 300 000 phrases, CC BY). N > 0 tolère
  les rares citations en dialecte de la presse. Le lexique actuel (78 marques) n'est pas filtré.

Règle de choix, fixée AVANT de lancer : meilleur macro-F1 sur « reglage » parmi les
configurations à 0 fausse alerte sur PADT dev ; égalité -> seuil le plus haut, puis filtre le
plus strict (N le plus petit), puis sans affixes (la configuration la plus simple).

Sorties : un tableau dans le terminal et data/interim/langid/silver_tuning*.tsv (chiffres
seulement, aucun texte du corpus).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import tarfile
from collections import Counter
from pathlib import Path

from common.schemas import Lang
from normalization.annotation import SAMPLES, load_tsac, read_annotations
from normalization.evaluate import DEFAULT_DATASET, REPO, load_examples
from normalization.langid import _key, is_dialectal_arabic, load_markers
from normalization.lexicon import load_padt, words
from normalization.normalize import (
    detect_language,
    detect_script,
    detect_script_by_rules,
    expand_presentation_forms,
    normalize_arabic,
)

INTERIM = REPO / "data" / "interim" / "langid"
DEV_ARABIC = INTERIM / "tsac_arabic_sample_reference.tsv"
DEV_LATIN = INTERIM / "tsac_latin_sample_reference.tsv"
RESULTS = INTERIM / "silver_tuning.tsv"
RESULTS_LEIPZIG = INTERIM / "silver_tuning_leipzig.tsv"

# Référence d'arabe standard (EXP-A2-013) : archive Leipzig telle que téléchargée, non versionnée.
LEIPZIG = REPO / "data" / "raw" / "langid" / "leipzig" / "ara_news_2022_300K.tar.gz"

LEXICON_THRESHOLD = 12  # seuil qui a produit le lexique actuel (lexicon.MIN_TEXTS)
THRESHOLDS = (12, 8, 6, 4)
MAX_LEIPZIG = (0, 2, 5)  # occurrences tolérées dans la référence (phrases contenant le mot)

# Mots écartés volontairement du lexique (voir l'en-tête de tn_markers.txt) : ils ne
# doivent pas revenir par la baisse du seuil. Formes repliées (après normalisation).
EXCLUDED = frozenset(
    {
        "الي",  # الي : confondu avec إلى
        "لي",  # لي
        "ياسر",  # ياسر : aussi un prénom
        "خاطر",  # خاطر
        "متاع",  # متاع
    }
)
NUN = "ن"  # verbes en نـ : نحب = « nous aimons » en arabe standard, exclus aussi


# ---------------------------------------------------------------------------
# Données
# ---------------------------------------------------------------------------

def half(text: str) -> str:
    """Moitié fixe d'un texte : même réponse à chaque lancement, sans graine aléatoire."""
    return "reglage" if hashlib.sha256(text.encode("utf-8")).digest()[0] % 2 == 0 else "mesure"


def annotated_texts() -> set[str]:
    """Textes annotés (échantillons et références) : jamais utilisés pour choisir des mots."""
    paths = [*SAMPLES.values(), DEV_ARABIC, DEV_LATIN]
    return {text for path in paths if path.exists() for _, text in read_annotations(path)}


def candidate_counts() -> Counter[str]:
    """Nombre de textes TSAC (lettres arabes, hors annotés) contenant chaque mot.

    Même critère que lexicon.py : on ne garde que les mots absents de PADT train.
    Les mots passent par _key, comme dans find_dialect_markers.
    """
    annotated = annotated_texts()
    tsac = [t for t in load_tsac()
            if detect_script_by_rules(t) == "arabic" and t not in annotated]
    in_padt = {_key(w) for sentence in load_padt("train") for w in words(sentence)}
    # On compte des TEXTES : un mot répété dans un même commentaire ne compte qu'une fois.
    in_tsac = Counter(w for text in tsac for w in {_key(x) for x in words(text)})
    return Counter({w: n for w, n in in_tsac.items() if w not in in_padt})


def read_leipzig_sentences(path: Path) -> list[str]:
    """Phrases de l'archive Leipzig, lues sans extraction (*-sentences.txt : id<TAB>phrase)."""
    with tarfile.open(path, "r:gz") as archive:
        member = next(m for m in archive.getmembers() if m.name.endswith("-sentences.txt"))
        raw = archive.extractfile(member).read().decode("utf-8")
    return [line.split("\t", 1)[1] for line in raw.splitlines() if "\t" in line]


def reference_counts(sentences: list[str]) -> Counter[str]:
    """Nombre de phrases de la référence contenant chaque mot (forme repliée, puis _key)."""
    return Counter(w for s in sentences for w in {_key(x) for x in words(s)})


def lexicon_for(
    threshold: int,
    counts: Counter[str],
    reference: Counter[str] | None = None,
    max_reference: int | None = None,
) -> frozenset[str]:
    """Lexique actuel, plus les mots trouvés dans [threshold, 12[ textes TSAC.

    Les mots à 12 textes ou plus qui ne sont pas dans le lexique ont déjà été examinés et
    écartés : on ne les rajoute pas. Avec `reference` (EXP-A2-013), un mot ajouté doit
    apparaître dans au plus `max_reference` phrases de la référence d'arabe standard.
    """
    base = load_markers()
    if threshold >= LEXICON_THRESHOLD:
        return base
    added = {
        w for w, n in counts.items()
        if threshold <= n < LEXICON_THRESHOLD
        and len(w) >= 3  # les fragments de 1 ou 2 lettres sont surtout des fautes de frappe
        and w not in EXCLUDED
        and not w.startswith(NUN)
        and (reference is None or reference[w] <= max_reference)
    }
    return base | added


# ---------------------------------------------------------------------------
# Décision et métriques
# ---------------------------------------------------------------------------

def predict(text: str, markers: frozenset[str], strip: bool) -> str:
    """Même décision que normalize.detect_language, avec un lexique et une option donnés."""
    if detect_script(text) in ("arabic", "mixed"):
        folded = normalize_arabic(expand_presentation_forms(text))
        dialect = is_dialectal_arabic(folded, markers=markers, strip_affixes=strip)
        return (Lang.TN if dialect else Lang.AR).value
    return detect_language(text).value  # latin / arabizi : inchangé


def macro_f1(golds: list[str], preds: list[str]) -> float:
    """Moyenne des F1 des classes présentes dans la référence (chaque classe pèse autant)."""
    f1s = []
    for label in sorted(set(golds)):
        tp = sum(g == label and p == label for g, p in zip(golds, preds, strict=True))
        fp = sum(g != label and p == label for g, p in zip(golds, preds, strict=True))
        fn = sum(g == label and p != label for g, p in zip(golds, preds, strict=True))
        f1s.append(2 * tp / (2 * tp + fp + fn) if tp + fp + fn else 0.0)
    return sum(f1s) / len(f1s)


def tn_recall_precision(golds: list[str], preds: list[str]) -> tuple[float, float]:
    """Rappel et précision de la classe « tn »."""
    tp = sum(g == "tn" and p == "tn" for g, p in zip(golds, preds, strict=True))
    recall = tp / max(1, golds.count("tn"))
    precision = tp / max(1, preds.count("tn"))
    return recall, precision


def measure(examples: list[dict], markers: frozenset[str], strip: bool) -> dict:
    golds = [e["lang"] for e in examples]
    preds = [predict(e["text"], markers, strip) for e in examples]
    recall, precision = tn_recall_precision(golds, preds)
    return {"n": len(examples), "f1": macro_f1(golds, preds),
            "rappel_tn": recall, "precision_tn": precision}


def press_alarms(sentences: list[str], markers: frozenset[str], strip: bool) -> int:
    """Phrases de presse (arabe standard) classées tunisien : des fausses alertes."""
    return sum(predict(s, markers, strip) == "tn" for s in sentences)


# ---------------------------------------------------------------------------
# Commandes
# ---------------------------------------------------------------------------

def load_reference() -> Counter[str]:
    """Charge la référence Leipzig, affiche son empreinte (à recopier dans le journal)."""
    if not LEIPZIG.exists():
        sys.exit(f"ARRÊT : référence absente : {LEIPZIG}")
    digest = hashlib.sha256(LEIPZIG.read_bytes()).hexdigest()
    sentences = read_leipzig_sentences(LEIPZIG)
    print(f"référence Leipzig : {len(sentences)} phrases ; SHA-256 de l'archive {digest}")
    return reference_counts(sentences)


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(rows[0])
    lines = ["\t".join(keys)] + ["\t".join(str(r[k]) for k in keys) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"tableau : {path}")


def command_tune(use_leipzig: bool) -> None:
    dev = load_examples(DEV_ARABIC)
    tune = [e for e in dev if half(e["text"]) == "reglage"]
    padt_dev = load_padt("dev")
    counts = candidate_counts()
    reference = load_reference() if use_leipzig else None

    # Contrôle : la configuration actuelle sur TOUT le dev doit redonner EXP-A2-011 (0.63).
    current = measure(dev, load_markers(), strip=False)
    print(f"contrôle, configuration actuelle sur tout le dev : macro-F1 {current['f1']:.2f}"
          f" (attendu 0.63), N = {current['n']}")
    print(f"moitié « reglage » : {len(tune)} textes ; PADT dev : {len(padt_dev)} phrases\n")

    # Sans Leipzig : EXP-A2-012 à l'identique. Avec : le seuil 12 n'ajoute rien (filtre sans effet).
    limits = MAX_LEIPZIG if use_leipzig else (None,)
    rows = []
    for threshold in THRESHOLDS:
        for limit in (limits if threshold < LEXICON_THRESHOLD else (None,)):
            markers = lexicon_for(threshold, counts, reference, limit)
            for strip in (False, True):
                scores = measure(tune, markers, strip)
                alarms = press_alarms(padt_dev, markers, strip)
                rows.append({"seuil": threshold, "max_leipzig": "-" if limit is None else limit,
                             "affixes": strip, "marques": len(markers), **scores,
                             "fausses_alertes_padt_dev": alarms})

    print("seuil  max_leipzig  affixes  marques  macro-F1  rappel_tn  précision_tn  alertes")
    for r in rows:
        print(f"{r['seuil']:>5}  {r['max_leipzig']!s:>11}  {'oui' if r['affixes'] else 'non':>7}"
              f"  {r['marques']:>7}  {r['f1']:>8.2f}  {r['rappel_tn']:>9.2f}"
              f"  {r['precision_tn']:>12.2f}  {r['fausses_alertes_padt_dev']:>7}")

    # Règle de choix fixée à l'avance (voir l'en-tête du module).
    def strictness(r: dict) -> int:  # filtre le plus strict d'abord ; « - » = pas de filtre
        return -r["max_leipzig"] if isinstance(r["max_leipzig"], int) else -99

    allowed = [r for r in rows if r["fausses_alertes_padt_dev"] == 0]
    best = max(allowed, key=lambda r: (round(r["f1"], 4), r["seuil"], strictness(r),
                                       not r["affixes"]))
    flags = " --affixes" if best["affixes"] else ""
    if isinstance(best["max_leipzig"], int):
        flags += f" --max-leipzig {best['max_leipzig']}"
    print(f"\nconfiguration retenue : seuil {best['seuil']}, max_leipzig {best['max_leipzig']},"
          f" affixes {'oui' if best['affixes'] else 'non'} (macro-F1 réglage {best['f1']:.2f})")
    command = "python -X utf8 -m normalization.silver_tuning final"
    print("mesure finale, UNE seule fois :")
    print(f"  {command} --min-texts {best['seuil']}{flags}")
    write_rows(RESULTS_LEIPZIG if use_leipzig else RESULTS, rows)


def command_final(threshold: int, strip: bool, max_leipzig: int | None) -> None:
    reference = load_reference() if max_leipzig is not None else None
    markers = lexicon_for(threshold, candidate_counts(), reference, max_leipzig)
    dev = load_examples(DEV_ARABIC)
    held = [e for e in dev if half(e["text"]) == "mesure"]
    eval_30 = load_examples(DEFAULT_DATASET)

    print(f"configuration : seuil {threshold}, max_leipzig {max_leipzig},"
          f" affixes {'oui' if strip else 'non'}, {len(markers)} marques\n")
    for name, examples in (("dev, moitié mesure", held), ("eval_30 (test)", eval_30)):
        before = measure(examples, load_markers(), strip=False)
        after = measure(examples, markers, strip)
        print(f"{name} (N = {after['n']})")
        for key in ("f1", "rappel_tn", "precision_tn"):
            print(f"  {key:13} {before[key]:.2f} -> {after[key]:.2f}")
    padt_test = load_padt("test")
    print(f"PADT test : {press_alarms(padt_test, load_markers(), False)} ->"
          f" {press_alarms(padt_test, markers, strip)} fausse(s) alerte(s)"
          f" sur {len(padt_test)} phrases")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # lettres arabes lisibles sous Windows
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    tune = commands.add_parser("tune", help="configurations sur la moitié « reglage » et PADT dev")
    tune.add_argument("--leipzig", action="store_true", help="EXP-A2-013 : filtre Leipzig")
    final = commands.add_parser("final", help="mesure unique de la configuration retenue")
    final.add_argument("--min-texts", type=int, required=True, choices=THRESHOLDS)
    final.add_argument("--affixes", action="store_true")
    final.add_argument("--max-leipzig", type=int, choices=MAX_LEIPZIG)
    args = parser.parse_args()
    if args.command == "tune":
        command_tune(args.leipzig)
    else:
        command_final(args.min_texts, args.affixes, args.max_leipzig)


if __name__ == "__main__":
    main()
