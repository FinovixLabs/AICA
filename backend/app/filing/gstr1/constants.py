"""
Static reference data and regex patterns for the GSTR-1 pipeline.

Everything here is deterministic and law-derived — no configuration or AI.
The one tunable is the B2CL threshold, sourced from settings with a spec default.
"""
from __future__ import annotations
import os
import re

# ── State / UT codes (first two digits of a GSTIN) ─────────────────────────────
STATE_CODES: dict[str, str] = {
    "01": "Jammu and Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "26": "Dadra and Nagar Haveli and Daman and Diu",
    "27": "Maharashtra",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman and Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh",
    "96": "Foreign Country",
    "97": "Other Territory",
}


def pos_label(code: str | None) -> str | None:
    """Format a 2-digit state code as the portal's '<code>-<State>' place-of-supply."""
    if not code:
        return None
    code = str(code).strip().zfill(2)[:2]
    name = STATE_CODES.get(code)
    return f"{code}-{name}" if name else None


# ── Regex patterns ─────────────────────────────────────────────────────────────
# GSTIN — spec version: entity code is [1-9A-Z], 14th char is literal 'Z'.
GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")

# Voucher number — strict (official) vs permissive (parse-tolerant).
VOUCHER_STRICT_RE = re.compile(r"^[A-Z0-9][A-Z0-9/-]{0,15}$")
VOUCHER_PERMISSIVE_RE = re.compile(r"^\S{1,32}$")


# ── Tunable thresholds ─────────────────────────────────────────────────────────
def b2cl_threshold() -> float:
    """
    Invoice-value cutoff (exclusive) above which an unregistered inter-state
    supply is reported invoice-wise as B2CL. Spec default ₹1,00,000; overridable
    via the GSTR1_B2CL_THRESHOLD env var.
    """
    raw = os.getenv("GSTR1_B2CL_THRESHOLD", "").strip()
    try:
        return float(raw) if raw else 100000.0
    except ValueError:
        return 100000.0


# ── Segregator buckets (four, per current scope) ───────────────────────────────
B2B = "B2B"
B2CL = "B2CL"
B2CS = "B2CS"
NIL = "Nil-rated"
SEGREGATORS = (B2B, B2CL, B2CS, NIL)


# ── Beta sales register — canonical column order ───────────────────────────────
BETA_COLUMNS: list[str] = [
    "date",
    "particulars",          # legal / trade name
    "voucher_type",
    "voucher_number",
    "gstin",                # buyer GSTIN (null for B2C)
    "invoice_value",        # gross total incl. tax
    "gross_total_sales",
    "cgst",
    "sgst",
    "round_off",
    "igst",
    "discount",
    "segregator",
    "taxable_value",
    "pos",                  # '<code>-<State>'
    "reverse_charge",       # 'Y' / 'N'
    "applicable_tax_rate",  # % (may be blank)
    "ecommerce_gstin",
    "cess",
    "hsn",
]
