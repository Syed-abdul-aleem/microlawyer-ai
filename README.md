# MicroLawyer AI

MicroLawyer AI is an informational legal assistant for everyday Pakistanis. It supports English, Urdu, and Roman Urdu workflows for legal education, document drafting, and retrieval from jurisdiction-tagged Pakistani legal sources.

## Project status

Phase 2 ingestion is implemented. The application is not legal advice and does not replace a licensed lawyer or the relevant authority.

## Structure

- `frontend/` Next.js user interface
- `backend/` FastAPI API and ingestion pipeline
- `docs/` architecture and legal safety documentation

## Development

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The frontend uses port 3000 by default. The backend uses port 8000 by default.

## Phase 2: legal document ingestion

Create a free Supabase project, open its SQL Editor, and run [docs/SUPABASE_SCHEMA.sql](docs/SUPABASE_SCHEMA.sql). Then copy [backend/.env.example](backend/.env.example) to `backend/.env` and set `SUPABASE_URL` plus the Supabase project **service-role** key. Keep that key server-side and never put it in `frontend/.env.local`.

Place PDFs in `backend/ingestion/raw_legal_docs/<jurisdiction>/` using the naming format `jurisdiction__domain__source-act.pdf`. Supported jurisdictions are `federal`, `punjab`, `sindh`, `kp`, and `balochistan`; supported domains are `constitutional`, `criminal`, `tenancy`, `labor`, and `consumer`. See [backend/ingestion/README.md](backend/ingestion/README.md) for examples and commands.
