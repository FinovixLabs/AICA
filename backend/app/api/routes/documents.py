from __future__ import annotations
import os
import re
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from app.core.db import get_db
from app.core.config import get_settings
from app.api.deps import get_or_create_default_ca, require_client, human_size
from app.services.uploading import extract_and_clean


def secure_filename(filename: str) -> str:
    filename = filename.strip().replace(" ", "_")
    filename = re.sub(r"[^\w\s\-.]", "", filename)
    filename = re.sub(r"\.{2,}", ".", filename)
    return filename or "upload"


router = APIRouter(prefix="/clients", tags=["documents"])

_settings = get_settings()
UPLOAD_ROOT = str(_settings.upload_root_path)
MAX_UPLOAD_BYTES = _settings.MAX_UPLOAD_MB * 1024 * 1024

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
    'ims_inward', 'ims_outward',
}

_IMS_DOC_TYPES = {'ims_inward', 'ims_outward'}


def _database_accepts_document_type(cur, doc_type: str) -> bool:
    """Check the enum attached to documents.doc_type, without hard-coding its name."""
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM pg_attribute attribute
            JOIN pg_class relation ON relation.oid = attribute.attrelid
            JOIN pg_namespace namespace ON namespace.oid = relation.relnamespace
            JOIN pg_enum enum_value ON enum_value.enumtypid = attribute.atttypid
            WHERE namespace.nspname = 'public'
              AND relation.relname = 'documents'
              AND attribute.attname = 'doc_type'
              AND enum_value.enumlabel = %s
              AND attribute.attnum > 0
              AND NOT attribute.attisdropped
        )
        """,
        (doc_type,),
    )
    row = cur.fetchone()
    return bool(row and row[0])


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

    if final_doc_type in _IMS_DOC_TYPES and not _database_accepts_document_type(cur, final_doc_type):
        raise HTTPException(
            status_code=503,
            detail=(
                f"Database document type '{final_doc_type}' is not installed. "
                "Apply backend/migrations/005_add_recon_doc_types.sql, then upload again."
            ),
        )

    dest_dir = os.path.join(UPLOAD_ROOT, client_id)
    os.makedirs(dest_dir, exist_ok=True)
    original_name = file.filename or "upload"
    stored_name = f"{uuid4().hex}_{secure_filename(original_name)}"
    dest_path = os.path.join(dest_dir, stored_name)

    written = 0
    try:
        with open(dest_path, "wb") as destination:
            while chunk := await file.read(1024 * 1024):
                written += len(chunk)
                if written > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds the {_settings.MAX_UPLOAD_MB} MB upload limit",
                    )
                destination.write(chunk)
    except Exception:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise

    size = os.path.getsize(dest_path)
    storage_path = os.path.relpath(dest_path, UPLOAD_ROOT)
    try:
        file_text = extract_and_clean(dest_path)
        cur.execute(
            """
            INSERT INTO documents (client_id, doc_type, file_name, storage_path, file_size_bytes, file_text)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING file_name, doc_type::text, file_size_bytes, tax_period
            """,
            (client_id, final_doc_type, original_name, storage_path, size, file_text),
        )
    except Exception:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise
    row = cur.fetchone()
    doc = _doc_row(row[0], row[1], row[2], row[3])
    return {**doc, "doc": doc}
