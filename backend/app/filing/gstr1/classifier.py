"""
Deterministic GSTR-1 classifier.

Takes a normalised list of invoice rows (dicts with canonical field names)
and classifies each row into a GSTR-1 table:

  B2B   — taxable supply to a registered person (GSTIN present)
  B2CL  — taxable supply to unregistered, inter-state, invoice value > 2.5L
  B2CS  — taxable supply to unregistered, intra-state OR value ≤ 2.5L (summary)
  EXP   — export invoice (with or without payment of IGST)
  CDNR  — credit/debit note issued to a registered person
  CDNUR — credit/debit note issued to an unregistered person
  AT    — advance received (services)
  ATA   — advance adjusted (services)
  EXEMP — nil-rated / exempt / non-GST supply
  HSN   — HSN summary (auto-derived from all rows)

Rules are hard-coded from the GST Act and Form GSTR-1 instructions.
No AI involved in classification — deterministic Python only.
"""
from __future__ import annotations

import csv
import re
from io import StringIO
from typing import Any

GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$")
B2CL_THRESHOLD = 250000  # ₹2,50,000

# ── Column name normalisation ─────────────────────────────────────────────────
# Maps common Tally/Excel export header variations to canonical names.
_ALIASES: dict[str, list[str]] = {
    "invoice_number": ["invoice no", "inv no", "invoice number", "voucher no", "bill no", "ref no"],
    "invoice_date": ["invoice date", "date", "voucher date", "bill date"],
    "gstin_buyer": ["gstin of buyer", "buyer gstin", "party gstin", "gstin", "customer gstin", "recipient gstin"],
    "buyer_name": ["party name", "buyer name", "customer name", "name", "ledger name"],
    "place_of_supply": ["place of supply", "pos", "state of supply", "supply state"],
    "taxable_value": ["taxable value", "taxable amount", "assessable value", "value", "amount", "net amount"],
    "igst": ["igst", "integrated tax", "integrated gst"],
    "cgst": ["cgst", "central tax", "central gst"],
    "sgst": ["sgst", "state tax", "state gst", "utgst"],
    "cess": ["cess", "compensation cess"],
    "invoice_type": ["invoice type", "type", "supply type", "transaction type"],
    "export_type": ["export type", "export", "with igst", "without igst"],
    "hsn_code": ["hsn", "hsn code", "hsn/sac", "hsn sac code"],
    "uqc": ["uqc", "unit", "unit of measure"],
    "quantity": ["qty", "quantity"],
    "rate": ["rate", "gst rate", "tax rate", "%"],
    "note_type": ["note type", "type of note", "cr/dr"],
    "original_invoice_number": ["original invoice no", "original inv no", "against invoice"],
    "original_invoice_date": ["original invoice date", "against date"],
    "supply_type": ["supply type", "nature of supply"],
    "seller_state_code": ["seller state code", "seller state", "from state", "our state"],
}


def _normalise_header(raw_header: str) -> str:
    """Map a raw CSV header to the canonical field name, or return it lowercased."""
    cleaned = raw_header.strip().lower().replace("-", " ").replace("_", " ")
    for canonical, aliases in _ALIASES.items():
        if cleaned in [a.lower() for a in aliases]:
            return canonical
    # fallback: snake_case the original
    return re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_")


