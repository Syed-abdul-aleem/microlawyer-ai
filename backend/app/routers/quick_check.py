from fastapi import APIRouter, HTTPException

from app.models.schemas import QuickCheckRequest, QuickCheckResponse, SourceCitation
from app.services.llm_service import quick_check
from app.services.rag_service import PROVINCE_DOMAINS, retrieve

router = APIRouter(prefix="/quick-check", tags=["quick-check"])


@router.post("", response_model=QuickCheckResponse)
async def quick_check_route(request: QuickCheckRequest) -> QuickCheckResponse:
    jurisdiction = "federal" if request.domain == "criminal" else (request.province or request.jurisdiction)
    if request.domain in PROVINCE_DOMAINS and jurisdiction is None:
        raise HTTPException(status_code=422, detail="Province is required for this legal topic")
    jurisdiction = jurisdiction or "federal"
    jurisdictions = [jurisdiction]
    if request.domain in PROVINCE_DOMAINS and jurisdiction != "federal":
        jurisdictions.append("federal")
    try:
        sources = retrieve(request.scenario, jurisdictions, request.domain)
        verdict, reason, provider = await quick_check(request.scenario, sources, request.language)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return QuickCheckResponse(
        verdict=verdict,
        reason=reason,
        jurisdiction=jurisdiction,
        provider=provider,
        sources=[SourceCitation(**source) for source in sources],
    )