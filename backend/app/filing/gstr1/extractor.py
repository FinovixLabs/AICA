"""
Step 1 of the GSTR-1 pipeline — turn a raw, non-standard sales document into a
flat list of transaction dicts with canonical field names.

Primary path: OpenAI extraction ("perfect extraction" for arbitrary layouts).
Fallback path: deterministic CSV header-alias parse when no API key is available
or the AI call fails — so the pipeline never hard-depends on the network.

Blank / missing values are represented as ``None`` (per spec).
"""
from __future__ import annotations
import csv
import json
import re
import urllib.error
import urllib.request
from io import StringIO
from typing import Any

from app.core.config import get_settings

# Canonical raw fields the data-filler expects downstream.
EXTRACTED_FIELDS: list[str] = [
    "date",
    "party_name",
    "buyer_gstin",
    "invoice_number",
    "invoice_type",
    "note_type",
    "invoice_value",
    "taxable_value",
    "cgst",
    "sgst",
    "igst",
    "cess",
    "rate",
    "hsn",
    "pos",
    "reverse_charge",
    "ecommerce_gstin",
    "discount",
    "quantity",
    "uqc",
]

_SYSTEM_PROMPT = (
    "You are a precise data-extraction engine for Indian GST sales documents. "
    "You are given the raw text of a sales register / invoice export in an arbitrary "
    "layout. Extract EVERY transaction row into a JSON object of the exact shape:\n"
    '{ "transactions": [ { <fields> }, ... ] }\n'
    "Each transaction must use exactly these keys: "
    + ", ".join(EXTRACTED_FIELDS)
    + ".\n"
    "Rules:\n"
    "- Use null for any field that is blank, missing, or not present in the source.\n"
    "- Do NOT invent, infer, or compute values that are not in the source "
    "(the downstream engine derives taxes and place of supply).\n"
    "- Keep GSTIN, invoice_number, hsn and ecommerce_gstin as strings exactly as written.\n"
    "- Strip currency symbols and thousands separators from numeric fields, "
    "returning plain numbers (or null).\n"
    "- invoice_type / note_type: copy the source label verbatim if present "
    "(e.g. 'Credit Note', 'Debit Note', 'Nil Rated', 'Export'), else null.\n"
    "- Return ONLY the JSON object, no prose, no markdown fences."
)


class ExtractionError(RuntimeError):
    pass


# Above this size, a single-shot AI extraction cannot fit every row in the model's
# output window, so we go straight to the deterministic parser. (A future
# improvement is chunked/batched AI extraction for large registers.)
_AI_MAX_CHARS = 40000


def extract(raw_texts: list[str]) -> list[dict[str, Any]]:
    """
    Extract transactions from one or more raw document texts.
    Tries the AI extractor for smaller docs; falls back to a deterministic CSV
    parse for large docs or on any AI failure.
    """
    combined = "\n\n".join(t for t in raw_texts if t and t.strip())
    if not combined.strip():
        return []

    api_key = get_settings().OPENAI_API_KEY
    if api_key and len(combined) <= _AI_MAX_CHARS:
        try:
            rows = _extract_ai(combined, api_key)
            if rows:
                return rows
        except ExtractionError:
            pass  # fall through to deterministic parse
    return _extract_csv_fallback(raw_texts)


# ── AI extraction ──────────────────────────────────────────────────────────────
def _extract_ai(text: str, api_key: str) -> list[dict[str, Any]]:
    settings = get_settings()
    base_url = settings.OPENAI_BASE_URL.rstrip("/")
    payload = {
        "model": settings.OPENAI_CHAT_MODEL,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    }
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            body = res.read().decode("utf-8")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise ExtractionError(str(exc)) from exc

    try:
        content = json.loads(body)["choices"][0]["message"]["content"]
        parsed = json.loads(_strip_fence(content))
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ExtractionError("Unexpected AI response") from exc

    transactions = parsed.get("transactions") if isinstance(parsed, dict) else parsed
    if not isinstance(transactions, list):
        raise ExtractionError("AI response missing 'transactions' list")

    return [_canonical_row(row) for row in transactions if isinstance(row, dict)]


def _canonical_row(row: dict[str, Any]) -> dict[str, Any]:
    """Coerce an extracted row to the canonical field set, blanks -> None."""
    out: dict[str, Any] = {}
    for field in EXTRACTED_FIELDS:
        val = row.get(field)
        if isinstance(val, str) and not val.strip():
            val = None
        out[field] = val
    return out


