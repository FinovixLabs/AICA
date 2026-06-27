# Notice Module Architecture

## 1. Module Scope

The notice module is responsible for:

- Rule-based classification of uploaded GST notices
- RAG-assisted structured reply drafting
- User review and approval of final reply

The notice module does **not** handle:

- File upload or storage
- OCR or raw text extraction (these are done by the Document Ingestion Module)
- GST portal submission
- Legal representation or demand payment

---

## 2. Module Boundary

The notice module starts after the notice PDF has been uploaded and text has been extracted.

Text extraction order:
1. pdfminer / pypdf (primary)
2. Gemini OCR (fallback if primary fails)

The notice module receives extracted plain text and works from that. It does not re-run extraction.

---

## 3. Endpoints

| Method | Path | Input | Purpose |
|---|---|---|---|
| POST | /api/notices/classify | multipart/form-data: gstin + file | Extract notice metadata |
| POST | /api/notices/draft-reply | JSON: gstin + noticeId | Generate structured reply |
| POST | /api/notices/approve | JSON: gstin + noticeId + html + version | Persist approved reply |

---

## 4. Classification Workflow

Classification is **rule-based only**. No LLM is used for classification.

Steps:
1. Receive PDF upload + GSTIN
2. Extract text from PDF (pdfminer → Gemini fallback)
3. Apply regex and keyword pattern matching to extract metadata fields
4. Return full metadata shape — empty string for any field that cannot be extracted

---

## 5. Notice Metadata Schema

Always return all fields. Use empty string if a field cannot be extracted.

```json
{
  "id": "notice reference or DIN number",
  "type": "demand | scrutiny | show_cause | clarification | audit | attachment",
  "template": "matched template identifier",
  "section": "GST Act section reference",
  "demand": "monetary amount demanded",
  "issue": "core compliance issue raised",
  "due": "response due date",
  "fileName": "uploaded file name"
}
```

---

## 6. GST Section References

Recognise these sections during extraction (list is not exhaustive):

| Section | Subject |
|---|---|
| Section 61 | Scrutiny of returns |
| Section 65 | Audit by tax authorities |
| Section 67 | Inspection, search and seizure |
| Section 73 | Tax not paid or short paid — non-fraud |
| Section 74 | Tax not paid or short paid — fraud / suppression |
| Section 75 | General provisions for demand and recovery |
| Section 76 | Tax collected but not paid to government |
| Section 79 | Recovery of tax |
| Section 83 | Provisional attachment of property |
| Rule 86A | Blocking of ITC in electronic credit ledger |

---

## 7. Draft Reply Workflow

1. Receive GSTIN + noticeId
2. Fetch the classified notice metadata from the database
3. Retrieve relevant chunks from the knowledge base via ensemble retrieval (RAG module)
4. Retrieve the approved reply format template from the knowledge base
5. Construct AI context from:
   - Notice metadata
   - Retrieved knowledge base chunks
   - Reply format template
6. Generate structured reply HTML following the format template exactly
7. Return draftHtml + refs list

The AI must not draft a reply until the knowledge base format document is available.

---

## 8. AI Grounding Rules for Reply Drafting

The AI must:

- Use only the notice metadata and retrieved knowledge base chunks
- Always cite the circular, notification, or section number for every legal claim
- Address each point in the notice individually
- Never hallucinate GST law, circular numbers, or section references
- Never invent case precedents
- Return only the structured draftHtml — no conversational text

If a required knowledge base document is missing:
- Return an error stating which KB document is needed
- Do not attempt to draft without it

---

## 9. Reply Output Format

```json
{
  "meta": {
    "id": "notice_id",
    "type": "notice_type",
    "section": "section_reference"
  },
  "draftHtml": "<formatted HTML reply following KB template>",
  "refs": [
    {
      "chunk_id": "chunk_identifier",
      "source": "source_file_name",
      "excerpt": "relevant text excerpt"
    }
  ]
}
```

---

## 10. Approval Workflow

- version increments on each approval call
- savedAt is always a UTC ISO string via _now_iso()
- Approved reply HTML is persisted against the notice record

Return shape:

```json
{
  "version": 2,
  "savedAt": "2026-06-19T00:00:00+00:00"
}
```

---

## 11. Strict Non-Goals

This module must never perform:

- GST portal submission or auto-response
- Legal representation
- Demand payment computation or challan generation
- Income tax or MCA notice handling
- Auto email or WhatsApp sending of replies
- Notice tracking dashboards
- SLA monitoring
