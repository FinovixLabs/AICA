"""The multi-PR key collision.

Section 3.3 says to sum the counterparty rows and compare against "the single
purchase-register entry". Section 2.4 guarantees that presupposition can be
false: two PR rows with the same key and different invoice values are two
different transactions, and both survive duplicate collapse.

Summing anyway would compare an aggregate against one arbitrary entry and report
a false Mismatch on a pair that actually reconciles. So the engine flags the whole
key and matches nothing.
"""
from __future__ import annotations

from conftest import make_row

from app.recon.core.engine import (
    AMBIGUOUS,
    MATCHED,
    MISMATCH,
    STATUS_CODES,
    reconcile,
)


class TestCollision:
    def test_two_register_entries_on_one_key_flag_the_whole_key(self):
        outcome = reconcile(
            [make_row(1, "100.00"), make_row(2, "250.00")],
            [make_row(1, "100.00"), make_row(2, "250.00")],
        )
        assert {r.status for r in outcome.results} == {AMBIGUOUS}

    def test_nothing_is_matched(self):
        outcome = reconcile(
            [make_row(1, "100.00"), make_row(2, "250.00")],
            [make_row(1, "100.00"), make_row(2, "250.00")],
        )
        assert MATCHED not in [r.status for r in outcome.results]
        assert MISMATCH not in [r.status for r in outcome.results]

    def test_no_false_mismatch_is_manufactured(self):
        """The bug this design exists to prevent: summing 100+250 to 350 and
        comparing against one 100 entry would report a false Mismatch on a pair
        that reconciles perfectly."""
        outcome = reconcile(
            [make_row(1, "100.00"), make_row(2, "250.00")],
            [make_row(1, "100.00"), make_row(2, "250.00")],
        )
        for result in outcome.results:
            assert result.cp_invoice != __import__("decimal").Decimal("350.00")

    def test_the_register_is_never_aggregated(self):
        outcome = reconcile(
            [make_row(1, "100.00"), make_row(2, "250.00")],
            [make_row(1, "350.00")],
        )
        assert {r.status for r in outcome.results} == {AMBIGUOUS}

    def test_every_row_from_both_sides_is_surfaced(self):
        outcome = reconcile(
            [make_row(1, "100.00"), make_row(2, "250.00")],
            [make_row(1, "100.00"), make_row(2, "90.00"), make_row(3, "160.00")],
        )
        assert len(outcome.results) == 5, "2 register rows + 3 counterparty rows, none hidden"

    def test_carries_a_reason_and_a_flag(self):
        outcome = reconcile(
            [make_row(1, "100.00"), make_row(2, "250.00")],
            [],
        )
        for result in outcome.results:
            assert "ambiguous_key_multiple_pr" in result.flags
            assert "twice in the purchase register" in result.reason or "2 times" in result.reason

    def test_reason_counts_the_colliding_entries(self):
        outcome = reconcile(
            [make_row(1, "100.00"), make_row(2, "250.00"), make_row(3, "300.00")],
            [],
        )
        assert "3 times" in outcome.results[0].reason


class TestScope:
    def test_a_different_key_is_unaffected(self):
        """The collision is per-key. A clean key alongside an ambiguous one still
        reconciles normally."""
        outcome = reconcile(
            [
                make_row(1, "100.00", doc_no="COLLIDE"),
                make_row(2, "250.00", doc_no="COLLIDE"),
                make_row(3, "500.00", doc_no="CLEAN"),
            ],
            [
                make_row(1, "100.00", doc_no="COLLIDE"),
                make_row(2, "500.00", doc_no="CLEAN"),
            ],
        )
        clean = [r for r in outcome.results if r.key.endswith("|CLEAN|2025-04-03")]
        assert [r.status for r in clean] == [MATCHED]

    def test_duplicates_collapse_before_the_collision_check(self):
        """Three rows where two are true duplicates leaves two distinct entries —
        which is still a collision."""
        outcome = reconcile(
            [make_row(1, "100.00"), make_row(2, "100.00"), make_row(3, "250.00")],
            [],
        )
        statuses = [r.status for r in outcome.results]
        assert statuses.count(AMBIGUOUS) == 2
        assert "duplicate_pr" in statuses

    def test_duplicates_alone_are_not_a_collision(self):
        """Identical copies collapse to one retained entry, so the key is clean."""
        outcome = reconcile(
            [make_row(1, "100.00"), make_row(2, "100.00")],
            [make_row(1, "100.00")],
        )
        assert AMBIGUOUS not in [r.status for r in outcome.results]


class TestSorting:
    def test_ambiguous_sorts_into_the_actionable_band(self):
        assert STATUS_CODES[AMBIGUOUS] == "03"
        assert STATUS_CODES[AMBIGUOUS] < STATUS_CODES[MATCHED]
