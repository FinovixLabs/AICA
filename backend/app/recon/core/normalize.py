"""Field normalization applied before matching (spec section 2.3).

    - Remove unnecessary spaces.
    - Ignore capitalization differences.
    - Ignore minor punctuation in document numbers (spaces, hyphens, slashes).
    - Convert different date formats into one standard date format.
    - Standardize Supplier GSTIN and document-type formatting.

Amounts are Decimal, never float: the 1% tolerance in engine.py compares at a
boundary where binary float drift changes the answer.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

__all__ = [
    "DATE_ORDERS",
    "GSTIN_RE",
    "infer_date_order",
    "is_valid_gstin",
    "norm_doc_no",
    "norm_gstin",
    "norm_text",
    "parse_date",
    "to_amount",
]

# Local copy of the GSTIN shape, deliberately not imported.
#
# The app currently holds three copies of this regex that do not agree:
# api/deps.py:6 and models/schemas.py:6 use [0-9A-Z] for the 13th character,
# filing/gstr1/constants.py:65 uses [1-9A-Z]. Importing either would couple 2B
# matching to a GSTR-1 internal and inherit whichever is wrong.
#
# We take the permissive form on purpose: a supplier GSTIN in a GSTR-2B file is
# the GST portal's own data. Rejecting a row here would silently drop a real
# transaction from the reconciliation, which is worse than carrying an odd value
# through to the CA.
GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$")

DATE_ORDERS = ("DMY", "MDY", "YMD")


def norm_text(val: Any) -> str:
    """Lower-case and collapse any run of non-alphanumerics to a single space.

    None normalizes to '', not to 'none': str(None) would otherwise produce a
    truthy key that a blank cell could canonicalize under.
    """
    if val is None:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(val).strip().lower()).strip()


# ── GSTIN ─────────────────────────────────────────────────────────────────────
def norm_gstin(val: Any) -> str | None:
    """Upper-case and strip all internal whitespace. Does not validate."""
    if val is None:
        return None
    s = re.sub(r"\s+", "", str(val)).upper()
    return s or None


def is_valid_gstin(val: Any) -> bool:
    s = norm_gstin(val)
    return bool(s and GSTIN_RE.match(s))


# ── Document number ───────────────────────────────────────────────────────────
_DOC_NO_PUNCT_RE = re.compile(r"[^A-Z0-9]+")


def norm_doc_no(val: Any) -> str | None:
    """Upper-case and drop every non-alphanumeric character.

    'INV-001', 'inv 001' and 'INV/001' all normalize to 'INV001' (spec 2.3).

    Leading zeros are deliberately NOT stripped: 'INV001' and 'INV1' stay
    distinct. The spec licenses ignoring punctuation, nothing more, and
    collapsing zeros would silently merge two real documents.
    """
    if val is None:
        return None
    s = _DOC_NO_PUNCT_RE.sub("", str(val).strip().upper())
    return s or None


# ── Amounts ───────────────────────────────────────────────────────────────────
_BLANK_AMOUNTS = {"", "-", "--", "NA", "N/A", "NIL", "NONE"}
_RS_RE = re.compile(r"(?i)\brs\.?")
_PARENS_RE = re.compile(r"^\((.*)\)$")


def to_amount(val: Any) -> Decimal | None:
    """Parse a money field. Returns None for blank/unparseable — distinct from 0.

    That distinction is load-bearing: engine.py treats a zero purchase-register
    invoice value as a real amount subject to zero-value protection, but treats a
    missing one as un-matchable.
    """
    if val is None or isinstance(val, bool):
        return None
    if isinstance(val, Decimal):
        return val
    if isinstance(val, int):
        return Decimal(val)
    if isinstance(val, float):
        return Decimal(str(val))

    s = str(val).strip()
    if s.upper() in _BLANK_AMOUNTS:
        return None

    s = s.replace(",", "").replace("₹", "").replace("%", "").replace(" ", "")
    s = _RS_RE.sub("", s).replace(" ", "")
    if s.upper() in _BLANK_AMOUNTS:
        return None

    negative = False
    parens = _PARENS_RE.match(s)  # (1234.00) — accounting notation for negative
    if parens:
        negative, s = True, parens.group(1)
        if s.upper() in _BLANK_AMOUNTS:
            return None

    try:
        amount = Decimal(s)
    except InvalidOperation:
        return None
    if not amount.is_finite():
        return None
    return -amount if negative else amount


# ── Dates ─────────────────────────────────────────────────────────────────────
_MONTH_NAMES = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

_TIME_SUFFIX_RE = re.compile(r"[ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?$")
_NUMERIC_RE = re.compile(r"^(\d{1,4})[/\-.](\d{1,2})[/\-.](\d{1,4})$")
_DAY_MONTH_RE = re.compile(r"^(\d{1,2})[\-/ ]*([A-Za-z]{3,9})[\-/ ,]*(\d{2,4})$")
_MONTH_DAY_RE = re.compile(r"^([A-Za-z]{3,9})[\-/ ]*(\d{1,2})[\-/ ,]*(\d{2,4})$")


def _expand_year(year: int) -> int:
    if year >= 100:
        return year
    return 2000 + year if year < 70 else 1900 + year


def _build(year: int, month: int, day: int) -> date | None:
    try:
        return date(_expand_year(year), month, day)
    except ValueError:
        return None


def parse_date(val: Any, order: str = "DMY") -> date | None:
    """Parse a date under a known day/month order.

    `order` is decided once per file by infer_date_order() and confirmed by the
    CA — never guessed per row. See infer_date_order's docstring for why.
    """
    if val is None or isinstance(val, bool):
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val

    s = str(val).strip()
    if not s:
        return None
    s = _TIME_SUFFIX_RE.sub("", s).strip()  # pandas/openpyxl stringified timestamps

    named = _DAY_MONTH_RE.match(s)  # 03-Apr-2025, 3 April 2025 — unambiguous
    if named:
        month = _MONTH_NAMES.get(named.group(2).lower())
        if month:
            return _build(int(named.group(3)), month, int(named.group(1)))
        return None

    named = _MONTH_DAY_RE.match(s)  # Apr-03-2025, April 3, 2025 — unambiguous
    if named:
        month = _MONTH_NAMES.get(named.group(1).lower())
        if month:
            return _build(int(named.group(3)), month, int(named.group(2)))
        return None

    numeric = _NUMERIC_RE.match(s)
    if not numeric:
        return None

    first, second, third = (int(g) for g in numeric.groups())
    if len(numeric.group(1)) == 4:
        # A 4-digit leading field is a year regardless of the declared order:
        # 2025-04-03 is ISO and means ISO even in a DMY file.
        return _build(first, second, third)
    if order == "YMD":
        return _build(first, second, third)
    if order == "MDY":
        return _build(third, first, second)
    return _build(third, second, first)  # DMY


def infer_date_order(samples: Iterable[Any]) -> tuple[str, str]:
    """Infer a file's day/month order. Returns (order, human-readable evidence).

    Resolved at FILE level, never per row. A per-row guess would read 03/04/2025
    as April 3rd and 25/12/2024 as December 25th in the same column, silently
    splitting one file into two conventions and scattering false
    Missing/Extra pairs that look like real reconciliation problems.

    The tell is any field that cannot be a month. If nothing in the file
    disambiguates, default to DMY (Indian convention) and let the CA confirm it
    in the mapping step.
    """
    dmy_hits: list[str] = []
    mdy_hits: list[str] = []
    ymd_hits = 0
    seen = 0

    for raw in samples:
        if raw is None:
            continue
        if isinstance(raw, (date, datetime)):
            seen += 1
            continue
        s = _TIME_SUFFIX_RE.sub("", str(raw).strip()).strip()
        if not s:
            continue
        if _DAY_MONTH_RE.match(s) or _MONTH_DAY_RE.match(s):
            seen += 1
            continue
        numeric = _NUMERIC_RE.match(s)
        if not numeric:
            continue

        seen += 1
        if len(numeric.group(1)) == 4:
            ymd_hits += 1
            continue
        first, second = int(numeric.group(1)), int(numeric.group(2))
        if first > 12:
            dmy_hits.append(s)  # first field can't be a month -> it's a day
        if second > 12:
            mdy_hits.append(s)  # second field can't be a month -> it's a day

    if dmy_hits and mdy_hits:
        # No single order reads this column. Real data problem — say so loudly
        # rather than picking a winner.
        return "DMY", (
            f"Conflicting date formats: {dmy_hits[0]!r} reads as day-first but "
            f"{mdy_hits[0]!r} reads as month-first. Defaulted to DMY — please confirm."
        )
    if dmy_hits:
        return "DMY", f"{dmy_hits[0]!r} has a first field above 12, so it is day-first."
    if mdy_hits:
        return "MDY", f"{mdy_hits[0]!r} has a second field above 12, so it is month-first."
    if ymd_hits and not seen - ymd_hits:
        return "YMD", f"All {ymd_hits} dates lead with a 4-digit year."
    return "DMY", (
        f"No date in {seen} sampled rows has a field above 12, so day and month "
        "are indistinguishable. Defaulted to DMY (Indian convention) — please confirm."
    )
