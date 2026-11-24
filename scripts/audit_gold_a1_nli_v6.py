"""Audit reproductible du corpus Gold A1 NLI V6.

Le script ne modifie aucune donnee et n'affiche aucun texte prive.
La normalisation et la reconstruction des articles viennent du Lot C.
"""

import argparse
import hashlib
import importlib.util
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

# Empreintes des copies effectivement controlees.
SHA_V6 = "FBB13F118F4A2F3B604C86BA1729295BED5A6BEA4A7EDBF80262CF15835B7B29"
SHA_V3 = "5FA857BE810D568E6266641EADE1C0FFFE805E804D6E4A989BA0CA5B5CFC1099"
SHA_SPLIT = "59582EB759DF4CD9E15F7A17D1DF7E85DFAE411717A111D52D536FC1C6C3552C"

PARTITIONS = ("train", "val", "test")


def sha256(path):
    # Calculer l'empreinte sans charger le fichier entier.
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def load_pairs(path):
    # Charger le JSONL et refuser les IDs dupliques.
    with path.open(encoding="utf-8-sig") as stream:
        pairs = [json.loads(line) for line in stream if line.strip()]

    index = {p["pair_id"]: p for p in pairs}
    if len(index) != len(pairs):
        raise ValueError("pair_id dupliques")
    return index


