from __future__ import annotations
import os
import re
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from app.core.db import get_db
from app.api.deps import get_or_create_default_ca, require_client, human_size
from app.services.uploading import extract_and_clean


def secure_filename(filename: str) -> str:
    filename = filename.strip().replace(" ", "_")
    filename = re.sub(r"[^\w\s\-.]", "", filename)
    filename = re.sub(r"\.{2,}", ".", filename)
    return filename or "upload"


router = APIRouter(prefix="/clients", tags=["documents"])

UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads")

_VALID_DOC_TYPES = {
    'sales_register', 'sales_invoice', 'debit_note', 'credit_note',
    'export_invoice', 'shipping_bill', 'sez_document', 'deemed_export_document',
    'advance_receipt_register', 'advance_adjustment_register', 'ecommerce_tcs_statement',
    'purchase_register', 'rcm_invoice', 'import_services_document',
    'inward_debit_note', 'inward_credit_note', 'isd_credit_document',
    'itc_register', 'itc_reversal_working', 'mismatch_rectification_report',
    'tds_credit_detail', 'tcs_credit_detail', 'interest_working', 'late_fee_working',
    'payment_challan', 'bank_account_details',
    'electronic_liability_ledger', 'electronic_cash_ledger', 'electronic_credit_ledger',
    'supplier_invoice', 'supplier_debit_note', 'supplier_credit_note',
    'gstr_2a', 'gstr_2b', 'gstr_3b', 'other',
}


def _doc_row(name: str, doc_type: str, size: int | None, period: str | None = None) -> dict:
    return {
        "name": name,
        "type": doc_type.replace("_", " ").title(),
        "route": period or "",
        "extracted": human_size(size),
        "status": "stored",
    }


@router.get("/{gstin}/documents")
async def list_documents(gstin: str, db=Depends(get_db)):
    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    client_id = require_client(cur, ca_id, gstin.upper())
    cur.execute(
        "SELECT file_name, doc_type::text, file_size_bytes, tax_period FROM documents WHERE client_id = %s ORDER BY uploaded_at DESC",
        (client_id,),
    )
    return [_doc_row(n, t, s, p) for (n, t, s, p) in cur.fetchall()]


@router.post("/{gstin}/documents", status_code=201)
async def upload_document(
    gstin: str,
    file: UploadFile = File(...),
    doc_type: str = Form("other"),
    db=Depends(get_db),
):
    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    client_id = require_client(cur, ca_id, gstin.upper())

    raw_type = (doc_type or "").strip().lower()
    final_doc_type = raw_type if raw_type in _VALID_DOC_TYPES else "other"

    dest_dir = os.path.join(UPLOAD_ROOT, client_id)
    os.makedirs(dest_dir, exist_ok=True)
    safe_name = secure_filename(file.filename or "upload")
    dest_path = os.path.join(dest_dir, safe_name)

    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)

    size = os.path.getsize(dest_path)
    storage_path = os.path.relpath(dest_path, UPLOAD_ROOT)
    file_text = extract_and_clean(dest_path)

    cur.execute(
        """
        INSERT INTO documents (client_id, doc_type, file_name, storage_path, file_size_bytes, file_text)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING file_name, doc_type::text, file_size_bytes, tax_period
        """,
        (client_id, final_doc_type, file.filename, storage_path, size, file_text),
    )
    row = cur.fetchone()
    doc = _doc_row(row[0], row[1], row[2], row[3])
    return {**doc, "doc": doc}