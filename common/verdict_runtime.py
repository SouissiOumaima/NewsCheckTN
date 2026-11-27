"""Lot E — Sélection du verdict et traçabilité des replis, sans changer Verdict."""

from __future__ import annotations

import os
from functools import lru_cache
from urllib.parse import urlparse

from common.schemas import Claim, Evidence, StanceResult, Verdict
from rag_llm.verdict import generate_verdict


def verdict_backend() -> str:
    backend = os.getenv("VERDICT_BACKEND", "gabarit").strip().lower()
    if backend not in {"gabarit", "llm"}:
        raise ValueError("VERDICT_BACKEND attendu : gabarit | llm")
    return backend


@lru_cache(maxsize=4)
def _generator(provider: str, model: str, base_url: str):
    """Réutilise notamment le modèle local entre deux requêtes."""
    from rag_llm.llm_verdict import get_generator

    return get_generator()


def resolve_verdict(
    claim: Claim, evidences: list[Evidence], stances: list[StanceResult]
) -> tuple[Verdict, dict]:
    """Renvoie le contrat existant et des métadonnées sans prompt ni réponse brute."""
    requested = verdict_backend()
    info = {"requested": requested, "used": "gabarit", "fallback_reason": None}
    if requested == "gabarit":
        return generate_verdict(claim, stances), info
    if not evidences:
        info["fallback_reason"] = "no_evidence"
        return generate_verdict(claim, []), info

    provider = os.getenv("LLM_PROVIDER", "hf").strip().lower()
    model = os.getenv("LLM_MODEL", "")
    base_url = os.getenv("LLM_BASE_URL", "").strip()
    if provider in {"openai", "ollama"}:
        host = urlparse(base_url or "https://api.openai.com/v1").hostname
        local = host in {"localhost", "127.0.0.1", "::1"}
        if not local and os.getenv("LLM_ALLOW_EXTERNAL", "0") != "1":
            info["fallback_reason"] = "external_provider_not_authorized"
            return generate_verdict(claim, stances), info
    try:
        from rag_llm.llm_verdict import llm_verdict

        generator = _generator(provider, model, base_url)
        result = llm_verdict(claim, evidences, generator, stances=stances)
        allowed = {item.doc_id for item in evidences}
        if not set(result.verdict.citations) <= allowed:
            info.update(
                fallback_reason="citation_hors_liste",
                model=generator.name,
                provider=provider,
            )
            return generate_verdict(claim, stances), info
        info.update(
            used="llm" if result.valid else (result.fallback or "gabarit"),
            fallback_reason=result.error,
            model=generator.name,
            provider=provider,
        )
        source = result.info.get("uncertainty_source")
        if result.valid and source in {"nli", "fixe"}:
            info["uncertainty_source"] = source
        return result.verdict, info
    except Exception:
        # Ne pas exposer une clé, un prompt ou un extrait dans une erreur API.
        info["fallback_reason"] = "llm_unavailable"
        return generate_verdict(claim, stances), info
