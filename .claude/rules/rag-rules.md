# RAG Rules

## Knowledge Base Status
The knowledge base files (gst_filing.txt, gst_notice.txt) are NOT yet uploaded.
Do not build or run ingestion pipelines until the user confirms the files are in ingestion/t_docs/.

## Chunking
- Chunk size: 500 characters (fixed — do not change without explicit instruction)
- Overlap: defined in config.py
- Minimum file size to chunk: 200 characters
- Splitter: LangChain RecursiveCharacterTextSplitter

## Retrieval
- Method: ensemble retrieval (dense vector search + sparse/keyword search combined)
- Top-K: defined in config.py
- Always return similarity/relevance scores with results
- Client documents: filter by client_id
- Knowledge base queries: no client_id filter (global)

## Storage
Store per chunk: client_id, chunk_text, embedding, source_file, chunk_index
Do not store raw file bytes in the DB.

## Embedding
- Model: configured in config.py
- Always batch embed — never stream
- Use LangChain wrappers — no direct openai.* calls

## Ingestion Flow
1. Extract text (pdfminer/pypdf → Gemini OCR fallback)
2. Chunk at 500 chars
3. Batch embed
4. INSERT into documents table with pgvector column
5. Do not re-ingest already-chunked documents
