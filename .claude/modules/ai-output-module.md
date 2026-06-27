# AI Output Module Architecture

## 1. Purpose

This module defines the cross-cutting rules that govern all AI-generated output in AICA.

These rules apply to every AI output produced by the filing module, notice module, and any future module.

No module may override these rules without explicit user approval.

---

## 2. Core Grounding Principle

The AI must use only the context provided to it.

Permitted sources:
- Parsed document data fetched from Supabase PostgreSQL
- Extracted text passed in the request context
- Knowledge base chunks retrieved from the RAG module
- Approved fillable format templates from the knowledge base

Prohibited:
- External knowledge from training data (GST law, circular numbers, ITC rules, etc.) unless it is explicitly present in retrieved chunks
- Assumptions about missing values
- Invented figures, dates, GSTINs, party names, or section references

---

## 3. Missing Field Protocol

When any required field cannot be filled from available context, the AI must return:

```json
{
  "missing_field": "field_name",
  "source_document_required": "document_that_would_provide_this_field",
  "reason": "Clear explanation of why the field cannot be filled"
}
```

The AI must never fill a field with a placeholder, zero, or estimated value when the source data is absent.

---

## 4. Output Format Standards

| Module | Required Output Format |
|---|---|
| Filing module | JSON only — structured filing fields |
| Notice module | HTML (draftHtml) + JSON refs list |
| Issue detection | JSON — source-linked issue objects |
| Validation errors | JSON — blocked status with missing_documents list |

No AI output may be returned as unstructured plain text where a structured format is defined.

---

## 5. Citation Requirements

Every legal claim in a notice reply must include a citation.

Permitted citations:
- GST Act section number (e.g. "Section 73(1)")
- CBIC circular number and date
- GST notification number
- Rule reference (e.g. "Rule 86A")

The AI must not write phrases like "as per GST law" or "according to the Act" without citing a specific provision.

---

## 6. Hard Constraints on AI Behaviour

The AI must never:

- Auto-submit to the GST portal
- Generate tax advisory opinions beyond the scope of the current document context
- Invent missing values, invoices, amounts, or tax figures
- Bypass prerequisite validation to proceed with filing
- Accept user-provided text as a substitute for missing source documents
- Make assumptions about the user's GST registration type, state, or scheme

---

## 7. Approval Gate

Every AI-generated output must pass through a user approval step before it is treated as final.

The system must never:
- Auto-apply AI output to a filing record without user review
- Treat a draft reply as approved unless the `/api/notices/approve` endpoint is called
- Mark a filing as complete unless the user explicitly approves the final JSON output

`approval_required: true` must be present in all final AI output objects.

---

## 8. Scope Boundary

This module governs output rules only.

It does not define:
- How documents are ingested (Document Ingestion Module)
- How retrieval is performed (RAG Module)
- How the filing or notice workflow is structured (their respective modules)