def _strip_fence(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = s.removeprefix("```json").removeprefix("```").strip().removesuffix("```").strip()
    return s


# ── Deterministic CSV fallback ─────────────────────────────────────────────────
# Header aliases salvaged from the retired classifier.
_ALIASES: dict[str, list[str]] = {
    "invoice_number": ["invoice no", "inv no", "invoice number", "voucher no", "voucher number", "bill no", "ref no"],
    "date": ["invoice date", "date", "voucher date", "bill date"],
    "buyer_gstin": ["gstin of buyer", "buyer gstin", "party gstin", "gstin", "customer gstin", "recipient gstin", "gstin uin", "gstin uin of recipient"],
    "party_name": ["party name", "buyer name", "customer name", "name", "ledger name", "receiver name", "particulars"],
    "pos": ["place of supply", "pos", "state of supply", "supply state"],
    # 'sales' is the taxable sales column in Tally registers; 'value' is the invoice total.
    "taxable_value": ["taxable value", "taxable amount", "assessable value", "sales", "net amount"],
    "invoice_value": ["invoice value", "value", "gross total", "gross total sales", "total value", "bill amount"],
    "igst": ["igst", "integrated tax", "integrated gst"],
    "cgst": ["cgst", "central tax", "central gst"],
    "sgst": ["sgst", "state tax", "state gst", "utgst"],
    "cess": ["cess", "compensation cess"],
    "invoice_type": ["invoice type", "voucher type", "type", "supply type", "transaction type"],
    "note_type": ["note type", "type of note", "cr dr", "credit note", "debit note"],
    "hsn": ["hsn", "hsn code", "hsn sac", "hsn sac code"],
    "uqc": ["uqc", "unit", "unit of measure"],
    "quantity": ["qty", "quantity"],
    "rate": ["rate", "gst rate", "tax rate", "applicable of tax rate", "applicable tax rate"],
    "reverse_charge": ["reverse charge", "rcm"],
    "ecommerce_gstin": ["e commerce gstin", "ecommerce gstin"],
    "discount": ["discount", "discount sales"],
}

# Normalised alias -> canonical field, precomputed for header detection/mapping.
_ALIAS_INDEX: dict[str, str] = {}


def _norm(s: str) -> str:
    """Lower-case and collapse any run of non-alphanumerics to a single space."""
    return re.sub(r"[^a-z0-9]+", " ", str(s).strip().lower()).strip()


for _canon, _aliases in _ALIASES.items():
    for _a in _aliases:
        _ALIAS_INDEX.setdefault(_norm(_a), _canon)


def _normalise_header(raw: str) -> str:
    cleaned = _norm(raw)
    return _ALIAS_INDEX.get(cleaned, cleaned.replace(" ", "_"))


def _extract_csv_fallback(raw_texts: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for text in raw_texts:
        for block in _split_sheets(text):
            rows.extend(_parse_csv_block(block))
    return rows


def _split_sheets(text: str) -> list[str]:
    """Split multi-sheet exports (see uploading._extract_excel) on '# Sheet:' markers."""
    if "# Sheet:" not in text:
        return [text]
    blocks, current = [], []
    for line in text.splitlines():
        if line.startswith("# Sheet:"):
            if current:
                blocks.append("\n".join(current))
            current = []
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def _parse_csv_block(text: str) -> list[dict[str, Any]]:
    text = text.lstrip("﻿").strip()
    if not text:
        return []
    try:
        grid = list(csv.reader(StringIO(text)))
    except csv.Error:
        return []
    if not grid:
        return []

    header_idx = _find_header_row(grid)
    headers = [_normalise_header(h) for h in grid[header_idx]]
    known = [i for i, h in enumerate(headers) if h in EXTRACTED_FIELDS]
    if not known:
        return []

    out: list[dict[str, Any]] = []
    for raw_row in grid[header_idx + 1:]:
        row: dict[str, Any] = {f: None for f in EXTRACTED_FIELDS}
        for i in known:
            if i < len(raw_row):
                val = (raw_row[i] or "").strip()
                # First non-empty wins when a field maps from duplicate columns.
                if val and row[headers[i]] is None:
                    row[headers[i]] = val
        if _is_total_row(row) or not any(row[f] is not None for f in EXTRACTED_FIELDS):
            continue
        out.append(row)
    return out


_TOTAL_RE = re.compile(r"\b(grand\s*total|sub\s*total|total|opening|closing)\b", re.IGNORECASE)


def _is_total_row(row: dict[str, Any]) -> bool:
    """Tally registers embed subtotal/grand-total rows — drop them."""
    name = str(row.get("party_name") or "")
    return bool(_TOTAL_RE.search(name))


def _find_header_row(grid: list[list[str]]) -> int:
    """Pick the row that maps to the most canonical fields (Tally/Excel exports
    often carry several metadata rows before the real header)."""
    best_idx, best_score = 0, -1
    for idx, cells in enumerate(grid[:40]):
        score = sum(1 for c in cells if _normalise_header(c) in EXTRACTED_FIELDS)
        if score > best_score:
            best_idx, best_score = idx, score
    return best_idx if best_score >= 3 else 0
