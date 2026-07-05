"""
Load the GST filing knowledge base into pgvector.

    python ingest_runner.py

Safe to re-run — PGVector assigns IDs from content so identical chunks
won't cause query errors (though duplicates may build up; clear the
collection manually if you need a clean re-ingest).
"""
import sys
from pathlib import Path

from config import RAG_CHUNK_OVERLAP, RAG_CHUNK_SIZE
from ingest import ingest_documents

FILING_KB = Path(__file__).parent / "ingestion" / "t_docs" / "gst_filing.txt"
FILING_COLLECTION = "gst"


def main() -> None:
    if not FILING_KB.exists():
        print(f"ERROR: KB file not found: {FILING_KB}", file=sys.stderr)
        sys.exit(1)

    print(f"Ingesting  : {FILING_KB.name}")
    print(f"Collection : {FILING_COLLECTION}")
    print(f"Chunk size : {RAG_CHUNK_SIZE}  Overlap: {RAG_CHUNK_OVERLAP}")

    try:
        result = ingest_documents(
            path=str(FILING_KB),
            collection_name=FILING_COLLECTION,
            chunk_size=RAG_CHUNK_SIZE,
            chunk_overlap=RAG_CHUNK_OVERLAP,
        )
        print(f"Done: {result}")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
