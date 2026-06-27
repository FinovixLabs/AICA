# Filing Module Architecture

## 1. Module Scope

The filing module is responsible for:

- Document prerequisite validation
- GST filing preparation
- Cross-document issue detection and user review
- AI field output generation (structured JSON)

The filing module does **not** handle:

- File upload
- File storage
- Text extraction or OCR
- Parsed-data creation

These are handled by the **Document Ingestion Module** before this module is triggered.

---

## 2. Supabase Structure

| Purpose | Supabase Component |
|---|---|
| Store original uploaded files | Supabase Storage |
| Store file metadata, extracted text, and parsed data | Supabase PostgreSQL |

The filing module reads only from Supabase PostgreSQL. It does not write to Supabase Storage.

---

## 3. Input from Document Ingestion Module

The Document Ingestion Module delivers processed output with this shape:

```json
{
  "client_id": "client_identifier",
  "document_id": "document_identifier",
  "document_type": "sales_register | purchase_register | gstr_2b | invoice | challan | other",
  "document_category": "scanned | text_based",
  "extracted_text": "raw extracted text",
  "parsed_data": {},
  "metadata": {
    "file_name": "file.pdf",
    "upload_status": "completed",
    "processing_status": "parsed"
  }
}
```

The filing module must not re-run extraction or parsing. It only consumes this output.

---

## 4. Filing Selection

The user selects the GST filing type.

Supported types:

- GSTR-1
- GSTR-3B

After selection, the system checks the selected type against the hardcoded prerequisite list.

---

## 5. Hardcoded Prerequisite List

```json
{
  "GSTR_1": [
    "sales_invoice",
    "credit_note",
    "debit_note",
    "customer_master"
  ],
  "GSTR_3B": [
    "sales_register",
    "purchase_register",
    "itc_register",
    "gstr_2b",
    "payment_challan"
  ]
}
```

This list is hardcoded in the backend. It must not be user-configurable in MVP1.

---

## 6. Document Validation Workflow

1. Fetch the prerequisite list for the selected filing type.
2. Fetch available documents from Supabase PostgreSQL for the client and period.
3. Compare required vs available.
4. If any document is missing → stop and return blocked error:

```json
{
  "status": "blocked",
  "reason": "missing_required_documents",
  "missing_documents": ["gstr_2b", "payment_challan"],
  "next_action": "Upload the missing documents through the Document Ingestion Lab."
}
```

5. If all documents are present → proceed to filing preparation.

---

## 7. Client Data Fetch

After document validation passes, fetch client details from Supabase PostgreSQL:

- Client name, GSTIN, business name
- Filing period
- Registration type, state code, return filing category
- Existing document records
- Previously processed filing data

Combine client details with validated document data before AI processing.

---

## 8. AI Data Processing and Issue Detection

The AI Processing Layer reads all required document data and:

- Compares values across documents (e.g. ITC in purchase register vs GSTR-2B)
- Identifies mismatches, missing fields, filing risks, unsupported values
- Traces every issue back to the source document

Each issue must be source-linked:

```json
{
  "issue_type": "data_mismatch",
  "field": "eligible_itc",
  "problem": "ITC value in purchase register does not match GSTR-2B.",
  "source_documents": ["purchase_register", "gstr_2b"],
  "recommended_action": "Review ITC reconciliation before filing."
}
```

The AI must not guess or fill values at this stage. Detection only.

---

## 9. Issue Resolution Box

Detected issues are sent to the issue-resolution interface.

The user must be able to:

- View all detected issues with source references
- Ask questions via the active chat box
- Approve or reject each resolution
- Continue only after all issues are approved

The system must not proceed to drafting until the user approves.

---

## 10. Filing Preparation and AI Drafting

After issue approval:

1. Fetch parsed data of required documents from Supabase PostgreSQL.
2. Fetch the relevant fillable GST filing format from the knowledge base (RAG module).
3. Construct AI context from:
   - Selected filing type
   - Parsed document data
   - Extracted text where required
   - Fillable GST format from knowledge base
   - Prerequisite validation status
   - Approved issue resolutions

The AI Drafting Layer generates the final structured filing output using only this context.

---

## 11. AI Grounding Rules

The AI must:

- Use only the parsed data fetched from Supabase
- Use only the extracted text provided in context
- Use only the fillable format from the knowledge base
- Never assume or invent missing values
- Never use external knowledge unless explicitly approved

When any field cannot be filled:

```json
{
  "missing_field": "field_name",
  "source_document_required": "required_document_name",
  "reason": "Why this field cannot be filled"
}
```

---

## 12. AI Output Format

Final output is JSON only:

```json
{
  "filing_type": "GSTR_3B",
  "client_id": "client_identifier",
  "filing_period": "month_year",
  "status": "draft_ready_for_approval",
  "fields": {
    "outward_taxable_supplies": 0,
    "eligible_itc": 0,
    "tax_payable": 0
  },
  "issues_resolved": [],
  "missing_fields": [],
  "source_documents_used": ["sales_register", "purchase_register", "gstr_2b", "payment_challan"],
  "approval_required": true
}
```

If filing is incomplete:

```json
{
  "filing_type": "GSTR_3B",
  "status": "incomplete",
  "fields": {},
  "missing_fields": [
    {
      "missing_field": "eligible_itc",
      "source_document_required": "gstr_2b",
      "reason": "GSTR-2B data is required to determine eligible ITC."
    }
  ],
  "source_documents_used": []
}
```

---

## 13. Final Approval

The output is sent to the user for approval. The system must not auto-submit to the GST portal.

`approval_required: true` must always be present in the final output.

---

## 14. Strict Non-Goals

This module must never perform:

- File upload, OCR, or raw text extraction
- Document ingestion or parsing
- GST portal submission or auto-filing
- Payment processing or challan generation
- Client billing
- WhatsApp integration or auto email reminders
- MCA or income tax filing
- Advanced analytics
- Firm management or mobile app workflows
