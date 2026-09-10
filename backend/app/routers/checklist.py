from fastapi import APIRouter, HTTPException

from app.models.schemas import ChecklistRequest, ChecklistResponse
from app.services.checklist_service import build_checklist

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/checklist", response_model=ChecklistResponse)
async def document_checklist(request: ChecklistRequest) -> ChecklistResponse:
    try:
        return await build_checklist(request.document_type, request.jurisdiction)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error