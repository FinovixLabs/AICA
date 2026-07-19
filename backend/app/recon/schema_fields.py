"""System fields and header aliases for the mapping layer (spec sections 2.1-2.2).

Both uploaded files pass through a manual field-matching layer: the CA maps each
of their columns onto the common system fields. This module supplies the
target field list and an alias table used for two things:

    1. Locating the header row past any banner rows (tabular._find_header_row
       takes the alias_index built here).
    2. Pre-filling the mapping UI with a suggestion per field, which the CA can
       override. Nothing here decides a mapping on its own.

The common fields are shared by GSTR-2B, IMS Inward and IMS Outward. Supplier
name is display-only: it never participates in the reconciliation key.
IMS files additionally carry an IMS Status column, offered only for those modules.
"""
from __future__ import annotations

from typing import Mapping

from app.recon.core.normalize import norm_text

__all__ = [
    "COMMON_FIELDS",
    "COMPONENT_ALIASES",
    "FIELD_ALIASES",
    "FIELD_DESCRIPTIONS",
    "FIELD_LABELS",
    "IMS_STATUS_FIELD",
    "INWARD_FIELDS",
    "INWARD_REQUIRED_FIELDS",
    "OUTWARD_EXTRA_FIELDS",
    "REQUIRED_FIELDS",
    "alias_index_for",
    "fields_for_module",
    "missing_required",
    "missing_required_for_module",
    "required_fields_for_module",
    "suggest_map",
]

# Common mapped fields, in the order the mapping UI shows them (2.2).
COMMON_FIELDS = (
    "supplier_gstin",
    "supplier_name",
    "doc_type",
    "doc_no",
    "doc_date",
    "taxable",
    "tax",
    "invoice",
)

IMS_STATUS_FIELD = "ims_status"

# IMS Inward has its own mapping contract. Date and taxable/combined-tax values
# are optional display fields; status is created by an in-app action, never read
# from the upload. Tax remains available for review but does not decide matching.
INWARD_FIELDS = (
    "supplier_gstin",
    "supplier_name",
    "doc_type",
    "doc_no",
    "invoice",
    "tax",
)

# IMS Outward carries two extra portal-context columns beyond the common set:
# the return period the invoice was reported in, and the form it was reported in
# (GSTR-1 / GSTR-1A / …). Both are display-only — never part of any match key.
OUTWARD_EXTRA_FIELDS = ("return_period", "reported_in_form")

# Fields a GSTR-2B run cannot proceed without. Taxable and combined tax are
# display-only and therefore optional.
REQUIRED_FIELDS = ("supplier_gstin", "doc_type", "doc_no", "doc_date", "invoice")

# IMS Inward can proceed from its three identity fields. Date and invoice value
# may still be mapped and displayed when available, but are not upload blockers;
# taxable value and combined tax remain optional as they are in every module.
INWARD_REQUIRED_FIELDS = ("supplier_gstin", "doc_type", "doc_no", "invoice")

# IMS Outward matches on GSTIN + invoice value only, and buckets by IMS status,
# so those three are the minimum needed; doc number/date/type are display-only
# here. The Sales Register side only needs GSTIN + invoice value to be matchable.
OUTWARD_IMS_REQUIRED_FIELDS = ("supplier_gstin", "invoice", "ims_status")
OUTWARD_SR_REQUIRED_FIELDS = ("supplier_gstin", "invoice")

FIELD_LABELS: dict[str, str] = {
    "supplier_gstin": "Supplier GSTIN",
    "supplier_name": "Trade / Legal Name",
    "doc_type": "Document Type",
    "doc_no": "Document Number",
    "doc_date": "Document Date",
    "taxable": "Taxable Value",
    "tax": "Combined Tax",
    "invoice": "Invoice Value",
    "ims_status": "IMS Status",
    "return_period": "Return Period",
    "reported_in_form": "Reported in Form",
}

