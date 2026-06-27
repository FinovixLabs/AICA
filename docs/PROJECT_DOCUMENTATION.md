# AICA Project Documentation

This document is the current implementation brief for the AICA workspace at
`C:\aicaa`. It describes what is implemented now, how the main files connect,
and which pieces are still placeholders.

Last reviewed from live files: 2026-06-27.

## 1. Project Summary

AICA is an AI-assisted compliance workspace for CA, CS, and GST practitioners.
The current MVP is a Flask application with a single-page frontend for:

- client management
- document upload and text extraction
- GST filing preparation, especially GSTR-1
- generated GSTR-1 CSV/JSON output
- assistant-driven edits to generated filing output
- early notice reply and RAG scaffolding

The project does not currently automate GST portal login/submission, payments,
subscriptions, full CRM workflows, or a production authentication model.

## 2. Current Status

| Area | Status | Notes |
| --- | --- | --- |
| Flask app | Implemented | `app.py` serves the static app, registers blueprints, manages DB connections, and exposes `/health`. |
| Client management | Partially implemented | Client list/create is DB-backed through a default CA. Client detail is still a placeholder. |
| Document upload | Partially implemented | Upload saves files locally, extracts text for supported files, and stores `file_text` in `documents`. |
| GSTR-1 requirements check | Implemented prototype | AI compares uploaded document list/text against `GSTR1_REQUIRED_DOCUMENTS`. |
| GSTR-1 filing output | Implemented prototype | Builds filing JSON/CSV from present uploaded docs and JSON templates. |
| Assistant filing edits | Implemented prototype | Assistant can edit current filing CSV/JSON through dedicated endpoints and update downloads. |
| RAG ingestion/search | Prototype implemented | LangChain ingestion, PGVector upload, Supabase chunk fetch, vector/BM25 retrieval. |
| Notice module | Route contract only | Notice classify/draft/approve endpoints still return placeholder responses. |
| Auth | Placeholder | Login returns a placeholder user/token; request auth is not enforced. |
| Tests | Not implemented | There is no dedicated test suite yet. |

## 3. Architecture

High-level request flow:

```text
static/index.html
    |
    v
Flask app in app.py
    |
    v
Blueprints in routes/clients.py
    |
    +--> db.py / Supabase PostgreSQL
    +--> uploading.py
    +--> requirement_checking.py
    +--> chat_assistant.py
    +--> filing/prerequisites.py
    +--> ingest.py / hybrid_search.py
```

Current layer responsibilities:

| Layer | Files | Responsibility |
| --- | --- | --- |
| Frontend | `static/index.html` | Single-page UI, API contract, filing workflow, generated output panel, chat interactions. |
| Flask app | `app.py` | App factory, static serving, CORS, DB connection lifecycle, blueprint registration. |
| Routes | `routes/clients.py` | Auth/client/document/filing/notice/chat/knowledge HTTP handlers. |
| DB config | `config.py`, `db.py` | `.env` loading and Supabase PostgreSQL connection pool. |
| Upload extraction | `uploading.py` | Extracts text from `.txt`, `.csv`, and `.pdf`; cleans text with pandas. |
| Filing checks/output | `requirement_checking.py` | GSTR-1 required document list, AI readiness check, filing JSON/CSV generation. |
| Assistant | `chat_assistant.py` | OpenAI-backed chat and filing-output edit helpers. |
| Filing prerequisites | `filing/prerequisites.py` | Older prerequisite checks for `GSTR_3` and `GSTR_2A`. |
| RAG ingestion | `ingest.py`, `ingest_runner.py` | Loads, chunks, embeds, and uploads documents to PGVector. |
| RAG search | `hybrid_search.py` | Supabase chunk retrieval plus vector/BM25/ensemble retrievers. |

Routes are still bundled in `routes/clients.py`. The comments point toward a
future split into auth/client/filing/notice modules, but that split has not been
done.

## 4. Backend

### `app.py`

Responsibilities:

- Creates the Flask app with `create_app()`.
- Serves `static/index.html` at `/`.
- Serves static assets with `static_url_path=""`.
- Enables CORS from `config.CORS_ORIGINS`.
- Registers:
  - `api_bp`
  - `auth_bp`
  - `client_bp`
  - `filing_bp`
  - `notice_bp`
- Opens one DB connection per request with `g.db = _pool.getconn()`.
- Commits successful requests and rolls back failed requests in teardown.
- Provides `/health`.

Operational note: when new routes are added, the Flask development server must
be restarted if debug reload is off. Otherwise the browser can call a route that
exists on disk but is not loaded in the running process.

### `config.py`

