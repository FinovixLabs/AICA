"""IMS Outward matching (app.recon.service.match_outward).

IMS Outward is NOT the two-sided reconcile(). Its records are grouped by the
recipient's IMS action (Accepted / Rejected / Pending) taken from the file, and
each is validated against the Sales Register on Recipient GSTIN + invoice value
(1% tolerance) — tagged in_sr / not_in_sr. Rows with no GSTIN are B2C and are
skipped entirely. These tests lock in that contract.
"""
from __future__ import annotations

from dataclasses import replace

from app.recon.service import match_outward

from conftest import GSTIN_A, GSTIN_B, make_row


def _by_row(result: dict) -> dict[int, dict]:
    return {rec["row_no"]: rec for rec in result["records"]}


def test_buckets_by_given_status():
    """Records land in the terminal named by their own IMS status, verbatim."""
    ims = [
        make_row(1, 1000, ims_status="Accepted"),
        make_row(2, 1000, gstin=GSTIN_B, ims_status="Rejected"),
        make_row(3, 1000, gstin=GSTIN_B, doc_no="INV003", ims_status="Pending"),
    ]
    result = match_outward([], ims)
    assert result["buckets"] == {"accepted": 1, "rejected": 1, "pending": 1}


def test_no_action_is_accepted_while_blank_or_unknown_falls_to_pending():
    ims = [
        make_row(1, 1000, ims_status=""),
        make_row(2, 1000, gstin=GSTIN_B, ims_status="No Action"),
        make_row(3, 1000, gstin=GSTIN_B, doc_no="INV003", ims_status="something-odd"),
    ]
    result = match_outward([], ims)
    assert result["buckets"] == {"accepted": 1, "rejected": 0, "pending": 2}
    assert _by_row(result)[2]["status"] == "accepted"
    assert _by_row(result)[2]["takeable"] is False


def test_sr_match_on_gstin_and_value_within_tolerance():
    """in_sr when a Sales Register row shares the GSTIN and an invoice value within
    1%; not_in_sr when the value is off by more, or the GSTIN is absent."""
    sr = [make_row(1, 1000, gstin=GSTIN_A)]
    ims = [
        make_row(1, 1005, gstin=GSTIN_A, ims_status="Accepted"),   # +0.5% -> in_sr
        make_row(2, 1200, gstin=GSTIN_A, ims_status="Accepted"),   # +20%  -> not_in_sr
        make_row(3, 1000, gstin=GSTIN_B, ims_status="Accepted"),   # GSTIN absent -> not_in_sr
    ]
    rows = _by_row(match_outward(sr, ims))
    assert rows[1]["sr_match"] == "in_sr"
    assert rows[2]["sr_match"] == "not_in_sr"
    assert rows[3]["sr_match"] == "not_in_sr"
    assert match_outward(sr, ims)["totals"]["in_sr"] == 1
    assert match_outward(sr, ims)["totals"]["not_in_sr"] == 2


def test_b2c_rows_are_skipped_entirely():
    """A row with no Recipient GSTIN is B2C: not matched, not bucketed, not counted
    — only surfaced as skipped_b2c."""
    ims = [
        make_row(1, 1000, gstin=GSTIN_A, ims_status="Accepted"),
        make_row(2, 500, gstin=None, ims_status="Accepted"),
        make_row(3, 300, gstin="", ims_status="Rejected"),
    ]
    result = match_outward([], ims)
    assert result["skipped_b2c"] == 2
    assert result["totals"]["total"] == 1
    assert sum(result["buckets"].values()) == 1
    assert all(rec["supplier_gstin"] for rec in result["records"])


def test_takeable_only_for_rejected_and_pending():
    ims = [
        make_row(1, 1000, ims_status="Accepted"),
        make_row(2, 1000, gstin=GSTIN_B, ims_status="Rejected"),
        make_row(3, 1000, gstin=GSTIN_B, doc_no="INV003", ims_status="Pending"),
    ]
    rows = _by_row(match_outward([], ims))
    assert rows[1]["takeable"] is False
    assert rows[2]["takeable"] is True
    assert rows[3]["takeable"] is True


def test_display_fields_are_carried_through():
    """Trade/legal name and the two outward-only columns reach the output.

    make_row doesn't set these, so add them with a dataclass replace()."""
    base = make_row(1, 1000, ims_status="Accepted")
    ims = [replace(base, supplier_name="Acme Traders",
                   return_period="042025", reported_in_form="GSTR-1")]
    rec = match_outward([], ims)["records"][0]
    assert rec["supplier_name"] == "Acme Traders"
    assert rec["return_period"] == "042025"
    assert rec["reported_in_form"] == "GSTR-1"
