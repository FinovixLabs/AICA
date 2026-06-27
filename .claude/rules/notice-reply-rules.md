# Notice Reply Rules

## Classification — Rule-Based Only
Notice classification uses regex and keyword pattern matching. No LLM for classification.

Fields to extract from PDF text:
- id: notice reference number (regex: DIN, notice number patterns)
- type: notice category (demand, scrutiny, clarification, show cause, etc.)
- template: matched template identifier
- section: GST Act section reference — recognise (not exhaustive):
  - Section 61 (scrutiny of returns), Section 65 (audit), Section 67 (inspection/search/seizure)
  - Section 73 (tax not paid, non-fraud), Section 74 (tax not paid, fraud/suppression)
  - Section 75 (general demand/recovery), Section 76 (tax collected but not paid)
  - Section 79 (recovery), Section 83 (provisional attachment), Rule 86A (ITC block)
- demand: monetary amount demanded
- issue: the core compliance issue raised
- due: response due date
- fileName: the uploaded filename

Always return all fields — use empty string for any field that cannot be extracted.

## Draft Reply Format
Draft replies must follow the structured format defined in the knowledge base.
Do not draft replies until the format document is available in the knowledge base.

The draft reply must:
- Address each point in the notice individually
- Cite the relevant GST circular, notification, or section number for every legal claim
- Be returned as formatted HTML (draftHtml), not plain text
- Include a refs list of source chunks used

## Endpoints
- POST /api/notices/classify — multipart/form-data; fields: gstin (required), file (required)
- POST /api/notices/draft-reply — JSON body; fields: gstin (required), noticeId (required)
- POST /api/notices/approve — JSON body; fields: gstin, noticeId, html, version (all required)

## Approval
- version increments on each approve call
- savedAt: UTC ISO string via _now_iso()
- Return: {"version": N, "savedAt": "..."}