Loads `.env` using `python-dotenv`.

Required values accessed directly:

- `SUPABASE_DATABASE_URL`
- `SUPABASE_JWT_SECRET`

Optional values:

- `SUPABASE_SERVICE_KEY`
- `SUPABASE_URL`
- `CORS_ORIGINS`
- `FLASK_DEBUG`
- `RAG_CHUNK_OVERLAP`
- `RAG_TOP_K`
- `OPENAI_EMBEDDING_MODEL`
- `OPENAI_CHAT_MODEL`

OpenAI helpers also read:

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_REQUIREMENTS_MODEL`

### `db.py`

Creates a `psycopg2.pool.SimpleConnectionPool` using `SUPABASE_DATABASE_URL`.
`app.py` uses this pool for per-request database connections.

## 5. Route Layer

Route definitions live in `routes/clients.py`.

Blueprints:

| Blueprint | Prefix |
| --- | --- |
| `api_bp` | `/api` |
| `auth_bp` | `/api/auth` |
| `client_bp` | `/api/clients` |
| `filing_bp` | `/api/filing` |
| `notice_bp` | `/api/notices` |

Current endpoints:

| Endpoint | Method | Current behavior |
| --- | --- | --- |
| `/` | GET | Serves the SPA. |
| `/health` | GET | Returns health JSON. |
| `/api/auth/login` | POST | Placeholder login; validates email/password presence and returns placeholder user/token. |
| `/api/auth/logout` | POST | Returns `{ok: true}`. |
| `/api/auth/me` | GET | Returns `{user: null}`. |
| `/api/dashboard` | GET | Returns empty dashboard-shaped data. |
| `/api/clients` | GET | Lists DB clients for the default CA. |
| `/api/clients` | POST | Creates a client after GSTIN/name validation. |
| `/api/clients/<gstin>` | GET | Placeholder client detail. |
| `/api/clients/<gstin>/documents` | GET | Lists uploaded documents for a client. |
| `/api/clients/<gstin>/documents` | POST | Saves upload locally, extracts text, inserts a `documents` row. |
| `/api/filing/prerequisites` | POST | Older prerequisite check for supported filing types. |
| `/api/filing/reconcile` | POST | Placeholder response used by the filing screen. |
| `/api/filing/requirements-check` | POST | Runs GSTR-1 AI document readiness check. |
| `/api/filing/start` | POST | Builds GSTR-1 filing JSON/CSV from matched documents and templates. |
| `/api/filing/edit-output` | POST | AI edits the current filing CSV/JSON and returns updated files. |
| `/api/filing/edit-output-stream` | POST | Streams updated CSV tokens, then JSON after a delimiter. |
| `/api/filing/output` | POST | Legacy placeholder CSV route. |
| `/api/notices/classify` | POST | Placeholder notice metadata. |
| `/api/notices/draft-reply` | POST | Placeholder draft reply. |
| `/api/notices/approve` | POST | Validates fields and returns saved version/time metadata. |
| `/api/chat` | POST | OpenAI-backed assistant chat, JSON or SSE depending on `Accept`. |
| `/api/knowledge` | GET | Placeholder knowledge metadata. |

## 6. Document Upload And Text Extraction

Upload route:

```text
POST /api/clients/<gstin>/documents
```

Implemented behavior:

- Resolves the client by GSTIN under the default CA.
- Saves the uploaded file under `uploads/<client_id>/`.
- Stores a relative `storage_path`.
- Sets `doc_type = "other"` for now.
- Calls `uploading.extract_and_clean(dest_path)`.
- Inserts `file_text` into the `documents` table.
- Returns a frontend-friendly row containing name, type, route, extracted size,
  and status.

`uploading.py` supports:

- `.txt`
- `.csv`
- `.pdf` through `pypdf`

CSV extraction uses pandas and returns normalized CSV text. Cleanup strips blank
lines, removes duplicate lines, and preserves row order.

Current limitations:

- ZIP files are not extracted.
- OCR for scanned PDFs is not implemented.
- Uploaded document category classification is not implemented.
- `doc_type` remains `other`, so the newer GSTR-1 flow matches by file name/text
  rather than by `doc_type`.

## 7. GSTR-1 Requirements And Filing Output

Main file:

```text
requirement_checking.py
```

### Required document list

`GSTR1_REQUIRED_DOCUMENTS` currently contains:

- `b2b_invoices`
- `b2cl_invoices`
- `b2cs_invoices`
- `credit_debit_notes_registered`
- `credit_debit_notes_unregistered`
- `export_invoices`
- `advance_receipts_services`
- `advance_adjustments_services`
- `nil_exempt_nongst_supplies`
- `hsn_summary`
- `document_issuance_summary`
- `ecommerce_sales_tcs`

### Requirements check

Endpoint:

```text
POST /api/filing/requirements-check
```

Flow:

1. Resolve client by GSTIN.
2. Fetch `client_id`, `file_name`, `file_text`, and `tax_period` from
   `documents`.
3. Send the required document list and fetched document data to OpenAI.
4. Require the model to return exact required-document identifiers in `present`
   and `missing`.
5. Backend normalizes the AI output and only accepts identifiers from
   `GSTR1_REQUIRED_DOCUMENTS`.
6. If anything is missing, frontend offers:
   - `Continue`
   - `Intimate client`

### Filing start

Endpoint:

```text
POST /api/filing/start
```

Flow:

1. Loads JSON templates from `filing/json_templates/<document_key>.json`.
2. Fetches document payloads from the `documents` table.
3. Dynamically uses `file_path` if present, otherwise `storage_path`.
4. Matches uploaded documents to required keys using:
   - required document key
   - normalized key variants
   - template aliases such as `template_name`, `source_file`, `section_code`,
     and `section_description`
5. Builds:
   - `filing_json`
   - `filing_csv`
   - `missing_documents`
   - `missing_json_templates`
6. Returns `message = "filing completed"`.

### Filing CSV generation

`_build_filing_csv(...)` no longer returns a present/missing document summary.
It skips missing sections and emits rows only from matched uploaded files.

When a JSON template exists, its `columns[*].column_name` values define the CSV
headers. Source rows are parsed from `file_text` and mapped by normalized column
names/canonical keys.

If multiple present sections produce rows, the CSV includes a `gstr1_section`
column. If one section produces rows, the CSV uses that section's filing columns
directly.

Current template present:

```text
filing/json_templates/credit_debit_notes_registered.json
```

Template name:

```text
GSTR-1_CDNR_Credit_Debit_Notes_Registered_Template
```

This template defines CDNR columns such as:

- `GSTIN/UIN of Recipient`
- `Receiver Name`
- `Note Number`
- `Note Date`
- `Note Type`
- `Place Of Supply`
- `Reverse Charge`
- `Note Supply Type`
- `Note Value`
- `Applicable % of Tax Rate`
- `Rate`
- `Taxable Value`
- `Cess Amount`

Current limitation: most required document keys do not yet have JSON templates.

## 8. Assistant And Filing Output Edits

Main file:

```text
chat_assistant.py
```

Implemented helpers:

- `stream_chat(...)`
- `edit_filing_output(...)`
- `stream_edit_filing_output(...)`

### Normal chat

Endpoint:

```text
POST /api/chat
```

The route supports both:

- JSON fallback response
- `text/event-stream` token streaming

The assistant uses OpenAI chat completions through the standard-library
`urllib.request` client. Context-specific system prompts exist for filing and
notice modes.

### Filing output edits

Endpoints:

```text
POST /api/filing/edit-output
POST /api/filing/edit-output-stream
```

The assistant can modify generated filing CSV/JSON after the filing output has
been created. The request includes:

- GSTIN
- period
- user instruction
- current `filing_csv`
- current `filing_json`

The non-streaming endpoint returns:

- `message`
- updated `filing_csv`
- updated `filing_json`

The streaming endpoint emits:

```text
<updated CSV tokens>
===FILING_JSON===
<updated JSON>
```

Frontend downloads read from the same in-memory `state.lastFilingOutput.result`,
so the Download CSV and Download JSON buttons use the latest edited output after
each successful assistant modification.

Current limitation: these edits are not persisted to the database; they live in
frontend state until downloaded or refreshed.

## 9. Frontend

Main file:

```text
static/index.html
```

Responsibilities:

- Defines all endpoint paths under `CONFIG.ENDPOINTS`.
- Implements login, dashboard, clients, document upload, filing, notice,
  knowledge, and assistant panels.
- Keeps generated filing output in `state.lastFilingOutput`.
- Renders generated CSV into the output panel.
- Downloads the current CSV/JSON state.

Important filing endpoint contract:

```javascript
requirementsCheck: "/api/filing/requirements-check"
filingStart: "/api/filing/start"
filingEditOutput: "/api/filing/edit-output"
filingEditOutputStream: "/api/filing/edit-output-stream"
filingCsv: "/api/filing/output"
```

Current filing UI behavior:

- Top row contains the uploaded-documents/requirements card and a capped-height
  assistant panel.
- Uploaded documents card expands to show the full generated requirement list.
- Assistant chat body scrolls instead of growing with messages.
- Generated output appears in a separate lower panel.
- CSV table is constrained inside the output panel and scrolls internally.
- Continue starts filing output generation.
- Assistant edit prompts stream changes directly into the generated output
  panel, without adding a normal chat reply.
- Download buttons are disabled during a streaming update.

Frontend CSV helper behavior:

- `buildGeneratedFilingCsv(...)` can build the visible CSV from `filing_json`.
- It currently prefers `credit_debit_notes_registered` when present.
- It ignores old summary-style CSV headers such as `document_found` and
  `json_template_found`.

## 10. Filing Prerequisites Legacy Module

File:

```text
filing/prerequisites.py
```

This older module is still present and supports:

- `GSTR_3`
- `GSTR_2A`

It checks `documents.doc_type` against static prerequisite lists and returns
`ready` or `blocked`.

This is separate from the newer GSTR-1 requirements check in
`requirement_checking.py`, which matches uploaded docs by file name/text and AI
comparison.

## 11. RAG Ingestion And Search

### `ingest.py`

Implemented:

- `DocumentLoadingService`
  - loads `.txt`, `.pdf`, `.docx`, `.csv`
  - supports files and folders
- `document_splitter`
  - uses `RecursiveCharacterTextSplitter`
  - `chunk_size=2500`
  - `chunk_overlap=300`
- `EmbeddingService`
  - uses `OpenAIEmbeddings`
  - writes to PGVector via `langchain-postgres`
  - supports caller-provided `collection_name`
- `ingest_documents(path, collection_name)`

### `ingest_runner.py`

Currently runs:

```python
ingest_documents(
    path="ingestion/t_docs/gst_filing.txt",
    collection_name="gst",
)
```

### `hybrid_search.py`

Implemented:

- Supabase client creation
- collection UUID lookup from `langchain_pg_collection`
- chunk fetch from `langchain_pg_embedding`
- vector retriever
- BM25 retriever
- ensemble retriever
- multi-query retriever
- contextual compression retriever
- `SearchEngine.search(query)`

Current limitation: RAG retrieval is still not wired into `/api/chat`,
requirements checking, notice drafting, or generated filing edits.

## 12. Filing Format Storage

Markdown form specs:

```text
filing_formats/form_gstr_1a.md
filing_formats/form_gstr_2a.md
filing_formats/form_gstr_2b.md
filing_formats/form_gstr_3.md
```

Loader:

```text
load_filing_formats.py
```

It loads all Markdown specs into the `filing_formats` table using `psycopg2`.

Current JSON filing templates:

```text
filing/json_templates/credit_debit_notes_registered.json
```

`filing/csv_templates/` exists but currently has no tracked CSV template files.

## 13. Database And Migrations

Migrations present:

```text
migrations/001_add_client_display_fields.sql
migrations/002_create_filing_formats.sql
migrations/003_extend_doc_type_enum.sql
```

Referenced DB tables include:

- `cas`
- `clients`
- `documents`
- `filing_formats`
- `langchain_pg_collection`
- `langchain_pg_embedding`

Known `documents` columns used by current code:

- `client_id`
- `doc_type`
- `file_name`
- `storage_path`
- `file_text`
- `file_size_bytes`
- `tax_period`
- `uploaded_at`

`requirement_checking.py` also checks whether `file_path` exists and falls back
to `storage_path` when it does not.

## 14. Dependencies

Current `requirements.txt` includes:

- `flask`
- `flask-cors`
- `docx2txt`
- `langchain-classic`
- `langchain-community`
- `langchain-core`
- `langchain-openai`
- `langchain-postgres`
- `langchain-text-splitters`
- `pandas`
- `psycopg2-binary`
- `pypdf`
- `python-dotenv`
- `rank-bm25`
- `supabase`

These cover the currently imported third-party packages in the Flask app,
upload extraction flow, and ingestion/search prototype.

## 15. Project File Map

Important source files and directories:

```text
C:\aicaa
|-- AGENTS.md
|-- AI_CONTEXT.md
|-- CLAUDE.md
|-- app.py
|-- config.py
|-- db.py
|-- routes\
|   `-- clients.py
|-- static\
|   `-- index.html
|-- chat_assistant.py
|-- requirement_checking.py
|-- uploading.py
|-- csv_management.py
|-- filing\
|   |-- __init__.py
|   |-- prerequisites.py
|   |-- csv_templates\
|   `-- json_templates\
|       `-- credit_debit_notes_registered.json
|-- filing_formats\
|   |-- form_gstr_1a.md
|   |-- form_gstr_2a.md
|   |-- form_gstr_2b.md
|   `-- form_gstr_3.md
|-- load_filing_formats.py
|-- ingest.py
|-- ingest_runner.py
|-- hybrid_search.py
|-- ingestion\
|   `-- t_docs\
|       |-- gst_filing.txt
|       `-- gst_notice.txt
|-- migrations\
|   |-- 001_add_client_display_fields.sql
|   |-- 002_create_filing_formats.sql
|   `-- 003_extend_doc_type_enum.sql
|-- uploads\
|-- requirements.txt
|-- ai_filing_agent.py
|-- orchestrator.py
`-- docs\
    `-- PROJECT_DOCUMENTATION.md
