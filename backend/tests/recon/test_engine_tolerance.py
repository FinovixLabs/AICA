"""The 1% tolerance, absolute values, and zero-value protection (spec 4.2-4.4)."""
from __future__ import annotations

from decimal import Decimal

import pytest
from conftest import make_row

from app.recon.core.engine import MATCHED, MISMATCH, reconcile


def status_of(pr_invoice, cp_invoice):
    outcome = reconcile([make_row(1, pr_invoice)], [make_row(1, cp_invoice)])
    assert len(outcome.results) == 1
    return outcome.results[0].status


class TestGoldenBoundary:
    """PR base = 100.00. The tolerance is inclusive: <= 1% is Matched (4.3)."""

    @pytest.mark.parametrize(
        "cp_invoice,expected",
        [
            ("100.00", MATCHED),
            ("100.99", MATCHED),
            ("101.00", MATCHED),   # exactly 1% — inclusive
            ("101.01", MISMATCH),  # first value past the boundary
            ("99.00", MATCHED),    # tolerance is symmetric
            ("98.99", MISMATCH),
        ],
    )
    def test_boundary(self, cp_invoice, expected):
        assert status_of("100.00", cp_invoice) == expected

    def test_purchase_register_is_the_base_not_the_counterparty(self):
        """4.3 names the PR value as the base. With PR=100 the 1% band is +-1.00;
        were the 2B the base, 101.02 would compute to 1.0097% and pass."""
        assert status_of("100.00", "101.02") == MISMATCH


class TestAbsoluteValues:
    def test_credit_notes_match_on_magnitude(self):
        assert status_of("-100.00", "-100.50") == MATCHED

    def test_sign_difference_is_matched_but_flagged(self):
        """4.2 mandates absolute comparison, so this is Matched. But a sign error
        is real, and abs() would hide it — hence the non-blocking chip."""
        outcome = reconcile([make_row(1, "-100.00")], [make_row(1, "100.00")])
        result = outcome.results[0]
        assert result.status == MATCHED
        assert "sign_mismatch" in result.flags

    def test_same_sign_carries_no_flag(self):
        outcome = reconcile([make_row(1, "100.00")], [make_row(1, "100.50")])
        assert outcome.results[0].flags == []


class TestZeroValueProtection:
    def test_zero_against_zero_is_matched(self):
        assert status_of("0", "0") == MATCHED

    def test_zero_against_nonzero_is_mismatch_without_dividing(self):
        assert status_of("0", "0.01") == MISMATCH

    def test_no_division_by_zero_is_attempted(self):
        outcome = reconcile([make_row(1, "0")], [make_row(1, "500.00")])
        result = outcome.results[0]
        assert result.status == MISMATCH
        assert result.diff_pct is None, "a percentage must not be computed against a zero base"

    def test_nonzero_against_zero_is_mismatch(self):
        assert status_of("100.00", "0") == MISMATCH


class TestMissingPurchaseRegisterValue:
    def test_never_matched(self):
        """The spec is silent. Matching on absent data is not defensible."""
        outcome = reconcile([make_row(1, None)], [make_row(1, "100.00")])
        result = outcome.results[0]
        assert result.status == MISMATCH
        assert "pr_invoice_missing" in result.flags

    def test_missing_is_not_treated_as_zero(self):
        """If None collapsed to 0, this would hit zero-value protection and match."""
        outcome = reconcile([make_row(1, None)], [make_row(1, "0")])
        assert outcome.results[0].status == MISMATCH


class TestDiff:
    def test_diff_is_signed_so_the_ui_can_say_which_side_is_higher(self):
        outcome = reconcile([make_row(1, "100.00")], [make_row(1, "150.00")])
        assert outcome.results[0].diff_invoice == Decimal("50.00")

        outcome = reconcile([make_row(1, "150.00")], [make_row(1, "100.00")])
        assert outcome.results[0].diff_invoice == Decimal("-50.00")

    def test_percentage_is_reported(self):
        outcome = reconcile([make_row(1, "100.00")], [make_row(1, "150.00")])
        assert outcome.results[0].diff_pct == Decimal("0.5")
