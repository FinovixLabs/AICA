"""
Builds the GSTR-1 portal-ready JSON from classified invoice rows.
Schema follows the GST portal API structure.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any
from app.filing.gstr1.classifier import _parse_amount


def build_gstr1_json(
    classified_tables: dict[str, list[dict[str, Any]]],
    gstin: str,
    period: str,  # format: MMYYYY e.g. "072026"
) -> dict[str, Any]:
    """
    Build a GSTR-1 JSON payload from classified tables.
    Returns the full JSON ready for portal upload or CA review.
    """
    return {
        "gstin": gstin,
        "fp": period,  # filing period MMYYYY
        "gt": _grand_total(classified_tables),
        "cur_gt": _grand_total(classified_tables),
        "b2b": _build_b2b(classified_tables.get("B2B", [])),
        "b2cl": _build_b2cl(classified_tables.get("B2CL", [])),
        "b2cs": _build_b2cs(classified_tables.get("B2CS", [])),
        "exp": _build_exp(classified_tables.get("EXP", [])),
        "cdnr": _build_cdnr(classified_tables.get("CDNR", [])),
        "cdnur": _build_cdnur(classified_tables.get("CDNUR", [])),
        "at": _build_at(classified_tables.get("AT", [])),
        "atadj": _build_at(classified_tables.get("ATA", [])),
        "hsn": _build_hsn(classified_tables.get("HSN", [])),
        "nil": _build_nil(classified_tables.get("EXEMP", [])),
        "_meta": {
            "generated_at": datetime.utcnow().isoformat(),
            "tool": "AICA",
            "status": "draft",
            "ca_approved": False,
        },
    }


def _grand_total(tables: dict[str, list[dict[str, Any]]]) -> float:
    total = 0.0
    for table_name, rows in tables.items():
        if table_name in ("HSN", "EXEMP"):
            continue
        for row in rows:
            total += _parse_amount(row.get("taxable_value"))
    return round(total, 2)


def _build_b2b(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group B2B invoices by buyer GSTIN."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        gstin = str(row.get("gstin_buyer") or "").strip().upper()
        if not gstin:
            continue
        if gstin not in grouped:
            grouped[gstin] = []
        grouped[gstin].append({
            "inum": str(row.get("invoice_number") or ""),
            "idt": str(row.get("invoice_date") or ""),
            "val": _parse_amount(row.get("taxable_value")) + _parse_amount(row.get("igst")) + _parse_amount(row.get("cgst")) + _parse_amount(row.get("sgst")),
            "pos": str(row.get("place_of_supply") or ""),
            "rchrg": "N",
            "inv_typ": "R",
            "itms": [{
                "num": 1,
                "itm_det": {
                    "txval": _parse_amount(row.get("taxable_value")),
                    "rt": _parse_amount(row.get("rate")),
                    "iamt": _parse_amount(row.get("igst")),
                    "camt": _parse_amount(row.get("cgst")),
                    "samt": _parse_amount(row.get("sgst")),
                    "csamt": _parse_amount(row.get("cess")),
                },
            }],
        })

    return [{"ctin": gstin, "inv": inv_list} for gstin, inv_list in grouped.items()]


def _build_b2cl(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group B2CL by place of supply."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        pos = str(row.get("place_of_supply") or "")
        if pos not in grouped:
            grouped[pos] = []
        grouped[pos].append({
            "inum": str(row.get("invoice_number") or ""),
            "idt": str(row.get("invoice_date") or ""),
            "val": _parse_amount(row.get("taxable_value")) + _parse_amount(row.get("igst")),
            "itms": [{
                "num": 1,
                "itm_det": {
                    "txval": _parse_amount(row.get("taxable_value")),
                    "rt": _parse_amount(row.get("rate")),
                    "iamt": _parse_amount(row.get("igst")),
                    "csamt": _parse_amount(row.get("cess")),
                },
            }],
        })

    return [{"pos": pos, "inv": inv_list} for pos, inv_list in grouped.items()]


def _build_b2cs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """B2CS is a summary — aggregate by (rate, pos)."""
    summary: dict[tuple, dict[str, Any]] = {}
    for row in rows:
        rate = _parse_amount(row.get("rate"))
        pos = str(row.get("place_of_supply") or "")
        key = (rate, pos)
        if key not in summary:
            summary[key] = {
                "sply_tp": "INTRA" if _parse_amount(row.get("cgst")) > 0 else "INTER",
                "rt": rate,
                "pos": pos,
                "txval": 0.0,
                "iamt": 0.0,
                "camt": 0.0,
                "samt": 0.0,
                "csamt": 0.0,
            }
        summary[key]["txval"] = round(summary[key]["txval"] + _parse_amount(row.get("taxable_value")), 2)
        summary[key]["iamt"] = round(summary[key]["iamt"] + _parse_amount(row.get("igst")), 2)
        summary[key]["camt"] = round(summary[key]["camt"] + _parse_amount(row.get("cgst")), 2)
        summary[key]["samt"] = round(summary[key]["samt"] + _parse_amount(row.get("sgst")), 2)
        summary[key]["csamt"] = round(summary[key]["csamt"] + _parse_amount(row.get("cess")), 2)

    return list(summary.values())


def _build_exp(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Export invoices grouped by export type."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        exp_typ = str(row.get("export_type") or "WPAY").strip().upper()
        if "without" in exp_typ.lower() or "lut" in exp_typ.lower():
            exp_typ = "WOPAY"
        else:
            exp_typ = "WPAY"
        if exp_typ not in grouped:
            grouped[exp_typ] = []
        grouped[exp_typ].append({
            "inum": str(row.get("invoice_number") or ""),
            "idt": str(row.get("invoice_date") or ""),
            "val": _parse_amount(row.get("taxable_value")) + _parse_amount(row.get("igst")),
            "sbpcode": "",
            "sbnum": "",
            "sbdt": "",
            "itms": [{
                "txval": _parse_amount(row.get("taxable_value")),
                "rt": _parse_amount(row.get("rate")),
                "iamt": _parse_amount(row.get("igst")),
                "csamt": _parse_amount(row.get("cess")),
            }],
        })

    return [{"exp_typ": exp_typ, "inv": inv_list} for exp_typ, inv_list in grouped.items()]


def _build_cdnr(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Credit/debit notes to registered persons, grouped by recipient GSTIN."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        gstin = str(row.get("gstin_buyer") or "").strip().upper()
        if not gstin:
            continue
        if gstin not in grouped:
            grouped[gstin] = []
        grouped[gstin].append({
            "ntnum": str(row.get("invoice_number") or ""),
            "ntdt": str(row.get("invoice_date") or ""),
            "ntty": _note_type(row),
            "val": _parse_amount(row.get("taxable_value")),
            "itms": [{
                "num": 1,
                "itm_det": {
                    "txval": _parse_amount(row.get("taxable_value")),
                    "rt": _parse_amount(row.get("rate")),
                    "iamt": _parse_amount(row.get("igst")),
                    "camt": _parse_amount(row.get("cgst")),
                    "samt": _parse_amount(row.get("sgst")),
                    "csamt": _parse_amount(row.get("cess")),
                },
            }],
        })

    return [{"ctin": gstin, "nt": nt_list} for gstin, nt_list in grouped.items()]


def _build_cdnur(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        result.append({
            "ntnum": str(row.get("invoice_number") or ""),
            "ntdt": str(row.get("invoice_date") or ""),
            "ntty": _note_type(row),
            "typ": "B2CL" if _parse_amount(row.get("igst")) > 0 else "B2CS",
            "val": _parse_amount(row.get("taxable_value")),
            "itms": [{
                "num": 1,
                "itm_det": {
                    "txval": _parse_amount(row.get("taxable_value")),
                    "rt": _parse_amount(row.get("rate")),
                    "iamt": _parse_amount(row.get("igst")),
                    "camt": _parse_amount(row.get("cgst")),
                    "samt": _parse_amount(row.get("sgst")),
                    "csamt": _parse_amount(row.get("cess")),
                },
            }],
        })
    return result


def _build_at(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    summary: dict[tuple, dict[str, Any]] = {}
    for row in rows:
        pos = str(row.get("place_of_supply") or "")
        rate = _parse_amount(row.get("rate"))
        key = (pos, rate)
        if key not in summary:
            summary[key] = {"pos": pos, "itms": [{"rt": rate, "ad_amt": 0.0, "iamt": 0.0, "camt": 0.0, "samt": 0.0, "csamt": 0.0}]}
        summary[key]["itms"][0]["ad_amt"] = round(summary[key]["itms"][0]["ad_amt"] + _parse_amount(row.get("taxable_value")), 2)
        summary[key]["itms"][0]["iamt"] = round(summary[key]["itms"][0]["iamt"] + _parse_amount(row.get("igst")), 2)
        summary[key]["itms"][0]["camt"] = round(summary[key]["itms"][0]["camt"] + _parse_amount(row.get("cgst")), 2)
        summary[key]["itms"][0]["samt"] = round(summary[key]["itms"][0]["samt"] + _parse_amount(row.get("sgst")), 2)
    return list(summary.values())


def _build_hsn(rows: list[dict[str, Any]]) -> dict[str, Any]:
    data = []
    for i, row in enumerate(rows, 1):
        data.append({
            "num": i,
            "hsn_sc": str(row.get("hsn_code") or ""),
            "uqc": str(row.get("uqc") or "OTH"),
            "qty": round(_parse_amount(row.get("total_quantity")), 3),
            "val": round(_parse_amount(row.get("total_taxable_value")), 2),
            "txval": round(_parse_amount(row.get("total_taxable_value")), 2),
            "iamt": round(_parse_amount(row.get("total_igst")), 2),
            "camt": round(_parse_amount(row.get("total_cgst")), 2),
            "samt": round(_parse_amount(row.get("total_sgst")), 2),
            "csamt": round(_parse_amount(row.get("total_cess")), 2),
            "rt": _parse_amount(row.get("rate")),
        })
    return {"hsn_sc_data": data}


def _build_nil(rows: list[dict[str, Any]]) -> dict[str, Any]:
    nil = {"sply_ty": "INTRB2B", "nil_amt": 0.0, "expt_amt": 0.0, "ngsup_amt": 0.0}
    for row in rows:
        inv_type = str(row.get("invoice_type") or "").lower()
        val = _parse_amount(row.get("taxable_value"))
        if "nil" in inv_type:
            nil["nil_amt"] = round(nil["nil_amt"] + val, 2)
        elif "exempt" in inv_type:
            nil["expt_amt"] = round(nil["expt_amt"] + val, 2)
        else:
            nil["ngsup_amt"] = round(nil["ngsup_amt"] + val, 2)
    return nil


def _note_type(row: dict[str, Any]) -> str:
    nt = str(row.get("note_type") or row.get("invoice_type") or "").strip().lower()
    if "credit" in nt or nt in ("c", "cr"):
        return "C"
    if "debit" in nt or nt in ("d", "dr"):
        return "D"
    return "C"
