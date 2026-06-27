from __future__ import annotations
from typing import Any

# Each entry maps a human-readable label to the doc_type enum value stored in DB.
# Non-document mandatory inputs (GSTIN, credentials, period) are excluded —
# those are validated from the client record and request body, not uploads.

_GSTR_3: list[dict[str, str]] = [
    # Outward supply documents
    {"label": "Sales Register",                     "doc_type": "sales_register"},
    {"label": "Tax Invoices",                       "doc_type": "sales_invoice"},
    {"label": "Debit Notes Issued",                 "doc_type": "debit_note"},
    {"label": "Credit Notes Issued",                "doc_type": "credit_note"},
    {"label": "Export Invoices",                    "doc_type": "export_invoice"},
    {"label": "Shipping Bills / Bill of Export",    "doc_type": "shipping_bill"},
    {"label": "SEZ Supply Documents",               "doc_type": "sez_document"},
    {"label": "Deemed Export Documents",            "doc_type": "deemed_export_document"},
    {"label": "Advance Receipt Register",           "doc_type": "advance_receipt_register"},
    {"label": "Advance Adjustment Register",        "doc_type": "advance_adjustment_register"},
    {"label": "E-commerce Operator TCS Statement",  "doc_type": "ecommerce_tcs_statement"},
    # Inward supply documents
    {"label": "Purchase Register",                  "doc_type": "purchase_register"},
    {"label": "RCM Invoices",                       "doc_type": "rcm_invoice"},
    {"label": "Import of Services Documents",       "doc_type": "import_services_document"},
    {"label": "Debit Notes Received",               "doc_type": "inward_debit_note"},
    {"label": "Credit Notes Received",              "doc_type": "inward_credit_note"},
    {"label": "ISD Credit Documents",               "doc_type": "isd_credit_document"},
    # ITC documents
    {"label": "ITC Register",                       "doc_type": "itc_register"},
    {"label": "ITC Reversal / Reclaim Working",     "doc_type": "itc_reversal_working"},
    {"label": "Mismatch and Rectification Reports", "doc_type": "mismatch_rectification_report"},
    # Credit and adjustment details
    {"label": "TDS Credit Details",                 "doc_type": "tds_credit_detail"},
    {"label": "TCS Credit Details",                 "doc_type": "tcs_credit_detail"},
    {"label": "Interest Calculation Working",       "doc_type": "interest_working"},
    {"label": "Late Fee Calculation Working",       "doc_type": "late_fee_working"},
    {"label": "Tax Payment Challans",               "doc_type": "payment_challan"},
    {"label": "Bank Account Details for Refund",    "doc_type": "bank_account_details"},
    # Ledgers
    {"label": "Electronic Liability Ledger",        "doc_type": "electronic_liability_ledger"},
    {"label": "Electronic Cash Ledger",             "doc_type": "electronic_cash_ledger"},
    {"label": "Electronic Credit Ledger",           "doc_type": "electronic_credit_ledger"},
]

_GSTR_2A: list[dict[str, str]] = [
    {"label": "Purchase Register",     "doc_type": "purchase_register"},
    {"label": "Supplier Invoices",     "doc_type": "supplier_invoice"},
    {"label": "Supplier Debit Notes",  "doc_type": "supplier_debit_note"},
    {"label": "Supplier Credit Notes", "doc_type": "supplier_credit_note"},
    {"label": "ITC Register",          "doc_type": "itc_register"},
    {"label": "GSTR-2A Download",      "doc_type": "gstr_2a"},
    {"label": "GSTR-2B Download",      "doc_type": "gstr_2b"},
    {"label": "GSTR-3B Filed Return",  "doc_type": "gstr_3b"},
]

PREREQUISITES: dict[str, list[dict[str, str]]] = {
    "GSTR_3":  _GSTR_3,
    "GSTR_2A": _GSTR_2A,
}

SUPPORTED_FILING_TYPES: list[str] = list(PREREQUISITES.keys())


def check(cur, client_id: str, filing_type: str) -> dict[str, Any]:
    """
    Check whether all required documents for the filing type are present
    for the given client. Returns a dict ready to be returned as JSON.
    """
    required = PREREQUISITES.get(filing_type.upper())
    if required is None:
        return {
            "status": "error",
            "reason": "unsupported_filing_type",
            "supported": SUPPORTED_FILING_TYPES,
        }

    required_types = [r["doc_type"] for r in required]

    cur.execute(
        """
        SELECT DISTINCT doc_type::text
        FROM documents
        WHERE client_id = %s
          AND doc_type::text = ANY(%s)
        """,
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
