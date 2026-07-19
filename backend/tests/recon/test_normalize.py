from __future__ import annotations

from decimal import Decimal

import pytest

from app.recon.core.normalize import (
    is_valid_gstin,
    norm_doc_no,
    norm_gstin,
    norm_text,
    to_amount,
)


class TestDocNo:
    @pytest.mark.parametrize("raw", ["INV-001", "inv 001", "INV/001", " INV.001 ", "inv_001", "INV001"])
    def test_punctuation_and_case_are_ignored(self, raw):
        """Spec 2.3: ignore spaces, hyphens and slashes in document numbers."""
        assert norm_doc_no(raw) == "INV001"

    def test_leading_zeros_are_kept(self):
        """Only punctuation is licensed by the spec. Collapsing zeros would merge
        two genuinely different documents."""
        assert norm_doc_no("INV001") != norm_doc_no("INV1")

    def test_blank_is_none(self):
        assert norm_doc_no("") is None
        assert norm_doc_no("   ") is None
        assert norm_doc_no(None) is None
        assert norm_doc_no("---") is None


class TestGstin:
    @pytest.mark.parametrize("raw", ["27AAAAA0000A1Z5", " 27aaaaa0000a1z5 ", "27 AAAAA 0000 A1Z5"])
    def test_case_and_spaces_are_normalized(self, raw):
        assert norm_gstin(raw) == "27AAAAA0000A1Z5"

    def test_validity_is_separate_from_normalization(self):
        """A malformed GSTIN still normalizes: rejecting it here would drop a real
        row out of the reconciliation."""
        assert norm_gstin("not-a-gstin") == "NOT-A-GSTIN"
        assert is_valid_gstin("not-a-gstin") is False
        assert is_valid_gstin("27aaaaa0000a1z5") is True


class TestAmount:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("1,234.56", "1234.56"),
            ("₹1,234.56", "1234.56"),
            ("Rs. 1,234.56", "1234.56"),
            ("  1234.56  ", "1234.56"),
            ("18%", "18"),
            ("-100.50", "-100.50"),
            ("(1,234.00)", "-1234.00"),  # accounting notation
            (1234.56, "1234.56"),
            (0, "0"),
        ],
    )
    def test_parsing(self, raw, expected):
        assert to_amount(raw) == Decimal(expected)

    def test_returns_decimal_not_float(self):
        assert isinstance(to_amount("1234.56"), Decimal)

    @pytest.mark.parametrize("raw", ["", "   ", "-", "--", "NA", "N/A", "nil", None, "garbage"])
    def test_blank_and_unparseable_are_none(self, raw):
        assert to_amount(raw) is None

    def test_none_is_distinct_from_zero(self):
        """Load-bearing: the engine applies zero-value protection to a real zero
        but refuses to match a missing value."""
        assert to_amount("") is None
        assert to_amount("0") == Decimal("0")
        assert to_amount("") != to_amount("0")

    def test_no_float_drift(self):
        """The 1% tolerance compares at a boundary where binary float would lie."""
        assert to_amount("0.1") + to_amount("0.2") == Decimal("0.3")


class TestNormText:
    def test_collapses_punctuation_runs(self):
        assert norm_text("  Invoice   No.  ") == "invoice no"
        assert norm_text("GSTIN/UIN of Supplier") == "gstin uin of supplier"
