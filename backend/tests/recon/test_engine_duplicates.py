"""Purchase-register duplicates (spec 2.4 and 2.5).

A duplicate requires all FIVE fields to match, invoice value included. One copy
is retained and reconciled; only the extra copies are omitted.
"""
from __future__ import annotations

from conftest import make_row

from app.recon.core.engine import DUPLICATE_PR, MATCHED, MISSING, reconcile


class TestDuplicateDetection:
    def test_five_field_identical_rows_are_duplicates(self):
        outcome = reconcile(
            [make_row(1, "100.00"), make_row(2, "100.00")],
            [make_row(1, "100.00")],
        )
        assert [r.status for r in outcome.results] == [DUPLICATE_PR, MATCHED]

    def test_the_retained_copy_still_reconciles(self):
        """2.5: 'the valid retained entry is not omitted'."""
        outcome = reconcile(
            [make_row(1, "100.00"), make_row(2, "100.00")],
            [make_row(1, "100.00")],
        )
        matched = [r for r in outcome.results if r.status == MATCHED]
        assert len(matched) == 1
        assert matched[0].pr.row_no == 1, "the lowest row_no is retained"

    def test_only_the_extra_copies_are_flagged(self):
        outcome = reconcile(
            [make_row(1, "100.00"), make_row(2, "100.00"), make_row(3, "100.00")],
            [make_row(1, "100.00")],
        )
        duplicates = [r for r in outcome.results if r.status == DUPLICATE_PR]
        assert [r.pr.row_no for r in duplicates] == [2, 3]

    def test_the_flag_names_the_row_it_duplicates(self):
        outcome = reconcile([make_row(1, "100.00"), make_row(2, "100.00")], [])
        duplicate = [r for r in outcome.results if r.status == DUPLICATE_PR][0]
        assert "row 1" in duplicate.reason

    def test_duplicates_are_detected_even_with_no_counterparty_file(self):
        outcome = reconcile([make_row(1, "100.00"), make_row(2, "100.00")], [])
        assert [r.status for r in outcome.results] == [MISSING, DUPLICATE_PR]


class TestInvoiceValueIsPartOfTheDuplicateKey:
    def test_same_key_different_value_is_not_a_duplicate(self):
        """2.4: two entries with the same GSTIN, type, number and date but
        different invoice values are two DIFFERENT transactions."""
        outcome = reconcile(
            [make_row(1, "100.00"), make_row(2, "250.00")],
            [],
        )
        assert DUPLICATE_PR not in [r.status for r in outcome.results]

    def test_sign_matters_in_the_duplicate_key(self):
        """A +100 invoice and a -100 credit note under one reference are not
        copies of each other, even though the engine compares on absolutes."""
        outcome = reconcile([make_row(1, "100.00"), make_row(2, "-100.00")], [])
        assert DUPLICATE_PR not in [r.status for r in outcome.results]

    def test_values_equal_to_two_decimals_are_duplicates(self):
        outcome = reconcile([make_row(1, "100.00"), make_row(2, "100.000")], [])
        assert DUPLICATE_PR in [r.status for r in outcome.results]

    def test_a_one_percent_difference_is_not_a_duplicate(self):
        """The 1% tolerance governs matching, never duplicate detection —
        duplicates require exact equality."""
        outcome = reconcile([make_row(1, "100.00"), make_row(2, "100.50")], [])
        assert DUPLICATE_PR not in [r.status for r in outcome.results]


class TestRegisterIsNeverAggregated:
    def test_two_duplicate_copies_are_not_summed(self):
        """2.4: purchase-register entries are never aggregated. If these were
        summed to 200 they would mismatch the 100 counterparty row."""
        outcome = reconcile(
            [make_row(1, "100.00"), make_row(2, "100.00")],
            [make_row(1, "100.00")],
        )
        matched = [r for r in outcome.results if r.status == MATCHED]
        assert len(matched) == 1
        assert matched[0].pr.invoice == __import__("decimal").Decimal("100.00")
