"""Embed chunk JSONL locally and upload records to Supabase pgvector."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from supabase import create_client

from app.config import settings


def read_chunks(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as input_file:
        return [json.loads(line) for line in input_file if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("ingestion/chunks.jsonl"))
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    records = read_chunks(args.input)
    if not records:
        raise SystemExit(f"No chunks found in {args.input}")

    model = SentenceTransformer(settings.embedding_model)
    embeddings = model.encode(
        [record["content"] for record in records],
        batch_size=args.batch_size,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    rows = []
    for record, embedding in zip(records, embeddings):
        rows.append(
            {
                "content": record["content"],
                "jurisdiction": record["jurisdiction"],
                "domain": record["domain"],
                "source_act": record["source_act"],
                "section_ref": record["section_ref"],
                "language": record.get("language", "en"),
                "embedding": embedding.tolist(),
            }
        )

    if args.dry_run:
        print(f"Dry run complete: prepared {len(rows)} embedded chunks")
        return
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env")

    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    for start in range(0, len(rows), args.batch_size):
        client.table("legal_documents").insert(rows[start : start + args.batch_size]).execute()
    print(f"Uploaded {len(rows)} embedded chunks to Supabase")


if __name__ == "__main__":
    main()