```

Generated or local workflow files that should not be treated as product source:

```text
venv\
__pycache__\
routes\__pycache__\
filing\__pycache__\
ingestion\__pycache__\
.dist\
logs\server_stdout.log
logs\server_stderr.log
TASK.md
STATUS.md
CHANGED_FILES.md
CODEX_TASK.md
CODEX_REVIEW.md
```

`ai_filing_agent.py` exists at the repository root and is currently effectively
empty. There is no live `ai/ai_filing_agent.py` file in the current tree.

## 16. Completed Work

Completed or partially completed:

- Flask app factory and static frontend serving.
- Supabase PostgreSQL connection pooling.
- Environment configuration through `.env`.
- Blueprint registration for auth, clients, filing, notices, general API.
- Default CA fallback.
- Client list/create route with GSTIN validation.
- Document upload/list route.
- Text extraction into `documents.file_text` for supported uploads.
- GSTR-1 required document list.
- AI-backed GSTR-1 requirements check.
- GSTR-1 filing start payload generation.
- Filing JSON generation.
- Filing CSV generation from present documents and JSON templates.
- Credit/debit notes registered JSON template.
- Frontend generated output panel with CSV rendering.
- Download CSV and Download JSON buttons.
- Assistant edit endpoints for generated filing output.
- Streaming assistant edits into the generated output panel.
- RAG ingestion and hybrid retrieval prototypes.
- Filing format Markdown specs and loader.
- Updated `requirements.txt` for current imports.

## 17. Known Gaps And TODOs

Documentation gaps:

- `docs/03_DATABASE_SCHEMA.md` is still missing.
- `docs/04_MVP1_SCOPE.md` is still missing.
- `docs/09_AI_WORKFLOW.md` is still missing.
- A dedicated module architecture document is still missing.

Implementation gaps:

- Auth remains placeholder.
- Dashboard data remains placeholder.
- Client detail remains placeholder.
- Document upload does not classify `doc_type`.
- ZIP extraction is not implemented.
- OCR/scanned PDF extraction is not implemented.
- GSTR-1 only has one JSON template currently: CDNR.
- Generated/edited filing output is not persisted to DB.
- `/api/filing/reconcile` remains placeholder.
- `/api/filing/output` remains a legacy placeholder route.
- Notice classify/draft/approve are placeholders.
- RAG retrieval is not wired into chat or notice drafting.
- Knowledge endpoint is placeholder.
- There is no dedicated automated test suite.

## 18. Suggested Next Steps

Recommended order:

1. Add the missing docs:
   - `docs/03_DATABASE_SCHEMA.md`
   - `docs/04_MVP1_SCOPE.md`
   - `docs/09_AI_WORKFLOW.md`
   - module architecture doc
2. Add JSON templates for the remaining `GSTR1_REQUIRED_DOCUMENTS`.
3. Persist generated filing JSON/CSV and edit history in the database.
4. Add document type classification so `doc_type` is no longer always `other`.
5. Add ZIP extraction and OCR fallback if those upload types are required.
6. Wire RAG retrieval into `/api/chat` and notice drafting.
7. Implement notice classification and draft generation.
8. Implement deterministic reconciliation or remove the placeholder route from
   the active filing workflow.
9. Add tests for:
   - app route registration
   - client validation
   - document upload/extraction
   - GSTR-1 requirements normalization
   - filing CSV generation
   - filing edit endpoints

## 19. Minimal Validation Commands

Useful local checks:

```powershell
py -m py_compile app.py routes\clients.py chat_assistant.py requirement_checking.py uploading.py ingest.py hybrid_search.py
```

For frontend syntax:

```powershell
$html = Get-Content -Raw -LiteralPath static\index.html
$m = [regex]::Match($html, '<script>([\s\S]*)</script>')
Set-Content -LiteralPath .dist\static-inline-check.js -Value $m.Groups[1].Value -Encoding UTF8
node --check .dist\static-inline-check.js
```

When backend routes change, restart the Flask server before testing in the
browser because debug reload may be off.
