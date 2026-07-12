"""
GSTR-1 pipeline orchestrator:

    raw document text(s)
      -> extractor.extract        (AI, with deterministic fallback)
      -> beta_register.build       (data filler -> beta sales register)
      -> validator.validate        (regex + duplicate-invoice checks)
      -> template_writer.fill       (exact government workbook)

Returns the beta register, a per-bucket summary, all flags, the CA notice, and
the path to the generated workbook.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any

from app.filing.gstr1 import beta_register, extractor, template_writer, validator
from app.filing.gstr1.beta_register import _num
from app.filing.gstr1.constants import BETA_COLUMNS, SEGREGATORS, pos_label


def run(raw_texts: list[str], client_gstin: str, output_path: Path) -> dict[str, Any]:
    extracted = extractor.extract(raw_texts)
    if not extracted:
        return {
            "beta_register": [], "summary": _empty_summary(), "flags": [],
            "ca_notice": None, "output_path": None, "row_count": 0,
        }

    # Keep only rows with a usable monetary base; rows where the source layout
    # dropped the taxable/invoice value are surfaced for review rather than
    # silently corrupting the totals.
    valid, needs_review = _partition_valid(extracted)
    review_flags: list[dict[str, Any]] = []
    if needs_review:
        review_flags.append({
            "type": "unparsable_rows",
            "severity": "warning",
            "count": needs_review,
            "message": (
                f"{needs_review} row(s) could not be reliably parsed from the source "
                f"layout (missing taxable/invoice value) and were excluded. Re-run with "
                f"AI extraction or check the source file."
            ),
        })

    beta_rows, tax_flags = beta_register.build(valid, client_gstin)
    tax_flags = review_flags + tax_flags
    result = validator.validate(beta_rows)
    flags = tax_flags + result["flags"]

    output = template_writer.fill(beta_rows, output_path)

    return {
        "beta_register": beta_rows,
        "summary": _summarise(beta_rows),
        "flags": flags,
        "ca_notice": _rebuild_notice(flags, result.get("ca_notice")),
        "output_path": str(output),
        "row_count": len(beta_rows),
    }


def rebuild(beta_rows: list[dict[str, Any]], output_path: Path) -> dict[str, Any]:
    """Revalidate an edited beta register and rebuild its workbook/summary."""
    result = validator.validate(beta_rows)
    flags = result["flags"]
    output = template_writer.fill(beta_rows, output_path)
    return {
        "beta_register": beta_rows,
        "summary": _summarise(beta_rows),
        "flags": flags,
        "ca_notice": _rebuild_notice(flags, result.get("ca_notice")),
        "output_path": str(output),
        "row_count": len(beta_rows),
    }


def apply_edit_operations(
    beta_rows: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    *,
    instruction: str = "",
    client_gstin: str | None = None,
) -> list[dict[str, Any]]:
    """Apply a guarded operation list without mutating the current UI payload."""
    rows = [{key: row.get(key) for key in BETA_COLUMNS} for row in beta_rows]
    allowed = set(BETA_COLUMNS)

    operations = _scope_operations_to_instruction(rows, operations, instruction)
    operation_kinds = [str(operation.get("op") or "").strip().lower() for operation in operations]
    updates = [operation for operation, kind in zip(operations, operation_kinds) if kind == "update"]
    deletes = [operation for operation, kind in zip(operations, operation_kinds) if kind == "delete"]
    additions = [operation for operation, kind in zip(operations, operation_kinds) if kind == "add"]
    if len(updates) + len(deletes) + len(additions) != len(operations):
        raise ValueError("AI returned an unsupported register operation")

    for operation in updates:
        index = _normalise_row_index(operation.get("row_index"))
        changes = operation.get("changes")
        if not isinstance(index, int) or not 0 <= index < len(rows):
            raise ValueError("Edit targeted a row that does not exist")
        if not isinstance(changes, dict) or not changes:
            raise ValueError("Edit did not contain any field changes")
        changes = _normalise_changes(changes)
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"Edit contains unsupported fields: {', '.join(sorted(unknown))}")
        rows[index].update(changes)
        _recalculate_dependent_values(rows[index], set(changes), client_gstin)

    delete_indexes: list[int] = []
    for operation in deletes:
        index = _normalise_row_index(operation.get("row_index"))
        if not isinstance(index, int) or not 0 <= index < len(rows):
            raise ValueError("Delete targeted a row that does not exist")
        delete_indexes.append(index)
    for index in sorted(set(delete_indexes), reverse=True):
        rows.pop(index)

    for operation in additions:
        row = operation.get("row")
        if not isinstance(row, dict):
            raise ValueError("Add operation did not contain a row")
        row = _normalise_changes(row)
        unknown = set(row) - allowed
        if unknown:
            raise ValueError(f"Added row contains unsupported fields: {', '.join(sorted(unknown))}")
        rows.append({key: row.get(key) for key in BETA_COLUMNS})

    for row in rows:
        if row.get("segregator") not in SEGREGATORS:
            raise ValueError("Edited row has an unsupported GSTR-1 bucket")
    return rows


def _scope_operations_to_instruction(
    rows: list[dict[str, Any]], operations: list[dict[str, Any]], instruction: str,
) -> list[dict[str, Any]]:
    """Prevent a specifically targeted row command from being broadcast to other rows."""
    targets = _explicit_target_indexes(rows, instruction)
    if not targets:
        return operations

    scoped: list[dict[str, Any]] = []
    row_operations: list[dict[str, Any]] = []
    for operation in operations:
        kind = str(operation.get("op") or "").strip().lower()
        if kind in {"update", "delete"}:
            row_operations.append(operation)
            if _normalise_row_index(operation.get("row_index")) in targets:
                scoped.append(operation)

    if scoped:
        return scoped
    if len(targets) == 1 and row_operations:
        remapped = dict(row_operations[0])
        remapped["row_index"] = next(iter(targets))
        return [remapped]
    raise ValueError("The requested entry could not be matched to the proposed edit")


def _explicit_target_indexes(rows: list[dict[str, Any]], instruction: str) -> set[int]:
    text = instruction.casefold()
    voucher_matches = {
        index for index, row in enumerate(rows)
        if str(row.get("voucher_number") or "").strip()
        and re.search(
            rf"(?<![a-z0-9]){re.escape(str(row.get('voucher_number')).strip().casefold())}(?![a-z0-9])",
            text,
        )
    }
    if voucher_matches:
        return voucher_matches

    for field in ("gstin", "particulars", "date", "hsn", "ecommerce_gstin"):
        matches = {
            index for index, row in enumerate(rows)
            if len(str(row.get(field) or "").strip()) >= 4
            and str(row.get(field)).strip().casefold() in text
        }
        if len(matches) == 1:
            return matches

    numeric = re.search(r"\b(?:row|entry|record)\s*(?:number|no\.?|#)?\s*(\d+)\b", text)
    if numeric:
        one_based = int(numeric.group(1))
        return {one_based - 1} if 1 <= one_based <= len(rows) else set()

    ordinals = {"first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4}
    for word, index in ordinals.items():
        if re.search(rf"\b{word}\s+(?:row|entry|record)\b", text) and index < len(rows):
            return {index}
    return set()


def _recalculate_dependent_values(
    row: dict[str, Any], changed_fields: set[str], client_gstin: str | None,
) -> None:
    tax_basis_changed = bool(
        changed_fields & {"applicable_tax_rate", "taxable_value", "gross_total_sales", "pos"}
    )
    tax_amount_changed = bool(changed_fields & {"igst", "cgst", "sgst", "cess", "round_off"})
    if not tax_basis_changed and not tax_amount_changed:
        return

    taxable = _num(row.get("taxable_value"))
    gross_sales = _num(row.get("gross_total_sales"))
    if "gross_total_sales" in changed_fields and gross_sales is not None:
        base = gross_sales
        row["taxable_value"] = round(base, 2)
    else:
        base = taxable if taxable is not None else gross_sales
    if base is None:
        raise ValueError("Cannot recalculate GST without gross sales or taxable value")

    # Gross sales is the pre-tax base; invoice value is gross sales plus GST.
    row["gross_total_sales"] = round(base, 2)
    if tax_basis_changed:
        rate = _num(row.get("applicable_tax_rate"))
        if rate is None:
            raise ValueError("Cannot recalculate GST without an applicable tax rate")
        total_tax = round(base * rate / 100.0, 2)
        if _is_inter_state(row, client_gstin):
            row["igst"], row["cgst"], row["sgst"] = total_tax, 0.0, 0.0
        else:
            half = round(total_tax / 2.0, 2)
            row["igst"], row["cgst"], row["sgst"] = 0.0, half, round(total_tax - half, 2)

    gst = sum(_num(row.get(key)) or 0.0 for key in ("igst", "cgst", "sgst"))
    cess = _num(row.get("cess")) or 0.0
    round_off = _num(row.get("round_off")) or 0.0
    row["invoice_value"] = round(base + gst + cess + round_off, 2)


def _is_inter_state(row: dict[str, Any], client_gstin: str | None) -> bool:
    client_state = str(client_gstin or "").strip()[:2]
    pos = str(row.get("pos") or "").strip()[:2]
    if len(client_state) == 2 and client_state.isdigit() and len(pos) == 2 and pos.isdigit():
        return client_state != pos
    return bool((_num(row.get("igst")) or 0.0) and not ((_num(row.get("cgst")) or 0.0) or (_num(row.get("sgst")) or 0.0)))


def _require_scalar_values(values: dict[str, Any]) -> None:
    if any(isinstance(value, (dict, list, tuple, set)) for value in values.values()):
        raise ValueError("Edit contains a non-scalar cell value")


def _normalise_row_index(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


_FIELD_ALIASES = {
    "invoice_date": "date",
    "voucher_date": "date",
    "party_name": "particulars",
    "receiver_name": "particulars",
    "customer_name": "particulars",
    "invoice_type": "voucher_type",
    "invoice_number": "voucher_number",
    "invoice_no": "voucher_number",
    "buyer_gstin": "gstin",
    "recipient_gstin": "gstin",
    "invoice_amount": "invoice_value",
    "gross_sales": "gross_total_sales",
    "gross_total": "gross_total_sales",
    "cgst_amount": "cgst",
    "sgst_amount": "sgst",
    "igst_amount": "igst",
    "rounding": "round_off",
    "round_off_amount": "round_off",
    "discount_amount": "discount",
    "category": "segregator",
    "bucket": "segregator",
    "taxable_amount": "taxable_value",
    "place_of_supply": "pos",
    "place_of_supply_code": "pos",
    "rcm": "reverse_charge",
    "rate": "applicable_tax_rate",
    "rate_percentage": "applicable_tax_rate",
    "gst_rate": "applicable_tax_rate",
    "gst_rate_percentage": "applicable_tax_rate",
    "tax_rate": "applicable_tax_rate",
    "tax_rate_percentage": "applicable_tax_rate",
    "e_commerce_gstin": "ecommerce_gstin",
    "ecommerce_operator_gstin": "ecommerce_gstin",
    "cess_amount": "cess",
    "hsn_code": "hsn",
}

_NUMERIC_COLUMNS = {
    "invoice_value", "gross_total_sales", "cgst", "sgst", "round_off", "igst",
    "discount", "taxable_value", "applicable_tax_rate", "cess",
}


def _normalise_changes(changes: dict[str, Any]) -> dict[str, Any]:
    _require_scalar_values(changes)
    normalised: dict[str, Any] = {}
    for raw_key, raw_value in changes.items():
        key = str(raw_key).strip().lower().replace(" ", "_").replace("-", "_")
        key = _FIELD_ALIASES.get(key, key)
        value = _normalise_cell_value(key, raw_value)
        normalised[key] = value
    return normalised


def _normalise_cell_value(key: str, value: Any) -> Any:
    if value is None or value == "":
        return None
    if key in _NUMERIC_COLUMNS:
        parsed = _num(value)
        if parsed is None:
            raise ValueError(f"'{value}' is not a valid number for {key}")
        return parsed
    if key in {"gstin", "ecommerce_gstin"}:
        return str(value).strip().upper() or None
    if key == "reverse_charge":
        return "Y" if str(value).strip().lower() in {"y", "yes", "true", "1", "rcm"} else "N"
    if key == "segregator":
        bucket = str(value).strip().lower().replace("_", "-")
        aliases = {"b2b": "B2B", "b2cl": "B2CL", "b2cs": "B2CS",
                   "nil": "Nil-rated", "nil-rated": "Nil-rated", "nil rated": "Nil-rated"}
        return aliases.get(bucket, str(value).strip())
    if key == "pos":
        raw = str(value).strip()
        if len(raw) >= 2 and raw[:2].isdigit():
            return pos_label(raw[:2]) or raw
        return raw
    return str(value).strip()


def _partition_valid(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Split rows into those with a positive taxable/invoice base and the rest."""
    valid: list[dict[str, Any]] = []
    invalid = 0
    for r in rows:
        base = _num(r.get("taxable_value"))
        if base is None or base <= 0:
            base = _num(r.get("invoice_value"))
        if base is not None and base > 0:
            valid.append(r)
        else:
            invalid += 1
    return valid, invalid