def _parse_amount(val: Any) -> float:
    """Parse an amount field to float, returning 0.0 on failure."""
    if val is None:
        return 0.0
    s = str(val).strip().replace(",", "").replace("₹", "").replace(" ", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _is_valid_gstin(val: Any) -> bool:
    if not val:
        return False
    return bool(GSTIN_RE.match(str(val).strip().upper()))


def _state_code(gstin_or_code: Any) -> str | None:
    """Extract 2-digit state code from GSTIN or return the value if it's already a 2-digit code."""
    if not gstin_or_code:
        return None
    s = str(gstin_or_code).strip()
    if GSTIN_RE.match(s.upper()):
        return s[:2]
    if re.match(r"^\d{2}$", s):
        return s
    return None


def parse_csv_to_rows(csv_text: str) -> tuple[list[str], list[dict[str, Any]]]:
    """
    Parse a CSV string into (canonical_headers, list_of_normalised_row_dicts).
    Returns empty lists if the CSV is empty or has no usable header.
    """
    text = csv_text.lstrip("\ufeff").strip()
    if not text:
        return [], []

    try:
        reader = csv.DictReader(StringIO(text))
        if not reader.fieldnames:
            return [], []

        raw_headers = list(reader.fieldnames)
        canonical_map = {h: _normalise_header(h) for h in raw_headers}
        canonical_headers = list(dict.fromkeys(canonical_map.values()))  # preserve order, dedup

        rows: list[dict[str, Any]] = []
        for raw_row in reader:
            norm_row: dict[str, Any] = {}
            for raw_h, val in raw_row.items():
                if raw_h is None:
                    continue
                canon = canonical_map.get(raw_h, _normalise_header(raw_h))
                norm_row[canon] = (val or "").strip()
            rows.append(norm_row)

        return canonical_headers, rows
    except csv.Error:
        return [], []


def classify_rows(
    rows: list[dict[str, Any]],
    seller_state_code: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    Classify invoice rows into GSTR-1 tables.

    Args:
        rows: Normalised invoice rows (from parse_csv_to_rows)
        seller_state_code: 2-digit state code of the selling entity (from client GSTIN)

    Returns:
        Dict mapping table name → list of classified rows with added 'gstr1_table' field
    """
    tables: dict[str, list[dict[str, Any]]] = {
        "B2B": [],
        "B2CL": [],
        "B2CS": [],
        "EXP": [],
        "CDNR": [],
        "CDNUR": [],
        "AT": [],
        "ATA": [],
        "EXEMP": [],
        "HSN": [],
    }

    hsn_accumulator: dict[str, dict[str, Any]] = {}

    for row in rows:
        invoice_type = str(row.get("invoice_type") or "").strip().lower()
        supply_type = str(row.get("supply_type") or "").strip().lower()
        note_type = str(row.get("note_type") or "").strip().lower()
        gstin_buyer = str(row.get("gstin_buyer") or "").strip().upper()
        pos = _state_code(row.get("place_of_supply"))
        taxable_value = _parse_amount(row.get("taxable_value"))
        igst = _parse_amount(row.get("igst"))
        cgst = _parse_amount(row.get("cgst"))
        sgst = _parse_amount(row.get("sgst"))
        cess = _parse_amount(row.get("cess"))
        hsn = str(row.get("hsn_code") or "").strip()
        rate = _parse_amount(row.get("rate"))
        quantity = _parse_amount(row.get("quantity"))
        uqc = str(row.get("uqc") or "").strip()

        # skip blank rows
        if taxable_value == 0 and igst == 0 and cgst == 0 and sgst == 0:
            continue

        classified_row = {**row, "gstr1_table": ""}

        # ── Credit / Debit notes ──────────────────────────────────────────────
        is_note = (
            "credit note" in invoice_type
            or "debit note" in invoice_type
            or note_type in ("credit", "debit", "cr", "dr", "c", "d")
        )
        if is_note:
            if _is_valid_gstin(gstin_buyer):
                classified_row["gstr1_table"] = "CDNR"
                tables["CDNR"].append(classified_row)
            else:
                classified_row["gstr1_table"] = "CDNUR"
                tables["CDNUR"].append(classified_row)
            _accumulate_hsn(hsn_accumulator, hsn, uqc, rate, quantity, taxable_value, igst, cgst, sgst, cess)
            continue

        # ── Advance receipts / adjustments ───────────────────────────────────
        if "advance" in invoice_type or "advance" in supply_type:
            if "adjust" in invoice_type or "adjust" in supply_type:
                classified_row["gstr1_table"] = "ATA"
                tables["ATA"].append(classified_row)
            else:
                classified_row["gstr1_table"] = "AT"
                tables["AT"].append(classified_row)
            continue

        # ── Exports ──────────────────────────────────────────────────────────
        is_export = (
            "export" in invoice_type
            or "export" in supply_type
            or str(row.get("export_type") or "").strip().lower() in ("with igst", "without igst", "lut", "bond")
            or pos == "96"  # GST portal state code for exports
        )
        if is_export:
            classified_row["gstr1_table"] = "EXP"
            tables["EXP"].append(classified_row)
            _accumulate_hsn(hsn_accumulator, hsn, uqc, rate, quantity, taxable_value, igst, cgst, sgst, cess)
            continue

        # ── Nil / exempt / non-GST ───────────────────────────────────────────
        is_nil_exempt = (
            "nil" in invoice_type
            or "exempt" in invoice_type
            or "non-gst" in invoice_type
            or "nongst" in invoice_type.replace(" ", "")
        )
        if is_nil_exempt:
            classified_row["gstr1_table"] = "EXEMP"
            tables["EXEMP"].append(classified_row)
            continue

        # ── B2B — registered buyer ───────────────────────────────────────────
        if _is_valid_gstin(gstin_buyer):
            classified_row["gstr1_table"] = "B2B"
            tables["B2B"].append(classified_row)
            _accumulate_hsn(hsn_accumulator, hsn, uqc, rate, quantity, taxable_value, igst, cgst, sgst, cess)
            continue

        # ── B2C — unregistered ───────────────────────────────────────────────
        # Determine if inter-state: POS ≠ seller state
        is_inter_state = (
            pos is not None
            and seller_state_code is not None
            and pos != seller_state_code
        ) or (igst > 0)  # IGST charged → inter-state

        if is_inter_state and taxable_value > B2CL_THRESHOLD:
            # B2CL: inter-state, unregistered, above ₹2.5L
            classified_row["gstr1_table"] = "B2CL"
            tables["B2CL"].append(classified_row)
        else:
            # B2CS: intra-state OR below ₹2.5L — summary, not invoice-wise
            classified_row["gstr1_table"] = "B2CS"
            tables["B2CS"].append(classified_row)

        _accumulate_hsn(hsn_accumulator, hsn, uqc, rate, quantity, taxable_value, igst, cgst, sgst, cess)

    # Build HSN summary from accumulator
    tables["HSN"] = list(hsn_accumulator.values())

    return tables


def _accumulate_hsn(
    acc: dict[str, dict[str, Any]],
    hsn: str,
    uqc: str,
    rate: float,
    quantity: float,
    taxable_value: float,
    igst: float,
    cgst: float,
    sgst: float,
    cess: float,
) -> None:
    """Accumulate totals into HSN summary by (hsn, uqc, rate) key."""
    if not hsn:
        return
    key = f"{hsn}|{uqc}|{rate}"
    if key not in acc:
        acc[key] = {
            "hsn_code": hsn,
            "uqc": uqc,
            "rate": rate,
            "total_quantity": 0.0,
            "total_taxable_value": 0.0,
            "total_igst": 0.0,
            "total_cgst": 0.0,
            "total_sgst": 0.0,
            "total_cess": 0.0,
            "gstr1_table": "HSN",
        }
    acc[key]["total_quantity"] += quantity
    acc[key]["total_taxable_value"] += taxable_value
    acc[key]["total_igst"] += igst
    acc[key]["total_cgst"] += cgst
    acc[key]["total_sgst"] += sgst
    acc[key]["total_cess"] += cess


def build_summary(tables: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Build a classification summary with counts and totals per table."""
    summary: dict[str, Any] = {}
    total_taxable = 0.0
    total_tax = 0.0

    for table_name, rows in tables.items():
        if table_name == "HSN":
            summary[table_name] = {"count": len(rows)}
            continue

        count = len(rows)
        taxable = sum(_parse_amount(r.get("taxable_value")) for r in rows)
        igst = sum(_parse_amount(r.get("igst")) for r in rows)
        cgst = sum(_parse_amount(r.get("cgst")) for r in rows)
        sgst = sum(_parse_amount(r.get("sgst")) for r in rows)
        cess = sum(_parse_amount(r.get("cess")) for r in rows)
        tax = igst + cgst + sgst

        summary[table_name] = {
            "count": count,
            "taxable_value": round(taxable, 2),
            "igst": round(igst, 2),
            "cgst": round(cgst, 2),
            "sgst": round(sgst, 2),
            "cess": round(cess, 2),
            "total_tax": round(tax, 2),
        }
        total_taxable += taxable
        total_tax += tax

    summary["TOTAL"] = {
        "total_taxable_value": round(total_taxable, 2),
        "total_tax": round(total_tax, 2),
    }

    return summary
