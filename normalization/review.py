"""Lot A2 — Chiffres de la revue Bronze, en une commande.

Usage (depuis la racine du dépôt) :
    python -X utf8 -m normalization.review

Ce que le script produit (rien n'est réglé ici : il ne fait que mesurer) :
1. Gel des jeux : empreinte SHA-256, taille, et dernier commit pour un fichier versionné.
2. Identification de langue contre deux baselines triviales, sur chaque jeu :
   - « majorité » : toujours la classe la plus fréquente du jeu ;
   - « alphabet seul » : lettres arabes -> arabe standard, sinon -> français (ce que faisait
     le stub avant le Lot A2).
3. Résultats par langue / script (tableau 2 du guide de la revue).
4. Normaliseur : nombres conservés (règle d'or) et réduction du vocabulaire, contre la baseline
   « copie de la source ».
5. CSV des erreurs (entrée, sortie, référence, catégorie), catégories lues dans
   docs/lot-a2_analyse_erreurs.md et regroupées en 5 familles.

Statut des jeux (voir experiments.md) :
- eval_30.jsonl (Lot B, 34 phrases) : jamais utilisé pour écrire les règles du Lot A2 (EXP-A2-002)
  -> c'est le TEST du Lot A2 ;
- échantillons TSAC de référence (EXP-A2-009) : ont servi à écrire le guide et à choisir des mots
  (EXP-A2-002) -> ce sont des jeux de MISE AU POINT (dev) ; l'analyse d'erreurs s'y fait.
"""

from __future__ import annotations

import csv
import hashlib
import re
import subprocess
from collections import Counter
from pathlib import Path

from normalization.evaluate import DEFAULT_DATASET, REPO, load_examples, scores
from normalization.normalize import normalize

INTERIM = REPO / "data" / "interim" / "langid"
DATASETS = [  # (nom affiché, chemin, statut)
    ("eval_30", DEFAULT_DATASET, "test"),
    ("tsac_arabe", INTERIM / "tsac_arabic_sample_reference.tsv", "dev"),
    ("tsac_latin", INTERIM / "tsac_latin_sample_reference.tsv", "dev"),
]
ERROR_DOC = REPO / "docs" / "lot-a2_analyse_erreurs.md"
ERRORS_CSV = INTERIM / "bronze_erreurs.csv"  # non versionné : contient des textes du corpus

# Les 10 catégories d'EXP-A2-009 regroupées en 5 familles (4 à 6 demandées par la revue).
FAMILIES = {
    "A1": "lexique incomplet", "A4": "lexique incomplet",
    "A2": "morphologie dialectale", "A3": "morphologie dialectale",
    "A6": "morphologie dialectale",
    "A7": "texte trop court / sous le seuil", "L2": "texte trop court / sous le seuil",
    "A5": "effet d'une règle choisie", "L1": "effet d'une règle choisie",
    "A8": "étiquette discutable",
}
ARABIC_LETTER = re.compile(r"[ء-ي]")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")  # 20, 12.5, 1,589


# ---------------------------------------------------------------------------
# Baselines
# ---------------------------------------------------------------------------

def majority_baseline(golds: list[str]) -> list[str]:
    """Répond toujours la classe la plus fréquente (égalité : ordre alphabétique)."""
    counts = Counter(golds)
    best = max(sorted(counts), key=counts.__getitem__)
    return [best] * len(golds)


def alphabet_baseline(texts: list[str]) -> list[str]:
    """Lettres arabes majoritaires -> « ar », sinon « fr » : l'alphabet seul, sans le Lot A2."""
    predictions = []
    for text in texts:
        arabic = len(ARABIC_LETTER.findall(text))
        latin = sum(c.isalpha() for c in text) - arabic
        predictions.append("ar" if arabic > latin else "fr")
    return predictions


# ---------------------------------------------------------------------------
# Gel, normaliseur, erreurs
# ---------------------------------------------------------------------------