def _summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for bucket in SEGREGATORS:
        group = [r for r in rows if r.get("segregator") == bucket]
        summary[bucket] = {
            "count": len(group),
            "taxable_value": round(sum(float(r.get("taxable_value") or 0.0) for r in group), 2),
            "igst": round(sum(float(r.get("igst") or 0.0) for r in group), 2),
            "cgst": round(sum(float(r.get("cgst") or 0.0) for r in group), 2),
            "sgst": round(sum(float(r.get("sgst") or 0.0) for r in group), 2),
            "cess": round(sum(float(r.get("cess") or 0.0) for r in group), 2),
        }
    summary["TOTAL"] = {
        "count": len(rows),
        "taxable_value": round(sum(float(r.get("taxable_value") or 0.0) for r in rows), 2),
    }
    return summary


def _empty_summary() -> dict[str, Any]:
    return {b: {"count": 0, "taxable_value": 0.0} for b in SEGREGATORS}


def _rebuild_notice(flags: list[dict[str, Any]], existing: str | None) -> str | None:
    # tax_flags are prepended after the validator built its notice, so recompute
    # so the CA sees tax-conflicts too.
    if not flags:
        return None
    from app.services.chat_assistant import build_ca_validation_notice
    # ensure severity present for tax flags
    for f in flags:
        f.setdefault("severity", "warning")
    return build_ca_validation_notice(flags)
