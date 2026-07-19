"""Row factories for the engine tests.

The engine is a pure function over NormRow, so these tests need no database, no
network and no FastAPI — they build rows and call reconcile().
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from app.recon.core.engine import NormRow

GSTIN_A = "27AAAAA0000A1Z5"
GSTIN_B = "29BBBBB1111B1Z3"
APRIL_3 = date(2025, 4, 3)


def _amount(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def make_row(
    row_no: int,
    invoice: Any = None,
    *,
    gstin: str = GSTIN_A,
    doc_type: str = "invoice",
    doc_no: str = "INV001",
    doc_date: date | None = APRIL_3,
    taxable: Any = None,
    tax: Any = None,
    ims_status: str | None = None,
) -> NormRow:
    return NormRow(
        row_no=row_no,
        gstin=gstin,
        doc_type=doc_type,
        doc_no=doc_no,
        doc_date=doc_date,
        taxable=_amount(taxable),
        tax=_amount(tax),
        invoice=_amount(invoice),
        ims_status=ims_status,
    )


@pytest.fixture
def row():
    return make_row


def statuses(outcome) -> list[str]:
    return [result.status for result in outcome.results]


def only(outcome, status: str) -> list:
    return [result for result in outcome.results if result.status == status]
