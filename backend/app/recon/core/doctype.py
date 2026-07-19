"""Document-type canonicalization (spec section 2.3, "standardize document-type formatting").

This is the highest-risk normalization in the module — higher than dates.

Document type is part of the match key, so a wrong mapping does not produce one
bad row, it makes EVERY row mismatch. And the vocabularies genuinely differ:
GSTR-2B carries portal codes ('R', 'CR', 'ISD', 'IMPG'), while a purchase
register carries whatever the client's accounting package writes ('Invoice',
'Credit Note', 'Purchase', 'GST Sales').

So nothing here decides anything. suggest() proposes, the CA confirms in the
mapping step, and the confirmed map is stored per upload in
recon.field_maps.doc_types. canonicalize() only ever reads that confirmed map.
"""
from __future__ import annotations

from typing import Any, Mapping

from app.recon.core.normalize import norm_text

__all__ = [
    "CANONICAL_DOC_TYPES",
    "DOC_TYPE_LABELS",
    "canonicalize",
    "distinct_raw_values",
    "suggest",
]

CANONICAL_DOC_TYPES = (
    "invoice",
    "credit_note",
    "debit_note",
    "isd",
    "impg",
    "impgsez",
    "other",
)

# Shown in the mapping UI's <Select>.
DOC_TYPE_LABELS: dict[str, str] = {
    "invoice": "Invoice",
    "credit_note": "Credit Note",
    "debit_note": "Debit Note",
    "isd": "ISD Invoice",
    "impg": "Import of Goods",
    "impgsez": "Import of Goods from SEZ",
    "other": "Other",
}

# Suggestions only — every one of these is overridable by the CA.
#
# Keys are norm_text()'d. The portal's own short codes and the common accounting
# spellings both appear; anything unrecognised suggests nothing, which forces an
# explicit choice rather than a silent default to 'invoice'.
_SUGGESTIONS: dict[str, str] = {
    # GSTR-2B / IMS portal codes
    "r": "invoice",
    "reg": "invoice",
    "regular": "invoice",
    "b2b": "invoice",
    "de": "invoice",
    "deemed export": "invoice",
    "sezwp": "invoice",
    "sezwop": "invoice",
    "c": "credit_note",
    "cr": "credit_note",
    "cdnr": "credit_note",
    "d": "debit_note",
    "dr": "debit_note",
    "isd": "isd",
    "isdcn": "isd",
    "impg": "impg",
    "impgsez": "impgsez",
    # Accounting-package spellings
    "invoice": "invoice",
    "tax invoice": "invoice",
    "purchase": "invoice",
    "purchase invoice": "invoice",
    "bill": "invoice",
    "bill of supply": "invoice",
    "gst purchase": "invoice",
    "credit note": "credit_note",
    "creditnote": "credit_note",
    "purchase credit note": "credit_note",
    "sales return": "credit_note",
    "debit note": "debit_note",
    "debitnote": "debit_note",
    "purchase return": "debit_note",
    "import": "impg",
    "import of goods": "impg",
}


def suggest(raw: Any) -> str | None:
    """Propose a canonical type for a raw value, or None if it isn't recognised.

    None is a feature: it forces the CA to choose rather than letting an
    unrecognised type default into 'invoice' and mismatch every row under it.
    """
    key = norm_text(raw)
    if not key:
        return None
    return _SUGGESTIONS.get(key)


def distinct_raw_values(values: list[Any]) -> list[str]:
    """The distinct raw doc-type values in a file, for the mapping UI to enumerate.

    Ordered by first appearance so the CA sees them in the file's own order.
    """
    seen: dict[str, str] = {}
    for value in values:
        key = norm_text(value)
        if key and key not in seen:
            seen[key] = str(value).strip()
    return list(seen.values())


def canonicalize(raw: Any, confirmed: Mapping[str, str]) -> str | None:
    """Map a raw value through the CA's confirmed map. Never guesses.

    `confirmed` is recon.field_maps.doc_types: norm_text(raw) -> canonical.
    An unmapped value returns None, which the caller records as a parse error and
    surfaces to the CA — it never silently becomes 'other'.
    """
    key = norm_text(raw)
    if not key:
        return None
    canonical = confirmed.get(key)
    if canonical in CANONICAL_DOC_TYPES:
        return canonical
    return None
