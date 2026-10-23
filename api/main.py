"""Lot E — API FastAPI exposant chaque étape du pipeline.

Lancer : uvicorn api.main:app --reload   (depuis la racine du repo)
Doc interactive : http://localhost:8000/docs
Plateforme web  : http://localhost:8000/app/   (pages de frontend/, servies par l'API)
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import pipeline
from common.schemas import Claim, Evidence, Lang
from data.loaders import load_evidence_corpus
from linguistic_analysis.claim_extraction import extract_claims
from models.claim_detector import filter_checkworthy
from models.nli.stance import predict_stance, predict_stances
from normalization.normalize import normalize
from rag_llm.retrieval.hybrid import retrieve
from rag_llm.verdict import generate_verdict

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "evaluation" / "results"
# Champs volumineux des fichiers de résultats, inutiles au tableau de bord.
HEAVY_RESULT_KEYS = {"items", "per_claim", "bootstrap", "errors"}

app = FastAPI(title="NewsCheck TN API", version="0.2.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class TextIn(BaseModel):
    text: str = Field(..., min_length=1, examples=["Le chômage en Tunisie est de 16,4 % en 2023."])


class ClaimIn(BaseModel):
    claim: str = Field(..., min_length=1)
    lang: Lang = Lang.FR
    k: int = Field(5, ge=1, le=50)


class VerdictDetailIn(ClaimIn):
    # "lot-c" : NLI du Lot C (models.nli.stance) ; "regles" : NLI provisoire du Lot D, pour
    # les démonstrations tant que le modèle du Lot C n'est pas branché.
    nli: Literal["lot-c", "regles"] = "lot-c"


class NLIIn(BaseModel):
    claim: str
    evidence: str
    lang: Lang = Lang.FR


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": app.version}


@app.post("/normalize")  # Lot A2
def normalize_route(body: TextIn) -> dict:
    return asdict(normalize(body.text))


@app.post("/extract")  # Lots B + C
def extract_route(body: TextIn) -> dict:
    claims = filter_checkworthy(extract_claims(normalize(body.text)))
    return {"claims": [asdict(c) for c in claims]}


@app.post("/retrieve")  # Lot D
def retrieve_route(body: ClaimIn) -> dict:
    claim = Claim(text=body.claim, lang=body.lang)
    return {"evidence": [asdict(e) for e in retrieve(claim, load_evidence_corpus(), k=body.k)]}


@app.post("/nli")  # Lot C
def nli_route(body: NLIIn) -> dict:
    claim = Claim(text=body.claim, lang=body.lang)
    ev = Evidence(doc_id="user-input", text=body.evidence, source="user")
    return asdict(predict_stance(claim, ev))


@app.post("/verdict")  # Lot D
def verdict_route(body: ClaimIn) -> dict:
    claim = Claim(text=body.claim, lang=body.lang)
    evidences = retrieve(claim, load_evidence_corpus(), k=body.k)
    return asdict(generate_verdict(claim, predict_stances(claim, evidences)))


@app.post("/check")  # pipeline complet
def check_route(body: TextIn) -> dict:
    return {"verdicts": [asdict(v) for v in pipeline.check_text(body.text)]}


# ---------------------------------------------------------------------------
# Routes de la plateforme web (Lot E partagé)
# ---------------------------------------------------------------------------


def _stance_function(nli: str):
    if nli == "lot-c":
        return predict_stances
    try:
        from rag_llm.baseline_stance import predict_stances as rules  # Lot D (PR #4)
    except ImportError:
        raise HTTPException(501, "Le NLI par règles du Lot D n'est pas encore dans main.") from None
    return rules


@app.post("/verdict/detail")  # Lot D — détail pour la page « Preuves et verdict »
def verdict_detail_route(body: VerdictDetailIn) -> dict:
    claim = Claim(text=body.claim, lang=body.lang)
    corpus = load_evidence_corpus()
    evidences = retrieve(claim, corpus, k=body.k)
    stances = _stance_function(body.nli)(claim, evidences)
    verdict = generate_verdict(claim, stances)
    return {
        "corpus_size": len(corpus),
        "nli": body.nli,
        "evidences": [
            {**asdict(s.evidence), "rank": i, "stance": s.stance.value, "confidence": s.confidence}
            for i, s in enumerate(stances, start=1)
        ],
        "verdict": asdict(verdict),
    }


@app.get("/corpus/stats")  # Lot A1 — état du corpus de preuves chargé par l'API
def corpus_stats_route() -> dict:
    corpus = load_evidence_corpus()
    return {
        "size": len(corpus),
        "by_source": dict(Counter(e.source for e in corpus).most_common()),
        "sample": [asdict(e) for e in corpus[:5]],
    }


@app.get("/results")  # tous les lots — fichiers de evaluation/results/ pour le tableau de bord
def results_route() -> dict:
    results = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            results.append({"file": path.name, "error": "fichier JSON illisible"})
            continue
        if isinstance(data, dict):
            light = {k: v for k, v in data.items() if k not in HEAVY_RESULT_KEYS}
            results.append({"file": path.name, **light})
    return {"results": results}


# Pages web (frontend/), montées en dernier pour ne masquer aucune route.
FRONTEND_DIR = ROOT / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="app")
