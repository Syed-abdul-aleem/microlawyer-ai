from __future__ import annotations

import asyncio
import json
import time

from app.models.schemas import LearnCard
from app.services.llm_service import simplify_learning
from app.services.rag_service import retrieve


CACHE_TTL_SECONDS = 60 * 30
_cache: dict[tuple[str, str], tuple[float, list[LearnCard], str]] = {}
_locks: dict[tuple[str, str], asyncio.Lock] = {}


def _jurisdictions(domain: str, jurisdiction: str) -> list[str]:
    if jurisdiction == "federal" or domain == "criminal":
        return ["federal"]
    return [jurisdiction, "federal"]


async def get_learning_cards(domain: str, jurisdiction: str) -> tuple[list[LearnCard], str]:
    key = (domain, jurisdiction)
    cached = _cache.get(key)
    if cached and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
        return cached[1], cached[2]

    lock = _locks.setdefault(key, asyncio.Lock())
    async with lock:
        cached = _cache.get(key)
        if cached and time.monotonic() - cached[0] < CACHE_TTL_SECONDS:
            return cached[1], cached[2]
        sources = retrieve(
            f"basic rights and important rules about {domain} in Pakistan",
            _jurisdictions(domain, jurisdiction),
            domain,
        )
        cards, provider = await simplify_learning(sources, domain, jurisdiction)
        _cache[key] = (time.monotonic(), cards, provider)
        return cards, provider