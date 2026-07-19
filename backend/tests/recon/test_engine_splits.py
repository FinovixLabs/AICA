"""Split-transaction handling (spec section 3).

Splitting occurs only on the counterparty side. One purchase-register transaction
may appear as two or more GSTR-2B rows; those rows are summed and compared
against the single PR entry, and displayed as ONE consolidated transaction.
"""
from __future__ import annotations

from decimal import Decimal

from conftest import make_row

from app.recon.core.engine import MATCHED, MISMATCH, reconcile


class TestSplitAggregation:
    def test_split_summing_to_the_register_value_is_one_matched_row(self):
        outcome = reconcile(
            [make_row(1, "1000.00")],
            [make_row(1, "300.00"), make_row(2, "500.00"), make_row(3, "200.00")],
        )
        assert len(outcome.results) == 1, "3.3: split rows display as one consolidated transaction"
        result = outcome.results[0]
        assert result.status == MATCHED
        assert result.cp_split_count == 3
        assert result.is_split is True
        assert result.cp_invoice == Decimal("1000.00")

    def test_extra_rows_are_not_independently_an_error_when_the_sum_matches(self):
        """3.2, verbatim: additional rows under the same 2B invoice identity do not
        independently create an error when the summed value matches."""
        outcome = reconcile(
            [make_row(1, "1000.00")],
            [make_row(1, "600.00"), make_row(2, "400.00")],
        )
        assert [r.status for r in outcome.results] == [MATCHED]

    def test_split_summing_wrong_is_one_mismatch_row(self):
        outcome = reconcile(
            [make_row(1, "1000.00")],
            [make_row(1, "300.00"), make_row(2, "500.00")],
        )
        assert len(outcome.results) == 1
        assert outcome.results[0].status == MISMATCH
        assert outcome.results[0].cp_invoice == Decimal("800.00")

    def test_split_is_summed_before_abs_is_taken(self):
        """A +100 / -20 split nets to 80, not 120. Summing after abs() would
        report a false match against a 120 register entry."""
        outcome = reconcile(
            [make_row(1, "80.00")],
            [make_row(1, "100.00"), make_row(2, "-20.00")],
        )
        assert outcome.results[0].cp_invoice == Decimal("80.00")
        assert outcome.results[0].status == MATCHED

    def test_split_within_tolerance(self):
        outcome = reconcile(
            [make_row(1, "1000.00")],
            [make_row(1, "600.00"), make_row(2, "405.00")],  # 1005 -> 0.5%
        )
        assert outcome.results[0].status == MATCHED


class TestConsolidatedDisplayValues:
    def test_taxable_and_tax_are_aggregated_for_display(self):
        """6.1: the consolidated row shows aggregated invoice value, aggregated
        taxable value and aggregated combined tax."""
        outcome = reconcile(
            [make_row(1, "1180.00", taxable="1000.00", tax="180.00")],
            [
                make_row(1, "590.00", taxable="500.00", tax="90.00"),
                make_row(2, "590.00", taxable="500.00", tax="90.00"),
            ],
        )
        result = outcome.results[0]
        assert result.cp_invoice == Decimal("1180.00")
        assert result.cp_taxable == Decimal("1000.00")
        assert result.cp_tax == Decimal("180.00")

    def test_all_source_rows_are_retained_on_the_consolidated_row(self):
        """The consolidated view must be expandable back to its members."""
        outcome = reconcile(
            [make_row(1, "1000.00")],
            [make_row(1, "600.00"), make_row(2, "400.00")],
        )
        assert [row.row_no for row in outcome.results[0].cp] == [1, 2]


class TestRegisterIsNeverSplit:
    def test_a_single_counterparty_row_is_not_a_split(self):
        outcome = reconcile([make_row(1, "100.00")], [make_row(1, "100.00")])
        assert outcome.results[0].is_split is False
        assert outcome.results[0].cp_split_count == 1

    def test_extra_rows_with_no_register_entry_still_consolidate(self):
        """3.3 display consolidation applies even when there is nothing to match."""
        outcome = reconcile([], [make_row(1, "600.00"), make_row(2, "400.00")])
        assert len(outcome.results) == 1
        assert outcome.results[0].cp_invoice == Decimal("1000.00")
