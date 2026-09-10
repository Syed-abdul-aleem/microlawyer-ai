from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import Domain, Jurisdiction, LearnResponse
from app.services.learn_service import get_learning_cards

router = APIRouter(prefix="/learn", tags=["learn"])


@router.get("/{domain}", response_model=LearnResponse)
async def learn(
    domain: Domain,
    jurisdiction: Jurisdiction = Query("federal"),
) -> LearnResponse:
    selected_jurisdiction = "federal" if domain == "criminal" else jurisdiction
    try:
        cards, provider = await get_learning_cards(domain, selected_jurisdiction)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return LearnResponse(domain=domain, jurisdiction=selected_jurisdiction, cards=cards, provider=provider)