# Plain-language description of each system field, handed to the AI mapper so it
# can reason about columns the static alias table has never seen (ai_mapping.py).
# The distinctions here — supplier vs. recipient GSTIN, invoice total vs. taxable
# base, combined tax vs. its components — are exactly the ones a manual alias list
# gets wrong, so spell them out.
FIELD_DESCRIPTIONS: dict[str, str] = {
    "supplier_gstin": (
        "The 15-character GSTIN/UIN of the SUPPLIER (the counterparty who issued "
        "the invoice), e.g. '27AAACS1429B1Z0'. In a purchase register this is the "
        "seller's GSTIN, NOT the buyer's/taxpayer's own GSTIN — if both appear, "
        "pick the supplier/seller/vendor one."
    ),
    "supplier_name": (
        "The supplier's trade name, legal name, vendor name, or party name. This "
        "is retained for display and review but is never used as a match key."
    ),
    "doc_type": (
        "The kind of document: Invoice, Credit Note, Debit Note, Bill of Entry, "
        "etc. May be labelled note type, nature/type of document, or supply type."
    ),
    "doc_no": (
        "The invoice / document / bill / voucher number that identifies the "
        "document. A reference or serial string, not a monetary amount."
    ),
    "doc_date": "The date the invoice / document was issued.",
    "taxable": (
        "The taxable (assessable) value — the amount BEFORE GST is added. Smaller "
        "than the invoice total. Also called taxable amount or assessable value."
    ),
    "tax": (
        "A single column holding the combined / total GST tax amount (a bare "
        "'GST' or 'Tax' amount column counts). Map it when one exists. Leave null "
        "ONLY when tax is split across separate IGST / CGST / SGST / Cess columns "
        "with no combined column — those components are summed elsewhere."
    ),
    "invoice": (
        "The total invoice value INCLUDING tax (the invoice grand total / bill "
        "amount). The largest per-row monetary figure; larger than the taxable "
        "value. Not a running or ledger balance."
    ),
    "ims_status": (
        "The IMS action/status recorded for the record on the GST portal: "
        "Accepted, Rejected, Pending, or No Action."
    ),
    "return_period": (
        "The GST return period the invoice was reported in, e.g. '042025' or "
        "'Apr-2025'. A month/period label, not a monetary amount."
    ),
    "reported_in_form": (
        "The return/form the invoice was reported in — GSTR-1, GSTR-1A, GSTR-5, "
        "etc. Sometimes labelled 'source form' or 'reported in'."
    ),
}

# norm_text(header) -> system field. Suggestions only; every one is overridable.
FIELD_ALIASES: dict[str, str] = {
    # supplier gstin
    "gstin": "supplier_gstin",
    "supplier gstin": "supplier_gstin",
    "gstin of supplier": "supplier_gstin",
    "gstin of the supplier": "supplier_gstin",
    "supplier gstin uin": "supplier_gstin",
    "gstin uin of supplier": "supplier_gstin",
    "supplier gstin uin of supplier": "supplier_gstin",
    "ctin": "supplier_gstin",
    "gstin uin": "supplier_gstin",
    # recipient gstin (IMS Outward / Sales Register wording — same system field)
    "recipient gstin": "supplier_gstin",
    "gstin of recipient": "supplier_gstin",
    "gstin uin of recipient": "supplier_gstin",
    "customer gstin": "supplier_gstin",
    "buyer gstin": "supplier_gstin",
    # supplier display name
    "supplier name": "supplier_name",
    "trade legal name": "supplier_name",
    "trade name": "supplier_name",
    "legal name": "supplier_name",
    "vendor name": "supplier_name",
    "party name": "supplier_name",
    "name of supplier": "supplier_name",
    # document type
    "document type": "doc_type",
    "doc type": "doc_type",
    "type": "doc_type",
    "note type": "doc_type",
    "invoice type": "doc_type",
    "nature of document": "doc_type",
    "supply type": "doc_type",
    # document number
    "document number": "doc_no",
    "document no": "doc_no",
    "doc no": "doc_no",
    "doc number": "doc_no",
    "invoice number": "doc_no",
    "invoice no": "doc_no",
    "bill no": "doc_no",
    "bill number": "doc_no",
    "note number": "doc_no",
    "note no": "doc_no",
    "voucher no": "doc_no",
    "voucher number": "doc_no",
    "reference no": "doc_no",
    "ref no": "doc_no",
    # document date
    "document date": "doc_date",
    "doc date": "doc_date",
    "invoice date": "doc_date",
    "date": "doc_date",
    "bill date": "doc_date",
    "note date": "doc_date",
    "voucher date": "doc_date",
    # taxable value
    "taxable value": "taxable",
    "taxable amount": "taxable",
    "taxable": "taxable",
    "taxable value rs": "taxable",
    "assessable value": "taxable",
    # combined tax
    "combined tax": "tax",
    "total tax": "tax",
    "tax amount": "tax",
    "tax": "tax",
    "gst amount": "tax",
    "total tax amount": "tax",
    # invoice value
    "invoice value": "invoice",
    "invoice value rs": "invoice",
    "total invoice value": "invoice",
    "invoice amount": "invoice",
    "bill value": "invoice",
    "total amount": "invoice",
    "total value": "invoice",
    "gross total": "invoice",
    "grand total": "invoice",
    # ims status
    "ims status": "ims_status",
    "status": "ims_status",
    "ims action": "ims_status",
    "action": "ims_status",
    "gstr 2b status": "ims_status",
    "gstr2b status": "ims_status",
    # return period (IMS Outward)
    "return period": "return_period",
    "tax period": "return_period",
    "period": "return_period",
    # reported in form (IMS Outward)
    "reported in form": "reported_in_form",
    "reported in gstr": "reported_in_form",
    "source form": "reported_in_form",
    "reported in": "reported_in_form",
    "form": "reported_in_form",
}

