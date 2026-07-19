"""GSTR-2B Reconciliation and IMS Management API (spec giu.txt).

Three functional areas with module-specific matching contracts:
  - gstr2b       : purchase register vs GSTR-2B, two-sided reconciliation.
  - ims_inward   : purchase register vs IMS Inward, then local CA action status.
  - ims_outward  : sales register vs IMS Outward, grouped by recipient action.

Source files are NOT uploaded here. The CA uploads them once through the
Documents workspace (tagged purchase_register / gstr_2b / ims_inward /
ims_outward) into the base `documents` table; reconciliation just references an
existing document by id. Flow:

  pick document(s) -> preview + confirm column map + doc-type map -> run
  -> results -> module-specific actions -> Download Excel.

Tenancy follows the rest of the app: the pseudo default CA plus require_client.
Uninstall: migrations/manual/999_drop_recon.sql and delete app/recon/.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from psycopg2 import Error as DatabaseError, errors as pg_errors

from app.api.deps import get_or_create_default_ca, require_client
from app.api.routes.documents import UPLOAD_ROOT
from app.core.db import get_db
from app.recon import excel, messages, service, store
from app.recon.core.errors import ParseError, ReconError
from app.recon.core.normalize import norm_text
from app.recon.schema_fields import missing_required_for_module

router = APIRouter(prefix="/recon", tags=["recon"])

_TWO_SIDED = ("gstr2b", "ims_inward")
_ALL_MODULES = ("gstr2b", "ims_inward", "ims_outward")

# Which document type feeds each side of each module. 'pr' is the register side
# (purchase register, or the sales register for outward); 'cp' is the counterparty
# file (2B / IMS).
MODULE_SOURCES: dict[str, dict[str, tuple[str, str]]] = {
    "gstr2b": {"pr": ("purchase_register", "Purchase Register"), "cp": ("gstr_2b", "GSTR-2B")},
    "ims_inward": {"pr": ("purchase_register", "Purchase Register"), "cp": ("ims_inward", "IMS Inward")},
    "ims_outward": {"pr": ("sales_register", "Sales Register"), "cp": ("ims_outward", "IMS Outward")},
}


# ── request bodies ────────────────────────────────────────────────────────────
class PreviewRequest(BaseModel):
    gstin: str
    module: str
    document_id: str
    sheet: str | None = None


class DocTypesRequest(BaseModel):
    gstin: str
    document_id: str
    doc_type_header: str
    sheet: str | None = None


class RunRequest(BaseModel):
    gstin: str
    period: str | None = None
    pr_document_id: str
    cp_document_id: str
    pr_map: dict[str, str | None] = {}
    cp_map: dict[str, str | None] = {}
    doc_type_map: dict[str, str] = {}
    pr_sheet: str | None = None
    cp_sheet: str | None = None
    pr_date_order: str | None = None
    cp_date_order: str | None = None


class OutwardReconcileRequest(BaseModel):
    gstin: str
    sr_document_id: str
    ims_document_id: str
    sr_map: dict[str, str | None] = {}
    ims_map: dict[str, str | None] = {}
    doc_type_map: dict[str, str] = {}
    sr_sheet: str | None = None
    ims_sheet: str | None = None
    sr_date_order: str | None = None
    ims_date_order: str | None = None


class DraftMessageRequest(BaseModel):
    gstin: str
    record: dict[str, Any] = {}


class IgnoreRequest(BaseModel):
    ignored: bool = True


class InwardActionRequest(BaseModel):
    action: Literal["accept", "reject", "hold"]


# ── helpers ───────────────────────────────────────────────────────────────────
def _check_module(module: str, allowed: tuple[str, ...]) -> None:
    if module not in allowed:
        raise HTTPException(status_code=404, detail=f"Unknown module {module!r}")


def _client(cur, gstin: str) -> str:
    ca_id = get_or_create_default_ca(cur)
    return require_client(cur, ca_id, gstin.upper())


def _abs_path(storage_path: str) -> str:
    root = Path(UPLOAD_ROOT).resolve()
    candidate = (root / storage_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise HTTPException(status_code=400, detail="Stored document path is invalid")
    if not candidate.is_file():
        raise HTTPException(
            status_code=410,
            detail="Stored document file is unavailable on this server",
        )
    return str(candidate)


def _norm_doc_type_map(raw_map: dict[str, str]) -> dict[str, str]:
    """The doc-type map is keyed on the CA's confirmed raw value; canonicalize()
    looks it up by norm_text(raw), so normalize the keys here."""
    return {norm_text(k): v for k, v in raw_map.items() if v}


def _require_document(cur, document_id: str, client_id: str) -> dict[str, Any]:
    doc = store.get_document(cur, document_id, client_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


# ── source documents (from the Documents workspace) ───────────────────────────
@router.get("/{module}/sources")
async def sources(module: str, gstin: str = Query(...), db=Depends(get_db)):
    """The document type each side needs, plus the client's matching uploads.

    Drives the document-picker: the CA uploads files in the Documents workspace,
    then chooses them here.
    """
    _check_module(module, _ALL_MODULES)
    cur = db.cursor()
    client_id = _client(cur, gstin)
    out: dict[str, Any] = {"module": module, "sides": {}}
    for side, (doc_type, label) in MODULE_SOURCES[module].items():
        out["sides"][side] = {
            "doc_type": doc_type,
            "label": label,
            "documents": store.list_documents_by_type(cur, client_id, [doc_type]),
        }
    return out


@router.post("/preview")
async def preview(body: PreviewRequest, db=Depends(get_db)):
    """Read a chosen document just enough to drive the mapping UI."""
    _check_module(body.module, _ALL_MODULES)
    cur = db.cursor()
    client_id = _client(cur, body.gstin)
    doc = _require_document(cur, body.document_id, client_id)
    try:
        prev = service.preview(_abs_path(doc["storage_path"]), body.module, sheet=body.sheet)
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    doc_type_values: list[dict[str, Any]] = []
    suggested_doc_col = prev["suggested_map"].get("doc_type")
    if suggested_doc_col:
        doc_type_values = service.doc_type_options(
            _abs_path(doc["storage_path"]), {"doc_type": suggested_doc_col},
            body.module, sheet=prev["sheet_name"],
        )
    return {
        "document_id": doc["id"],
        "file_name": doc["file_name"],
        "headers": prev["headers"],
        "sample_rows": prev["sample_rows"],
        "sample_row_numbers": prev["sample_row_numbers"],
        "row_count": prev["row_count"],
        "sheet_name": prev["sheet_name"],
        "sheet_names": prev["sheet_names"],
        "header_row": prev["header_row"],
        "header_end_row": prev["header_end_row"],
        "omitted_count": prev["omitted_count"],
        "omitted_rows": prev["omitted_rows"],
        "suggested_map": prev["suggested_map"],
        "doc_type_values": doc_type_values,
    }


@router.post("/{module}/doc-types")
async def doc_types(module: str, body: DocTypesRequest, db=Depends(get_db)):
    """Distinct raw doc-type values for a chosen column, with canonical
    suggestions — refreshed when the CA maps a different column to Document Type."""
    _check_module(module, _ALL_MODULES)
    cur = db.cursor()
    client_id = _client(cur, body.gstin)
    doc = _require_document(cur, body.document_id, client_id)
    values = service.doc_type_options(
        _abs_path(doc["storage_path"]), {"doc_type": body.doc_type_header},
        module, sheet=body.sheet,
    )
    return {"doc_type_values": values}


# ── run (two-sided reconciliation) ────────────────────────────────────────────
@router.post("/{module}/run")
async def run(module: str, body: RunRequest, db=Depends(get_db)):
    _check_module(module, _TWO_SIDED)
    cur = db.cursor()
    client_id = _client(cur, body.gstin)

    pr_doc = _require_document(cur, body.pr_document_id, client_id)
    cp_doc = _require_document(cur, body.cp_document_id, client_id)

    for side, label, mapping in (
        ("pr", "purchase register", body.pr_map),
        ("cp", "2B/IMS file", body.cp_map),
    ):
        missing = missing_required_for_module(mapping, module, side)
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Map these {label} fields before running: {', '.join(missing)}",
            )

    doc_type_map = _norm_doc_type_map(body.doc_type_map)
    run_period = body.period if module == "gstr2b" else None

    try:
        pr_rows, pr_order, pr_evidence = service.build_norm_rows(
            _abs_path(pr_doc["storage_path"]), body.pr_map,
            module=module, doc_type_map=doc_type_map,
            date_order=body.pr_date_order, sheet=body.pr_sheet,
        )
        cp_rows, cp_order, cp_evidence = service.build_norm_rows(
            _abs_path(cp_doc["storage_path"]), body.cp_map,
            module=module, doc_type_map=doc_type_map,
            date_order=body.cp_date_order, sheet=body.cp_sheet,
        )
        outcome = service.run_reconcile(pr_rows, cp_rows, module=module, period=run_period)
    except (ParseError, ReconError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    serialized = service.serialize_outcome(outcome, module=module)

    config = {
        "pr_map": body.pr_map,
        "cp_map": body.cp_map,
        "doc_type_map": body.doc_type_map,
        "pr_date_order": pr_order,
        "cp_date_order": cp_order,
        "pr_date_evidence": pr_evidence,
        "cp_date_evidence": cp_evidence,
        "pr_file": pr_doc["file_name"],
        "cp_file": cp_doc["file_name"],
    }
    try:
        run_id = store.create_run(
            cur,
            client_id=client_id,
            module=module,
            period=run_period,
            pr_document_id=body.pr_document_id,
            cp_document_id=body.cp_document_id,
            config=config,
            totals=serialized["totals"],
            excluded=serialized["excluded"],
            engine_version=serialized["engine_version"],
        )
        results = store.insert_results(cur, run_id, serialized["results"])
    except (pg_errors.UndefinedTable, pg_errors.InvalidSchemaName) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Reconciliation storage is not installed in the configured database. "
                "Apply backend/migrations/004_create_recon_schema.sql, then run reconciliation again."
            ),
        ) from exc
    except pg_errors.UndefinedColumn as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "IMS Inward action storage is not installed. Apply "
                "backend/migrations/006_add_ims_inward_action_status.sql, then run again."
            ),
        ) from exc
    except DatabaseError as exc:
        raise HTTPException(
            status_code=503,
            detail="Reconciliation was calculated but could not be saved because the database rejected the result.",
        ) from exc

    return {
        "run_id": run_id,
        "module": module,
        "period": run_period,
        "results": results,
        "excluded": serialized["excluded"],
        "totals": serialized["totals"],
        "config": config,
        "engine_version": serialized["engine_version"],
    }


# ── IMS Outward: match against the Sales Register, bucket by IMS status ────────
# Not the two-sided engine. The client's outward invoices (with the recipient's
# IMS action) are matched against the Sales Register on Recipient GSTIN + invoice
# value, then grouped into Accepted / Rejected / Pending terminals. Rejected and
# Pending rows offer Take Action (draft-message below); B2C rows (no GSTIN) are
# skipped.
@router.post("/ims_outward/reconcile")
async def outward_reconcile(body: OutwardReconcileRequest, db=Depends(get_db)):
    cur = db.cursor()
    client_id = _client(cur, body.gstin)

    sr_doc = _require_document(cur, body.sr_document_id, client_id)
    ims_doc = _require_document(cur, body.ims_document_id, client_id)

    for side, label, mapping in (
        ("pr", "sales register", body.sr_map),
        ("cp", "IMS Outward file", body.ims_map),
    ):
        missing = missing_required_for_module(mapping, "ims_outward", side)
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Map these {label} fields before matching: {', '.join(missing)}",
            )

    doc_type_map = _norm_doc_type_map(body.doc_type_map)
    try:
        sr_rows, _, _ = service.build_norm_rows(
            _abs_path(sr_doc["storage_path"]), body.sr_map,
            module="ims_outward", doc_type_map=doc_type_map,
            date_order=body.sr_date_order, sheet=body.sr_sheet,
        )
        ims_rows, _, _ = service.build_norm_rows(
            _abs_path(ims_doc["storage_path"]), body.ims_map,
            module="ims_outward", doc_type_map=doc_type_map,
            date_order=body.ims_date_order, sheet=body.ims_sheet,
        )
        result = service.match_outward(sr_rows, ims_rows)
    except (ParseError, ReconError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "module": "ims_outward",
        "sr_file": sr_doc["file_name"],
        "ims_file": ims_doc["file_name"],
        **result,
    }


@router.post("/ims_outward/send-email")
async def outward_send_email(body: DraftMessageRequest, db=Depends(get_db)):
    """Email-delivery hook for a Rejected/Pending record. The drafting path is
    live (draft-message); actual send awaits Email/GSP integration, so this is a
    deliberate, explicit 501 rather than a silent no-op."""
    raise HTTPException(
        status_code=501,
        detail="Email delivery is not configured yet. Use Take Action to draft and copy the message.",
    )


@router.post("/draft-message")
async def draft_message(body: DraftMessageRequest, db=Depends(get_db)):
    """Take Action for a single record with no persisted run (IMS Outward
    client intimation, spec 10.4). Stateless: nothing is stored."""
    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    client_id = require_client(cur, ca_id, body.gstin.upper())
    cur.execute("SELECT legal_name FROM clients WHERE id = %s", (client_id,))
    row = cur.fetchone()
    draft = messages.generate_message(body.record, client_name=row[0] if row else None)
    return {"message": draft}


# ── runs / results ────────────────────────────────────────────────────────────
@router.get("/{module}/runs")
async def list_runs(module: str, gstin: str = Query(...), db=Depends(get_db)):
    _check_module(module, _ALL_MODULES)
    cur = db.cursor()
    client_id = _client(cur, gstin)
    return store.list_runs(cur, client_id, module)


@router.get("/runs/{run_id}")
async def get_run(run_id: str, gstin: str = Query(...), db=Depends(get_db)):
    cur = db.cursor()
    client_id = _client(cur, gstin)
    run_meta = store.get_run(cur, run_id, client_id)
    if run_meta is None:
        raise HTTPException(status_code=404, detail="Run not found")
    results = store.list_results(cur, run_id, client_id) or []
    return {**run_meta, "results": results}


@router.post("/results/{result_id}/ims-action")
async def set_inward_action(
    result_id: str, body: InwardActionRequest, gstin: str = Query(...), db=Depends(get_db)
):
    """Save the CA's local Accept / Reject / Hold decision for IMS Inward."""
    cur = db.cursor()
    client_id = _client(cur, gstin)
    try:
        updated = store.set_result_ims_action(cur, result_id, client_id, body.action)
    except pg_errors.UndefinedColumn as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "IMS Inward action storage is not installed. Apply "
                "backend/migrations/006_add_ims_inward_action_status.sql."
            ),
        ) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="IMS Inward result not found")
    return updated


