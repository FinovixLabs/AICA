from decimal import Decimal

import pytest

from app.recon.core.engine import NormRow
from app.recon.service import build_norm_rows, run_reconcile, serialize_outcome

openpyxl = pytest.importorskip("openpyxl")


def test_supplier_name_survives_mapping_and_uses_original_source_row(tmp_path):
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(["GSTIN of Supplier", "Trade/Legal name", "Invoice Details", None, None, None])
    worksheet.append([None, None, "Invoice number", "Document Type", "Invoice date", "Invoice value"])
    worksheet.append(["27AAAAA0000A1Z5", "Acme Traders", "INV-1", "Invoice", "03/04/2025", 1180])
    path = tmp_path / "gstr2b.xlsx"
    workbook.save(path)

    mapping = {
        "supplier_gstin": "GSTIN of Supplier",
        "supplier_name": "Trade/Legal name",
        "doc_no": "Invoice Details / Invoice number",
        "doc_type": "Invoice Details / Document Type",
        "doc_date": "Invoice Details / Invoice date",
        "invoice": "Invoice Details / Invoice value",
    }
    rows, _, _ = build_norm_rows(
        str(path), mapping, module="gstr2b", doc_type_map={"Invoice": "invoice"},
    )
    assert rows[0].row_no == 3
    assert rows[0].supplier_name == "Acme Traders"


def test_serialized_reconciliation_displays_name_without_using_it_as_key():
    pr = NormRow(
        row_no=1, gstin="27AAAAA0000A1Z5", supplier_name="PR Trade Name",
        doc_type="invoice", doc_no="INV-1", invoice=Decimal("1180"),
    )
    cp = NormRow(
        row_no=1, gstin="27AAAAA0000A1Z5", supplier_name="Different Portal Name",
        doc_type="invoice", doc_no="INV-1", invoice=Decimal("1180"),
    )
    result = serialize_outcome(run_reconcile([pr], [cp], module="gstr2b"), module="gstr2b")
    assert result["totals"]["matched"] == 1
    assert result["results"][0]["supplier_name"] == "PR Trade Name"