def check(condition, message):
    # Arreter l'audit si une hypothese est invalide.
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--v6", type=Path, required=True)
    parser.add_argument("--v3", type=Path, required=True)
    parser.add_argument("--split", type=Path, required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    source = root / "models/nli/data.py"

    # Proteger les versions exactes des trois fichiers.
    check(sha256(args.v6) == SHA_V6, "SHA V6 incorrect")
    check(sha256(args.v3) == SHA_V3, "SHA V3 incorrect")
    check(sha256(args.split) == SHA_SPLIT, "SHA split incorrect")

    # Reutiliser exactement les methodes du Lot C.
    spec = importlib.util.spec_from_file_location(
        "gold_a1_nli_data", source
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    v6 = load_pairs(args.v6)
    v3 = load_pairs(args.v3)

    split = json.loads(
        args.split.read_text(encoding="utf-8-sig")
    )

    # Verifier l'identite des paires et des partitions.
    check(len(v6) == 300, "Effectif V6 inattendu")
    check(set(v6) == set(v3), "IDs V3/V6 differents")

    all_ids = [
        pid
        for name in PARTITIONS + ("excluded_drafts",)
        for pid in split[name]
    ]

    check(len(all_ids) == len(set(all_ids)), "IDs dupliques dans le split")
    check(set(all_ids) == set(v6), "Split incompatible avec V6")

    rows = {
        name: [v6[pid] for pid in split[name]]
        for name in PARTITIONS
    }

    counts = {
        name: len(split[name])
        for name in PARTITIONS + ("excluded_drafts",)
    }
    check(
        counts == {
            "train": 174,
            "val": 33,
            "test": 56,
            "excluded_drafts": 37,
        },
        "Effectifs du split inattendus"
    )

    # Calculer les recouvrements et repetitions par variable.
    extractors = {
        "claim_id": lambda p: p["claim_id"],
        "evidence_id": lambda p: p["evidence_id"],
        "claim_norm": lambda p: module._norm(p["claim"]),
        "evidence_norm": lambda p: module._norm(p["evidence"]),
        "article_id": lambda p: module.article_id(p),
    }

    audits = {}

    for field, extract in extractors.items():
        values = {
            name: [extract(p) for p in rows[name]]
            for name in PARTITIONS
        }

        distinct = {
            name: set(values[name])
            for name in PARTITIONS
        }

        overlap = {
            f"{left}_{right}": len(distinct[left] & distinct[right])
            for left, right in itertools.combinations(PARTITIONS, 2)
        }

        audits[field] = {
            "unique": {
                name: len(distinct[name])
                for name in PARTITIONS
            },
            "duplicates_internal": {
                name: len(values[name]) - len(distinct[name])
                for name in PARTITIONS
            },
            "overlap": overlap,
        }

        check(
            all(n == 0 for n in overlap.values()),
            "Chevauchement detecte : " + field
        )

    # Controler la separation des articles du test Lot D.
    protected = {str(x).lower() for x in split["lot_d_test_articles"]}
    test_articles = {
        module.article_id(p) for p in rows["test"]
    }
    other_articles = {
        module.article_id(p)
        for name in ("train", "val")
        for p in rows[name]
    }

    check(
        protected <= test_articles,
        "Articles Lot D manquants dans test"
    )
    check(
        not protected & other_articles,
        "Fuite des articles Lot D"
    )

    # Reproduire les categories de reconstruction des articles.
    provenance = Counter()
    urls = set()
    domains = set()
    empty_paths = 0
    short_paths = 0

    for p in v6.values():
        evidence_id = str(p.get("evidence_id") or "")
        remarque = str(p.get("remarque") or "")

        if p.get("article_id"):
            category = "explicit"
        elif module._TUNIFACT_ID.search(evidence_id):
            category = "tunifact_evidence_id"
        elif module._TUNIFACT_URL.search(remarque):
            category = "tunifact_remarque"
        elif match := module._URL.search(remarque):
            category = "url_remarque"
            url = match.group(0).rstrip("/").lower()
            parsed = urlsplit(url)
            segments = [s for s in parsed.path.split("/") if s]
            urls.add(url)
            domains.add(parsed.netloc)
            empty_paths += int(not segments)
            short_paths += int(len(segments) < 2)
        else:
            category = "unknown"

        provenance[category] += 1

    check(
        dict(provenance) == {
            "tunifact_evidence_id": 259,
            "tunifact_remarque": 3,
            "url_remarque": 38,
        },
        "Provenance differente du rapport"
    )

    # Comparer les labels V3/V6 sans afficher les pair_id.
    label_changes = Counter()

    for name in PARTITIONS + ("excluded_drafts",):
        for pid in split[name]:
            before = v3[pid]["label"]
            after = v6[pid]["label"]

            if before != after:
                label_changes[(name, before, after)] += 1

    check(
        dict(label_changes) == {("val", "neutral", "refutes"): 1},
        "Evolution de labels inattendue"
    )

    test_labels_v3 = Counter(v3[p]["label"] for p in split["test"])
    test_labels_v6 = Counter(v6[p]["label"] for p in split["test"])

    check(
        test_labels_v3 == test_labels_v6,
        "Labels de test differents"
    )

    # Identifier le commit source des fonctions Lot C.
    commit = subprocess.check_output(
        ["git", "-C", str(root), "log", "-1",
         "--format=%H", "--", "models/nli/data.py"],
        text=True
    ).strip()

    # Generer un rapport JSON sans donnees privees.
    result = {
        "status": "PASS",
        "corpus_v6_sha256": SHA_V6,
        "corpus_v3_sha256": SHA_V3,
        "split_v3_sha256": SHA_SPLIT,
        "split_seed": split["seed"],
        "counts": counts,
        "normalization": "re.sub(whitespace, single_space).strip().lower()",
        "unicode_nfkc": False,
        "audit": audits,
        "protected_articles": {
            "total": len(protected),
            "in_test": len(protected & test_articles),
            "outside_test": len(protected & other_articles),
        },
        "provenance": dict(provenance),
        "distinct_articles_v6": len({
            module.article_id(p) for p in v6.values()
        }),
        "urls": {
            "unique": len(urls),
            "domains": len(domains),
            "empty_paths": empty_paths,
            "short_paths": short_paths,
        },
        "v3_to_v6_label_changes": [
            {
                "partition": partition,
                "from": before,
                "to": after,
                "count": count,
            }
            for (partition, before, after), count
            in sorted(label_changes.items())
        ],
        "test_labels_v6": dict(test_labels_v6),
        "lot_c_source_commit": commit,
        "experiment_note": "EXP-C-011 is V3; no V6 model evaluation claimed",
    }

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
