# Document Ingestion Module Architecture

## 1. Module Scope

The document ingestion module is responsible for:

- Receiving uploaded files from the client-facing upload endpoint
- Categorising documents as scanned or text-based
- Extracting raw text (pdfminer/pypdf → Gemini OCR fallback)
- Parsing extracted text into structured data
- Storing metadata, extracted text, parsed data, and the original file in Supabase

This module is the entry point for all client documents. Every other module consumes its output — it never consumes theirs.

---

## 2. Module Boundary

The document ingestion module ends when the processed document record is written to Supabase PostgreSQL with `processing_status: "parsed"`.

What happens after that is the responsibility of the filing module, notice module, or RAG module.

---

## 3. Supported Document Types

| document_type | Description |
|---|---|
| sales_register | Monthly outward supply summary |
| purchase_register | Monthly inward supply summary |
| gstr_2b | Auto-drafted ITC statement from GST portal |
| itc_register | ITC eligibility tracking |
| payment_challan | GST payment challan (PMT-06 or similar) |
| sales_invoice | Individual tax invoice |
| credit_note | Credit note issued |
| debit_note | Debit note issued |
| customer_master | Customer GSTIN and details |
| notice | GST notice PDF |
| other | Any document not matching above types |

---

## 4. Document Categories

| document_category | Meaning |
|---|---|
| text_based | PDF with selectable text — pdfminer/pypdf can extract directly |
| scanned | Scanned image PDF — requires Gemini OCR |

Categorisation is determined automatically during text extraction:
- If pdfminer/pypdf returns non-empty text → `text_based`
- If pdfminer/pypdf returns empty or near-empty text → `scanned`, trigger Gemini OCR

---

## 5. Ingestion Pipeline

```
User uploads file via /api/clients/<gstin>/documents
            ↓
Save original file to Supabase Storage
Record file metadata in Supabase PostgreSQL (upload_status: "uploaded")
            ↓
Attempt text extraction with pdfminer / pypdf
  → If text extracted: document_category = "text_based"
  → If empty: call Gemini OCR, document_category = "scanned"
Update processing_status: "extracted"
            ↓
Parse extracted text into structured data (document_type-specific parsing)
Update processing_status: "parsed"
            ↓
Send parsed output to RAG module for chunking and embedding
```

---

## 6. Output Schema

The ingestion module writes this record to Supabase PostgreSQL:

```json
{
  "client_id": "client_uuid",
  "document_id": "document_uuid",
  "document_type": "sales_register | gstr_2b | ...",
  "document_category": "scanned | text_based",
  "extracted_text": "full raw extracted text",
  "parsed_data": {},
  "metadata": {
    "file_name": "file.pdf",
    "file_size_bytes": 204800,
    "storage_path": "relative/path/in/supabase/storage",
    "upload_status": "completed",
    "processing_status": "parsed"
  }
}
```

`parsed_data` shape is document_type-specific. Define per type when implementing.

---

## 7. Current Implementation State

The current `POST /api/clients/<gstin>/documents` endpoint handles:
- File upload ✓
- Local disk storage ✓
- Basic metadata recording ✓

Not yet implemented:
- Supabase Storage upload (files are currently stored on local disk in `uploads/`)
- Text extraction pipeline
- Parsed data generation
- RAG ingestion trigger

---

## 8. Strict Non-Goals

This module must never perform:

- GST filing logic or output generation
- Notice classification or reply drafting
- Direct calls to the GST portal
- Payment processing
- Auto-emailing of documents
- Ingestion of knowledge base files (those are ingested separately via the RAG module)
