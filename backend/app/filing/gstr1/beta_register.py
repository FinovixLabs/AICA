"""
Step 2 of the GSTR-1 pipeline — the DATA FILLER.

Takes raw extracted rows + the client's own GSTIN and produces the standardized
*beta sales register*: one dict per transaction with the canonical BETA_COLUMNS.
Every rule here is hard-coded and deterministic (no AI):

  * segregator          — B2B / B2CL / B2CS / Nil-rated
  * place of supply     — buyer GSTIN (B2B) or client GSTIN (B2C)
  * reverse charge      — default 'N'
  * tax reconciliation  — derive rate from amounts or amounts from rate
  * tax-conflict rule   — the tax AMOUNT is authoritative over the rate
  * IGST vs CGST/SGST   — from place-of-supply vs client state
  * rounding            — frac > 0.5 -> ceil, < 0.5 -> floor (0.5 -> up)
"""
from __future__ import annotations
import math
from typing import Any

from app.filing.gstr1.constants import (
    B2B, B2CL, B2CS, NIL, GSTIN_RE, b2cl_threshold, pos_label,
)

# Relative tolerance for declaring rate vs amount inconsistent.
_TAX_TOLERANCE = 0.02  # 2% or ₹1, whichever is larger (see _rates_conflict)


def build(rows: list[dict[str, Any]], client_gstin: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Build the beta sales register.

    Returns (beta_rows, flags). Flags carry tax-conflict notices raised while
    reconciling rate against amount.
    """
    client_state = _state_of(client_gstin)
    beta_rows: list[dict[str, Any]] = []
    flags: list[dict[str, Any]] = []

    for idx, row in enumerate(rows):
        beta, row_flags = _fill_row(row, client_state, idx)
        beta_rows.append(beta)
        flags.extend(row_flags)

    return beta_rows, flags


def _fill_row(row: dict[str, Any], client_state: str | None, idx: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    flags: list[dict[str, Any]] = []

    buyer_gstin = _clean_gstin(row.get("buyer_gstin"))
    is_registered = bool(buyer_gstin and GSTIN_RE.match(buyer_gstin))

    taxable = _num(row.get("taxable_value"))
    invoice_val_src = _num(row.get("invoice_value"))
    cess = _num(row.get("cess")) or 0.0
    src_rate = _num(row.get("rate"))
    src_igst = _num(row.get("igst"))
    src_cgst = _num(row.get("cgst"))
    src_sgst = _num(row.get("sgst"))

    # Base amount for reconciliation: taxable value, else invoice value net of nothing.
    base = taxable if taxable is not None else invoice_val_src

    # ── Reconcile rate <-> tax amount ─────────────────────────────────────────
    rate, total_tax, conflict = _reconcile_tax(base, src_rate, src_igst, src_cgst, src_sgst)
    if conflict:
        flags.append({
            "type": "tax_rate_amount_conflict",
            "row_index": idx,
            "invoice_number": row.get("invoice_number"),
            "message": (
                f"Rate {src_rate}% and tax amount disagree on invoice "
                f"{row.get('invoice_number')}; tax amount treated as authoritative."
            ),
        })

    # ── Segregator ────────────────────────────────────────────────────────────
    if is_registered:
        segregator = B2B
    elif _is_nil(row, rate, total_tax):
        segregator = NIL
    elif (invoice_val_src or base or 0.0) > b2cl_threshold():
        segregator = B2CL
    else:
        segregator = B2CS

    # ── Place of supply ───────────────────────────────────────────────────────
    if segregator == B2B:
        pos_state = _state_of(buyer_gstin)
    else:
        # B2C: per spec, use the client's own GSTIN state. (See plan Open Items.)
        pos_state = client_state
    # Honour an explicit, resolvable source POS if we could not derive one.
    if pos_state is None:
        pos_state = _state_of(row.get("pos")) or _pos_prefix(row.get("pos"))
    pos = pos_label(pos_state)

    # ── IGST vs CGST/SGST split ───────────────────────────────────────────────
    inter_state = (
        pos_state is not None and client_state is not None and pos_state != client_state
    )
    if inter_state:
        igst, cgst, sgst = round(total_tax, 2), 0.0, 0.0
    else:
        half = round(total_tax / 2, 2)
        igst, cgst, sgst = 0.0, half, round(total_tax - half, 2)

    # ── Rounding / totals ─────────────────────────────────────────────────────
    net_base = base or 0.0
    gross = round(net_base + igst + cgst + sgst + cess, 2)
    rounded_invoice = _round_whole(gross)
    round_off = round(rounded_invoice - gross, 2)
    invoice_value = rounded_invoice

    beta = {
        "date": row.get("date"),
        "particulars": row.get("party_name"),
        "voucher_type": _voucher_type(row),
        "voucher_number": row.get("invoice_number"),
        "gstin": buyer_gstin if is_registered else None,
        "invoice_value": invoice_value,
        "gross_total_sales": round(net_base, 2),
        "cgst": cgst,
        "sgst": sgst,
        "round_off": round_off,
        "igst": igst,
        "discount": _num(row.get("discount")),
        "segregator": segregator,
        "taxable_value": round(net_base, 2),
        "pos": pos,
        "reverse_charge": _reverse_charge(row),
        "applicable_tax_rate": round(rate, 2) if rate is not None else None,
        "ecommerce_gstin": _clean_gstin(row.get("ecommerce_gstin")),
        "cess": cess,
        "hsn": (str(row.get("hsn")).strip() or None) if row.get("hsn") is not None else None,
    }
    return beta, flags


# ── Tax reconciliation ─────────────────────────────────────────────────────────
def _reconcile_tax(
    base: float | None,
    rate: float | None,
    igst: float | None,
    cgst: float | None,
    sgst: float | None,
) -> tuple[float | None, float, bool]:
    """
    Resolve (effective_rate, total_tax_amount, conflict_flag).

    - amount present, rate missing   -> derive rate from amount
    - rate present, amount missing   -> derive amount from rate
    - both present but inconsistent  -> AMOUNT authoritative (conflict=True)
    """
    amount = None
    if igst is not None or cgst is not None or sgst is not None:
        amount = (igst or 0.0) + (cgst or 0.0) + (sgst or 0.0)

    has_base = base is not None and base > 0

    # amount known
    if amount is not None:
        derived_rate = (amount / base * 100.0) if has_base else None
        if rate is None:
            return derived_rate, round(amount, 2), False
        # both present — check consistency
        expected = (base * rate / 100.0) if has_base else None
        conflict = expected is not None and _rates_conflict(expected, amount)
        # amount authoritative either way; rate reported = derived when conflict
        eff_rate = derived_rate if conflict else rate
        return eff_rate, round(amount, 2), conflict

    # amount unknown — derive from rate
    if rate is not None and has_base:
        return rate, round(base * rate / 100.0, 2), False

    # nothing to go on
    return rate, 0.0, False


def _rates_conflict(expected: float, actual: float) -> bool:
    tol = max(1.0, abs(expected) * _TAX_TOLERANCE)
    return abs(expected - actual) > tol


# ── Small rule helpers ─────────────────────────────────────────────────────────
def _is_nil(row: dict[str, Any], rate: float | None, total_tax: float) -> bool:
    label = " ".join(
        str(row.get(k) or "") for k in ("invoice_type", "note_type")
    ).lower()
    if "nil" in label or "exempt" in label or "non-gst" in label or "non gst" in label:
        return True
    # 0% GST with no tax charged.
    return (rate is not None and rate == 0) and total_tax == 0.0


def _voucher_type(row: dict[str, Any]) -> str:
    label = str(row.get("note_type") or row.get("invoice_type") or "").strip().lower()
    if "credit" in label or label in ("c", "cr"):
        return "Credit Note"
    if "debit" in label or label in ("d", "dr"):
        return "Debit Note"
    return (str(row.get("invoice_type")).strip() if row.get("invoice_type") else "Sales")


def _reverse_charge(row: dict[str, Any]) -> str:
    val = str(row.get("reverse_charge") or "").strip().lower()
    if val in ("y", "yes", "true", "1", "reverse", "rcm"):
        return "Y"
    return "N"


def _round_whole(x: float) -> float:
    """frac > 0.5 -> ceil, frac < 0.5 -> floor, frac == 0.5 -> round half up."""
    floor = math.floor(x)
    frac = x - floor
    if frac > 0.5:
        return float(floor + 1)
    if frac < 0.5:
        return float(floor)
    return float(floor + 1)  # exactly .5 -> up


# ── Parsing / GSTIN utilities ──────────────────────────────────────────────────
def _num(val: Any) -> float | None:
    """Parse a numeric field; None for blank/unparseable (distinct from 0)."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(",", "").replace("₹", "").replace("%", "").replace(" ", "")
    if not s or s in ("-", "--"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _clean_gstin(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip().upper()
    return s or None


def _state_of(gstin: Any) -> str | None:
    s = _clean_gstin(gstin)
    if s and GSTIN_RE.match(s):
        return s[:2]
    return None


def _pos_prefix(val: Any) -> str | None:
    """Pull a leading 2-digit code out of a '<code>-<State>' or bare-code POS."""
    if val is None:
        return None
    s = str(val).strip()
    if len(s) >= 2 and s[:2].isdigit():
        return s[:2]
    return None
