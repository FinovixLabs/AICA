"""Engine invariants.

These two are worth more than the rest of the suite combined. They don't test a
case, they test a property — so they catch classes of future bug that no
enumerated example would.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from conftest import GSTIN_A, GSTIN_B, make_row

from app.recon.core.engine import (
    AMBIGUOUS,
    DUPLICATE_PR,
    EXTRA,
    STATUS_CODES,
    reconcile,
)


def _scenario():
    """A deliberately nasty mix: matched, mismatched, missing, extra, a split,
    exact duplicates, a key collision, a credit note, a zero and a None."""
    pr = [
        make_row(1, "1000.00", doc_no="MATCH", taxable="900.00", tax="100.00"),
        make_row(2, "1000.00", doc_no="MISMATCH", taxable="900.00", tax="100.00"),
        make_row(3, "1000.00", doc_no="MISSING", taxable="900.00", tax="100.00"),
        make_row(4, "1000.00", doc_no="SPLIT", taxable="900.00", tax="100.00"),
        make_row(5, "500.00", doc_no="DUP", taxable="450.00", tax="50.00"),
        make_row(6, "500.00", doc_no="DUP", taxable="450.00", tax="50.00"),
        make_row(7, "100.00", doc_no="COLLIDE", taxable="90.00", tax="10.00"),
        make_row(8, "250.00", doc_no="COLLIDE", taxable="225.00", tax="25.00"),
        make_row(9, "-300.00", doc_no="CREDIT", taxable="-270.00", tax="-30.00"),
        make_row(10, "0", doc_no="ZERO", taxable="0", tax="0"),
        make_row(11, None, doc_no="NOVALUE", taxable="900.00", tax="100.00"),
        make_row(12, "700.00", doc_no="OTHERGSTIN", gstin=GSTIN_B, taxable="630.00", tax="70.00"),
    ]
    cp = [
        make_row(1, "1000.00", doc_no="MATCH", taxable="900.00", tax="100.00"),
        make_row(2, "2500.00", doc_no="MISMATCH", taxable="2200.00", tax="300.00"),
        make_row(3, "600.00", doc_no="SPLIT", taxable="540.00", tax="60.00"),
        make_row(4, "400.00", doc_no="SPLIT", taxable="360.00", tax="40.00"),
        make_row(5, "500.00", doc_no="DUP", taxable="450.00", tax="50.00"),
        make_row(6, "100.00", doc_no="COLLIDE", taxable="90.00", tax="10.00"),
        make_row(7, "300.00", doc_no="CREDIT", taxable="270.00", tax="30.00"),
        make_row(8, "0", doc_no="ZERO", taxable="0", tax="0"),
        make_row(9, "100.00", doc_no="NOVALUE", taxable="90.00", tax="10.00"),
        make_row(10, "999.00", doc_no="EXTRA", taxable="900.00", tax="99.00"),
        make_row(11, "700.00", doc_no="OTHERGSTIN", gstin=GSTIN_B, taxable="630.00", tax="70.00"),
    ]
    return pr, cp


class TestPurchaseRegisterConservation:
    """Every purchase-register row is accounted for exactly once — never dropped,
    never counted twice. One assertion that catches any future aggregation or
    omission bug (2.4, 2.5)."""

    def test_every_register_row_appears_exactly_once(self):
        pr, cp = _scenario()
        outcome = reconcile(pr, cp)

        seen = [result.pr.row_no for result in outcome.results if result.pr is not None]
        seen += [item.row.row_no for item in outcome.excluded if item.side == "pr"]

        assert sorted(seen) == [row.row_no for row in pr]
        assert len(seen) == len(set(seen)), "no register row may appear in two results"

    def test_holds_under_period_scoping(self):
        pr = [
            make_row(1, "100.00", doc_no="APR", doc_date=date(2025, 4, 1)),
            make_row(2, "100.00", doc_no="MAY", doc_date=date(2025, 5, 1)),
            make_row(3, "100.00", doc_no="JUN", doc_date=date(2025, 6, 1)),
        ]
        outcome = reconcile(pr, [], period="2025-04")
        seen = [r.pr.row_no for r in outcome.results if r.pr] + [
            e.row.row_no for e in outcome.excluded if e.side == "pr"
        ]
        assert sorted(seen) == [1, 2, 3]

    def test_duplicates_are_reported_not_swallowed(self):
        """2.5: only the extra copies are omitted from matching — but they still
        have to reach the CA."""
        pr = [make_row(1, "100.00"), make_row(2, "100.00"), make_row(3, "100.00")]
        outcome = reconcile(pr, [make_row(1, "100.00")])
        seen = [r.pr.row_no for r in outcome.results if r.pr]
        assert sorted(seen) == [1, 2, 3]
        assert [r.status for r in outcome.results].count(DUPLICATE_PR) == 2

    def test_every_counterparty_row_is_accounted_for(self):
        pr, cp = _scenario()
        outcome = reconcile(pr, cp)

        seen: list[int] = []
        for result in outcome.results:
            seen += [row.row_no for row in result.cp]
        seen += [item.row.row_no for item in outcome.excluded if item.side == "cp"]

        assert sorted(seen) == sorted(row.row_no for row in cp)


class TestFinancialStatusIndependence:
    """4.1: invoice value alone decides Matched vs Mismatch. Taxable value and
    combined tax are displayed but never determine the status."""

    def test_perturbing_taxable_and_tax_changes_no_status(self):
        pr, cp = _scenario()
        baseline = [(r.status, r.key) for r in reconcile(pr, cp).results]

        def wreck(row):
            return make_row(
                row.row_no,
                row.invoice,
                gstin=row.gstin,
                doc_type=row.doc_type,
                doc_no=row.doc_no,
                doc_date=row.doc_date,
                taxable="999999.99",  # nonsense
                tax="-4242.42",
            )

        perturbed = [(r.status, r.key) for r in reconcile(
            [wreck(row) for row in pr], [wreck(row) for row in cp]
        ).results]

        assert perturbed == baseline

    def test_nulling_taxable_and_tax_changes_no_status(self):
        pr, cp = _scenario()
        baseline = [(r.status, r.key) for r in reconcile(pr, cp).results]

        def strip(row):
            return make_row(
                row.row_no,
                row.invoice,
                gstin=row.gstin,
                doc_type=row.doc_type,
                doc_no=row.doc_no,
                doc_date=row.doc_date,
                taxable=None,
                tax=None,
            )

        stripped = [(r.status, r.key) for r in reconcile(
            [strip(row) for row in pr], [strip(row) for row in cp]
        ).results]

        assert stripped == baseline

    def test_a_wildly_wrong_taxable_value_still_matches(self):
        outcome = reconcile(
            [make_row(1, "1000.00", taxable="1.00", tax="0.01")],
            [make_row(1, "1000.00", taxable="900000.00", tax="88888.00")],
        )
        assert outcome.results[0].status == "matched"


class TestDeterminism:
    def test_input_order_does_not_change_the_outcome(self):
        """row_no is the only tiebreaker anywhere, so shuffling the input lists
        must not move a single status."""
        pr, cp = _scenario()
        forward = [(r.status, r.key, r.pr.row_no if r.pr else None) for r in reconcile(pr, cp).results]
        backward = [
            (r.status, r.key, r.pr.row_no if r.pr else None)
            for r in reconcile(list(reversed(pr)), list(reversed(cp))).results
        ]
        assert forward == backward

    def test_repeated_runs_are_identical(self):
        pr, cp = _scenario()
        first = [(r.status, r.key, r.seq) for r in reconcile(pr, cp).results]
        second = [(r.status, r.key, r.seq) for r in reconcile(pr, cp).results]
        assert first == second


class TestStatusCodesNeverReachOutput:
    def test_codes_are_sort_keys_only(self):
        """5: 'the status codes are used only for backend sorting' and 'are not
        added to the contemporary Excel output file'. excel.py enforces the second
        half; this locks the codes themselves."""
        assert sorted(STATUS_CODES.values()) == ["00", "01", "02", "03", "10", "11"]

    def test_sorting_by_code_puts_actionable_first_and_matched_last(self):
        pr, cp = _scenario()
        outcome = reconcile(pr, cp)
        codes = [r.status_code for r in outcome.results]
        assert codes == sorted(codes)
        assert codes[-1] == STATUS_CODES["matched"]


class TestAmountTypes:
    def test_every_amount_is_decimal_never_float(self):
        pr, cp = _scenario()
        for result in reconcile(pr, cp).results:
            for value in (result.cp_invoice, result.cp_taxable, result.cp_tax, result.diff_invoice):
                assert value is None or isinstance(value, Decimal)
