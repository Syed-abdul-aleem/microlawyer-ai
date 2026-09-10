# MicroLawyer AI Architecture

The system has two applications:

1. `frontend/` provides the public Next.js interface.
2. `backend/` provides the FastAPI API, retrieval orchestration, speech processing, and PDF generation.

Legal source chunks are stored with a mandatory `jurisdiction` value: `federal`, `punjab`, `sindh`, `kp`, or `balochistan`. Tenancy, labor, and consumer retrieval must have a known province before a response is produced. FIR and criminal-law retrieval uses the federal jurisdiction.

The backend will use local multilingual embeddings during ingestion and Supabase pgvector for storage and similarity search. LLM providers are accessed server-side so API keys never reach the browser.
