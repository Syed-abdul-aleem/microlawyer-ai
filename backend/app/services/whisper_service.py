from __future__ import annotations

import httpx

from app.config import settings


async def transcribe(filename: str, content: bytes, content_type: str) -> str:
    if not settings.groq_api_key:
        raise RuntimeError("Groq is not configured")
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            files={"file": (filename, content, content_type)},
            data={"model": settings.groq_whisper_model, "response_format": "json"},
        )
        response.raise_for_status()
        return response.json()["text"]