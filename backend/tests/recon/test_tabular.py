"""Regression guard for the reader.

The headline test here is test_identical_rows_survive_*. app.services.uploading
flattens a workbook to text and drops duplicate lines (uploading.py:67-73), which
would delete exactly the rows spec 2.5 requires us to flag as Duplicate Purchase
Register Entry. read_table must never acquire that behaviour.
"""
from __future__ import annotations

from datetime import datetime

import pytest

from app.recon.core.errors import ParseError
from app.recon.core.tabular import read_table

openpyxl = pytest.importorskip("openpyxl")

ALIAS_INDEX = {
    "gstin of supplier": "supplier_gstin",
    "trade legal name": "supplier_name",
    "supplier name": "supplier_name",
    "document type": "doc_type",
    "invoice number": "doc_no",
    "invoice date": "doc_date",
    "taxable value": "taxable",
    "invoice value": "invoice_value",
}

HEADER = "GSTIN of Supplier,Invoice Number,Invoice Date,Invoice Value"
DUPLICATE_ROW = "27AAAAA0000A1Z5,INV-001,03/04/2025,1180.00"


def write_csv(tmp_path, lines):
    path = tmp_path / "register.csv"
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def write_xlsx(tmp_path, grid, sheet_title="Sheet1"):
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_title
    for row in grid:
        worksheet.append(row)
    path = tmp_path / "register.xlsx"
    workbook.save(path)
    return str(path)


class TestNoDedupe:
    def test_identical_rows_survive_csv(self, tmp_path):
        path = write_csv(tmp_path, [HEADER, DUPLICATE_ROW, DUPLICATE_ROW, DUPLICATE_ROW])
        table = read_table(path, alias_index=ALIAS_INDEX)
        assert table.row_count == 3, "byte-identical rows must all survive — 2.5 depends on it"

    def test_identical_rows_survive_xlsx(self, tmp_path):
        row = ["27AAAAA0000A1Z5", "INV-001", "03/04/2025", 1180.00]
        path = write_xlsx(
            tmp_path,
            [["GSTIN of Supplier", "Invoice Number", "Invoice Date", "Invoice Value"], row, list(row)],
        )
        table = read_table(path, alias_index=ALIAS_INDEX)
        assert table.row_count == 2


class TestHeaderDetection:
    def test_skips_banner_rows(self, tmp_path):
        """Government 2B exports and Tally registers both lead with metadata."""
        path = write_csv(
            tmp_path,
            [
                "Goods and Services Tax - GSTR-2B",
                "Financial Year,2025-26",
                "Tax Period,April",
                "",
                HEADER,
                DUPLICATE_ROW,
            ],
        )
        table = read_table(path, alias_index=ALIAS_INDEX)
        assert table.header_row == 4
        assert table.headers[0] == "GSTIN of Supplier"
        assert table.row_count == 1

    def test_falls_back_to_widest_row_not_row_zero(self, tmp_path):
        """With no alias hits, a one-cell title banner must not win."""
        path = write_csv(tmp_path, ["Some Title Banner", "A,B,C,D", "1,2,3,4"])
        table = read_table(path, alias_index=None)
        assert table.header_row == 1
        assert table.headers == ["A", "B", "C", "D"]

    def test_flattens_two_row_gstr2b_header_and_uses_gstin_regex_boundary(self, tmp_path):
        path = write_xlsx(
            tmp_path,
            [
                ["GSTIN of Supplier", "Trade/Legal name", "Invoice Details", None, None, None, "Taxable Value"],
                [None, None, "Invoice number", "Document Type", "Invoice date", "Invoice value", None],
                ["27AAAAA0000A1Z5", "Acme Traders", "INV-1", "Invoice", "03/04/2025", 1180, 1000],
            ],
        )
        table = read_table(path, alias_index=ALIAS_INDEX)
        assert table.header_row == 0
        assert table.header_end_row == 1
        assert table.headers[1] == "Trade/Legal name"
        assert table.headers[2] == "Invoice Details / Invoice number"
        assert table.headers[5] == "Invoice Details / Invoice value"
        assert table.row_count == 1
        assert table.rows[0][0] == "27AAAAA0000A1Z5"
        assert table.source_row_numbers == [3]
        assert table.omitted_rows[0].reason == "header_continuation"

    def test_transaction_after_single_header_is_not_treated_as_header(self, tmp_path):
        """The existing GSTIN regex marks the adjacent row as data, not header text."""
        path = write_csv(tmp_path, [HEADER, DUPLICATE_ROW])
        table = read_table(path, alias_index=ALIAS_INDEX)
        assert table.header_end_row == table.header_row
        assert table.row_count == 1


