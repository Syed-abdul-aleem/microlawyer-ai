import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import cases, chat, checklist, documents, learn, quick_check, voice

logger = logging.getLogger(__name__)


def _parse_origins(value: str) -> list[str]:
    return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]


allowed_origins = _parse_origins(settings.frontend_origin)
if not allowed_origins:
    raise RuntimeError("FRONTEND_ORIGIN must contain at least one origin")

app = FastAPI(
    title="MicroLawyer AI API",
    description="Informational legal assistance for Pakistan with jurisdiction-aware retrieval.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https://microlawyer-ai(?:-[a-z0-9-]+)?\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("CORS configured for origins: %s and Vercel preview deployments", allowed_origins)

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
