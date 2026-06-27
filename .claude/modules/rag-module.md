# RAG Module Architecture

## 1. Module Scope

The RAG module is responsible for:

- Ingesting client documents and knowledge base files into pgvector
- Providing ensemble retrieval to the filing module and notice module
- Managing the global GST knowledge base

The RAG module does **not** handle:

- Original file upload or storage (Document Ingestion Module)
- OCR or text extraction (Document Ingestion Module)
- Generating replies or filing output (filing and notice modules)
- Persisting client application state

---

## 2. Knowledge Base Types

| Type | Scope | client_id filter |
|---|---|---|
| Global knowledge base | GST rules, notice templates, filing formats | No filter — shared across all clients |
| Client documents | Uploaded invoices, registers, notices | Filter by client_id |

---

## 3. Global Knowledge Base Sources

Located in `ingestion/t_docs/`:

- `gst_filing.txt` — GST filing rules, prerequisites, format definitions
- `gst_notice.txt` — GST notice templates, reply formats, section references

**Status: Not yet uploaded.** Do not ingest or build retrieval chains until the user confirms these files are present.

---

## 4. Tech Stack

- LangChain — document loading, text splitting, chain composition
- OpenAI embeddings — model from `config.OPENAI_EMBEDDING_MODEL`
- pgvector on Supabase PostgreSQL — cosine similarity via `<=>` operator
- BM25 / keyword search — sparse retrieval component
- psycopg2 pool from `db.py` — all database operations
- Ensemble retriever — combines dense (pgvector) + sparse (BM25) results

---

## 5. Ingestion Pipeline

```
PDF / TXT file
     ↓
Text extraction (pdfminer/pypdf → Gemini OCR fallback)
     ↓
Chunk (RecursiveCharacterTextSplitter, size=500, overlap from config)
     ↓
Batch embed (OpenAI via LangChain)
     ↓
INSERT into documents table (chunk_text, embedding, client_id, source_file, chunk_index)
```

---

## 6. Chunking Rules

- Chunk size: **500 characters** (fixed — do not change without explicit instruction)
- Overlap: `config.RAG_CHUNK_OVERLAP` (default 100)
- Splitter: `LangChain RecursiveCharacterTextSplitter`
- Minimum file size to chunk: 200 characters
- Do not re-ingest already-chunked documents without explicit user request

---

## 7. Embedding Rules

- Model: `config.OPENAI_EMBEDDING_MODEL`
- Always batch embed — never stream
- Use LangChain wrappers — no direct `openai.*` API calls

---

## 8. Storage Schema (per chunk)

| Column | Description |
|---|---|
| client_id | UUID — null for global knowledge base chunks |
| chunk_text | Extracted text chunk |
| embedding | pgvector column |
| source_file | Original file name |
| chunk_index | Position of chunk within the source file |

Do not store raw file bytes in the database.

---

## 9. Retrieval

- Method: **Ensemble retrieval** — dense (pgvector cosine similarity) + sparse (BM25/keyword)
- Top-K: `config.RAG_TOP_K` (default 5)
- Always return similarity/relevance scores with results
- Client document queries: filter by `client_id`
- Global knowledge base queries: no `client_id` filter

---

## 10. Retrieval Output Shape

```json
[
  {
    "chunk_id": "identifier",
    "source_file": "file_name",
    "chunk_text": "retrieved text",
    "score": 0.87,
    "client_id": null
  }
]
```

---

## 11. Strict Non-Goals

This module must never perform:

- File upload or user-facing API endpoints
- OCR or document parsing
- Reply generation or filing output
- Re-ingestion of already-chunked documents without explicit instruction
- Streaming embeddings
- Direct `openai.*` API calls outside LangChain wrappers
