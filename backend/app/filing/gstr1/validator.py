"""
Step 3 of the GSTR-1 pipeline — validate the beta sales register.

Checks:
  * GSTIN format (regex) for registered rows
  * voucher number — strict (official) vs permissive (parse) regex
  * duplicate invoice number across DIFFERENT customers -> flag for the CA

Returns the (unchanged) rows plus a list of flags and a CA-facing notice that is
surfaced through the Assistant module.
"""
from __future__ import annotations
from typing import Any

from app.filing.gstr1.constants import GSTIN_RE, VOUCHER_STRICT_RE, VOUCHER_PERMISSIVE_RE


def validate(beta_rows: list[dict[str, Any]]) -> dict[str, Any]:
    flags: list[dict[str, Any]] = []

    for idx, row in enumerate(beta_rows):
        flags.extend(_validate_gstin(row, idx))
        flags.extend(_validate_voucher(row, idx))

    flags.extend(_detect_duplicate_invoices(beta_rows))

    notice = _ca_notice(flags)
    return {"valid_rows": beta_rows, "flags": flags, "ca_notice": notice}


def _validate_gstin(row: dict[str, Any], idx: int) -> list[dict[str, Any]]:
    gstin = row.get("gstin")
    if gstin and not GSTIN_RE.match(str(gstin).strip().upper()):
        return [{
            "type": "invalid_gstin",
            "severity": "error",
            "row_index": idx,
            "invoice_number": row.get("voucher_number"),
            "value": gstin,
            "message": f"GSTIN '{gstin}' does not match the required format.",
        }]
    return []


def _validate_voucher(row: dict[str, Any], idx: int) -> list[dict[str, Any]]:
    raw = row.get("voucher_number")
    if raw is None or str(raw).strip() == "":
        return [{
            "type": "missing_voucher_number",
            "severity": "warning",
            "row_index": idx,
            "message": "Row has no voucher / invoice number.",
        }]
    value = str(raw).strip()
    if VOUCHER_STRICT_RE.match(value):
        return []
    if VOUCHER_PERMISSIVE_RE.match(value):
        return [{
            "type": "voucher_number_non_standard",
            "severity": "warning",
            "row_index": idx,
            "invoice_number": value,
            "message": f"Voucher number '{value}' parsed but does not meet the strict format.",
        }]
    return [{
        "type": "voucher_number_invalid",
        "severity": "error",
        "row_index": idx,
        "invoice_number": value,
        "message": f"Voucher number '{value}' is not a valid voucher number.",
    }]


def _detect_duplicate_invoices(beta_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Same invoice number on rows with different customers -> flag."""
    by_number: dict[str, list[tuple[int, str]]] = {}
    for idx, row in enumerate(beta_rows):
        num = row.get("voucher_number")
        if num is None or str(num).strip() == "":
            continue
        customer = _customer_key(row)
        by_number.setdefault(str(num).strip(), []).append((idx, customer))

    flags: list[dict[str, Any]] = []
    for num, entries in by_number.items():
        customers = {c for _, c in entries if c}
        if len(customers) > 1:
            flags.append({
                "type": "duplicate_invoice_number",
                "severity": "error",
                "invoice_number": num,
                "row_indexes": [i for i, _ in entries],
                "customers": sorted(customers),
                "message": (
                    f"Invoice number '{num}' appears for {len(customers)} different "
                    f"customers ({', '.join(sorted(customers))}). Please verify."
                ),
            })
    return flags


def _customer_key(row: dict[str, Any]) -> str:
    gstin = row.get("gstin")
    if gstin and str(gstin).strip():
        return str(gstin).strip().upper()
    name = row.get("particulars")
    return str(name).strip().upper() if name else ""


def _ca_notice(flags: list[dict[str, Any]]) -> str | None:
    """Compose a CA-facing notice via the Assistant module (deferred import to avoid cycles)."""
    if not flags:
        return None
    from app.services.chat_assistant import build_ca_validation_notice
    return build_ca_validation_notice(flags)
