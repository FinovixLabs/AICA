from __future__ import annotations
import logging
import os
from typing import Any, cast
from dotenv import load_dotenv
from langchain_core.documents import Document

load_dotenv()
logger = logging.getLogger(__name__)


class FilingSearchEngine:
    def __init__(self, collection_name: str = "gst", top_k: int = 5):
        self.collection_name = collection_name
        self.top_k = top_k
        self._retriever = self._build()

    def _build(self):
        from app.services.ingest import EmbeddingService
        from langchain_community.retrievers import BM25Retriever
        from langchain_classic.retrievers import EnsembleRetriever

        vectorstore = EmbeddingService(collection_name=self.collection_name).get_vectorstore()
        vector_retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.top_k},
        )

        chunks = self._fetch_all_chunks()
        if not chunks:
            logger.warning("BM25: no chunks in collection '%s'. Run ingest first.", self.collection_name)
            from langchain_classic.retrievers import EnsembleRetriever
            return EnsembleRetriever(retrievers=[vector_retriever], weights=[1.0])

        bm25 = BM25Retriever.from_documents(chunks)
        bm25.k = self.top_k
        return EnsembleRetriever(retrievers=[bm25, vector_retriever], weights=[0.4, 0.6])

    def _fetch_all_chunks(self) -> list[Document]:
        from supabase import create_client
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
        if not supabase_url or not supabase_key:
            logger.error("SUPABASE_URL or SUPABASE_SERVICE_KEY not set")
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
                Document(page_content=row["document"] or "", metadata=row["cmetadata"] or {})
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
        docs = self.search(query)
        if not docs:
            return ""
        return "\n\n".join(f"[Source {i}]\n{doc.page_content.strip()}" for i, doc in enumerate(docs, 1))


try:
    filing_search_engine: FilingSearchEngine | None = FilingSearchEngine(collection_name="gst")
    logger.info("FilingSearchEngine ready")
except Exception as _exc:
    logger.error("FilingSearchEngine init failed: %s", _exc)
    filing_search_engine = None
