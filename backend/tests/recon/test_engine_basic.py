"""The four statuses of spec section 5, one clean case each."""
from __future__ import annotations

from conftest import GSTIN_A, GSTIN_B, make_row

from app.recon.core.engine import (
    EXTRA,
    MATCHED,
    MISMATCH,
    MISSING,
    STATUS_CODES,
    reconcile,
)


class TestFourStatuses:
    def test_matched(self):
        outcome = reconcile([make_row(1, "1180.00")], [make_row(1, "1180.00")])
        assert [r.status for r in outcome.results] == [MATCHED]

    def test_mismatch(self):
        outcome = reconcile([make_row(1, "1180.00")], [make_row(1, "2000.00")])
        assert [r.status for r in outcome.results] == [MISMATCH]

    def test_missing_is_in_the_register_but_not_the_counterparty(self):
        outcome = reconcile([make_row(1, "1180.00")], [])
        result = outcome.results[0]
        assert result.status == MISSING
        assert result.pr is not None and result.cp == []

    def test_extra_is_in_the_counterparty_but_not_the_register(self):
        outcome = reconcile([], [make_row(1, "1180.00")])
        result = outcome.results[0]
        assert result.status == EXTRA
        assert result.pr is None and len(result.cp) == 1


class TestMatchKey:
    def test_all_four_fields_participate(self):
        """2.3: GSTIN, document type, number and date identify a transaction.
        Changing any one of them breaks the match."""
        pr = [make_row(1, "100.00")]
        for changed in [
            make_row(1, "100.00", gstin=GSTIN_B),
            make_row(1, "100.00", doc_type="credit_note"),
            make_row(1, "100.00", doc_no="INV002"),
            make_row(1, "100.00", doc_date=__import__("datetime").date(2025, 5, 3)),
        ]:
            outcome = reconcile(pr, [changed])
            assert {r.status for r in outcome.results} == {MISSING, EXTRA}

    def test_normalized_values_match(self):
        """The engine consumes already-normalized rows, so punctuation and case
        differences are gone by the time it runs."""
        outcome = reconcile([make_row(1, "100.00", doc_no="INV001")], [make_row(1, "100.00", doc_no="INV001")])
        assert outcome.results[0].status == MATCHED


class TestSortAndCodes:
    def test_worst_first(self):
        outcome = reconcile(
            [
                make_row(1, "100.00", doc_no="A"),   # matched
                make_row(2, "100.00", doc_no="B"),   # mismatch
                make_row(3, "100.00", doc_no="C"),   # missing
            ],
            [
                make_row(1, "100.00", doc_no="A"),
                make_row(2, "999.00", doc_no="B"),
                make_row(3, "100.00", doc_no="D"),   # extra
            ],
        )
        assert [r.status for r in outcome.results] == [MISMATCH, MISSING, EXTRA, MATCHED]

    def test_codes_are_as_specified(self):
        assert STATUS_CODES[MATCHED] == "11"
        assert STATUS_CODES[MISMATCH] == "00"
        assert STATUS_CODES[MISSING] == "01"
        assert STATUS_CODES[EXTRA] == "10"

    def test_sort_is_deterministic_across_runs(self):
        pr = [make_row(i, "100.00", doc_no=f"INV{i:03d}") for i in range(1, 20)]
        cp = [make_row(i, "999.00", doc_no=f"INV{i:03d}") for i in range(1, 20)]
        first = [(r.status, r.key) for r in reconcile(pr, cp).results]
        second = [(r.status, r.key) for r in reconcile(pr, cp).results]
        assert first == second


class TestTotals:
    def test_counts_by_status(self):
        outcome = reconcile(
            [make_row(1, "100.00", doc_no="A"), make_row(2, "100.00", doc_no="B")],
            [make_row(1, "100.00", doc_no="A"), make_row(2, "100.00", doc_no="C")],
        )
        totals = outcome.totals
        assert totals[MATCHED] == 1
        assert totals[MISSING] == 1
        assert totals[EXTRA] == 1
        assert totals[MISMATCH] == 0


class TestEmptyInputs:
    def test_both_sides_empty(self):
        outcome = reconcile([], [])
        assert outcome.results == []
        assert outcome.excluded == []
