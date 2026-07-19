"""Network-free tests for the AI mapping layer (app.recon.ai_mapping).

The AI call itself is monkeypatched out — these lock in the surrounding contract:
the deterministic fallback, the backfill-never-worse guarantee, and the header
validation that keeps a hallucinated or reused header from reaching the CA.
"""
from __future__ import annotations

import pytest

from app.recon import ai_mapping
from app.recon.schema_fields import fields_for_module, suggest_map as deterministic

# Headers a real messy purchase register might carry: Tally abbreviations the
# static alias table cannot know, plus a decoy buyer-GSTIN column.
MESSY = ["Our GSTIN", "Seller GSTIN No.", "Vch Type", "Vch No.", "Dt", "Net Amt", "GST", "Bill Total"]
# Headers the static alias table *does* recognise.
KNOWN = ["GSTIN of supplier", "Note type", "Invoice number", "Invoice date",
         "Taxable Value", "Combined Tax", "Total Invoice Value"]


@pytest.fixture
def no_ai(monkeypatch):
    """Force the deterministic path by clearing the key."""
    monkeypatch.setattr(ai_mapping, "get_settings", lambda: _Settings(""))


class _Settings:
    def __init__(self, key: str) -> None:
        self.OPENAI_API_KEY = key
        self.OPENAI_CHAT_MODEL = "gpt-4o-mini"
        self.OPENAI_BASE_URL = "https://api.openai.com/v1"


def test_no_key_returns_deterministic_map(no_ai):
    result = ai_mapping.suggest_map(KNOWN, [], "gstr2b")
    assert result == deterministic(KNOWN, "gstr2b")
    assert result["supplier_gstin"] == "GSTIN of supplier"
    assert result["invoice"] == "Total Invoice Value"


def test_transport_error_falls_back(monkeypatch):
    monkeypatch.setattr(ai_mapping, "get_settings", lambda: _Settings("sk-test"))

    def boom(*_args, **_kwargs):
        raise ai_mapping._MappingError("network down")

    monkeypatch.setattr(ai_mapping, "_ai_map", boom)
    assert ai_mapping.suggest_map(KNOWN, [], "gstr2b") == deterministic(KNOWN, "gstr2b")


def test_ai_result_overlays_and_backfills(monkeypatch):
    """AI wins where it answers; deterministic backfills the fields it leaves null,
    so coverage is never below the static baseline."""
    monkeypatch.setattr(ai_mapping, "get_settings", lambda: _Settings("sk-test"))

    # AI maps the abbreviations the aliases miss, but omits doc_type.
    def fake(headers, sample, fields):
        return {
            "supplier_gstin": "Seller GSTIN No.",
            "doc_no": "Vch No.",
            "doc_date": "Dt",
            "taxable": "Net Amt",
            "invoice": "Bill Total",
        }

    monkeypatch.setattr(ai_mapping, "_ai_map", fake)
    result = ai_mapping.suggest_map(MESSY, [], "gstr2b")
    assert result["supplier_gstin"] == "Seller GSTIN No."  # AI, not the decoy "Our GSTIN"
    assert result["invoice"] == "Bill Total"
    # Field the AI omitted and aliases also miss stays None, never a wrong guess.
    assert result["doc_type"] is None
    assert set(result) == set(fields_for_module("gstr2b"))


def test_validate_rejects_hallucinated_header():
    raw = {"supplier_gstin": "A GSTIN That Is Not In The File", "invoice": "Bill Total"}
    out = ai_mapping._validate(raw, MESSY, fields_for_module("gstr2b"))
    assert out["supplier_gstin"] is None
    assert out["invoice"] == "Bill Total"


def test_validate_matches_header_case_insensitively():
    raw = {"supplier_gstin": "seller  gstin no."}  # reformatted echo of "Seller GSTIN No."
    out = ai_mapping._validate(raw, MESSY, fields_for_module("gstr2b"))
    assert out["supplier_gstin"] == "Seller GSTIN No."


def test_validate_uses_each_header_once():
    raw = {"taxable": "Net Amt", "invoice": "Net Amt"}  # same header claimed twice
    out = ai_mapping._validate(raw, MESSY, fields_for_module("gstr2b"))
    assert (out["taxable"], out["invoice"]) == ("Net Amt", None)
