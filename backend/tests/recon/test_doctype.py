from __future__ import annotations

from app.recon.core.doctype import (
    CANONICAL_DOC_TYPES,
    canonicalize,
    distinct_raw_values,
    suggest,
)


class TestSuggest:
    def test_portal_codes(self):
        assert suggest("R") == "invoice"
        assert suggest("CR") == "credit_note"
        assert suggest("ISD") == "isd"
        assert suggest("IMPG") == "impg"

    def test_accounting_spellings(self):
        assert suggest("Credit Note") == "credit_note"
        assert suggest("  tax invoice  ") == "invoice"
        assert suggest("Purchase") == "invoice"

    def test_unrecognised_suggests_nothing(self):
        """None forces the CA to choose. Defaulting to 'invoice' here would put a
        wrong value in the match key and mismatch every row under that type."""
        assert suggest("XYZ-Custom-Type") is None
        assert suggest("") is None
        assert suggest(None) is None

    def test_every_suggestion_is_canonical(self):
        for raw in ["R", "CR", "DR", "ISD", "IMPG", "Invoice", "Credit Note"]:
            assert suggest(raw) in CANONICAL_DOC_TYPES


class TestCanonicalize:
    def test_reads_only_the_confirmed_map(self):
        confirmed = {"r": "invoice", "cr": "credit_note"}
        assert canonicalize("R", confirmed) == "invoice"
        assert canonicalize(" cr ", confirmed) == "credit_note"

    def test_never_guesses(self):
        """suggest() knows 'ISD', but canonicalize must not use that knowledge —
        only what the CA confirmed."""
        assert suggest("ISD") == "isd"
        assert canonicalize("ISD", {"r": "invoice"}) is None

    def test_unmapped_returns_none_not_other(self):
        """None becomes a visible parse error. Silently bucketing into 'other'
        would corrupt the match key without telling anyone."""
        assert canonicalize("Mystery", {}) is None

    def test_rejects_a_non_canonical_confirmation(self):
        assert canonicalize("R", {"r": "not_a_real_type"}) is None


class TestDistinctRawValues:
    def test_ordered_by_first_appearance(self):
        assert distinct_raw_values(["Invoice", "CR", "Invoice", "DR"]) == ["Invoice", "CR", "DR"]

    def test_case_and_spacing_collapse(self):
        assert distinct_raw_values(["Invoice", " invoice ", "INVOICE"]) == ["Invoice"]

    def test_blanks_dropped(self):
        assert distinct_raw_values(["Invoice", "", None, "  "]) == ["Invoice"]
