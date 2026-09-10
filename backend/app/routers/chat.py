from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse, SourceCitation
from app.services.llm_service import answer
from app.services.rag_service import PROVINCE_DOMAINS, retrieve

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    jurisdiction = request.province or request.jurisdiction
    if request.domain in PROVINCE_DOMAINS and jurisdiction is None:
        raise HTTPException(status_code=422, detail="Province is required for this legal topic")
    jurisdiction = jurisdiction or "federal"
    jurisdictions = [jurisdiction]
    if request.domain in PROVINCE_DOMAINS and jurisdiction != "federal":
        jurisdictions.append("federal")
    try:
        sources = retrieve(request.message, jurisdictions, request.domain)
        response, provider = await answer(request.message, sources, request.language)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return ChatResponse(
        answer=response,
        jurisdiction=jurisdiction,
        provider=provider,
        sources=[SourceCitation(**source) for source in sources],
    )