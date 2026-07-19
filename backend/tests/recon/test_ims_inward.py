from datetime import date

from app.recon.core.ims_inward import IMS_INWARD_ENGINE_VERSION, reconcile_inward
from app.recon.service import run_reconcile, serialize_outcome


def test_matches_on_identity_and_exact_invoice_while_ignoring_date_and_tax(row):
    pr = row(1, 1180, doc_date=date(2025, 4, 1), taxable=1000, tax=180)
    ims = row(1, 1180, doc_date=date(2026, 7, 31), taxable=999, tax=181)
    outcome = reconcile_inward([pr], [ims])
    assert outcome.results[0].status == "matched"
    assert outcome.results[0].key == "27AAAAA0000A1Z5|invoice|INV001"
    assert IMS_INWARD_ENGINE_VERSION == "ims-inward-1.0.0"


def test_same_identity_with_different_invoice_flags_mismatch(row):
    outcome = reconcile_inward([row(1, 1180)], [row(1, 1200)])
    result = outcome.results[0]
    assert result.status == "mismatch"
    assert result.flags == ["invoice_value_mismatch"]


def test_absent_on_either_side_is_missing_not_extra(row):
    outcome = reconcile_inward(
        [row(1, 100, doc_no="PR-ONLY")],
        [row(1, 200, doc_no="IMS-ONLY")],
    )
    assert [result.status for result in outcome.results] == ["missing", "missing"]
    assert all("not found" in (result.reason or "") for result in outcome.results)


def test_pairs_repeated_identity_by_invoice_value_not_source_order(row):
    pr = [row(1, 100), row(2, 200)]
    ims = [row(1, 200), row(2, 100)]
    outcome = reconcile_inward(pr, ims)
    assert [result.status for result in outcome.results] == ["matched", "matched"]


def test_service_routes_inward_to_dedicated_engine_and_initializes_action(row):
    outcome = run_reconcile([row(1, 1180)], [row(1, 1180)], module="ims_inward")
    serialized = serialize_outcome(outcome, module="ims_inward")
    result = serialized["results"][0]
    assert serialized["engine_version"] == IMS_INWARD_ENGINE_VERSION
    assert result["ims_action"] == "not_actioned"
    assert result["ims_status"] is None
    assert result["actionable"] is True


def test_missing_invoice_cell_never_auto_matches(row):
    outcome = reconcile_inward([row(1, None)], [row(1, None)])
    assert outcome.results[0].status == "mismatch"
    assert "invoice_value_mismatch" in outcome.results[0].flags