def freeze(path: Path) -> dict:
    """Empreinte du fichier et, s'il est versionné, son dernier commit."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    commit = subprocess.run(["git", "log", "-1", "--format=%h %cs", "--", str(path)],
                            capture_output=True, text=True, cwd=REPO, check=False).stdout.strip()
    return {"sha256": digest, "bytes": path.stat().st_size,
            "commit": commit or "non versionné"}


def numbers_kept(texts: list[str]) -> tuple[int, int]:
    """(textes dont les nombres sont identiques après normalisation, textes avec un nombre).

    Les chiffres arabes-indiens (U+0660 à U+0669) convertis en 0-9 par le normaliseur comptent comme
    conservés : la valeur ne change pas.
    """
    kept = with_number = 0
    for text in texts:
        before = NUMBER.findall(text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")))
        if not before:
            continue
        with_number += 1
        kept += before == NUMBER.findall(normalize(text).text)
    return kept, with_number


def vocabulary(texts: list[str]) -> tuple[int, int]:
    """(mots différents dans le texte brut, mots différents après normalisation)."""
    raw = {word for text in texts for word in text.split()}
    normalized = {word for text in texts for word in normalize(text).text.split()}
    return len(raw), len(normalized)


def read_categories() -> dict[tuple[str, int], str]:
    """(« arabe » | « latin », numéro de ligne) -> catégorie, depuis le tableau du document."""
    categories = {}
    row = re.compile(r"^\| (arabe|latin) \| (\d+) \| ([AL]\d) \|")
    for line in ERROR_DOC.read_text(encoding="utf-8").splitlines():
        match = row.match(line)
        if match:
            categories[(match.group(1), int(match.group(2)))] = match.group(3)
    return categories


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

def line(name: str, result: dict) -> str:
    return f"  {name:15} macro-F1 {result['macro_f1']:.2f} | exactitude {result['accuracy']:.2f}"


def main() -> None:
    errors_rows = []
    categories = read_categories()
    all_texts = []
    print("== 1. Gel des jeux ==")
    for name, path, status in DATASETS:
        info = freeze(path)
        print(f"  {name:11} ({status}) sha256 {info['sha256'][:16]}… | {info['bytes']} octets"
              f" | commit {info['commit']}")
    print()

    print("== 2. Identification de langue contre les baselines ==")
    for name, path, status in DATASETS:
        examples = load_examples(path)
        texts = [e["text"] for e in examples]
        golds = [e["lang"] for e in examples]
        all_texts += texts
        system = [normalize(t).lang.value for t in texts]
        print(f"-- {name} ({status}, {len(examples)} textes, référence : {dict(Counter(golds))})")
        print(line("système A2", scores(examples, system, "lang")))
        print(line("majorité", scores(examples, majority_baseline(golds), "lang")))
        print(line("alphabet seul", scores(examples, alphabet_baseline(texts), "lang")))
        detail = scores(examples, system, "lang")["by_class"]
        for label, c in detail.items():
            print(f"    {label}: précision {c['precision']:.2f} rappel {c['recall']:.2f}"
                  f" F1 {c['f1']:.2f} (n={c['support']})")
        if "script" in examples[0]:  # tableau 2 : par langue et par alphabet
            groups = Counter((e["lang"], e["script"]) for e in examples)
            good = Counter((e["lang"], e["script"]) for e, p in zip(examples, system, strict=True)
                           if p == e["lang"])
            print("    par langue / alphabet : " + " ; ".join(
                f"{lang}/{script} {good[(lang, script)]}/{n}"
                for (lang, script), n in sorted(groups.items())))
        if name.startswith("tsac"):  # erreurs de la mise au point -> CSV
            sample = "arabe" if name == "tsac_arabe" else "latin"
            for example, predicted in zip(examples, system, strict=True):
                if predicted != example["lang"]:
                    number = int(example["id"][1:])
                    code = categories.get((sample, number), "?")
                    errors_rows.append({
                        "echantillon": sample, "ligne": number, "entree": example["text"],
                        "sortie": predicted, "reference": example["lang"],
                        "categorie": code, "famille": FAMILIES.get(code, "?")})
        print()

    print("== 3. Normaliseur (tous les textes ci-dessus) ==")
    kept, with_number = numbers_kept(all_texts)
    raw, normalized = vocabulary(all_texts)
    print(f"  nombres conservés : {kept}/{with_number} textes (baseline copie : {with_number}/"
          f"{with_number})")
    print(f"  mots différents : {raw} -> {normalized} ({1 - normalized / raw:.1%} de moins ;"
          f" baseline copie : 0 %)")
    print()

    print("== 4. Erreurs (jeux de mise au point) ==")
    ERRORS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with ERRORS_CSV.open("w", encoding="utf-8-sig", newline="") as handle:  # BOM : ouverture Excel
        writer = csv.DictWriter(handle, fieldnames=list(errors_rows[0]) if errors_rows else ["-"])
        writer.writeheader()
        writer.writerows(errors_rows)
    unknown = [(r["echantillon"], r["ligne"]) for r in errors_rows if r["categorie"] == "?"]
    missing = sorted(set(categories) - {(r["echantillon"], r["ligne"]) for r in errors_rows})
    for family, count in Counter(r["famille"] for r in errors_rows).most_common():
        print(f"  {family:35} {count}")
    print(f"  total : {len(errors_rows)} | sans catégorie : {unknown}"
          f" | catégorisées mais plus en erreur : {missing}")
    print(f"  CSV écrit : {ERRORS_CSV}")


if __name__ == "__main__":
    main()