@router.post("/runs/{run_id}/ims-actions/reset")
async def reset_inward_actions(run_id: str, gstin: str = Query(...), db=Depends(get_db)):
    """Restore every action in an IMS Inward run to Not actioned."""
    cur = db.cursor()
    client_id = _client(cur, gstin)
    try:
        updated = store.reset_run_ims_actions(cur, run_id, client_id)
    except pg_errors.UndefinedColumn as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "IMS Inward action storage is not installed. Apply "
                "backend/migrations/006_add_ims_inward_action_status.sql."
            ),
        ) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="IMS Inward run not found")
    return {"run_id": run_id, "ims_action": "not_actioned", "updated": updated}


@router.post("/runs/{run_id}/ims-actions/accept-matched")
async def accept_matched_inward_actions(
    run_id: str, gstin: str = Query(...), db=Depends(get_db)
):
    """Accept every still-unactioned Matched row in one IMS Inward run."""
    cur = db.cursor()
    client_id = _client(cur, gstin)
    try:
        result_ids = store.accept_matched_inward_results(cur, run_id, client_id)
    except pg_errors.UndefinedColumn as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "IMS Inward action storage is not installed. Apply "
                "backend/migrations/006_add_ims_inward_action_status.sql."
            ),
        ) from exc
    if result_ids is None:
        raise HTTPException(status_code=404, detail="IMS Inward run not found")
    return {"run_id": run_id, "ims_action": "accept", "updated": len(result_ids), "result_ids": result_ids}


