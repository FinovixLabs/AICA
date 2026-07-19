"""Take Action: a pre-filled client-intimation message (spec 6.4, 10.4).

For a selected unresolved transaction the CA can generate a message that uses the
transaction's details and can be reviewed and sent to the client. This belongs to
the GSTR-2B and IMS Outward workflows.

The message is drafted by the AI when a key is configured, with a fully
deterministic template fallback so the feature works with no external dependency.
The OpenAI-compatible call mirrors app/services/chat_assistant.py (blocking
urllib, same settings) but is kept local so the module has no hard coupling to the
filing assistant.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are AICA, assisting an Indian Chartered Accountant. Draft a short, "
    "professional email to a client (or their supplier) about ONE GST "
    "reconciliation discrepancy found between the client's purchase register and "
    "the GST portal data (GSTR-2B / IMS). Use only the figures provided; never "
    "invent amounts, GSTINs or dates. State the issue plainly, ask the client to "
    "verify or take the corrective step, and keep it under 150 words. Output only "
    "the message body — no subject line, no placeholders, no markdown."
)

# IMS Outward intimation: the record carries the recipient's IMS action, not a
# reconciliation status (spec 10.4).
_IMS_STATUS_GUIDANCE = {
    "rejected": (
        "The recipient has rejected this outward invoice in the GST IMS, so the "
        "input tax credit will not flow to them and it may affect the supplier's liability."
    ),
    "reject": (
        "The recipient has rejected this outward invoice in the GST IMS, so the "
        "input tax credit will not flow to them and it may affect the supplier's liability."
    ),
    "pending": (
        "The recipient has left this outward invoice pending in the GST IMS; no "
        "action has been taken yet and it needs a follow-up."
    ),
    "accepted": (
        "The recipient has accepted this outward invoice in the GST IMS."
    ),
    "accept": (
        "The recipient has accepted this outward invoice in the GST IMS."
    ),
}

_ISSUE_GUIDANCE = {
    "mismatch": (
        "The invoice value in the purchase register does not match the value "
        "reported by the supplier in GSTR-2B/IMS, beyond the allowed 1% tolerance."
    ),
    "missing": (
        "This purchase appears in the client's books but the supplier has not "
        "reported it in GSTR-2B/IMS, so input tax credit is currently unavailable."
    ),
    "extra": (
        "This document appears in GSTR-2B/IMS but is not found in the client's "
        "purchase register, so it may be unrecorded or wrongly attributed."
    ),
    "duplicate_pr": (
        "This document appears more than once in the client's purchase register "
        "with identical details and may have been recorded twice."
    ),
    "ambiguous": (
        "The same invoice reference appears multiple times with different values "
        "and could not be matched automatically; it needs manual review."
    ),
}


def generate_message(result: dict[str, Any], *, client_name: str | None = None) -> str:
    """Return a client-ready message for one reconciliation result.

    Falls back to a deterministic template if no API key is set or the AI call
    fails, so Take Action always returns something the CA can review and edit.
    """
    settings = get_settings()
    key = getattr(settings, "OPENAI_API_KEY", "")
    if not key:
        return _template(result, client_name)
    try:
        return _ai_message(result, client_name, settings) or _template(result, client_name)
    except Exception as exc:  # pragma: no cover - network/provider variance
        logger.warning("Take Action AI draft failed, using template: %s", exc)
        return _template(result, client_name)


def _is_ims_record(result: dict[str, Any]) -> bool:
    """True for a single IMS Outward record (has an IMS status, no reconcile
    status) versus a reconciliation-list row."""
    return not result.get("status") and result.get("ims_status") is not None


def _facts(result: dict[str, Any], client_name: str | None) -> str:
    ims = _is_ims_record(result)
    issue = result.get("status_label") or result.get("status") or (
        "IMS Outward — recipient action" if ims else "GST reconciliation discrepancy"
    )
    lines = [
        f"Client: {client_name or 'the client'}",
        f"Issue: {issue}",
        f"Supplier GSTIN: {result.get('supplier_gstin') or 'not available'}",
        f"Document: {result.get('doc_no') or 'not available'} "
        f"({result.get('doc_type') or 'document'}) dated {result.get('doc_date') or 'unknown'}",
    ]
    if result.get("ims_status"):
        lines.append(f"Recipient IMS action: {result['ims_status']}")
    pr = result.get("pr_invoice")
    cp = result.get("cp_invoice")
    if pr is not None:
        lines.append(f"Purchase register invoice value: {_inr(pr)}")
    if cp is not None:
        lines.append(f"GSTR-2B / IMS invoice value: {_inr(cp)}")
    if result.get("invoice") is not None:
        lines.append(f"Invoice value: {_inr(result['invoice'])}")
    if result.get("diff_invoice") is not None:
        lines.append(f"Difference: {_inr(result['diff_invoice'])}")
    guidance = _ISSUE_GUIDANCE.get(result.get("status", ""))
    if not guidance and ims:
        guidance = _IMS_STATUS_GUIDANCE.get(str(result.get("ims_status", "")).lower())
    if guidance:
        lines.append(f"Context: {guidance}")
    return "\n".join(lines)


def _template(result: dict[str, Any], client_name: str | None) -> str:
    status = result.get("status", "")
    doc = result.get("doc_no") or "the document"
    supplier = result.get("supplier_gstin") or "the supplier"
    greeting = f"Dear {client_name}," if client_name else "Dear Sir/Madam,"

    if _is_ims_record(result):
        ims = str(result.get("ims_status", ""))
        context = _IMS_STATUS_GUIDANCE.get(ims.lower(), f"The recipient's IMS action is '{ims}'.")
        inv = result.get("invoice")
        figures = f" The invoice value is {_inr(inv)}." if inv is not None else ""
        ask = (
            "Please confirm the correct treatment of this invoice so the IMS action "
            "can be aligned and, if needed, take it up with the recipient."
        )
        return (
            f"{greeting}\n\n"
            f"Regarding outward invoice {doc}: {context}{figures}\n\n"
            f"{ask}\n\n"
            f"Regards,\nfor the compliance team"
        )

    context = _ISSUE_GUIDANCE.get(status, "A discrepancy was found during GST reconciliation.")
    pr, cp = result.get("pr_invoice"), result.get("cp_invoice")
    figures = ""
    if pr is not None and cp is not None:
        figures = (
            f" Your records show an invoice value of {_inr(pr)}, while the GST portal "
            f"reflects {_inr(cp)}."
        )
    elif pr is not None:
        figures = f" Your records show an invoice value of {_inr(pr)}."
    elif cp is not None:
        figures = f" The GST portal reflects an invoice value of {_inr(cp)}."

    ask = {
        "mismatch": "Please verify the correct invoice value and share the supporting invoice so we can reconcile it.",
        "missing": "Please follow up with the supplier to report this invoice in their GST return so the input tax credit can be claimed.",
        "extra": "Please confirm whether this document belongs to you and share the corresponding invoice for our records.",
        "duplicate_pr": "Please confirm whether this entry was recorded twice so we can correct the purchase register.",
        "ambiguous": "Please share the correct details for this invoice so we can match it accurately.",
    }.get(status, "Please review this entry and share any supporting document.")

    return (
        f"{greeting}\n\n"
        f"During the GST reconciliation for document {doc} (supplier {supplier}), "
        f"we identified the following: {context}{figures}\n\n"
        f"{ask}\n\n"
        f"Regards,\nfor the compliance team"
    )


def _ai_message(result: dict[str, Any], client_name: str | None, settings: Any) -> str | None:
    payload = {
        "model": settings.OPENAI_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _facts(result, client_name)},
        ],
        "temperature": 0.3,
        "stream": False,
    }
    request = urllib.request.Request(
        f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    return content.strip() or None


def _inr(value: Any) -> str:
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)
