"""Lot D — Preuve du gel du jeu de test réel Tunifact v1 (hash SHA-256 et date).

Le jeu de test du Lot D est figé depuis EXP-D-006 (23/10/2026) : 21 affirmations
(`tests/fixtures/rag_llm/claims_tunifact_v1.jsonl`) et un corpus de 84 passages reconstruit
depuis la branche du Lot A1 (`lot-a1-data`, commit 77a00b9) par `rag_llm.build_tunifact_eval`.
Ce jeu ne sert jamais à régler une règle, un seuil ou un paramètre.

Les empreintes sont calculées sur les octets du fichier, fins de ligne ramenées à « \\n »
(le dépôt impose `eol=lf`, ce qui donne la même empreinte sous Windows et sous Linux).

Usage (depuis la racine du dépôt) :
    python -m rag_llm.freeze_test --check     # vérifie que le test n'a pas changé
    python -m rag_llm.freeze_test --write     # (re)écrit data/splits/lot_d_tunifact_v1.json
Le corpus n'est pas versionné (droits Tunifact non confirmés) : s'il est absent, seul le fichier
des affirmations est vérifié (`python -m rag_llm.build_tunifact_eval` pour le reconstruire).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "tests" / "fixtures" / "rag_llm" / "claims_tunifact_v1.jsonl"
CORPUS = ROOT / "data" / "interim" / "lot_d" / "evidence_tunifact_v1.jsonl"
SPLIT = ROOT / "data" / "splits" / "lot_d_tunifact_v1.json"

FROZEN_ON = "2026-10-23"
FROZEN_IN = "EXP-D-006 (commit ff08633 : ajout de claims_tunifact_v1.jsonl)"
CORPUS_SOURCE = "branche lot-a1-data, commit 77a00b9 (export tunifact_sentences_46.jsonl)"


def sha256(path: Path) -> str:
    """Empreinte du fichier, fins de ligne normalisées en « \\n »."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def describe() -> dict:
    claims = _jsonl(CLAIMS)
    record = {
        "name": "Lot D — jeu de test réel Tunifact v1",
        "frozen_on": FROZEN_ON,
        "frozen_in": FROZEN_IN,
        "hash_recorded_on": date.today().isoformat(),
        "rule": "jamais utilisé pour régler une règle, un seuil ou un paramètre",
        "claims": {
            "path": CLAIMS.relative_to(ROOT).as_posix(),
            "sha256": sha256(CLAIMS),
            "n": len(claims),
            "ids": [c["claim_id"] for c in claims],
        },
        "corpus": {
            "path": CORPUS.relative_to(ROOT).as_posix(),
            "built_by": "python -m rag_llm.build_tunifact_eval  (version v1)",
            "source": CORPUS_SOURCE,
            "versioned": False,
        },
    }
    if CORPUS.exists():
        record["corpus"]["sha256"] = sha256(CORPUS)
        record["corpus"]["n"] = len(_jsonl(CORPUS))
    return record


def check(split: Path = SPLIT) -> list[str]:
    """Liste des écarts entre les fichiers actuels et l'empreinte enregistrée (vide = intact)."""
    saved = json.loads(split.read_text(encoding="utf-8"))
    problems = []
    if sha256(CLAIMS) != saved["claims"]["sha256"]:
        problems.append(f"affirmations modifiées : {CLAIMS.name}")
    expected = saved["corpus"].get("sha256")
    if CORPUS.exists() and expected and sha256(CORPUS) != expected:
        problems.append(f"corpus différent : {CORPUS.name} (à reconstruire depuis {CORPUS_SOURCE})")
    return problems


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--write", action="store_true", help="écrire data/splits/lot_d_tunifact_v1.json")
    p.add_argument("--check", action="store_true", help="vérifier les empreintes enregistrées")
    args = p.parse_args()
    if args.write:
        SPLIT.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(describe(), ensure_ascii=False, indent=2) + "\n"
        SPLIT.write_text(text, encoding="utf-8")
        print(f"empreintes écrites dans {SPLIT.relative_to(ROOT)}")
    if args.check or not args.write:
        problems = check()
        saved = json.loads(SPLIT.read_text(encoding="utf-8"))
        print(f"test gelé le {saved['frozen_on']} — affirmations {saved['claims']['sha256'][:16]}…")
        if not CORPUS.exists():
            print("corpus absent : seul le fichier des affirmations est vérifié")
        if problems:
            print("ÉCHEC :", "; ".join(problems))
            sys.exit(1)
        print("OK : le jeu de test est identique à celui qui a été gelé")


if __name__ == "__main__":
    main()
