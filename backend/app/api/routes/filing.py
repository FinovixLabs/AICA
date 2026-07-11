from __future__ import annotations
import csv
import json
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.core.db import get_db
from app.api.deps import get_or_create_default_ca, require_client
from app.models.schemas import (
    PrerequisitesRequest, RequirementsCheckRequest,
    FilingStartRequest, FilingEditRequest,
)
from app.filing.prerequisites import check as check_prerequisites, SUPPORTED_FILING_TYPES
from app.filing.gstr1.classifier import parse_csv_to_rows, classify_rows, build_summary
from app.filing.gstr1.builder import build_gstr1_json

router = APIRouter(prefix="/filing", tags=["filing"])


@router.post("/prerequisites")
async def prerequisites(body: PrerequisitesRequest, db=Depends(get_db)):
    gstin = body.gstin.strip().upper()
    filing_type = body.filing_type.strip().upper()

    if filing_type not in SUPPORTED_FILING_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported filing_type. Supported: {SUPPORTED_FILING_TYPES}")

    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    client_id = require_client(cur, ca_id, gstin)

    result = check_prerequisites(cur, client_id, filing_type)
    status_code = 200 if result.get("status") == "ready" else 422
    return result


@router.post("/classify")
async def classify_sales_register(body: FilingStartRequest, db=Depends(get_db)):
    """
    Core GSTR-1 pipeline:
    1. Fetch uploaded sales register for the client
    2. Parse CSV → normalise headers
    3. Deterministically classify each row into B2B / B2CL / B2CS / EXP / etc.
    4. Build GSTR-1 JSON
    5. Return classified tables + summary + JSON + downloadable CSV
    """
    gstin = body.gstin.strip().upper()
    period = body.period or ""

    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    client_id = require_client(cur, ca_id, gstin)

    # Fetch sales register documents
    cur.execute(
        """
        SELECT file_name, file_text, doc_type::text
        FROM documents
        WHERE client_id = %s
          AND doc_type::text IN ('sales_register', 'sales_invoice', 'credit_note', 'debit_note', 'export_invoice')
        ORDER BY uploaded_at DESC
        """,
        (client_id,),
    )
    docs = [{"file_name": r[0], "file_text": r[1], "doc_type": r[2]} for r in cur.fetchall()]

    if not docs:
        raise HTTPException(
            status_code=422,
            detail="No sales register or invoice documents found for this client. Upload documents first.",
        )

    # Get seller state code from GSTIN (first 2 digits)
    seller_state_code = gstin[:2] if len(gstin) >= 2 else None

    # Parse and classify all documents
    all_rows: list[dict] = []
    parse_errors: list[str] = []

    for doc in docs:
        file_text = doc.get("file_text") or ""
        if not file_text.strip():
            continue
        headers, rows = parse_csv_to_rows(file_text)
        if not rows:
            parse_errors.append(f"{doc['file_name']}: could not parse CSV or no data rows")
            continue
        all_rows.extend(rows)

    if not all_rows:
        raise HTTPException(
            status_code=422,
            detail=f"No parseable invoice rows found. {'; '.join(parse_errors) if parse_errors else 'Check that uploaded files are valid CSV.'}",
        )

    # Classify
    classified_tables = classify_rows(all_rows, seller_state_code=seller_state_code)
    summary = build_summary(classified_tables)

    # Convert period to MMYYYY for JSON (from YYYY-MM or MMYYYY)
    json_period = _normalise_period(period)

    # Build GSTR-1 JSON
    gstr1_json = build_gstr1_json(classified_tables, gstin=gstin, period=json_period)

    # Build classification CSV for CA review
    classification_csv = _build_classification_csv(classified_tables)

    return {
        "status": "classified",
        "gstin": gstin,
        "period": period,
        "total_rows_processed": len(all_rows),
        "summary": summary,
        "tables": {
            table: rows for table, rows in classified_tables.items()
            if table != "HSN"  # HSN is in the JSON
        },
        "gstr1_json": gstr1_json,
        "classification_csv": classification_csv,
        "parse_errors": parse_errors,
    }


@router.post("/requirements-check")
async def requirements_check(body: RequirementsCheckRequest, db=Depends(get_db)):
    from app.filing.requirement_checking import run_gstr1_requirement_check, RequirementCheckError
    gstin = body.gstin.strip().upper()
    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    client_id = require_client(cur, ca_id, gstin)

    try:
        result = run_gstr1_requirement_check(db, client_id=client_id, gstin=gstin, period=body.period)
    except RequirementCheckError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return result


@router.post("/edit-output")
async def edit_filing_output(body: FilingEditRequest, db=Depends(get_db)):
    from app.services.chat_assistant import edit_filing_output as _edit
    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    require_client(cur, ca_id, body.gstin.strip().upper())

    try:
        result = _edit(
            instruction=body.instruction,
            filing_json=body.filing_json,
            filing_csv=body.filing_csv,
            gstin=body.gstin,
            period=body.period,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {"status": "updated", **result}


@router.post("/edit-output-stream")
async def edit_filing_output_stream(body: FilingEditRequest, db=Depends(get_db)):
    from app.services.chat_assistant import stream_edit_filing_output
    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    require_client(cur, ca_id, body.gstin.strip().upper())

    def event_stream():
        for token in stream_edit_filing_output(
            instruction=body.instruction,
            filing_json=body.filing_json,
            filing_csv=body.filing_csv,
            gstin=body.gstin,
            period=body.period,
        ):
            if token:
                yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/reconcile")
async def reconcile(db=Depends(get_db)):
    return {"rows": [], "output": {"rows": []}, "status": "pending"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalise_period(period: str) -> str:
    """Convert YYYY-MM → MMYYYY for GST portal, or pass through if already MMYYYY."""
    if not period:
        return ""
    if "-" in period:
        parts = period.split("-")
        if len(parts) == 2:
            year, month = parts[0], parts[1]
            if len(year) == 4:
                return f"{month}{year}"
    return period


def _build_classification_csv(tables: dict) -> str:
    """Build a flat CSV showing all classified rows with their GSTR-1 table assignment."""
    all_rows = []
    for table_name, rows in tables.items():
        if table_name == "HSN":
            continue
        for row in rows:
            flat = {"gstr1_table": table_name}
            for k, v in row.items():
                if k != "gstr1_table":
                    flat[k] = v
            all_rows.append(flat)

    if not all_rows:
        return ""

    # Collect all keys in order
    fieldnames: list[str] = ["gstr1_table"]
    for row in all_rows:
        for k in row:
            if k not in fieldnames:
                fieldnames.append(k)

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(all_rows)
    return output.getvalue()