@router.post("/results/{result_id}/ignore")
async def ignore_result(
    result_id: str, body: IgnoreRequest, gstin: str = Query(...), db=Depends(get_db)
):
    """Ignore removes a transaction from the unresolved-problems box (spec 6.5).
    It stays in the contemporary list and Excel; only its ignored flag changes."""
    cur = db.cursor()
    client_id = _client(cur, gstin)
    if not store.set_result_ignored(cur, result_id, client_id, body.ignored):
        raise HTTPException(status_code=404, detail="Result not found")
    return {"id": result_id, "ignored": body.ignored}


@router.post("/results/{result_id}/message")
async def message_result(result_id: str, gstin: str = Query(...), db=Depends(get_db)):
    """Take Action: generate a pre-filled client message for one transaction
    (spec 6.4 / 10.4). Persisted so the CA can review it on return."""
    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    client_id = require_client(cur, ca_id, gstin.upper())

    result = store.get_result(cur, result_id, client_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")

    cur.execute("SELECT legal_name FROM clients WHERE id = %s", (client_id,))
    row = cur.fetchone()
    client_name = row[0] if row else None

    draft = messages.generate_message(result["payload"], client_name=client_name)
    store.set_result_message(cur, result_id, client_id, draft)
    return {"id": result_id, "message": draft}


# ── Excel download (spec 7) ───────────────────────────────────────────────────
@router.get("/runs/{run_id}/excel")
async def download_excel(run_id: str, gstin: str = Query(...), db=Depends(get_db)):
    cur = db.cursor()
    client_id = _client(cur, gstin)
    run_meta = store.get_run(cur, run_id, client_id)
    if run_meta is None:
        raise HTTPException(status_code=404, detail="Run not found")
    results = store.list_results(cur, run_id, client_id) or []

    workbook = excel.build_workbook(
        results, run_meta.get("excluded") or [],
        module=run_meta["module"], period=run_meta.get("period"),
    )
    filename = excel.filename_for(run_meta["module"], run_meta.get("period"))
    return Response(
        content=workbook,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
