from __future__ import annotations
import json
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from app.core.db import get_db
from app.api.deps import get_or_create_default_ca, require_client
from app.models.schemas import (
    PrerequisitesRequest, RequirementsCheckRequest,
    FilingStartRequest, FilingEditRequest, RegisterEditRequest,
)
from app.filing.prerequisites import check as check_prerequisites, SUPPORTED_FILING_TYPES
from app.filing.gstr1 import pipeline as gstr1_pipeline

router = APIRouter(prefix="/filing", tags=["filing"])

# Where generated workbooks are written (mirrors documents.UPLOAD_ROOT).
_UPLOAD_ROOT = Path(__file__).resolve().parents[3] / "uploads"


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


@router.post("/generate")
async def generate_gstr1(body: FilingStartRequest, db=Depends(get_db)):
    """
    Core GSTR-1 pipeline:
    1. Fetch the client's uploaded sales documents (raw extracted text).
    2. AI-extract transactions → data-filler → beta sales register.
    3. Validate (regex + duplicate-invoice) and flag issues for the CA.
    4. Fill the exact government GSTR-1 workbook.
    5. Return the beta register, summary, flags, CA notice, and a download route.
    """
    gstin = body.gstin.strip().upper()
    period = _normalise_period(body.period or "")

    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    client_id = require_client(cur, ca_id, gstin)

    cur.execute(
        """
        SELECT file_name, file_text
        FROM documents
        WHERE client_id = %s
          AND doc_type::text IN ('sales_register', 'sales_invoice', 'credit_note', 'debit_note', 'export_invoice')
        ORDER BY uploaded_at DESC
        """,
        (client_id,),
    )
    raw_texts = [r[1] for r in cur.fetchall() if r[1] and r[1].strip()]

    if not raw_texts:
        raise HTTPException(
            status_code=422,
            detail="No sales register or invoice documents found for this client. Upload documents first.",
        )

    out_name = f"GSTR1_{period or 'draft'}.xlsx"
    output_path = _UPLOAD_ROOT / client_id / out_name

    result = gstr1_pipeline.run(raw_texts, client_gstin=gstin, output_path=output_path)

    if not result["row_count"]:
        raise HTTPException(
            status_code=422,
            detail="Could not extract any transactions from the uploaded documents.",
        )

    return {
        "status": "generated",
        "gstin": gstin,
        "period": body.period,
        "row_count": result["row_count"],
        "summary": result["summary"],
        "beta_register": result["beta_register"],
        "flags": result["flags"],
        "ca_notice": result["ca_notice"],
        "download": f"/filing/download/{gstin}/{out_name}",
    }


@router.get("/download/{gstin}/{filename}")
async def download_workbook(gstin: str, filename: str, db=Depends(get_db)):
    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    client_id = require_client(cur, ca_id, gstin.strip().upper())

    safe_name = os.path.basename(filename)
    path = _UPLOAD_ROOT / client_id / safe_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Generated workbook not found.")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=safe_name,
    )


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


@router.post("/edit-register")
async def edit_register(body: RegisterEditRequest, db=Depends(get_db)):
    from app.services.chat_assistant import plan_beta_register_edit

    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    gstin = body.gstin.strip().upper()
    client_id = require_client(cur, ca_id, gstin)

    try:
        plan = plan_beta_register_edit(
            instruction=body.instruction,
            beta_register=body.beta_register,
            gstin=gstin,
            period=body.period,
        )
        edited_register = gstr1_pipeline.apply_edit_operations(
            body.beta_register,
            plan["operations"],
            instruction=body.instruction,
            client_gstin=gstin,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    period = _normalise_period(body.period or "")
    out_name = f"GSTR1_{period or 'draft'}.xlsx"
    rebuilt = gstr1_pipeline.rebuild(
        edited_register,
        _UPLOAD_ROOT / client_id / out_name,
    )
    return {
        "status": "updated",
        "message": plan["message"],
        "row_count": rebuilt["row_count"],
        "summary": rebuilt["summary"],
        "beta_register": rebuilt["beta_register"],
        "flags": rebuilt["flags"],
        "ca_notice": rebuilt["ca_notice"],
        "download": f"/filing/download/{gstin}/{out_name}",
    }


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
