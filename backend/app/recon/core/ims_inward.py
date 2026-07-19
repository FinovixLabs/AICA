"""Dedicated IMS Inward matcher.

IMS Inward is not GSTR-2B reconciliation. Transactions correspond on normalized
Supplier GSTIN + Document Type + Document Number; invoice value is then compared
exactly to two decimal places. Document date, taxable value and combined tax are
display-only and never decide the result.
"""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from app.recon.core.engine import (
    MATCHED,
    MISMATCH,
    MISSING,
    STATUS_CODES,
    MatchRow,
    NormRow,
    ReconOutcome,
)

__all__ = ["IMS_INWARD_ENGINE_VERSION", "reconcile_inward"]

IMS_INWARD_ENGINE_VERSION = "ims-inward-1.0.0"
_CENTS = Decimal("0.01")


def _identity(row: NormRow) -> str:
    return "|".join((row.gstin or "", row.doc_type or "", row.doc_no or ""))


def _invoice(row: NormRow) -> Decimal | None:
    return None if row.invoice is None else abs(row.invoice).quantize(_CENTS)


def reconcile_inward(pr_rows: list[NormRow], ims_rows: list[NormRow]) -> ReconOutcome:
    """One-to-one IMS comparison, with Missing used for an absent transaction."""
    pr_groups: dict[str, list[NormRow]] = defaultdict(list)
    ims_groups: dict[str, list[NormRow]] = defaultdict(list)
    for row in pr_rows:
        pr_groups[_identity(row)].append(row)
    for row in ims_rows:
        ims_groups[_identity(row)].append(row)

    results: list[MatchRow] = []
    sequence = 0
    for key in sorted(set(pr_groups) | set(ims_groups)):
        available_pr = sorted(pr_groups.get(key, []), key=lambda row: row.row_no)
        pending_ims = sorted(ims_groups.get(key, []), key=lambda row: row.row_no)

        # Exact-value pairs first so repeated document references remain stable.
        unmatched_ims: list[NormRow] = []
        for ims in pending_ims:
            ims_invoice = _invoice(ims)
            match_index = next(
                (
                    index for index, pr in enumerate(available_pr)
                    if ims_invoice is not None and _invoice(pr) == ims_invoice
                ),
                None,
            )
            if match_index is None:
                unmatched_ims.append(ims)
                continue
            pr = available_pr.pop(match_index)
            sequence += 1
            results.append(
                MatchRow(
                    status=MATCHED,
                    status_code=STATUS_CODES[MATCHED],
                    key=key,
                    pr=pr,
                    cp=[ims],
                    cp_invoice=ims.invoice,
                    cp_taxable=ims.taxable,
                    cp_tax=ims.tax,
                    diff_invoice=Decimal("0"),
                    diff_pct=Decimal("0") if pr.invoice not in (None, Decimal("0")) else None,
                    seq=sequence,
                )
            )

        # Same identity but different invoice value is a real mismatch.
        while available_pr and unmatched_ims:
            pr = available_pr.pop(0)
            ims = unmatched_ims.pop(0)
            sequence += 1
            diff = None
            if pr.invoice is not None and ims.invoice is not None:
                diff = abs(ims.invoice) - abs(pr.invoice)
            invoice_missing = pr.invoice is None or ims.invoice is None
            results.append(
                MatchRow(
                    status=MISMATCH,
                    status_code=STATUS_CODES[MISMATCH],
                    key=key,
                    pr=pr,
                    cp=[ims],
                    cp_invoice=ims.invoice,
                    cp_taxable=ims.taxable,
                    cp_tax=ims.tax,
                    diff_invoice=diff,
                    reason=(
                        "Invoice value is missing or unreadable for the same transaction."
                        if invoice_missing
                        else "Invoice value differs for the same GSTIN, document type and document number."
                    ),
                    flags=(
                        ["invoice_value_missing", "invoice_value_mismatch"]
                        if invoice_missing else ["invoice_value_mismatch"]
                    ),
                    seq=sequence,
                )
            )

        # Absence on either side is reported uniformly as Missing.
        for pr in available_pr:
            sequence += 1
            results.append(
                MatchRow(
                    status=MISSING,
                    status_code=STATUS_CODES[MISSING],
                    key=key,
                    pr=pr,
                    reason="Purchase-register transaction was not found in IMS Inward.",
                    seq=sequence,
                )
            )
        for ims in unmatched_ims:
            sequence += 1
            results.append(
                MatchRow(
                    status=MISSING,
                    status_code=STATUS_CODES[MISSING],
                    key=key,
                    cp=[ims],
                    cp_invoice=ims.invoice,
                    cp_taxable=ims.taxable,
                    cp_tax=ims.tax,
                    reason="IMS Inward transaction was not found in the purchase register.",
                    seq=sequence,
                )
            )

    results.sort(key=lambda row: (row.status_code, row.seq))
    return ReconOutcome(results=results, excluded=[])
