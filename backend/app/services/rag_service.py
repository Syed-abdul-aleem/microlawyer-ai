from __future__ import annotations

import logging
import re

import httpx
from supabase import Client, create_client

from app.config import settings


logger = logging.getLogger(__name__)
EMBEDDING_FAILURE_MESSAGE = "Our AI service is temporarily busy. Please try again in a moment."
HF_INFERENCE_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/{model}"


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


def get_query_embedding(text: str) -> list[float]:
    if not settings.huggingface_api_key:
        raise RuntimeError(EMBEDDING_FAILURE_MESSAGE)

    url = HF_INFERENCE_URL.format(model=settings.embedding_model)
    request_payload = {
        "inputs": text,
        "options": {"wait_for_model": True},
    }
    logger.info(
        "Hugging Face embedding request: url=%s payload_keys=%s input_chars=%d authorization=Bearer <redacted>",
        url,
        sorted(request_payload),
        len(text),
    )
    try:
        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.huggingface_api_key}",
                "Content-Type": "application/json",
            },
            json=request_payload,
            timeout=httpx.Timeout(30.0, connect=10.0),
        )
        if response.is_error:
            logger.error(
                "Hugging Face embedding failed: status=%d response_body=%s",
                response.status_code,
                response.text[:4000],
            )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as error:
        logger.error("Hugging Face embedding request failed: %s", error)
        raise RuntimeError(EMBEDDING_FAILURE_MESSAGE) from error

    if isinstance(payload, list) and len(payload) == 1 and isinstance(payload[0], list):
        payload = payload[0]
    if isinstance(payload, list) and payload and isinstance(payload[0], list):
        if not all(isinstance(row, list) and len(row) == 384 for row in payload):
            logger.error("Hugging Face returned an incompatible embedding response")
            raise RuntimeError(EMBEDDING_FAILURE_MESSAGE)
        payload = [sum(row[index] for row in payload) / len(payload) for index in range(384)]
    if not isinstance(payload, list) or len(payload) != 384 or not all(
        isinstance(value, (int, float)) for value in payload
    ):
        logger.error("Hugging Face returned an incompatible embedding response")
        raise RuntimeError(EMBEDDING_FAILURE_MESSAGE)

    magnitude = sum(value * value for value in payload) ** 0.5
    if magnitude == 0:
        raise RuntimeError(EMBEDDING_FAILURE_MESSAGE)
    return [value / magnitude for value in payload]


def get_supabase() -> Client:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("Supabase is not configured")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def retrieve(message: str, jurisdictions: list[str], domain: str | None) -> list[dict]:
    query_embedding = get_query_embedding(_retrieval_query(message, domain))
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