class TestStructuralOmission:
    def test_omits_grand_total_but_keeps_transaction_and_source_row_number(self, tmp_path):
        path = write_xlsx(
            tmp_path,
            [
                ["GSTIN of Supplier", "Supplier Name", "Invoice Details", None, None, None, "Taxable Value"],
                [None, None, "Invoice Number", "Document Type", "Invoice Date", "Invoice Value", None],
                ["27AAAAA0000A1Z5", "Acme Traders", "INV-1", "Invoice", "03/04/2025", 1180, 1000],
                ["GRAND TOTAL", None, None, None, None, 1180, 1000],
            ],
        )
        table = read_table(path, alias_index=ALIAS_INDEX)
        assert table.row_count == 1
        assert table.source_row_numbers == [3]
        footer = next(row for row in table.omitted_rows if row.reason == "total_footer")
        assert footer.row_no == 4
        assert footer.label == "GRAND TOTAL"

    def test_total_shaped_document_number_with_identity_is_retained(self, tmp_path):
        path = write_csv(
            tmp_path,
            [HEADER, "27AAAAA0000A1Z5,TOTAL-001,03/04/2025,1180.00"],
        )
        table = read_table(path, alias_index=ALIAS_INDEX)
        assert table.row_count == 1
        assert not any(row.reason == "total_footer" for row in table.omitted_rows)

    def test_invalid_gstin_transaction_is_retained_for_review(self, tmp_path):
        path = write_csv(tmp_path, [HEADER, "BAD-GSTIN,INV-2,03/04/2025,1180.00"])
        assert read_table(path, alias_index=ALIAS_INDEX).row_count == 1


class TestReading:
    def test_blank_spacer_rows_dropped_data_rows_kept(self, tmp_path):
        path = write_csv(tmp_path, [HEADER, DUPLICATE_ROW, ",,,", DUPLICATE_ROW])
        assert read_table(path, alias_index=ALIAS_INDEX).row_count == 2

    def test_native_datetimes_survive_xlsx(self, tmp_path):
        """Preserving the real cell type is why we use openpyxl rather than
        round-tripping through text: no date-order ambiguity for these."""
        path = write_xlsx(
            tmp_path,
            [
                ["GSTIN of Supplier", "Invoice Number", "Invoice Date", "Invoice Value"],
                ["27AAAAA0000A1Z5", "INV-001", datetime(2025, 4, 3), 1180.00],
            ],
        )
        table = read_table(path, alias_index=ALIAS_INDEX)
        assert isinstance(table.rows[0][2], datetime)

    def test_ragged_rows_keep_their_cells(self, tmp_path):
        path = write_csv(tmp_path, ["A,B", "1,2,3"])
        table = read_table(path, alias_index=None)
        assert table.records()[0] == {"A": "1", "B": "2", "column_2": "3"}

    def test_short_rows_pad_with_none(self, tmp_path):
        path = write_csv(tmp_path, ["A,B,C", "1"])
        assert read_table(path, alias_index=None).records()[0] == {"A": "1", "B": None, "C": None}

    def test_blank_header_cells_stay_addressable(self, tmp_path):
        path = write_csv(tmp_path, ["A,,C", "1,2,3"])
        assert read_table(path, alias_index=None).headers == ["A", "column_1", "C"]


class TestErrors:
    def test_unsupported_extension(self, tmp_path):
        path = tmp_path / "notes.pdf"
        path.write_text("x", encoding="utf-8")
        with pytest.raises(ParseError, match="Unsupported file type"):
            read_table(str(path))

    def test_empty_file(self, tmp_path):
        path = tmp_path / "empty.csv"
        path.write_text("", encoding="utf-8")
        with pytest.raises(ParseError, match="empty"):
            read_table(str(path))
