from __future__ import annotations
import hashlib
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from langchain_community.document_loaders import CSVLoader, Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()
DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL")
_PRECHUNK_SEPARATOR = "---"


class DocumentLoadingService:
    SUPPORTED = {".txt", ".pdf", ".docx", ".csv"}

    def load(self, path: str) -> List[Document]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Not found: {p}")
        if p.is_file():
            return self._load_file(p)
        if p.is_dir():
            docs: List[Document] = []
            for f in p.rglob("*"):
                if f.is_file() and f.suffix.lower() in self.SUPPORTED:
                    docs.extend(self._load_file(f))
            return docs
        raise ValueError(f"Invalid path: {p}")

    def _load_file(self, file_path: Path) -> List[Document]:
        suffix = file_path.suffix.lower()
        if suffix == ".txt":
            return TextLoader(str(file_path), encoding="utf-8").load()
        if suffix == ".pdf":
            return PyPDFLoader(str(file_path)).load()
        if suffix == ".docx":
            return Docx2txtLoader(str(file_path)).load()
        if suffix == ".csv":
            return CSVLoader(str(file_path), encoding="utf-8").load()
        raise ValueError(f"Unsupported: {suffix}")


def chunk_documents(documents: List[Document], chunk_size: int = 500, chunk_overlap: int = 100) -> List[Document]:
    result: List[Document] = []
    for doc in documents:
        text = doc.page_content
        if _PRECHUNK_SEPARATOR in text and "[CHUNK_" in text:
            for block in text.split(_PRECHUNK_SEPARATOR):
                block = block.strip()
                if block and len(block) >= 50:
                    result.append(Document(page_content=block, metadata=doc.metadata))
        else:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ". ", " "],
            )
            result.extend(splitter.split_documents([doc]))
    return result


class EmbeddingService:
    def __init__(self, collection_name: str):
        if not DATABASE_URL:
            raise ValueError("SUPABASE_DATABASE_URL missing")
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = PGVector(
            embeddings=self.embeddings,
            collection_name=self.collection_name,
            connection=DATABASE_URL,
            use_jsonb=True,
        )

    def upload_chunks(self, chunks: List[Document]) -> str:
        if not chunks:
            return "No chunks to upload"
        for chunk in chunks:
            chunk.metadata["content_hash"] = hashlib.sha256(chunk.page_content.encode()).hexdigest()
        self.vectorstore.add_documents(chunks)
        return f"Uploaded {len(chunks)} chunks to '{self.collection_name}'"

    def get_vectorstore(self) -> PGVector:
        return self.vectorstore


def ingest_documents(path: str, collection_name: str, chunk_size: int = 500, chunk_overlap: int = 100) -> str:
    documents = DocumentLoadingService().load(path)
    chunks = chunk_documents(documents, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return EmbeddingService(collection_name).upload_chunks(chunks)
