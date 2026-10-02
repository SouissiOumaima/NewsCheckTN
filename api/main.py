"""Lot E — API FastAPI exposant chaque étape du pipeline.

Lancer : uvicorn api.main:app --reload   (depuis la racine du repo)
Doc interactive : http://localhost:8000/docs
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

app = FastAPI(title="NewsCheck TN API", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


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
