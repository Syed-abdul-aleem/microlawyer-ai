from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.whisper_service import transcribe

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/transcribe")
async def voice_transcribe(file: UploadFile = File(...)) -> dict[str, str]:
    try:
        text = await transcribe(
            file.filename or "recording.webm",
            await file.read(),
            file.content_type or "application/octet-stream",
        )
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {"text": text}