from __future__ import annotations
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

DEFAULT_MODEL = "gpt-4o-mini"
JSON_TEMPLATE_DIR = Path(__file__).resolve().parent / "json_templates"

GSTR1_REQUIRED_DOCUMENTS: list[str] = [
    "b2b_invoices", "b2cl_invoices", "b2cs_invoices",
    "credit_debit_notes_registered", "credit_debit_notes_unregistered",
    "export_invoices", "advance_receipts_services", "advance_adjustments_services",
    "nil_exempt_nongst_supplies", "hsn_summary", "document_issuance_summary",
]


class RequirementCheckError(RuntimeError):
    pass


def run_gstr1_requirement_check(conn, *, client_id: str, gstin: str, period: str | None = None) -> dict[str, Any]:
    required = list(GSTR1_REQUIRED_DOCUMENTS)
    cur = conn.cursor()
    cur.execute(
        "SELECT client_id, file_name, file_text, tax_period FROM documents WHERE client_id = %s ORDER BY uploaded_at DESC",
        (client_id,),
    )
    documents = [
        {"client_id": str(r[0]), "file_name": r[1], "file_text": r[2], "tax_period": r[3]}
        for r in cur.fetchall()
    ]

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Fallback to basic check without AI
        return {"status": "ready", "message": "Basic check passed.", "missing": [], "present": required, "flags": [], "actions": ["continue"], "documents": documents}

    try:
        ai_result = _ask_ai(gstin=gstin, period=period, required_documents=required, documents=documents, guidelines="Check documents for GSTR-1 readiness.")
    except RequirementCheckError:
        return {"status": "ready", "message": "Could not reach AI for check.", "missing": [], "present": [], "flags": [], "actions": ["continue"], "documents": documents}

    missing = _missing_from_ai_result(ai_result, required)
    status = "missing_data" if missing else "ready"
    message = ai_result.get("message") if missing else "All required documents present."
    actions = ai_result.get("actions", [])
    if missing:
        actions = _merge_actions(actions, ["continue", "intimate_client"])

    return {
        "status": status,
        "message": message or "Requirement check completed.",
        "missing": missing,
        "present": _required_only_list(ai_result.get("present", []), required),
        "flags": ai_result.get("flags", []),
        "actions": actions,
        "documents": documents,
    }


def _ask_ai(*, gstin: str, period: str | None, required_documents: list[str], documents: Sequence[Mapping[str, Any]], guidelines: str) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RequirementCheckError("OPENAI_API_KEY not configured")

    model = os.getenv("OPENAI_REQUIREMENTS_MODEL", DEFAULT_MODEL)
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    payload = {
        "model": model, "temperature": 0,
        "messages": [
            {"role": "system", "content": "You are a GST return readiness checker. Return only compact JSON with keys: status, message, present, missing, flags, actions."},
            {"role": "user", "content": json.dumps({"filing": "GSTR-1", "gstin": gstin, "period": period, "required_documents": required_documents, "documents": list(documents), "guidelines": guidelines}, default=str)},
        ],
    }

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            body = res.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise RequirementCheckError(f"OpenAI error ({exc.code})") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RequirementCheckError(str(exc)) from exc

    try:
        content = json.loads(body)["choices"][0]["message"]["content"]
        return json.loads(_strip_json_fence(content))
    except Exception as exc:
        raise RequirementCheckError("Unexpected AI response") from exc


def _document_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _required_keys(values: Any, required_documents: Sequence[str]) -> set[str]:
    if not isinstance(values, list):
        return set()
    allowed = {_document_key(doc) for doc in required_documents}
    keys = {_document_key(str(item)) for item in values}
    return keys & allowed


def _missing_from_ai_result(ai_result: Mapping[str, Any], required_documents: Sequence[str]) -> list[str]:
    present_keys = _required_keys(ai_result.get("present", []), required_documents)
    if present_keys:
        return [doc for doc in required_documents if _document_key(doc) not in present_keys]
    missing_keys = _required_keys(ai_result.get("missing", []), required_documents)
    return [doc for doc in required_documents if _document_key(doc) in missing_keys]


def _required_only_list(values: Any, required_documents: Sequence[str]) -> list[str]:
    value_keys = _required_keys(values, required_documents)
    return [doc for doc in required_documents if _document_key(doc) in value_keys]


def _merge_actions(actions: Any, defaults: Sequence[str]) -> list[str]:
    ordered: list[str] = []
    for action in [*(actions if isinstance(actions, list) else []), *defaults]:
        if isinstance(action, str) and action not in ordered:
            ordered.append(action)
    return ordered


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        stripped = stripped.removesuffix("```").strip()
    return stripped
