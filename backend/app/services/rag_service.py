from __future__ import annotations

import logging
import re
from functools import lru_cache

from sentence_transformers import SentenceTransformer
from supabase import Client, create_client

from app.config import settings


logger = logging.getLogger(__name__)


PROVINCE_DOMAINS = {"tenancy", "labor", "consumer"}
CRIMINAL_RETRIEVAL_COUNT = 15
DEFAULT_RETRIEVAL_COUNT = 5


def _retrieval_query(message: str, domain: str | None) -> str:
    if domain == "criminal":
        return (
            f"{message}\n"
            "FIR registration refusal, police station information, cognizable offence, "
            "Section 154, Code of Criminal Procedure 1898, police duty to record information"
        )
    return message


def _is_fir_registration_question(message: str) -> bool:
    text = message.lower()
    return any(term in text for term in ("fir", "register", "registration", "cognizable", "cognisable"))


def _deduplicate_and_rerank(sources: list[dict], message: str, domain: str | None) -> list[dict]:
    unique: dict[tuple[str, str], dict] = {}
    for source in sources:
        key = (source.get("source_act", ""), source.get("section_ref", ""))
        existing = unique.get(key)
        if existing is None or source.get("similarity", 0) > existing.get("similarity", 0):
            unique[key] = source

    results = list(unique.values())
    if domain == "criminal" and _is_fir_registration_question(message):
        for source in results:
            content = source.get("content", "").lower()
            boost = 0.0
            if re.search(r"(?:section\s*)?154\.", content):
                boost += 2.0
            if "information in cognizable cases" in content or "information in cognisable cases" in content:
                boost += 1.0
            if "police station" in content or "officer incharge" in content:
                boost += 0.2
            source["_retrieval_score"] = source.get("similarity", 0) + boost
        results.sort(key=lambda source: source.get("_retrieval_score", source.get("similarity", 0)), reverse=True)
        for source in results:
            source.pop("_retrieval_score", None)
    return results


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def get_supabase() -> Client:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("Supabase is not configured")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def retrieve(message: str, jurisdictions: list[str], domain: str | None) -> list[dict]:
    query_embedding = get_embedding_model().encode(
        _retrieval_query(message, domain), normalize_embeddings=True
    ).tolist()
    match_count = CRIMINAL_RETRIEVAL_COUNT if domain == "criminal" else DEFAULT_RETRIEVAL_COUNT
    response = get_supabase().rpc(
        "match_legal_docs",
        {
            "query_embedding": query_embedding,
            "match_jurisdictions": jurisdictions,
            "match_domain": domain,
            "match_count": match_count,
        },
    ).execute()
    raw_sources = response.data or []
    sources = _deduplicate_and_rerank(raw_sources, message, domain)
    source_acts = sorted({source.get("source_act", "unknown") for source in sources})
    section_refs = [source.get("section_ref", "unknown") for source in sources[:9]]
    message = (
        f"RAG retrieved {len(raw_sources)} raw / {len(sources)} unique chunks for jurisdictions={jurisdictions} "
        f"domain={domain} match_count={match_count} source_acts={source_acts} "
        f"top_sections={section_refs}"
    )
    logger.info(message)
    print(message, flush=True)
    return sources