"""Lot E — API FastAPI exposant chaque étape du pipeline.

Lancer : uvicorn api.main:app --reload   (depuis la racine du repo)
Doc interactive : http://localhost:8000/docs
Plateforme web  : http://localhost:8000/app/
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import pipeline
from common.schemas import Claim, Evidence, Lang
from data.loaders import CorpusError, corpus_origin, load_evidence_corpus
from models.claim_detector import filter_checkworthy, model_status
from models.nli.stance import predict_stance, predict_stances
from normalization.normalize import normalize
from rag_llm.retrieval.hybrid import retrieve
from rag_llm.verdict import generate_verdict

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "evaluation" / "results"
HEAVY_RESULT_KEYS = {"items", "per_claim", "bootstrap", "errors"}

app = FastAPI(title="NewsCheck TN API", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(CorpusError)
def corpus_error_handler(_: Request, exc: CorpusError) -> JSONResponse:
    """Corpus de preuves demandé mais introuvable ou invalide : message clair, pas d'erreur 500."""
    return JSONResponse(status_code=503, content={"detail": f"Corpus de preuves : {exc}"})


class TextIn(BaseModel):
    text: str = Field(..., min_length=1, examples=["Le chômage en Tunisie est de 16,4 % en 2023."])


class ClaimIn(BaseModel):
    claim: str = Field(..., min_length=1)
    lang: Lang = Lang.FR
    k: int = Field(5, ge=1, le=50)


class NLIIn(BaseModel):
    claim: str
    evidence: str
    lang: Lang = Lang.FR


class VerdictDetailIn(ClaimIn):
    """Option NLI affichée par la page Lot D de la plateforme."""

    nli: Literal["lot-c", "regles"] = "lot-c"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": app.version, "claim_detector": model_status()}


@app.post("/normalize")  # Lot A2
def normalize_route(body: TextIn) -> dict:
    return asdict(normalize(body.text))


@app.post("/extract")  # Lots B + C
def extract_route(body: TextIn) -> dict:
    claims, raw_texts = pipeline._claims_for_model1(body.text)
    claims = filter_checkworthy(claims, classification_texts=raw_texts)
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


@app.post("/check/detail")  # pipeline complet, chaque étape visible (mode détail, démo)
def check_detail_route(body: TextIn) -> dict:
    return pipeline.check_text_detail(body.text)


# ---------------------------------------------------------------------------
# Plateforme web partagée (Lot E) et informations Lot C.
# ---------------------------------------------------------------------------


@app.get("/model-c/model1")
def model1_route() -> dict:
    """Résumé public du Model 1, utilisé par la page Lot C."""
    return {
        "task": "Détection d'affirmations vérifiables",
        "classes": ["AFFIRMATION", "OPINION", "AUTRE"],
        "threshold": 0.5,
        "model": model_status(),
        "evaluation": {
            "exp_id": "EXP-C-003",
            "split": "test gelé (n=120)",
            "accuracy": 0.7916666666666666,
            "macro_f1": 0.7107843137254902,
            "by_lang": {
                "fr": {"n": 26, "macro_f1": 0.9148148148148149},
                "ar": {"n": 30, "macro_f1": 0.698898898898899},
                "tn": {"n": 64, "macro_f1": 0.6445406445406445},
            },
        },
        "nli": {
            "status": "baseline",
            "message": "Le fine-tuning NLI attend les paires claim–evidence annotées par Lot A1.",
        },
    }


def _stance_function(nli: str):
    if nli == "lot-c":
        return predict_stances
    try:
        from rag_llm.baseline_stance import predict_stances as rules
    except ImportError:
        raise HTTPException(
            501, "Le NLI par règles du Lot D n'est pas encore disponible."
        ) from None
    return rules


@app.post("/verdict/detail")
def verdict_detail_route(body: VerdictDetailIn) -> dict:
    """Détail retrieval/NLI/verdict pour la page Lot D."""
    claim = Claim(text=body.claim, lang=body.lang)
    corpus = load_evidence_corpus()
    evidences = retrieve(claim, corpus, k=body.k)
    stances = _stance_function(body.nli)(claim, evidences)
    verdict = generate_verdict(claim, stances)
    return {
        "corpus_size": len(corpus),
        "corpus": corpus_origin(),
        "nli": body.nli,
        "evidences": [
            {
                **asdict(item.evidence),
                "rank": rank,
                "stance": item.stance.value,
                "confidence": item.confidence,
            }
            for rank, item in enumerate(stances, start=1)
        ],
        "verdict": asdict(verdict),
    }


@app.get("/corpus/stats")
def corpus_stats_route() -> dict:
    """Résumé du corpus chargé, pour la page Lot A1."""
    corpus = load_evidence_corpus()
    return {
        "size": len(corpus),
        **corpus_origin(),
        "by_source": dict(Counter(item.source for item in corpus).most_common()),
        "sample": [asdict(item) for item in corpus[:5]],
    }


@app.get("/results")
def results_route() -> dict:
    """Expose les fichiers JSON légers de ``evaluation/results`` au dashboard."""
    results = []
    for path in sorted(RESULTS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            results.append({"file": path.name, "error": "fichier JSON illisible"})
            continue
        if isinstance(data, dict):
            results.append(
                {
                    "file": path.name,
                    **{key: value for key, value in data.items() if key not in HEAVY_RESULT_KEYS},
                }
            )
    return {"results": results}


# Les assets statiques sont montés en dernier : ils ne masquent aucune route API.
FRONTEND_DIR = ROOT / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="app")
