from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import cases, chat, checklist, documents, learn, quick_check, voice

app = FastAPI(
    title="MicroLawyer AI API",
    description="Informational legal assistance for Pakistan with jurisdiction-aware retrieval.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(checklist.router, prefix="/api")
app.include_router(quick_check.router, prefix="/api")
app.include_router(learn.router, prefix="/api")
app.include_router(cases.router, prefix="/api")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "microlawyer-ai-api"}
