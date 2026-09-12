# Local ingestion dependencies

The Render runtime calls Hugging Face for query embeddings. Install the separate ingestion
requirements on the computer used to build document embeddings:

```bash
pip install -r requirements-ingestion.txt
```

`embed_and_upload.py` uses `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
The production API requests the same model through Hugging Face's feature-extraction API.
# Legal document ingestion

Place source PDFs in one of these folders:

`backend/ingestion/raw_legal_docs/federal/`

`backend/ingestion/raw_legal_docs/punjab/`

`backend/ingestion/raw_legal_docs/sindh/`

`backend/ingestion/raw_legal_docs/kp/`

`backend/ingestion/raw_legal_docs/balochistan/`

Use this filename format:

`jurisdiction__domain__source-act.pdf`

Examples: `federal__criminal__pakistan-penal-code-1860.pdf` and `punjab__tenancy__punjab-rented-premises-act-2009.pdf`.

From `backend/`, run:

```powershell
python -m pip install -r requirements.txt
python -m ingestion.scripts.load_and_chunk
python -m ingestion.scripts.embed_and_upload --dry-run
python -m ingestion.scripts.embed_and_upload
```

The first script writes `ingestion/chunks.jsonl`; the second downloads the embedding model on its first run, creates local embeddings, and uploads them using the Supabase service-role key.