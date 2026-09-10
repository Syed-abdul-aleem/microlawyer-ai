from __future__ import annotations

from app.models.schemas import ChecklistResponse
from app.services.llm_service import create_document_checklist
from app.services.rag_service import retrieve


DOCUMENT_DOMAINS = {
    "legal_notice": "tenancy",
    "fir_draft": "criminal",
    "rental_dispute_letter": "tenancy",
}


async def build_checklist(document_type: str, jurisdiction: str) -> ChecklistResponse:
    domain = DOCUMENT_DOMAINS[document_type]
    jurisdictions = ["federal"] if domain == "criminal" else [jurisdiction, "federal"]
    sources = retrieve(
        f"practical documents and information needed to prepare a {document_type}",
        jurisdictions,
        domain,
    )
    items, provider = await create_document_checklist(document_type, jurisdiction, sources)
    return ChecklistResponse(
        items=items,
        provider=provider,
        sources=sorted({source["source_act"] for source in sources}),
    )