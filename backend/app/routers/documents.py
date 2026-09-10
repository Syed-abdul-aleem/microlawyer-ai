from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.models.schemas import DocumentDraftRequest, DocumentDraftResponse, DocumentRequest
from app.services.pdf_service import create_pdf
from app.services.llm_service import draft_document as draft_with_ai

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/draft", response_model=DocumentDraftResponse)
async def draft_document(request: DocumentDraftRequest) -> DocumentDraftResponse:
    try:
        draft, provider = await draft_with_ai(
            request.details, request.document_type, request.jurisdiction, request.language
        )
        return DocumentDraftResponse(
            facts=draft["facts"], requested_action=draft["requested_action"], provider=provider
        )
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=502, detail="The AI returned an invalid document draft") from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/generate", response_class=Response)
def generate_document(request: DocumentRequest) -> Response:
    pdf = create_pdf(request.document_type, request.language, request.jurisdiction, request.facts)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{request.document_type}-draft.pdf"'},
    )