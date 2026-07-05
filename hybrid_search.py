from __future__ import annotations

import logging
import os
from typing import Any, cast

from dotenv import load_dotenv
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_classic.retrievers import EnsembleRetriever
from supabase import create_client

from ingest import EmbeddingService

load_dotenv()
logger = logging.getLogger(__name__)


class FilingSearchEngine:
    """
    Hybrid retriever for the GST filing knowledge base.

    Dense (PGVector similarity) + Sparse (BM25 keyword) ensemble.
    Built once at app startup and reused across all requests.
    """

    def __init__(self, collection_name: str = "gst", top_k: int = 5):
        self.collection_name = collection_name
        self.top_k = top_k
        self._retriever = self._build()

    def _build(self) -> EnsembleRetriever:
        # --- vector store (dense) ---
        vectorstore = EmbeddingService(collection_name=self.collection_name).get_vectorstore()
        vector_retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.top_k},
        )

        # --- BM25 (sparse) — needs all chunks in memory ---
        chunks = self._fetch_all_chunks()
        if not chunks:
            logger.warning(
                "BM25: no chunks found in collection '%s'. "
                "Run ingest_runner.py first.",
                self.collection_name,
            )
            # Fall back to vector-only if KB is empty
            return EnsembleRetriever(
                retrievers=[vector_retriever],
                weights=[1.0],
            )

        bm25 = BM25Retriever.from_documents(chunks)
        bm25.k = self.top_k

        return EnsembleRetriever(
            retrievers=[bm25, vector_retriever],
            weights=[0.4, 0.6],   # favour dense for semantic GST queries
        )

    def _fetch_all_chunks(self) -> list[Document]:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
        if not supabase_url or not supabase_key:
            logger.error("SUPABASE_URL or SUPABASE_SERVICE_KEY not set — BM25 disabled")
            return []

        try:
            client = create_client(supabase_url, supabase_key)

            coll = (
                client.table("langchain_pg_collection")
                .select("uuid")
                .eq("name", self.collection_name)
                .execute()
            )
            rows = cast(list[dict[str, Any]], coll.data)
            if not rows:
                return []

            collection_id = rows[0]["uuid"]
            resp = (
                client.table("langchain_pg_embedding")
                .select("document, cmetadata")
                .eq("collection_id", collection_id)
                .execute()
            )
            return [
                Document(
                    page_content=row["document"] or "",
                    metadata=row["cmetadata"] or {},
                )
                for row in cast(list[dict[str, Any]], resp.data)
            ]
        except Exception as exc:
            logger.error("Failed to fetch chunks for BM25: %s", exc)
            return []

    def search(self, query: str) -> list[Document]:
        try:
            return self._retriever.invoke(query)
        except Exception as exc:
            logger.error("Search failed: %s", exc)
            return []

    def search_as_context(self, query: str) -> str:
        """Return retrieved chunks formatted as a context block for injection into prompts."""
        docs = self.search(query)
        if not docs:
            return ""
        parts = []
        for i, doc in enumerate(docs, 1):
            parts.append(f"[Source {i}]\n{doc.page_content.strip()}")
        return "\n\n".join(parts)


# Singleton — built once at import time so BM25 index is ready on first request.
# Will be None if env vars are missing; chat_assistant handles that gracefully.
try:
    filing_search_engine = FilingSearchEngine(collection_name="gst")
    logger.info("FilingSearchEngine ready")
except Exception as _exc:
    logger.error("FilingSearchEngine failed to init: %s", _exc)
    filing_search_engine = None  # type: ignore[assignment]
