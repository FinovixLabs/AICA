from __future__ import annotations
from typing import Any

_GSTR_1_DOCS: list[dict[str, str]] = [
    {"label": "Sales Register", "doc_type": "sales_register"},
    {"label": "Tax Invoices (B2B)", "doc_type": "sales_invoice"},
    {"label": "Credit Notes Issued", "doc_type": "credit_note"},
    {"label": "Debit Notes Issued", "doc_type": "debit_note"},
    {"label": "Export Invoices", "doc_type": "export_invoice"},
]

_GSTR_3B_DOCS: list[dict[str, str]] = [
    {"label": "Sales Register", "doc_type": "sales_register"},
    {"label": "Purchase Register", "doc_type": "purchase_register"},
    {"label": "ITC Register", "doc_type": "itc_register"},
    {"label": "Electronic Cash Ledger", "doc_type": "electronic_cash_ledger"},
    {"label": "Payment Challans", "doc_type": "payment_challan"},
]

PREREQUISITES: dict[str, list[dict[str, str]]] = {
    "GSTR_1": _GSTR_1_DOCS,
    "GSTR_3B": _GSTR_3B_DOCS,
}

SUPPORTED_FILING_TYPES: list[str] = list(PREREQUISITES.keys())


def check(cur, client_id: str, filing_type: str) -> dict[str, Any]:
    required = PREREQUISITES.get(filing_type.upper())
    if required is None:
        return {"status": "error", "reason": "unsupported_filing_type", "supported": SUPPORTED_FILING_TYPES}

    required_types = [r["doc_type"] for r in required]
    cur.execute(
        "SELECT DISTINCT doc_type::text FROM documents WHERE client_id = %s AND doc_type::text = ANY(%s)",
        (client_id, required_types),
    )
    present = {row[0] for row in cur.fetchall()}
    missing = [r for r in required if r["doc_type"] not in present]

    if missing:
        return {
            "status": "blocked",
            "reason": "missing_required_documents",
            "missing_documents": missing,
            "next_action": "Upload the missing documents through the Document Ingestion Lab.",
        }

    return {"status": "ready", "filing_type": filing_type.upper()}
