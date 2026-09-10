"""Extract and chunk jurisdiction-tagged legal PDFs into JSONL records."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from pypdf import PdfReader


JURISDICTIONS = {"federal", "punjab", "sindh", "kp", "balochistan"}
DOMAINS = {"constitutional", "criminal", "tenancy", "labor", "consumer"}
FILENAME_PATTERN = re.compile(
    r"^(?P<jurisdiction>[a-z]+)__(?P<domain>[a-z]+)__(?P<source>.+)\.pdf$",
    re.IGNORECASE,
)


def parse_metadata(pdf_path: Path) -> dict[str, str]:
    match = FILENAME_PATTERN.match(pdf_path.name)
    if not match:
        raise ValueError(
            f"{pdf_path.name}: use jurisdiction__domain__source-act.pdf"
        )

    metadata = {key: value.lower() for key, value in match.groupdict().items()}
    if metadata["jurisdiction"] not in JURISDICTIONS:
        raise ValueError(f"{pdf_path.name}: unsupported jurisdiction")
    if metadata["domain"] not in DOMAINS:
        raise ValueError(f"{pdf_path.name}: unsupported domain")
    metadata["source_act"] = metadata.pop("source").replace("-", " ").title()
    return metadata


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    step = chunk_size - overlap
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(words):
            break
    return chunks


def load_pdf(pdf_path: Path, chunk_size: int, overlap: int) -> list[dict]:
    metadata = parse_metadata(pdf_path)
    records = []
    reader = PdfReader(str(pdf_path))
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        for chunk_number, content in enumerate(
            chunk_text(page_text, chunk_size, overlap), start=1
        ):
            records.append(
                {
                    **metadata,
                    "section_ref": f"page {page_number}, chunk {chunk_number}",
                    "language": "en",
                    "content": content,
                    "source_file": pdf_path.name,
                }
            )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("ingestion/raw_legal_docs"))
    parser.add_argument("--output", type=Path, default=Path("ingestion/chunks.jsonl"))
    parser.add_argument("--chunk-size", type=int, default=900)
    parser.add_argument("--overlap", type=int, default=120)
    args = parser.parse_args()

    pdf_paths = sorted(args.input.rglob("*.pdf"))
    if not pdf_paths:
        raise SystemExit(f"No PDFs found under {args.input}")
    if args.overlap >= args.chunk_size:
        raise SystemExit("--overlap must be smaller than --chunk-size")

    records = []
    for pdf_path in pdf_paths:
        records.extend(load_pdf(pdf_path, args.chunk_size, args.overlap))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as output_file:
        for record in records:
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Created {len(records)} chunks from {len(pdf_paths)} PDF(s): {args.output}")


if __name__ == "__main__":
    main()
