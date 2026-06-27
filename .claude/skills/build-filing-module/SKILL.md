# Filing Module Architecture

## 1. Module Scope

The filing module is responsible only for:

* Document validation and checking
* GST filing preparation
* AI field output generation

The filing module does **not** handle file upload.

File upload, file storage, text extraction, and parsed-data storage are managed separately before this module is triggered.

---

## 2. Supabase Structure

The system uses Supabase in two ways:

| Purpose                                              | Supabase Component         |
| ---------------------------------------------------- | -------------------------- |
| Store original uploaded files                        | Supabase Storage           |
| Store file metadata, extracted text, and parsed data | Supabase Postgres Database |

The filing module should fetch required document metadata, extracted text, and parsed structured data from Supabase Postgres.

Original files may be referenced from Supabase Storage only when needed.

---

## 3. Filing Selection Workflow

The user selects the GST filing type to prepare.

Supported filing examples:

* GSTR-1
* GSTR-3B

After the filing type is selected, the system checks the selected filing against a hardcoded prerequisite document list.

---

## 4. Hardcoded Prerequisite List

The prerequisite list defines which documents must be available before a GST filing can be prepared.

Example:

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

---

## 5. Document Validation Workflow

For the selected filing type:

1. Fetch the required prerequisite list.
2. Fetch available documents from Supabase Postgres.
3. Compare required documents with available documents.
4. Identify whether all required documents are present.

### If documents are missing:

The system must return a validation error.

The error should include:

* Filing type selected
* Missing document names
* Message requesting the user to upload the missing documents through the separate upload module

### If all documents are available:

The system proceeds to GST filing preparation.

---

## 6. Filing Preparation Workflow

Once all prerequisite documents are available:

* Fetch the parsed data of the required documents from Supabase Postgres.
* Fetch the relevant fillable GST filing format from the knowledge base.
* Prepare the AI context using:
  * Selected filing type
  * Parsed document data
  * Extracted document text where required
  * Fillable GST filing format
  * Prerequisite validation status

---

## 7. AI Grounding Rules

The AI must strictly follow these rules:

* Use only the parsed data fetched from Supabase.
* Use only the extracted text provided in the filing context.
* Use only the fillable format provided from the knowledge base.
* Do not assume missing values.
* Do not invent tax figures, invoice values, GSTINs, dates, party names, ITC values, liability values, or filing fields.
* Do not use external knowledge unless explicitly allowed.
* If required data is missing, the AI must not guess.

When any field cannot be filled, the AI must return:

```json
{
  "missing_field": "field_name",
  "source_document_required": "required_document_name",
  "reason": "Explanation of why the field cannot be filled"
}
```

---

## 8. AI Output Format

The generated AI output must be in JSON format only.

The JSON output should represent the completed GST filing fields according to the selected filing type and the provided fillable format.

Example structure:

```json
{
  "filing_type": "GSTR_3B",
  "status": "completed",
  "fields": {
    "outward_taxable_supplies": null,
    "eligible_itc": null,
    "tax_payable": null
  },
  "missing_fields": [],
  "source_documents_used": [
    "sales_register",
    "purchase_register",
    "gstr_2b"
  ]
}
```

If the filing cannot be completed due to missing or insufficient data, return:

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

## 9. Final Output Requirement

The filing module must generate a structured JSON output only after:

* Filing type is selected
* Required prerequisite documents are validated
* Parsed document data is fetched from Supabase
* Fillable GST format is fetched from the knowledge base
* AI fills the format using only the provided context

The output must be traceable, structured, and grounded in the available documents.
