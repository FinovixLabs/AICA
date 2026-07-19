"""The reconciliation match engine (spec sections 2.4, 2.5, 3, 4, 5).

A pure function. No cursor, no network, no FastAPI, no I/O of any kind:
reconcile() takes normalized rows and returns results. That is deliberate — it
is what makes the hardest and most ambiguous logic in the module fully testable
before a single line of wiring exists, and it is why this file imports nothing
from app.core or app.api.

This engine is the GSTR-2B contract. IMS Inward and IMS Outward have dedicated
matchers because their identity, action and status rules differ.

The rules this file implements, and the sections they come from:

  2.4  A purchase-register entry is never split, mixed, or aggregated.
  2.5  A PR entry is a duplicate only when all FIVE fields match, invoice value
       included. One copy is retained and reconciled; only the extra copies are
       omitted.
  3.2  Splitting happens only on the counterparty side.
  3.3  Counterparty rows sharing a key are summed and compared against the single
       PR entry, and displayed as one consolidated transaction.
  4.1  Invoice value alone decides Matched vs Mismatch. Taxable value and
       combined tax are carried for display and never read here.
  4.2  Comparison is on absolute values.
  4.3  1% tolerance, with the PR invoice value as the base.
  4.4  Zero-value protection: never divide by a zero PR value.
  5    Four statuses; the codes are for backend sorting only and never reach the
       Excel output.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Iterable, Mapping

__all__ = [
    "AMBIGUOUS",
    "DUPLICATE_PR",
    "ENGINE_VERSION",
    "EXTRA",
    "MATCHED",
    "MISMATCH",
    "MISSING",
    "STATUS_CODES",
    "STATUS_LABELS",
    "ExcludedRow",
    "MatchRow",
    "NormRow",
    "ReconOutcome",
    "reconcile",
]

ENGINE_VERSION = "recon-1.0.0"

MATCHED = "matched"
MISMATCH = "mismatch"
MISSING = "missing"
EXTRA = "extra"
DUPLICATE_PR = "duplicate_pr"
AMBIGUOUS = "ambiguous"

# Backend sort keys ONLY. Never exported to Excel — see excel.py and test_excel.py.
# Ascending order is worst-first: Mismatch, Missing, Duplicate, Ambiguous, Extra, Matched.
STATUS_CODES: dict[str, str] = {
    MISMATCH: "00",
    MISSING: "01",
    DUPLICATE_PR: "02",
    AMBIGUOUS: "03",
    EXTRA: "10",
    MATCHED: "11",
}

# The CA-facing wording. These are what reach the UI and the workbook.
STATUS_LABELS: dict[str, str] = {
    MATCHED: "Matched",
    MISMATCH: "Mismatch",
    MISSING: "Missing Transaction",
    EXTRA: "Extra Transaction",
    DUPLICATE_PR: "Duplicate Purchase Register Entry",
    AMBIGUOUS: "Needs Review",
}

# Statuses the CA can act on — the top box. Matched is display-only.
UNRESOLVED = (MISMATCH, MISSING, DUPLICATE_PR, AMBIGUOUS, EXTRA)

_ZERO = Decimal("0")
_CENTS = Decimal("0.01")
DEFAULT_TOLERANCE = Decimal("0.01")  # 1%, section 4.3


@dataclass(frozen=True)
class NormRow:
    """One normalized source row, from either side."""

    row_no: int  # 1-based position in the source file — the ONLY tiebreaker used anywhere
    row_id: int | None = None  # recon.source_rows.id; None in unit tests
    gstin: str | None = None
    supplier_name: str | None = None  # display-only; deliberately excluded from key
    doc_type: str | None = None
    doc_no: str | None = None
    doc_date: date | None = None
    taxable: Decimal | None = None
    tax: Decimal | None = None
    invoice: Decimal | None = None
    ims_status: str | None = None
    return_period: str | None = None  # display-only (IMS Outward); never in the key
    reported_in_form: str | None = None  # display-only (IMS Outward); never in the key
    raw: Mapping[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        """The match key: Supplier GSTIN, document type, number and date (2.3)."""
        return "|".join(
            [
                self.gstin or "",
                self.doc_type or "",
                self.doc_no or "",
                self.doc_date.isoformat() if self.doc_date else "",
            ]
        )

    @property
    def dup_key(self) -> tuple[str, Decimal | None]:
        """The duplicate key: the match key PLUS invoice value (2.5).

        Invoice value is SIGNED here, not absolute: a +100 invoice and a -100
        credit note under one reference are not copies of each other.
        """
        return (self.key, None if self.invoice is None else self.invoice.quantize(_CENTS))


@dataclass
class MatchRow:
    """One row of the contemporary reconciliation list."""

    status: str
    status_code: str
    key: str
    pr: NormRow | None = None
    cp: list[NormRow] = field(default_factory=list)
    cp_invoice: Decimal | None = None
    cp_taxable: Decimal | None = None
    cp_tax: Decimal | None = None
    diff_invoice: Decimal | None = None
    diff_pct: Decimal | None = None
    reason: str | None = None
    flags: list[str] = field(default_factory=list)
    seq: int = 0

    @property
    def cp_split_count(self) -> int:
        return len(self.cp)

    @property
    def is_split(self) -> bool:
        return len(self.cp) > 1


@dataclass
class ExcludedRow:
    """A row held out of matching. Never silently dropped — surfaced to the CA."""

    row: NormRow
    side: str  # 'pr' | 'cp'
    reason: str


@dataclass
class ReconOutcome:
    results: list[MatchRow]
    excluded: list[ExcludedRow]

    @property
    def totals(self) -> dict[str, int]:
        counts = {status: 0 for status in STATUS_CODES}
        for row in self.results:
            counts[row.status] += 1
        counts["excluded"] = len(self.excluded)
        return counts


# ── Amount comparison (4.1 - 4.4) ─────────────────────────────────────────────
def _compare(
    pr_invoice: Decimal | None,
    cp_invoice: Decimal | None,
    tolerance: Decimal,
) -> tuple[bool, Decimal, Decimal | None]:
    """Compare invoice values. Returns (is_match, signed_diff_of_absolutes, pct).

    Absolute values (4.2), so a credit note's sign convention cannot manufacture a
    mismatch. The purchase-register value is always the tolerance base (4.3).
    """
    base = abs(pr_invoice) if pr_invoice is not None else _ZERO
    other = abs(cp_invoice) if cp_invoice is not None else _ZERO
    diff = other - base  # signed on the absolutes, so the UI can say which side is higher

    if base == _ZERO:
        # Zero-value protection (4.4): never divide. Matched only if both are zero.
        return (other == _ZERO, diff, None)

    pct = abs(diff) / base
    return (pct <= tolerance, diff, pct)


def _sum(values: Iterable[Decimal | None]) -> Decimal | None:
    """Sum, ignoring None. Returns None only when every value is None.

    Summing BEFORE any abs() is taken is what makes a split of +100 / -20 net to
    80 rather than to 120 (3.3).
    """
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present, _ZERO)


def _sign_mismatch(pr_invoice: Decimal | None, cp_invoice: Decimal | None) -> bool:
    """True when the two sides disagree on sign.

    Section 4.2 mandates absolute comparison, so this never changes the status —
    but a purchase register showing -100 against a 2B showing +100 is a real data
    error that abs() would otherwise render invisible. Carried as a non-blocking
    flag so the CA can see it.
    """
    if pr_invoice is None or cp_invoice is None:
        return False
    if pr_invoice == _ZERO or cp_invoice == _ZERO:
        return False
    return (pr_invoice < _ZERO) != (cp_invoice < _ZERO)


# ── Phase 0: period scope ─────────────────────────────────────────────────────
def _in_period(row: NormRow, period: tuple[int, int] | None) -> bool:
    if period is None:
        return True
    if row.doc_date is None:
        # Absence is not evidence of being out of period. Keep it in matching and
        # let it surface as a real result rather than vanishing into the
        # excluded panel.
        return True
    return (row.doc_date.year, row.doc_date.month) == period


def _parse_period(period: str | None) -> tuple[int, int] | None:
    if not period:
        return None
    try:
        year, month = period.split("-")
        return (int(year), int(month))
    except (ValueError, AttributeError):
        return None


# ── Phase 1: purchase-register duplicate collapse (2.5) ───────────────────────
def _collapse_pr_duplicates(
    pr_rows: list[NormRow],
    counter: "_Counter",
) -> tuple[list[NormRow], list[MatchRow]]:
    """Retain one copy of each duplicate set; flag the extras.

    A duplicate requires all five fields to match, invoice value included. Two PR
    entries sharing a key but differing in invoice value are two different
    transactions (2.4) and both survive here.

    Only the extra copies are omitted from matching. The retained copy — the
    lowest row_no — always goes on to reconcile (2.5).
    """
    seen: dict[tuple[str, Decimal | None], NormRow] = {}
    kept: list[NormRow] = []
    duplicates: list[MatchRow] = []

    for row in sorted(pr_rows, key=lambda r: r.row_no):
        if row.dup_key in seen:
            original = seen[row.dup_key]
            duplicates.append(
                MatchRow(
                    status=DUPLICATE_PR,
                    status_code=STATUS_CODES[DUPLICATE_PR],
                    key=row.key,
                    pr=row,
                    reason=(
                        f"Identical to purchase-register row {original.row_no}: same supplier, "
                        "document type, number, date and invoice value."
                    ),
                    seq=counter.next(),
                )
            )
        else:
            seen[row.dup_key] = row
            kept.append(row)

    return kept, duplicates


# ── Phase 2: matching ─────────────────────────────────────────────────────────
class _Counter:
    """Stable sequence for deterministic sorting of equal-status rows."""

    def __init__(self) -> None:
        self._value = 0

    def next(self) -> int:
        self._value += 1
        return self._value


def _group_by_key(rows: list[NormRow]) -> dict[str, list[NormRow]]:
    grouped: dict[str, list[NormRow]] = {}
    for row in sorted(rows, key=lambda r: r.row_no):
        grouped.setdefault(row.key, []).append(row)
    return grouped


def _extra_row(key: str, cps: list[NormRow], counter: _Counter, reason: str | None = None) -> MatchRow:
    """Present in the counterparty file but absent from the purchase register (10).

    Still consolidated per 3.3: split rows show as one transaction.
    """
    return MatchRow(
        status=EXTRA,
        status_code=STATUS_CODES[EXTRA],
        key=key,
        pr=None,
        cp=list(cps),
        cp_invoice=_sum(row.invoice for row in cps),
        cp_taxable=_sum(row.taxable for row in cps),
        cp_tax=_sum(row.tax for row in cps),
        reason=reason,
        seq=counter.next(),
    )


def _aggregate_against(
    pr: NormRow,
    cps: list[NormRow],
    tolerance: Decimal,
    counter: _Counter,
) -> MatchRow:
    """Compare one purchase-register entry against its counterparty split group (3.3).

    The counterparty rows are summed; the purchase-register entry is never split
    or aggregated (2.4).
    """
    if not cps:
        return MatchRow(
            status=MISSING,
            status_code=STATUS_CODES[MISSING],
            key=pr.key,
            pr=pr,
            seq=counter.next(),
        )

    cp_invoice = _sum(row.invoice for row in cps)
    cp_taxable = _sum(row.taxable for row in cps)
    cp_tax = _sum(row.tax for row in cps)

    row = MatchRow(
        status=MISMATCH,
        status_code=STATUS_CODES[MISMATCH],
        key=pr.key,
        pr=pr,
        cp=list(cps),
        cp_invoice=cp_invoice,
        cp_taxable=cp_taxable,
        cp_tax=cp_tax,
        seq=counter.next(),
    )

    if pr.invoice is None:
        # The spec is silent here. Matching on absent data is not defensible, so
        # this is never Matched.
        row.reason = "Purchase-register invoice value is missing or unreadable."
        row.flags.append("pr_invoice_missing")
        return row

    is_match, diff, pct = _compare(pr.invoice, cp_invoice, tolerance)
    row.diff_invoice = diff
    row.diff_pct = pct
    row.status = MATCHED if is_match else MISMATCH
    row.status_code = STATUS_CODES[row.status]

    if _sign_mismatch(pr.invoice, cp_invoice):
        row.flags.append("sign_mismatch")

    if not is_match:
        if pct is None:
            row.reason = (
                "Purchase-register invoice value is zero but the counterparty value is not."
            )
        else:
            row.reason = f"Invoice values differ by {pct * 100:.2f}%, beyond the 1% tolerance."

    return row


def reconcile(
    pr_rows: list[NormRow],
    cp_rows: list[NormRow],
    *,
    period: str | None = None,
    tolerance: Decimal = DEFAULT_TOLERANCE,
) -> ReconOutcome:
    """Reconcile a purchase register against a counterparty file.

    `period` is 'YYYY-MM'. Rows dated outside it are held out of matching and
    returned in `excluded` — never silently dropped. Without this, an annual
    purchase register run against a one-month GSTR-2B produces thousands of false
    Missing rows that look like real problems.
    """
    counter = _Counter()
    scope = _parse_period(period)

    excluded: list[ExcludedRow] = []
    pr_scoped: list[NormRow] = []
    cp_scoped: list[NormRow] = []

    for row in pr_rows:
        if _in_period(row, scope):
            pr_scoped.append(row)
        else:
            excluded.append(ExcludedRow(row=row, side="pr", reason="out_of_period"))
    for row in cp_rows:
        if _in_period(row, scope):
            cp_scoped.append(row)
        else:
            excluded.append(ExcludedRow(row=row, side="cp", reason="out_of_period"))

    pr_kept, results = _collapse_pr_duplicates(pr_scoped, counter)

    pr_by_key = _group_by_key(pr_kept)
    cp_by_key = _group_by_key(cp_scoped)

    for key in sorted(set(pr_by_key) | set(cp_by_key)):
        prs = pr_by_key.get(key, [])
        cps = cp_by_key.get(key, [])

        # Nothing in the purchase register: everything here is an Extra
        # Transaction (10), still consolidated per 3.3.
        if not prs:
            results.append(_extra_row(key, cps, counter))
            continue

        # Exactly one purchase-register entry: the spec path, verbatim (3.3).
        if len(prs) == 1:
            results.append(_aggregate_against(prs[0], cps, tolerance, counter))
            continue

        # Two or more distinct purchase-register entries share this key.
        #
        # Section 3.3 says to sum the counterparty rows and compare against "the
        # single purchase-register entry" — but 2.4 guarantees that presupposition
        # can be false, because two PR rows with the same key and different
        # invoice values are two different transactions. Summing anyway would
        # compare an aggregate against one arbitrary entry and report a false
        # Mismatch on a pair that actually reconciles.
        #
        # So: flag the whole key and match nothing. Never aggregate the purchase
        # register (2.4), never invent a pairing. The CA resolves it.
        reason = (
            f"The same invoice reference appears {len(prs)} times in the purchase register "
            "with different values — it cannot be matched automatically."
        )
        for pr in prs:
            results.append(
                MatchRow(
                    status=AMBIGUOUS,
                    status_code=STATUS_CODES[AMBIGUOUS],
                    key=key,
                    pr=pr,
                    reason=reason,
                    flags=["ambiguous_key_multiple_pr"],
                    seq=counter.next(),
                )
            )
        for cp in cps:
            results.append(
                MatchRow(
                    status=AMBIGUOUS,
                    status_code=STATUS_CODES[AMBIGUOUS],
                    key=key,
                    cp=[cp],
                    cp_invoice=cp.invoice,
                    cp_taxable=cp.taxable,
                    cp_tax=cp.tax,
                    reason=reason,
                    flags=["ambiguous_key_multiple_pr"],
                    seq=counter.next(),
                )
            )

    results.sort(key=lambda row: (row.status_code, row.key, row.seq))
    return ReconOutcome(results=results, excluded=excluded)
