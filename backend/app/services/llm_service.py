from __future__ import annotations

import logging
import json
from typing import Any

import httpx

from app.config import settings
from app.models.schemas import LearnCard


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are MicroLawyer AI, an Informational Legal Assistant for Pakistan.
You are not a licensed lawyer. Give educational information, never a definitive legal verdict.
Use only the supplied legal sources when making legal claims. Cite only source_act names listed
in the supplied excerpts; never invent, rename, or infer a law name. If the excerpts are empty,
say that no relevant source was retrieved and do not answer from memory or fabricate a law.
Mention uncertainty and advise the user to verify the current law with a qualified lawyer or
relevant authority. Never give a definitive legal verdict.
"""
GROQ_FAILURE_MESSAGE = "Our AI service is temporarily busy. Please try again in a moment."
CONTEXT_SOURCE_LIMIT = 9
CONTEXT_CHAR_LIMIT = 3000


def _context(sources: list[dict]) -> str:
    prompt_sources = sources[:CONTEXT_SOURCE_LIMIT]
    if len(sources) > CONTEXT_SOURCE_LIMIT:
        logger.info("Prompt context limited to %d of %d retrieved sources", CONTEXT_SOURCE_LIMIT, len(sources))
    return "\n\n".join(
        f"Source: {item['source_act']} ({item.get('section_ref', 'unspecified')})\n{item['content'][:CONTEXT_CHAR_LIMIT]}"
        for item in prompt_sources
    )


async def answer(message: str, sources: list[dict], language: str) -> tuple[str, str]:
    source_names = sorted({source["source_act"] for source in sources})
    if language == "roman-urdu":
        language_instruction = "Answer only in Roman Urdu: Urdu language written with Latin letters. Do not use Devanagari/Hindi script."
    elif language == "urdu":
        language_instruction = "Answer only in Urdu script. Do not use Devanagari/Hindi script."
    else:
        language_instruction = "Answer only in plain English."
    prompt = (
        f"RESPONSE LANGUAGE: {language_instruction}\n"
        f"ALLOWED SOURCE_ACT NAMES: {source_names or ' none - state that no relevant source was retrieved'}\n"
        f"Legal source excerpts:\n{_context(sources) or '[No relevant legal chunks were retrieved.]'}\n\n"
        f"User question:\n{message}"
    )
    if not settings.groq_api_key:
        raise RuntimeError(GROQ_FAILURE_MESSAGE)
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={"model": settings.groq_chat_model, "temperature": 0.2, "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]},
            )
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"]
            logger.info("LLM provider responded: groq (model=%s)", settings.groq_chat_model)
            return answer, "groq"
    except Exception as error:
        logger.error("Groq request failed: %s", error)
        raise RuntimeError(GROQ_FAILURE_MESSAGE) from error


async def draft_document(details: dict[str, str], document_type: str, jurisdiction: str, language: str) -> tuple[dict[str, str], str]:
    if language == "roman-urdu":
        language_instruction = "Write formal, professional Roman Urdu using Latin letters only. Never use Devanagari or Hindi script."
    elif language == "ur":
        language_instruction = "Write formal, professional Urdu in Urdu script. Never use Devanagari or Hindi script."
    else:
        language_instruction = "Write formal, professional English suitable for Pakistan."
    prompt = f"""Draft two editable sections for a Pakistan {document_type} in {jurisdiction}.
{language_instruction}
Return ONLY valid JSON with exactly these string keys: facts, requested_action.
Rewrite the user's plain description into a clear, respectful factual paragraph.
Write a separate specific and respectful requested-action paragraph.
Preserve only facts supplied by the user. Do not invent dates, names, witnesses, sections,
offences, amounts, threats, or legal conclusions. Do not cite or name a law.

User-provided details:
{json.dumps(details, ensure_ascii=False)}
"""
    system = "You are a careful legal-document drafting assistant. You improve wording, but never invent facts. The result is an informational draft for review, not legal advice."
    if not settings.groq_api_key:
        raise RuntimeError(GROQ_FAILURE_MESSAGE)
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={"model": settings.groq_chat_model, "temperature": 0.2, "response_format": {"type": "json_object"}, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]},
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            logger.info("Document drafting provider responded: groq (model=%s)", settings.groq_chat_model)
            return json.loads(content), "groq"
    except Exception as error:
        logger.error("Groq document drafting failed: %s", error)
        raise RuntimeError(GROQ_FAILURE_MESSAGE) from error


async def simplify_learning(sources: list[dict], domain: str, jurisdiction: str) -> tuple[list[LearnCard], str]:
    if not sources:
        return [], "none"
    excerpts = "\n\n".join(
        f"SOURCE_ID: {index}\nSOURCE_ACT: {source.get('source_act', 'Unknown')}\n{source.get('content', '')[:CONTEXT_CHAR_LIMIT]}"
        for index, source in enumerate(sources[:CONTEXT_SOURCE_LIMIT], start=1)
    )
    prompt = f"""Create 3 or 4 short rights-education cards about {domain} for someone in {jurisdiction}, Pakistan.