# Component columns used to derive combined tax when no single combined-tax column
# is mapped. Combined tax is display-only (2.2), so summing components is safe:
# it never changes a reconciliation status.
COMPONENT_ALIASES: dict[str, str] = {
    "integrated tax": "igst",
    "igst": "igst",
    "igst amount": "igst",
    "integrated tax amount": "igst",
    "central tax": "cgst",
    "cgst": "cgst",
    "cgst amount": "cgst",
    "central tax amount": "cgst",
    "state ut tax": "sgst",
    "state tax": "sgst",
    "sgst": "sgst",
    "sgst amount": "sgst",
    "sgst utgst": "sgst",
    "state ut tax amount": "sgst",
    "cess": "cess",
    "cess amount": "cess",
}


def fields_for_module(module: str) -> tuple[str, ...]:
    """The mapped fields offered for a module: the common ones, plus IMS Status
    for the IMS modules, plus the two outward portal-context columns for IMS
    Outward (return period, reported-in-form)."""
    if module == "ims_outward":
        # doc_type is not part of the outward match (GSTIN + invoice + IMS status
        # only), so it is not offered for mapping here.
        base = tuple(f for f in COMMON_FIELDS if f != "doc_type")
        return base + (IMS_STATUS_FIELD,) + OUTWARD_EXTRA_FIELDS
    if module == "ims_inward":
        return INWARD_FIELDS
    return COMMON_FIELDS


def alias_index_for(module: str) -> dict[str, str]:
    """norm_text(header) -> system field, restricted to the module's fields.

    Handed to read_table so the header row is found past banner rows.
    """
    # Header detection needs the full common vocabulary even when a module hides
    # some fields from its mapping UI. A second header row containing only
    # taxable/tax details is still structural, not a transaction.
    allowed = set(fields_for_module(module)) | set(COMMON_FIELDS)
    index = {key: field for key, field in FIELD_ALIASES.items() if field in allowed}
    return index


def suggest_map(headers: list[str], module: str) -> dict[str, str | None]:
    """Propose header -> field for each system field. First matching header wins.

    Returns system_field -> header (the human-readable header string) or None.
    """
    aliases = alias_index_for(module)
    suggestion: dict[str, str | None] = {field: None for field in fields_for_module(module)}
    for header in headers:
        field = _lookup_header(header, aliases)
        if field in suggestion and suggestion[field] is None:
            suggestion[field] = header
    return suggestion


def component_columns(headers: list[str]) -> dict[str, int]:
    """Detect tax-component columns by header alias. Returns component -> column index."""
    found: dict[str, int] = {}
    for index, header in enumerate(headers):
        component = _lookup_header(header, COMPONENT_ALIASES)
        if component and component not in found:
            found[component] = index
    return found


def _lookup_header(header: str, aliases: Mapping[str, str]) -> str | None:
    """Resolve a plain label or the leaf part of a flattened group / leaf label."""
    found = aliases.get(norm_text(header))
    if found:
        return found
    parts = header.split(" / ")
    return aliases.get(norm_text(parts[-1])) if len(parts) > 1 else None


def missing_required(mapping: Mapping[str, str | None]) -> list[str]:
    """Required system fields that the mapping leaves unset (two-sided modules)."""
    return [field for field in REQUIRED_FIELDS if not mapping.get(field)]


def required_fields_for_module(module: str, side: str = "cp") -> tuple[str, ...]:
    """The minimum fields a side must map for a module to run.

    IMS Inward requires only supplier GSTIN, document type and document number.
    IMS Outward matches on GSTIN + invoice value and buckets by IMS status, so
    its two sides have their own minimum sets.
    """
    if module == "ims_inward":
        return INWARD_REQUIRED_FIELDS
    if module == "ims_outward":
        return OUTWARD_SR_REQUIRED_FIELDS if side == "pr" else OUTWARD_IMS_REQUIRED_FIELDS
    return REQUIRED_FIELDS


def missing_required_for_module(
    mapping: Mapping[str, str | None], module: str, side: str = "cp"
) -> list[str]:
    """Required fields left unset for a given module/side."""
    return [field for field in required_fields_for_module(module, side) if not mapping.get(field)]
