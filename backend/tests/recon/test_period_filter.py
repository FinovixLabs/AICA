"""Period scoping.

A GSTR-2B is one month; a purchase register is often a whole year. Without
scoping, an annual register produces thousands of false Missing rows that look
like real problems. Out-of-period rows are held out of matching and returned in
`excluded` — never silently dropped.
"""
from __future__ import annotations

from datetime import date

from conftest import make_row

from app.recon.core.engine import MATCHED, MISSING, reconcile

APRIL = date(2025, 4, 3)
MAY = date(2025, 5, 3)
MARCH = date(2025, 3, 3)


class TestFiltering:
    def test_out_of_period_register_rows_are_excluded(self):
        outcome = reconcile(
            [
                make_row(1, "100.00", doc_no="APR", doc_date=APRIL),
                make_row(2, "100.00", doc_no="MAY", doc_date=MAY),
            ],
            [make_row(1, "100.00", doc_no="APR", doc_date=APRIL)],
            period="2025-04",
        )
        assert [r.status for r in outcome.results] == [MATCHED]
        assert len(outcome.excluded) == 1
        assert outcome.excluded[0].row.doc_no == "MAY"

    def test_excluded_rows_are_surfaced_not_dropped(self):
        outcome = reconcile(
            [make_row(1, "100.00", doc_date=MAY)],
            [],
            period="2025-04",
        )
        assert outcome.results == []
        assert len(outcome.excluded) == 1
        assert outcome.excluded[0].side == "pr"
        assert outcome.excluded[0].reason == "out_of_period"

    def test_this_is_what_prevents_the_false_missing_pile(self):
        """An annual register against a one-month 2B: without scoping this would
        report 11 false Missing rows."""
        register = [
            make_row(i, "100.00", doc_no=f"INV{i:03d}", doc_date=date(2025, i, 1))
            for i in range(1, 13)
        ]
        outcome = reconcile(
            register,
            [make_row(1, "100.00", doc_no="INV004", doc_date=date(2025, 4, 1))],
            period="2025-04",
        )
        assert [r.status for r in outcome.results] == [MATCHED]
        assert len(outcome.excluded) == 11

    def test_counterparty_rows_are_scoped_too(self):
        outcome = reconcile(
            [],
            [make_row(1, "100.00", doc_date=MARCH)],
            period="2025-04",
        )
        assert outcome.results == []
        assert outcome.excluded[0].side == "cp"

    def test_totals_report_the_excluded_count(self):
        outcome = reconcile(
            [make_row(1, "100.00", doc_date=MAY), make_row(2, "100.00", doc_date=MARCH)],
            [],
            period="2025-04",
        )
        assert outcome.totals["excluded"] == 2


class TestNoPeriod:
    def test_omitting_the_period_matches_everything(self):
        outcome = reconcile(
            [make_row(1, "100.00", doc_date=MAY)],
            [make_row(1, "100.00", doc_date=MAY)],
        )
        assert [r.status for r in outcome.results] == [MATCHED]
        assert outcome.excluded == []

    def test_an_unparseable_period_matches_everything(self):
        outcome = reconcile(
            [make_row(1, "100.00", doc_date=MAY)],
            [make_row(1, "100.00", doc_date=MAY)],
            period="garbage",
        )
        assert outcome.excluded == []


class TestMissingDates:
    def test_a_row_with_no_date_is_never_excluded(self):
        """Absence of a date is not evidence of being out of period. Excluding it
        would hide a real row in a panel the CA reads as 'not this month'."""
        outcome = reconcile(
            [make_row(1, "100.00", doc_date=None)],
            [],
            period="2025-04",
        )
        assert outcome.excluded == []
        assert [r.status for r in outcome.results] == [MISSING]