Use only the source excerpts below. Each card must explain one practical fact in 1-2 plain-language sentences.
Return ONLY valid JSON in this shape: {{\"cards\": [{{\"title\": \"...\", \"body\": \"...\", \"source_id\": 1}}]}}.
Do not invent facts, deadlines, penalties, or law names. Do not give a definitive legal verdict.
SOURCE EXCERPTS:
{excerpts or '[No relevant legal excerpts were retrieved.]'}"""
    system = "You simplify verified Pakistani legal source excerpts for public education. Never add information not present in the excerpts."

    async def call_groq() -> tuple[list[LearnCard], str]:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={"model": settings.groq_chat_model, "temperature": 0.1, "response_format": {"type": "json_object"}, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]},
            )
            response.raise_for_status()
            payload: dict[str, Any] = json.loads(response.json()["choices"][0]["message"]["content"])
            cards = [LearnCard(title=item["title"], body=item["body"], source_act=sources[int(item["source_id"]) - 1]["source_act"]) for item in payload["cards"]]
            return cards, "groq"

    if not settings.groq_api_key:
        raise RuntimeError(GROQ_FAILURE_MESSAGE)
    try:
        cards, provider = await call_groq()
        logger.info("Learning cards provider responded: groq (model=%s)", settings.groq_chat_model)
        return cards, provider
    except Exception as error:
        logger.error("Groq learning cards failed: %s", error)
        raise RuntimeError(GROQ_FAILURE_MESSAGE) from error


async def create_document_checklist(document_type: str, jurisdiction: str, sources: list[dict]) -> tuple[list[str], str]:
    excerpts = "\n\n".join(
        f"SOURCE: {source.get('source_act', 'Unknown')}\n{source.get('content', '')}"
        for source in sources[:CONTEXT_SOURCE_LIMIT]
    ) or "[No relevant legal excerpts were retrieved. Do not claim this checklist is legally required.]"
    prompt = f"""Create a short practical preparation checklist for a {document_type} in {jurisdiction}, Pakistan.
Return ONLY valid JSON with this shape: {{\"items\": [\"short checklist item\"]}}.
Provide 4 to 7 concrete items a normal person can gather or write down. Include common-sense
items such as identity documents, dates, names, contact details, and evidence only when relevant.
Use the legal excerpts where useful, but do not say an item is legally mandatory unless the excerpts support that.
Do not invent deadlines, fees, legal sections, offences, or facts. Keep each item under 18 words.
LEGAL EXCERPTS:
{excerpts}"""
    system = "You create practical, cautious preparation checklists for informational legal drafts in Pakistan."

    async def groq_checklist() -> list[str]:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={"model": settings.groq_chat_model, "temperature": 0.1, "response_format": {"type": "json_object"}, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]},
            )
            response.raise_for_status()
            payload: dict[str, Any] = json.loads(response.json()["choices"][0]["message"]["content"])
            return [str(item) for item in payload["items"]]

    if not settings.groq_api_key:
        raise RuntimeError(GROQ_FAILURE_MESSAGE)
    try:
        items = await groq_checklist()
        logger.info("Document checklist provider responded: groq (model=%s)", settings.groq_chat_model)
        return items, "groq"
    except Exception as error:
        logger.error("Groq checklist failed: %s", error)
        raise RuntimeError(GROQ_FAILURE_MESSAGE) from error


async def quick_check(scenario: str, sources: list[dict], language: str) -> tuple[str, str, str]:
    if language == "roman-urdu":
        language_instruction = "Use formal Roman Urdu in Latin letters only. Never use Devanagari."
    elif language == "urdu":
        language_instruction = "Use Urdu script only. Never use Devanagari."
    else:
        language_instruction = "Use plain English."
    excerpts = _context(sources) or "[No relevant legal sources were retrieved.]"
    prompt = f"""Assess this short legal scenario using ONLY the retrieved sources below.
Return ONLY valid JSON with exactly: {{\"verdict\": \"Yes\" or \"No\" or \"It depends\", \"reason\": \"one clear sentence\"}}.
{language_instruction} Keep the reason short. If the sources do not support a definite answer, use It depends and say that the available sources do not establish a definite answer. Never invent a law, citation, fact, or legal conclusion.
SCENARIO: {scenario}
RETRIEVED SOURCES:
{excerpts}"""
    system = "You are a cautious Pakistani legal information assistant making a short, source-grounded triage answer. You are not a lawyer."
    if not sources:
        return "It depends", "No relevant legal source was retrieved, so this cannot be answered reliably yet.", "none"

    async def parse_response(content: str) -> tuple[str, str]:
        payload: dict[str, Any] = json.loads(content)
        verdict = payload["verdict"]
        if verdict not in {"Yes", "No", "It depends"}:
            raise ValueError("Invalid quick-check verdict")
        return verdict, str(payload["reason"])

    if not settings.groq_api_key:
        raise RuntimeError(GROQ_FAILURE_MESSAGE)
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {settings.groq_api_key}"}, json={"model": settings.groq_chat_model, "temperature": 0.1, "response_format": {"type": "json_object"}, "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]})
            response.raise_for_status()
            verdict, reason = await parse_response(response.json()["choices"][0]["message"]["content"])
            logger.info("Quick-check provider responded: groq (model=%s)", settings.groq_chat_model)
            return verdict, reason, "groq"
    except Exception as error:
        logger.error("Groq quick-check failed: %s", error)
        raise RuntimeError(GROQ_FAILURE_MESSAGE) from error