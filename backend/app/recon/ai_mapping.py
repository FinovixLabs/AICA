"""AI-assisted column mapping for the recon upload step (spec 2.1-2.2).

A purchase register has no fixed schema: every accountant, ERP and Tally export
labels its columns differently, so the static alias table in schema_fields.py
inevitably misses columns and mis-maps look-alikes (supplier vs. buyer GSTIN,
invoice total vs. taxable base). This module asks an LLM to produce the mapping
PLAN instead — given the real headers and a few sample rows it reasons about
what each column actually holds and returns system_field -> header.

It is a suggestion layer, exactly like schema_fields.suggest_map: the plan
pre-fills the mapping UI and the CA still confirms it before any run. So a wrong
guess is corrected by a human, never acted on blindly.

The network is never a hard dependency. On a missing API key, a transport error,
or any malformed response we fall straight back to the deterministic alias map,
and even on success we backfill AI-null fields from the alias map — so the AI can
only ever add coverage, never remove it. This mirrors filing/gstr1/extractor.py,
the other AI-or-deterministic path in this codebase.
"""
from __future__ import annotations

import json
from typing import Any, Sequence

from app.core.config import get_settings
from app.core.openai_client import LLMError, post_chat
from app.recon.core.normalize import norm_text
from app.recon.schema_fields import (
    FIELD_DESCRIPTIONS,
    FIELD_LABELS,
    fields_for_module,
    suggest_map as deterministic_suggest_map,
)

__all__ = ["suggest_map"]

# Only a handful of rows are needed to disambiguate columns, and keeping the
# prompt small keeps the call cheap and fast for the interactive upload step.
_MAX_SAMPLE_ROWS = 6
_MAX_CELL_CHARS = 60
_TIMEOUT_SECONDS = 30

_SYSTEM_PROMPT = (
    "You are a precise column-mapping engine for Indian GST reconciliation files "
    "(purchase registers, GSTR-2B and IMS exports). You are given the exact column "
    "headers of one uploaded file, a few sample data rows, and a list of target "
    "system fields with descriptions. For each system field, choose the ONE header "
    "whose column best holds that field's data.\n"
    "Rules:\n"
    "- Return the header string EXACTLY as given, copied verbatim from the headers "
    "list. Never invent, translate, or reword a header.\n"
    "- Use null when no column fits a field. A wrong guess is worse than null.\n"
    "- Map each header to at most one field; do not reuse a header for two fields.\n"
    "- Use the sample rows as evidence: GSTINs look like '27AAACS1429B1Z0'; the "
    "invoice value is the largest amount and exceeds the taxable value; dates and "
    "document numbers are distinct from amounts.\n"
    "- Return ONLY a JSON object of the shape "
    '{ "mapping": { "<field>": "<header or null>", ... } }, no prose.'
)


def suggest_map(
    headers: list[str],
    sample_rows: Sequence[Sequence[Any]],
    module: str,
) -> dict[str, str | None]:
    """Propose system_field -> header for a module, AI-first.

    Returns a mapping over exactly the module's fields (fields_for_module). Any
    field the AI declines or that fails validation is backfilled from the
    deterministic alias map, so the result is never worse than the static one.
    """
    fields = fields_for_module(module)
    fallback = deterministic_suggest_map(headers, module)

    settings = get_settings()
    api_key = settings.OPENAI_API_KEY
    if not api_key or not headers:
        return fallback

    try:
        ai_map = _ai_map(headers, sample_rows, fields)
    except _MappingError:
        return fallback

    # AI wins where it has an opinion; the alias map backfills the rest. Coverage
    # only grows relative to the deterministic baseline.
    merged: dict[str, str | None] = dict(fallback)
    for field in fields:
        chosen = ai_map.get(field)
        if chosen is not None:
            merged[field] = chosen
    return merged


class _MappingError(RuntimeError):
    """Any reason the AI plan is unusable; the caller falls back on it."""


def _ai_map(
    headers: list[str],
    sample_rows: Sequence[Sequence[Any]],
    fields: tuple[str, ...],
) -> dict[str, str | None]:
    payload = {
        "model": get_settings().OPENAI_CHAT_MODEL,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _user_prompt(headers, sample_rows, fields)},
        ],
    }
    try:
        body = post_chat(payload, timeout=_TIMEOUT_SECONDS)
    except LLMError as exc:
        raise _MappingError(str(exc)) from exc

    try:
        content = json.loads(body)["choices"][0]["message"]["content"]
        parsed = json.loads(_strip_fence(content))
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise _MappingError("Unexpected AI response") from exc

    raw = parsed.get("mapping") if isinstance(parsed, dict) else None
    if not isinstance(raw, dict):
        raise _MappingError("AI response missing 'mapping' object")

    return _validate(raw, headers, fields)


def _user_prompt(
    headers: list[str],
    sample_rows: Sequence[Sequence[Any]],
    fields: tuple[str, ...],
) -> str:
    field_lines = [
        f"- {field} ({FIELD_LABELS.get(field, field)}): {FIELD_DESCRIPTIONS.get(field, '')}"
        for field in fields
    ]
    header_lines = [f"{i}: {h!r}" for i, h in enumerate(headers)]
    sample_lines = _sample_lines(headers, sample_rows)
    return (
        "TARGET SYSTEM FIELDS:\n"
        + "\n".join(field_lines)
        + "\n\nFILE HEADERS (index: header):\n"
        + "\n".join(header_lines)
        + "\n\nSAMPLE ROWS (header -> value):\n"
        + ("\n".join(sample_lines) if sample_lines else "(no sample rows)")
        + "\n\nReturn the mapping JSON now."
    )


def _sample_lines(headers: list[str], sample_rows: Sequence[Sequence[Any]]) -> list[str]:
    lines: list[str] = []
    for row in list(sample_rows)[:_MAX_SAMPLE_ROWS]:
        pairs = []
        for index, header in enumerate(headers):
            value = row[index] if index < len(row) else None
            if value in (None, ""):
                continue
            pairs.append(f"{header}={_clip(value)}")
        if pairs:
            lines.append("row: " + " | ".join(pairs))
    return lines


def _clip(value: Any) -> str:
    text = str(value)
    return text if len(text) <= _MAX_CELL_CHARS else text[:_MAX_CELL_CHARS] + "…"


def _validate(
    raw: dict[str, Any],
    headers: list[str],
    fields: tuple[str, ...],
) -> dict[str, str | None]:
    """Keep only fields the module offers, mapped to a real header. A returned
    header is matched to the file's headers case-/whitespace-insensitively so a
    trivially reformatted echo still resolves; each header is used at most once."""
    by_norm = {norm_text(h): h for h in headers}
    exact = set(headers)
    used: set[str] = set()
    result: dict[str, str | None] = {field: None for field in fields}
    for field in fields:
        candidate = raw.get(field)
        if not isinstance(candidate, str):
            continue
        header = candidate if candidate in exact else by_norm.get(norm_text(candidate))
        if header is not None and header not in used:
            result[field] = header
            used.add(header)
    return result


def _strip_fence(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = s.removeprefix("```json").removeprefix("```").strip().removesuffix("```").strip()
    return s
