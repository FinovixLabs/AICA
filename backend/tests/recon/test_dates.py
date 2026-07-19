from __future__ import annotations

from datetime import date, datetime

import pytest

from app.recon.core.normalize import infer_date_order, parse_date


class TestParseDate:
    @pytest.mark.parametrize(
        "raw,order,expected",
        [
            ("03/04/2025", "DMY", date(2025, 4, 3)),
            ("03/04/2025", "MDY", date(2025, 3, 4)),
            ("2025/04/03", "YMD", date(2025, 4, 3)),
            ("03-04-2025", "DMY", date(2025, 4, 3)),
            ("03.04.2025", "DMY", date(2025, 4, 3)),
            ("3/4/25", "DMY", date(2025, 4, 3)),
        ],
    )
    def test_numeric_forms_honour_the_declared_order(self, raw, order, expected):
        assert parse_date(raw, order) == expected

    def test_iso_wins_over_the_declared_order(self):
        """A 4-digit leading field is a year even in a DMY file."""
        assert parse_date("2025-04-03", "DMY") == date(2025, 4, 3)

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("03-Apr-2025", date(2025, 4, 3)),
            ("3 April 2025", date(2025, 4, 3)),
            ("Apr-03-2025", date(2025, 4, 3)),
            ("April 3, 2025", date(2025, 4, 3)),
        ],
    )
    def test_named_months_are_unambiguous(self, raw, expected):
        assert parse_date(raw, "MDY") == expected  # order is irrelevant here
        assert parse_date(raw, "DMY") == expected

    def test_native_types_pass_through(self):
        """openpyxl hands back real datetimes — no ambiguity to resolve."""
        assert parse_date(datetime(2025, 4, 3, 0, 0)) == date(2025, 4, 3)
        assert parse_date(date(2025, 4, 3)) == date(2025, 4, 3)

    def test_stringified_timestamps(self):
        assert parse_date("2025-04-03 00:00:00", "DMY") == date(2025, 4, 3)

    def test_two_digit_year_pivot(self):
        assert parse_date("01/01/25", "DMY") == date(2025, 1, 1)
        assert parse_date("01/01/99", "DMY") == date(1999, 1, 1)

    @pytest.mark.parametrize("raw", ["", None, "garbage", "31/02/2025", "45/13/2025"])
    def test_blank_and_impossible_are_none(self, raw):
        assert parse_date(raw, "DMY") is None


class TestInferDateOrder:
    def test_day_above_twelve_pins_dmy(self):
        order, evidence = infer_date_order(["03/04/2025", "25/12/2024"])
        assert order == "DMY"
        assert "25/12/2024" in evidence

    def test_month_position_above_twelve_pins_mdy(self):
        order, evidence = infer_date_order(["04/03/2025", "12/25/2024"])
        assert order == "MDY"
        assert "12/25/2024" in evidence

    def test_four_digit_lead_pins_ymd(self):
        order, _ = infer_date_order(["2025/04/03", "2024/12/25"])
        assert order == "YMD"

    def test_undecidable_defaults_to_dmy_and_says_so(self):
        """Nothing here disambiguates — every field is <= 12."""
        order, evidence = infer_date_order(["03/04/2025", "05/06/2025"])
        assert order == "DMY"
        assert "confirm" in evidence.lower()

    def test_conflicting_file_is_flagged_not_silently_resolved(self):
        """No single order reads this column. That's a real data problem and the
        evidence has to say so rather than picking a quiet winner."""
        order, evidence = infer_date_order(["25/12/2024", "12/25/2024"])
        assert order == "DMY"
        assert "conflict" in evidence.lower()

    def test_decided_at_file_level_not_per_row(self):
        """The whole point: one order applies to every row in the column. A
        per-row guess would read these two under different conventions and
        scatter false Missing/Extra pairs."""
        samples = ["03/04/2025", "25/12/2024"]
        order, _ = infer_date_order(samples)
        assert [parse_date(value, order) for value in samples] == [
            date(2025, 4, 3),
            date(2024, 12, 25),
        ]
