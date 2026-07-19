"""Orchestration for the GSTR-2B / IMS modules.

Pure over its inputs — no database, no FastAPI. It takes file paths plus a
confirmed mapping and returns plain dicts. The route layer (api/routes/recon.py)
handles persistence and HTTP; this file handles the domain flow:

    file on disk
      -> read_table()                       (tabular.py: never dedupes/drops)
      -> preview()                          for the mapping UI
      -> build_norm_rows() with the CA's confirmed map
      -> module-specific matcher            (GSTR-2B or IMS Inward)
      -> serialize_outcome()                plain JSON-able dicts for the frontend

IMS Outward is organized differently — it buckets records by the recipient's IMS
action and validates them against the Sales Register on GSTIN + invoice value, so
it takes its own path: match_outward().
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Mapping

from app.recon.core.doctype import (
    canonicalize,
    distinct_raw_values,
    suggest as suggest_doctype,
)
from app.recon.core.engine import (
    DEFAULT_TOLERANCE,
    ENGINE_VERSION,
    STATUS_CODES,
    STATUS_LABELS,
    UNRESOLVED,
    ExcludedRow,
    MatchRow,
    NormRow,
    ReconOutcome,
    reconcile,
)
from app.recon.core.normalize import (
    infer_date_order,
    norm_doc_no,
    norm_gstin,
    parse_date,
    to_amount,
)
from app.recon.core.tabular import Table, read_table
from app.recon.core.ims_inward import IMS_INWARD_ENGINE_VERSION, reconcile_inward
from app.recon import ai_mapping
from app.recon.schema_fields import (
    component_columns,
    fields_for_module,
)

_SAMPLE_ROWS = 8


# ── Preview (upload step) ─────────────────────────────────────────────────────
def preview(path: str, module: str, *, sheet: str | None = None) -> dict[str, Any]:
    """Read a file just enough to drive the mapping UI.

    Returns headers, a few sample rows, a suggested field map, and the workbook's
    sheet list. Nothing is matched or normalized yet.
    """
    alias_index = {k: v for k, v in _alias_norm(module).items()}
    table = read_table(path, alias_index=alias_index, sheet=sheet)
    headers = table.headers
    sample = [_json_cells(row) for row in table.rows[:_SAMPLE_ROWS]]
    return {
        "headers": headers,
        "sample_rows": sample,
        "sample_row_numbers": table.source_row_numbers[:_SAMPLE_ROWS],
        "row_count": table.row_count,
        "sheet_name": table.sheet_name,
        "sheet_names": table.sheet_names,
        "header_row": table.header_row + 1,
        "header_end_row": (table.header_end_row if table.header_end_row is not None else table.header_row) + 1,
        "omitted_count": len(table.omitted_rows),
        "omitted_rows": [
            {"row_no": row.row_no, "reason": row.reason, "label": row.label}
            for row in table.omitted_rows
        ],
        # AI reasons over the headers + sample rows to build the mapping plan the
        # CA confirms; it falls back to the static alias map (ai_mapping.py).
        "suggested_map": ai_mapping.suggest_map(headers, sample, module),
    }


def _alias_norm(module: str) -> dict[str, str]:
    from app.recon.schema_fields import alias_index_for

    return alias_index_for(module)


def doc_type_options(
    path: str, mapping: Mapping[str, str | None], module: str, *, sheet: str | None = None
) -> list[dict[str, str | None]]:
    """Distinct raw doc-type values in a file, each with a suggested canonical type.

    Feeds the doc-type confirmation step. The CA confirms these before a run so
    canonicalize() only ever reads a confirmed map (doctype.py contract).
    """
    header = mapping.get("doc_type")
    if not header:
        return []
    table = read_table(path, alias_index=_alias_norm(module), sheet=sheet)
    index = _header_index(table.headers, header)
    if index is None:
        return []
    raw_values = [row[index] if index < len(row) else None for row in table.rows]
    out: list[dict[str, str | None]] = []
    for raw in distinct_raw_values(raw_values):
        out.append({"raw": raw, "suggested": suggest_doctype(raw)})
    return out


# ── Build normalized rows from a confirmed mapping ────────────────────────────
def build_norm_rows(
    path: str,
    mapping: Mapping[str, str | None],
    *,
    module: str,
    doc_type_map: Mapping[str, str],
    date_order: str | None = None,
    sheet: str | None = None,
) -> tuple[list[NormRow], str, str]:
    """Turn a file into NormRows using the CA's confirmed column map.

    Returns (rows, date_order_used, date_evidence). row_no is the 1-based position
    in the source file — the engine's only tiebreaker — so it is assigned before
    anything is dropped (nothing is dropped here anyway).
    """
    table = read_table(path, alias_index=_alias_norm(module), sheet=sheet)
    idx = {field: _header_index(table.headers, header) for field, header in mapping.items() if header}
    components = component_columns(table.headers)

    date_col = idx.get("doc_date")
    if date_order:
        order, evidence = date_order, "confirmed by user"
    elif date_col is not None:
        samples = [row[date_col] if date_col < len(row) else None for row in table.rows]
        order, evidence = infer_date_order(samples)
    else:
        order, evidence = "DMY", "no date column mapped"

    rows: list[NormRow] = []
    positions = table.source_row_numbers or list(range(1, len(table.rows) + 1))
    for position, cells in zip(positions, table.rows):
        rows.append(
            NormRow(
                row_no=position,
                gstin=norm_gstin(_cell(cells, idx.get("supplier_gstin"))),
                supplier_name=_text_value(_cell(cells, idx.get("supplier_name"))),
                doc_type=_canon_doc_type(_cell(cells, idx.get("doc_type")), doc_type_map),
                doc_no=norm_doc_no(_cell(cells, idx.get("doc_no"))),
                doc_date=parse_date(_cell(cells, idx.get("doc_date")), order),
                taxable=to_amount(_cell(cells, idx.get("taxable"))),
                tax=_tax_value(cells, idx.get("tax"), components),
                invoice=to_amount(_cell(cells, idx.get("invoice"))),
                ims_status=_status_value(_cell(cells, idx.get("ims_status"))),
                return_period=_text_value(_cell(cells, idx.get("return_period"))),
                reported_in_form=_text_value(_cell(cells, idx.get("reported_in_form"))),
                raw={},
            )
        )
    return rows, order, evidence


def _canon_doc_type(raw: Any, doc_type_map: Mapping[str, str]) -> str | None:
    """Canonicalize through the confirmed map, defaulting an unmapped value to
    'other' rather than None so a stray type does not silently drop its row from
    matching — it is carried and, if it fails to find a partner, surfaces as a
    real Missing/Extra the CA can see."""
    canonical = canonicalize(raw, doc_type_map)
    if canonical is not None:
        return canonical
    return "other" if raw not in (None, "") else None


def _tax_value(cells: list[Any], tax_index: int | None, components: Mapping[str, int]) -> Decimal | None:
    """Combined tax: the mapped column if present, else the sum of any detected
    IGST/CGST/SGST/Cess columns (spec 2.2). Display-only, never affects status."""
    if tax_index is not None:
        direct = to_amount(_cell(cells, tax_index))
        if direct is not None:
            return direct
    if not components:
        return None
    parts = [to_amount(_cell(cells, index)) for index in components.values()]
    present = [part for part in parts if part is not None]
    return sum(present, Decimal("0")) if present else None


def _status_value(raw: Any) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


# ── Reconcile + serialize ─────────────────────────────────────────────────────
def run_reconcile(
    pr_rows: list[NormRow],
    cp_rows: list[NormRow],
    *,
    module: str,
    period: str | None = None,
) -> ReconOutcome:
    """Route each module to its own matching contract."""
    if module == "ims_inward":
        return reconcile_inward(pr_rows, cp_rows)
    return reconcile(pr_rows, cp_rows, period=period)


def serialize_outcome(outcome: ReconOutcome, *, module: str) -> dict[str, Any]:
    show_ims = module in ("ims_inward", "ims_outward")
    results = [serialize_match_row(row, show_ims=show_ims) for row in outcome.results]
    if module == "ims_inward":
        for result in results:
            # IMS Inward action is created in-app; it is never imported from the file.
            result["ims_status"] = None
            result["ims_action"] = "not_actioned"
            result["actionable"] = True
    excluded = [serialize_excluded(row) for row in outcome.excluded]
    return {
        "results": results,
        "excluded": excluded,
        "totals": _totals(outcome),
        "engine_version": IMS_INWARD_ENGINE_VERSION if module == "ims_inward" else ENGINE_VERSION,
    }


def _totals(outcome: ReconOutcome) -> dict[str, int]:
    totals = outcome.totals  # status -> count, plus 'excluded'
    totals["unresolved"] = sum(totals.get(status, 0) for status in UNRESOLVED)
    totals["total"] = len(outcome.results)
    return totals


def serialize_match_row(row: MatchRow, *, show_ims: bool) -> dict[str, Any]:
    """One reconciliation-list row as a flat, JSON-able dict for the frontend.

    Consolidates a GSTR-2B split group into single aggregated values (spec 3.3,
    6.1): cp_invoice/cp_taxable/cp_tax are already summed by the engine.
    """
    anchor = row.pr or (row.cp[0] if row.cp else None)
    ims_status = None
    if show_ims:
        ims_status = _first_ims_status(row)
    return {
        "seq": row.seq,
        "status": row.status,
        "status_code": row.status_code,
        "status_label": STATUS_LABELS.get(row.status, row.status),
        "actionable": row.status in UNRESOLVED,
        "key": row.key,
        "supplier_gstin": anchor.gstin if anchor else None,
        "supplier_name": _first_supplier_name(row),
        "doc_type": anchor.doc_type if anchor else None,
        "doc_no": anchor.doc_no if anchor else None,
        "doc_date": _iso(anchor.doc_date) if anchor else None,
        "pr_invoice": _f(row.pr.invoice) if row.pr else None,
        "pr_taxable": _f(row.pr.taxable) if row.pr else None,
        "pr_tax": _f(row.pr.tax) if row.pr else None,
        "cp_invoice": _f(row.cp_invoice),
        "cp_taxable": _f(row.cp_taxable),
        "cp_tax": _f(row.cp_tax),
        "cp_split_count": row.cp_split_count,
        "is_split": row.is_split,
        "diff_invoice": _f(row.diff_invoice),
        "diff_pct": _f(row.diff_pct),
        "reason": row.reason,
        "flags": list(row.flags),
        "ims_status": ims_status,
    }


def _first_ims_status(row: MatchRow) -> str | None:
    for source in ([row.pr] if row.pr else []) + list(row.cp):
        if source and source.ims_status:
            return source.ims_status
    return None


def _first_supplier_name(row: MatchRow) -> str | None:
    for source in ([row.pr] if row.pr else []) + list(row.cp):
        if source and source.supplier_name:
            return source.supplier_name
    return None


def serialize_excluded(row: ExcludedRow) -> dict[str, Any]:
    return {
        "side": row.side,
        "reason": row.reason,
        "supplier_gstin": row.row.gstin,
        "supplier_name": row.row.supplier_name,
        "doc_type": row.row.doc_type,
        "doc_no": row.row.doc_no,
        "doc_date": _iso(row.row.doc_date),
        "invoice": _f(row.row.invoice),
        "taxable": _f(row.row.taxable),
        "tax": _f(row.row.tax),
        "ims_status": row.row.ims_status,
    }


# ── IMS Outward: match against the Sales Register, bucket by IMS status ────────
# The recipient's action on the invoice, taken verbatim from the file's status
# column and collapsed onto the three terminals shown in the UI.
_OUTWARD_STATUS_BUCKET = {
    "accepted": "accepted",
    "accept": "accepted",
    "rejected": "rejected",
    "reject": "rejected",
    "pending": "pending",
    "no action": "accepted",
    "": "pending",
}

OUTWARD_BUCKETS = ("accepted", "rejected", "pending")


def _bucket_for_status(raw: str | None) -> str:
    """Map a raw IMS status onto a terminal. IMS Outward treats an explicit
    'No Action' as Accepted; unknown/blank values fall to Pending."""
    return _OUTWARD_STATUS_BUCKET.get((raw or "").strip().lower(), "pending")


def _within_tolerance(a: Decimal | None, b: Decimal | None, tolerance: Decimal) -> bool:
    """True when two invoice values agree within tolerance, on absolute values and
    with `a` (the Sales Register side) as the base — mirrors engine._compare (4.2-4.4)."""
    base = abs(a) if a is not None else Decimal("0")
    other = abs(b) if b is not None else Decimal("0")
    if base == Decimal("0"):
        return other == Decimal("0")
    return abs(other - base) / base <= tolerance


def match_outward(
    sr_rows: list[NormRow],
    ims_rows: list[NormRow],
    *,
    tolerance: Decimal = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """Match IMS Outward records against the client's Sales Register.

    This is deliberately NOT the two-sided reconcile(). IMS Outward is organized
    by the recipient's IMS action (Accepted / Rejected / Pending), taken from the
    file. Each record is checked against the Sales Register on Recipient GSTIN +
    total invoice value (1% tolerance) and tagged in_sr / not_in_sr — not every
    record needs a match; not_in_sr is a normal outcome.

    Rows with no Recipient GSTIN are B2C: they have no IMS counterparty and are
    skipped entirely — not matched, not bucketed, not counted (only surfaced as a
    skipped_b2c tally).
    """
    # Index the Sales Register by GSTIN -> its invoice values. B2C SR rows are
    # irrelevant to an IMS (B2B) match, so they never enter the index.
    sr_index: dict[str, list[Decimal | None]] = {}
    for row in sr_rows:
        if not row.gstin:
            continue
        sr_index.setdefault(row.gstin, []).append(row.invoice)

    records: list[dict[str, Any]] = []
    buckets = {name: 0 for name in OUTWARD_BUCKETS}
    in_sr = 0
    skipped_b2c = 0

    for row in ims_rows:
        if not row.gstin:  # B2C — not counted anywhere
            skipped_b2c += 1
            continue
        bucket = _bucket_for_status(row.ims_status)
        matched = any(
            _within_tolerance(sr_invoice, row.invoice, tolerance)
            for sr_invoice in sr_index.get(row.gstin, [])
        )
        buckets[bucket] += 1
        if matched:
            in_sr += 1
        records.append(
            {
                "row_no": row.row_no,
                "supplier_gstin": row.gstin,
                "supplier_name": row.supplier_name,
                "doc_no": row.doc_no,
                "doc_date": _iso(row.doc_date),
                "taxable": _f(row.taxable),
                "tax": _f(row.tax),
                "invoice": _f(row.invoice),
                "return_period": row.return_period,
                "reported_in_form": row.reported_in_form,
                "ims_status": row.ims_status,
                "status": bucket,
                "sr_match": "in_sr" if matched else "not_in_sr",
                "takeable": bucket in ("rejected", "pending"),
            }
        )

    total = len(records)
    return {
        "records": records,
        "buckets": buckets,
        "totals": {
            "total": total,
            "in_sr": in_sr,
            "not_in_sr": total - in_sr,
            **buckets,
        },
        "skipped_b2c": skipped_b2c,
        "engine_version": ENGINE_VERSION,
        # Live Accept/Reject and email delivery await GSP/SMTP integration.
        "actions_executable": False,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────
def _header_index(headers: list[str], header: str | None) -> int | None:
    if not header:
        return None
    try:
        return headers.index(header)
    except ValueError:
        return None


def _cell(cells: list[Any], index: int | None) -> Any:
    if index is None or index >= len(cells):
        return None
    return cells[index]


def _text_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _f(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


def _iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _json_cells(cells: list[Any]) -> list[Any]:
    """Sample cells for the preview, coerced to JSON-safe scalars."""
    out: list[Any] = []
    for cell in cells:
        if cell is None or isinstance(cell, (str, int, float, bool)):
            out.append(cell)
        elif isinstance(cell, (date,)):
            out.append(cell.isoformat())
        elif isinstance(cell, Decimal):
            out.append(float(cell))
        else:
            out.append(str(cell))
    return out
