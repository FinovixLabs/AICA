from __future__ import annotations

import csv
from dataclasses import dataclass, field
from io import StringIO
import json
import os
from typing import Any, Mapping
import urllib.error
import urllib.request

from dotenv import load_dotenv


load_dotenv()

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_FORMAT_KEY = "gstr_3b"


class CsvGenerationError(RuntimeError):
    """Raised when the OpenAI-backed CSV generator cannot return valid CSV."""


class CsvRequestError(CsvGenerationError):
    """Raised when the CSV request payload is invalid."""


@dataclass(frozen=True)
class CsvFormat:
    key: str
    label: str
    filename_prefix: str
    columns: tuple[str, ...]
    instructions: str = ""
    source_aliases: Mapping[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class GeneratedCsv:
    text: str
    filename: str
    format_key: str


# Add or change CSV formats here. The rest of the module reads this registry.
CSV_FORMATS: dict[str, CsvFormat] = {
    "gstr_3b": CsvFormat(
        key="gstr_3b",
        label="GSTR-3B",
        filename_prefix="GSTR3B",
        columns=("table", "description", "igst", "cgst", "sgst"),
        instructions=(
            "This is a GSTR-3B summary output. Preserve table labels from the "
            "source rows and do not invent tax amounts."
        ),
        source_aliases={"description": ("desc",)},
    ),
    "gstr_1": CsvFormat(
        key="gstr_1",
        label="GSTR-1",
        filename_prefix="GSTR1",
        columns=(
            "section",
            "description",
            "taxable_value",
            "igst",
            "cgst",
            "sgst",
            "cess",
        ),
        instructions=(
            "This is an outward-supplies CSV. Keep invoice or section values "
            "from the source rows and leave unavailable numeric cells blank."
        ),
        source_aliases={
            "section": ("table", "return_table"),
            "description": ("desc", "particulars"),
            "taxable_value": ("taxableValue", "taxable_amount", "value"),
        },
    ),
    "gstr_2": CsvFormat(
        key="gstr_2",
        label="GSTR-2",
        filename_prefix="GSTR2",
        columns=(
            "section",
            "description",
            "taxable_value",
            "igst",
            "cgst",
            "sgst",
            "cess",
            "itc_eligibility",
        ),
        instructions=(
            "This is an inward-supplies or ITC CSV. Keep supplier or section "
            "context from the source rows and leave unavailable cells blank."
        ),
        source_aliases={
            "section": ("table", "return_table"),
            "description": ("desc", "particulars", "supplier"),
            "taxable_value": ("taxableValue", "taxable_amount", "value"),
            "itc_eligibility": ("itcEligibility", "eligibility", "itc"),
        },
    ),
}

FORMAT_ALIASES = {
    "gstr3b": "gstr_3b",
    "gstr_3": "gstr_3b",
    "gstr_3b": "gstr_3b",
    "gstr1": "gstr_1",
    "gstr_1": "gstr_1",
    "gstr2": "gstr_2",
    "gstr_2": "gstr_2",
    "gstr2a": "gstr_2",
    "gstr_2a": "gstr_2",
    "gstr2b": "gstr_2",
    "gstr_2b": "gstr_2",
}


def generate_csv(
    format_key: str | None,
    gstin: str,
    period: str,
    output_rows: Any = None,
    extra_context: Mapping[str, Any] | None = None,
) -> str:
    csv_format = get_csv_format(format_key)
    rows = _clean_output_rows(output_rows, csv_format)
    raw_csv = _request_openai_csv(
        csv_format=csv_format,
        gstin=gstin,
        period=period,
        output_rows=rows,
        extra_context=extra_context or {},
    )
    return _normalize_csv(raw_csv, csv_format)


def create_filing_csv(request_data: Mapping[str, Any]) -> GeneratedCsv:
    gstin = str(request_data.get("gstin", "")).strip().upper()
    period = str(request_data.get("period", "")).strip()
    if not gstin or not period:
        raise CsvRequestError("gstin and period are required")

    format_key = str(
        request_data.get("csv_type")
        or request_data.get("format")
        or request_data.get("return_type")
        or DEFAULT_FORMAT_KEY
    )
    csv_format = get_csv_format(format_key)
    context = request_data.get("context")
    csv_text = generate_csv(
        csv_format.key,
        gstin,
        period,
        request_data.get("rows", []),
        context if isinstance(context, Mapping) else {},
    )
    return GeneratedCsv(
        text=csv_text,
        filename=csv_filename(csv_format.key, gstin, period),
        format_key=csv_format.key,
    )


def generate_gstr3b_csv(gstin: str, period: str, output_rows: Any = None) -> str:
    return generate_csv("gstr_3b", gstin, period, output_rows)


def get_csv_format(format_key: str | None = None) -> CsvFormat:
    key = _normalize_format_key(format_key)
    try:
        return CSV_FORMATS[key]
    except KeyError as exc:
        supported = ", ".join(sorted(CSV_FORMATS))
        raise CsvRequestError(f"Unsupported CSV format '{format_key}'. Supported: {supported}") from exc


def csv_filename(format_key: str | None, gstin: str, period: str) -> str:
    csv_format = get_csv_format(format_key)
    return f"{csv_format.filename_prefix}_{gstin}_{period}.csv"


def _normalize_format_key(format_key: str | None) -> str:
    raw = (format_key or DEFAULT_FORMAT_KEY).strip().lower().replace("-", "_").replace(" ", "_")
    return FORMAT_ALIASES.get(raw, raw)


def _clean_output_rows(output_rows: Any, csv_format: CsvFormat) -> list[dict[str, Any]]:
    if not isinstance(output_rows, list):
        return []

    cleaned: list[dict[str, Any]] = []
    for row in output_rows[:100]:
        if not isinstance(row, dict):
            continue
        cleaned.append({column: _row_value(row, column, csv_format) for column in csv_format.columns})
    return cleaned


def _row_value(row: Mapping[str, Any], column: str, csv_format: CsvFormat) -> Any:
    keys = (column, *csv_format.source_aliases.get(column, ()))
    lowered = {str(k).lower(): v for k, v in row.items()}
    for key in keys:
        if key in row:
            return row[key]
        lowered_value = lowered.get(str(key).lower())
        if lowered_value is not None:
            return lowered_value
    return ""


def _request_openai_csv(
    csv_format: CsvFormat,
    gstin: str,
    period: str,
    output_rows: list[dict[str, Any]],
    extra_context: Mapping[str, Any],
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise CsvGenerationError("OPENAI_API_KEY is not configured")

    model = os.getenv("OPENAI_CHAT_MODEL", DEFAULT_MODEL)
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    prompt = _build_csv_prompt(
        csv_format=csv_format,
        gstin=gstin,
        period=period,
        output_rows=output_rows,
        extra_context=extra_context,
    )

    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You create GST filing CSV output for {csv_format.label}. "
                    "Return only RFC 4180 CSV. Do not use markdown. "
                    f"The header must be exactly: {_header(csv_format)}. "
                    "Do not invent tax amounts."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as res:
            body = res.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise CsvGenerationError(_openai_error_message(exc)) from exc
    except urllib.error.URLError as exc:
        raise CsvGenerationError(f"OpenAI request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise CsvGenerationError("OpenAI request timed out") from exc

    try:
        data = json.loads(body)
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise CsvGenerationError("OpenAI returned an unexpected response") from exc


def _build_csv_prompt(
    csv_format: CsvFormat,
    gstin: str,
    period: str,
    output_rows: list[dict[str, Any]],
    extra_context: Mapping[str, Any],
) -> str:
    rows_json = json.dumps(output_rows, ensure_ascii=True, default=str)
    context_json = json.dumps(extra_context, ensure_ascii=True, default=str)
    return (
        f"Create the downloadable {csv_format.label} CSV for GSTIN {gstin} "
        f"and period {period}.\n"
        f"Header: {_header(csv_format)}\n"
        f"Format instructions: {csv_format.instructions}\n"
        "Use these backend generated rows as the only source of amounts:\n"
        f"{rows_json}\n\n"
        "Extra context, if useful:\n"
        f"{context_json}\n\n"
        "Rules:\n"
        f"- Output exactly {len(csv_format.columns)} columns in this order: {_header(csv_format)}.\n"
        "- Use decimal-safe numeric cells; no currency symbols or thousands separators.\n"
        "- Leave unavailable cells blank.\n"
        "- If no source rows are provided, return only the header row."
    )


def _normalize_csv(raw_csv: str, csv_format: CsvFormat) -> str:
    text = _strip_markdown_fence(raw_csv)
    reader = csv.reader(StringIO(text))
    rows = [row for row in reader if any(cell.strip() for cell in row)]

    if not rows:
        rows = [list(csv_format.columns)]

    header = [cell.strip().lower() for cell in rows[0]]
    expected_header = [cell.lower() for cell in csv_format.columns]
    if header != expected_header:
        rows.insert(0, list(csv_format.columns))
    else:
        rows[0] = list(csv_format.columns)

    normalized = StringIO()
    writer = csv.writer(normalized, lineterminator="\n")
    width = len(csv_format.columns)
    for row in rows:
        padded = [*row, *([""] * width)]
        writer.writerow([str(cell).strip() for cell in padded[:width]])
    return normalized.getvalue()


def _header(csv_format: CsvFormat) -> str:
    return ",".join(csv_format.columns)


def _strip_markdown_fence(text: str) -> str:
    stripped = (text or "").strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _openai_error_message(exc: urllib.error.HTTPError) -> str:
    fallback = f"OpenAI request failed ({exc.code})"
    try:
        body = exc.read().decode("utf-8")
        data = json.loads(body)
    except Exception:
        return fallback

    error = data.get("error")
    if isinstance(error, dict) and error.get("message"):
        return str(error["message"])
    return fallback
