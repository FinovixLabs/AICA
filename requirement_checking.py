from __future__ import annotations

import csv
import json
import os
import re
import urllib.error
import urllib.request
from io import StringIO
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


DEFAULT_MODEL = "gpt-4o-mini"
JSON_TEMPLATE_DIR = Path(__file__).resolve().parent / "filing" / "json_templates"



# Predefine the GSTR-1 document requirements here.
GSTR1_REQUIRED_DOCUMENTS: list[str]= [
    "b2b_invoices",
    "b2cl_invoices",
    "b2cs_invoices",
    "credit_debit_notes_registered",
    "credit_debit_notes_unregistered",
    "export_invoices",
    "advance_receipts_services",
    "advance_adjustments_services",
    "nil_exempt_nongst_supplies",
    "hsn_summary",
    "document_issuance_summary",
    "ecommerce_sales_tcs",
]

GSTR1_GUIDELINES = """
Review the uploaded documents for GSTR-1 filing readiness.
Compare the required document identifiers against the documents retrieved from
the database. A required document is present if its identifier clearly matches
an uploaded file name or the uploaded file text. Return only required document
identifiers that are actually missing. Do not add generic filing fields or
examples to the missing list.
""".strip()


class RequirementCheckError(RuntimeError):
    pass


def fetch_filing_documents(
    conn,
    *,
    client_id: str,
    required_documents: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Database connection point for loading filing documents.

    The required document list is intentionally configurable. Once the GSTR-1
    list is finalized, pass it in from `GSTR1_REQUIRED_DOCUMENTS` or replace the
    filter below with the app's canonical document taxonomy.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT client_id, file_name, file_text, tax_period
        FROM documents
        WHERE client_id = %s
        ORDER BY uploaded_at DESC
        """,
        (client_id,),
    )

    docs: list[dict[str, Any]] = []
    for row_client_id, file_name, file_text, tax_period in cur.fetchall():
        docs.append(
            {
                "client_id": str(row_client_id),
                "file_name": file_name,
                "file_text": file_text,
                "tax_period": tax_period,
            }
        )
    return docs


def run_gstr1_requirement_check(
    conn,
    *,
    client_id: str,
    gstin: str,
    period: str | None = None,
    required_documents: Iterable[str] | None = None,
) -> dict[str, Any]:
    required = list( GSTR1_REQUIRED_DOCUMENTS)
    documents = fetch_filing_documents(
        conn,
        client_id=client_id,
        required_documents=required,
    )
    ai_result = _ask_ai(
        gstin=gstin,
        period=period,
        required_documents=required,
        documents=documents,
        guidelines=GSTR1_GUIDELINES,
    )
    missing = _missing_from_ai_result(ai_result, required)
    status = "missing_data" if missing else ai_result.get("status", "ready")
    message = (
        ai_result.get("message")
        if missing
        else "All required GSTR-1 documents are present. You can start filing now."
    )
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


def build_gstr1_filing_start_payload(
    conn,
    *,
    client_id: str,
    gstin: str,
    period: str | None = None,
    required_documents: Iterable[str] | None = None,
) -> dict[str, Any]:
    required = list(required_documents or GSTR1_REQUIRED_DOCUMENTS)
    templates = load_gstr1_json_templates(required)
    documents = fetch_required_document_payloads(
        conn,
        client_id=client_id,
        required_documents=required,
        templates=templates,
    )
    missing_documents = [item["document_key"] for item in documents if not item["found"]]
    missing_templates = [key for key in required if key not in templates]
    system_prompt = (
        "You are AICA, an expert GST filing assistant for Indian Chartered Accountants. "
        "Start the GSTR-1 filing workflow using only the supplied uploaded document text "
        "and JSON filing templates. Do not invent transaction data. If a required document "
        "or template is missing, continue with the available material, clearly list the "
        "assumptions and risks, and ask the CA only for the specific missing inputs needed."
    )
    base_payload = {
        "filing": "GSTR-1",
        "gstin": gstin,
        "period": period,
        "system_prompt": system_prompt,
        "required_documents": required,
        "documents": documents,
        "json_templates": templates,
        "missing_documents": missing_documents,
        "missing_json_templates": missing_templates,
    }
    filing_json = _build_filing_json(base_payload)
    return {
        **base_payload,
        "status": "filing_completed",
        "message": "filing completed",
        "filing_json": filing_json,
        "filing_csv": _build_filing_csv(filing_json),
    }


def fetch_required_document_payloads(
    conn,
    *,
    client_id: str,
    required_documents: Sequence[str],
    templates: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    cur = conn.cursor()
    path_column = _documents_path_column(cur)
    cur.execute(
        f"""
        SELECT file_name, {path_column}, file_text, tax_period
        FROM documents
        WHERE client_id = %s
        ORDER BY uploaded_at DESC
        """,
        (client_id,),
    )
    rows = [
        {
            "file_name": file_name,
            "file_path": file_path,
            "file_text": file_text,
            "tax_period": tax_period,
        }
        for file_name, file_path, file_text, tax_period in cur.fetchall()
    ]

    grouped: dict[str, list[dict[str, Any]]] = {key: [] for key in required_documents}
    aliases = _document_aliases(required_documents, templates or {})
    for row in rows:
        matched_key = _match_required_document(row, required_documents, aliases=aliases)
        if matched_key:
            grouped[matched_key].append(row)

    payloads: list[dict[str, Any]] = []
    for key in required_documents:
        matched = grouped.get(key, [])
        payloads.append(
            {
                "document_key": key,
                "found": bool(matched),
                "files": matched,
            }
        )
    return payloads


def load_gstr1_json_templates(required_documents: Sequence[str]) -> dict[str, Any]:
    templates: dict[str, Any] = {}
    for key in required_documents:
        path = JSON_TEMPLATE_DIR / f"{key}.json"
        if not path.exists():
            continue
        try:
            templates[key] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            templates[key] = {"raw_template": path.read_text(encoding="utf-8")}
    return templates


def _document_aliases(
    required_documents: Sequence[str],
    templates: Mapping[str, Any],
) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = {key: set() for key in required_documents}
    for key in required_documents:
        template = templates.get(key) if isinstance(templates, Mapping) else None
        if not isinstance(template, dict):
            continue

        values = [
            template.get("template_name"),
            template.get("source_file"),
        ]
        context = template.get("filing_context")
        if isinstance(context, dict):
            values.extend(
                [
                    context.get("section_code"),
                    context.get("section_description"),
                ]
            )

        for value in values:
            if not value:
                continue
            text = str(value).strip()
            aliases[key].add(text)
            if "." in text:
                aliases[key].add(Path(text).stem)
    return aliases


def _documents_path_column(cur) -> str:
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'documents'
          AND column_name IN ('file_path', 'storage_path')
        ORDER BY CASE column_name WHEN 'file_path' THEN 0 ELSE 1 END
        LIMIT 1
        """
    )
    row = cur.fetchone()
    return row[0] if row else "storage_path"


def _match_required_document(
    row: Mapping[str, Any],
    required_documents: Sequence[str],
    *,
    aliases: Mapping[str, set[str]] | None = None,
) -> str | None:
    file_name = str(row.get("file_name") or "")
    file_stem = Path(file_name).stem
    file_text = str(row.get("file_text") or "")
    searchable = f"{file_name}\n{file_stem}\n{file_text}".lower()
    for key in required_documents:
        normalized = _document_key(key)
        candidates = {
            key.lower(),
            normalized,
            normalized.replace("_", " "),
            normalized.replace("_", "-"),
        }
        for alias in (aliases or {}).get(key, set()):
            alias_key = _document_key(alias)
            candidates.update(
                {
                    alias.lower(),
                    alias_key,
                    alias_key.replace("_", " "),
                    alias_key.replace("_", "-"),
                }
            )
        if any(candidate and candidate in searchable for candidate in candidates):
            return key
    return None


def _build_filing_json(payload: Mapping[str, Any]) -> dict[str, Any]:
    templates = payload.get("json_templates", {})
    documents = payload.get("documents", [])
    sections: list[dict[str, Any]] = []
    for item in documents if isinstance(documents, list) else []:
        if not isinstance(item, dict):
            continue
        key = str(item.get("document_key") or "")
        files = item.get("files", [])
        sections.append(
            {
                "document_key": key,
                "document_found": bool(item.get("found")),
                "json_template_found": isinstance(templates, dict) and key in templates,
                "json_template": templates.get(key) if isinstance(templates, dict) else None,
                "source_files": files if isinstance(files, list) else [],
            }
        )

    return {
        "return_type": "GSTR-1",
        "gstin": payload.get("gstin"),
        "period": payload.get("period"),
        "status": "draft_generated",
        "system_prompt": payload.get("system_prompt"),
        "required_documents": payload.get("required_documents", []),
        "missing_documents": payload.get("missing_documents", []),
        "missing_json_templates": payload.get("missing_json_templates", []),
        "sections": sections,
    }


def _build_filing_csv(filing_json: Mapping[str, Any]) -> str:
    section_outputs: list[dict[str, Any]] = []
    for section in filing_json.get("sections", []):
        if not isinstance(section, dict) or not section.get("document_found"):
            continue

        files = section.get("source_files", [])
        if not isinstance(files, list):
            continue

        column_specs = _template_column_specs(section.get("json_template"))
        output_rows: list[dict[str, Any]] = []
        source_columns: list[str] = []
        for file in files:
            if not isinstance(file, dict):
                continue
            parsed_rows = _parse_source_csv_rows(str(file.get("file_text") or ""))
            for source_row in parsed_rows:
                if column_specs:
                    mapped = _map_source_row_to_template(source_row, column_specs)
                else:
                    mapped = {str(key): value for key, value in source_row.items() if key}
                    source_columns = _merge_columns(source_columns, mapped.keys())
                if any(str(value).strip() for value in mapped.values()):
                    output_rows.append(mapped)

        if output_rows:
            section_outputs.append(
                {
                    "document_key": str(section.get("document_key") or ""),
                    "columns": [spec["name"] for spec in column_specs] if column_specs else source_columns,
                    "rows": output_rows,
                }
            )

    if not section_outputs:
        return ""

    if len(section_outputs) == 1:
        fieldnames = section_outputs[0]["columns"]
        rows = section_outputs[0]["rows"]
    else:
        fieldnames = ["gstr1_section"]
        for section in section_outputs:
            fieldnames = _merge_columns(fieldnames, section["columns"])
        rows = []
        for section in section_outputs:
            for row in section["rows"]:
                rows.append({"gstr1_section": section["document_key"], **row})

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)

    return output.getvalue()


def _template_column_specs(template: Any) -> list[dict[str, Any]]:
    if not isinstance(template, dict):
        return []

    specs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for column in template.get("columns", []):
        if not isinstance(column, dict):
            continue
        name = str(column.get("column_name") or "").strip()
        if not name or name in seen:
            continue
        keys = [_field_key(name), _field_key(str(column.get("canonical_key") or ""))]
        specs.append({"name": name, "keys": [key for key in keys if key]})
        seen.add(name)

    row_template = template.get("row_template")
    if isinstance(row_template, dict):
        for name in row_template.keys():
            name = str(name).strip()
            if name and name not in seen:
                specs.append({"name": name, "keys": [_field_key(name)]})
                seen.add(name)

    return specs


def _parse_source_csv_rows(file_text: str) -> list[dict[str, Any]]:
    if not file_text.strip():
        return []
    try:
        reader = csv.DictReader(StringIO(file_text.lstrip("\ufeff")))
        if not reader.fieldnames:
            return []
        return [{key: value for key, value in row.items() if key is not None} for row in reader]
    except csv.Error:
        return []


def _map_source_row_to_template(
    source_row: Mapping[str, Any],
    column_specs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    lookup = {_field_key(str(key)): value for key, value in source_row.items() if key is not None}
    mapped: dict[str, Any] = {}
    for spec in column_specs:
        name = str(spec.get("name") or "")
        keys = spec.get("keys", [])
        mapped[name] = next(
            (lookup[key] for key in keys if isinstance(key, str) and key in lookup),
            "",
        )
    return mapped


def _merge_columns(existing: Sequence[str], incoming: Iterable[str]) -> list[str]:
    merged = list(existing)
    for column in incoming:
        column = str(column)
        if column and column not in merged:
            merged.append(column)
    return merged


def _field_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _ask_ai(
    *,
    gstin: str,
    period: str | None,
    required_documents: list[str],
    documents: Sequence[Mapping[str, Any]],
    guidelines: str,
) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RequirementCheckError("OPENAI_API_KEY is not configured")

    model = os.getenv("OPENAI_REQUIREMENTS_MODEL", DEFAULT_MODEL)
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a GST return readiness checker for Indian CAs. "
                    "Compare required_documents against uploaded file_name and file_text. "
                    "Return only compact JSON with keys: status, message, "
                    "present, missing, flags, actions. status must be one of "
                    "ready, missing_data, needs_review. actions must contain "
                    "zero or more of: continue, intimate_client. "
                    "For each item in required_documents, copy that exact string "
                    "into present if the uploaded documents contain it, otherwise "
                    "copy that exact string into missing. The present and missing "
                    "arrays must contain only exact strings copied from "
                    "required_documents. Do not invent labels, summaries, generic "
                    "fields, or human-readable rewrites."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "filing": "GSTR-1",
                        "gstin": gstin,
                        "period": period,
                        "required_documents": required_documents,
                        "filing_documents_retrieved_from_database": documents,
                        "guidelines": guidelines,
                    },
                    default=str,
                ),
            },
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
        with urllib.request.urlopen(req, timeout=60) as res:
            body = res.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise RequirementCheckError(_openai_error_message(exc)) from exc
    except urllib.error.URLError as exc:
        raise RequirementCheckError(f"OpenAI request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RequirementCheckError("OpenAI request timed out") from exc

    try:
        content = json.loads(body)["choices"][0]["message"]["content"]
        return json.loads(_strip_json_fence(content))
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RequirementCheckError("OpenAI returned an unexpected requirement check response") from exc


def _missing_from_ai_result(ai_result: Mapping[str, Any], required_documents: Sequence[str]) -> list[str]:
    ordered_required = list(required_documents)
    present_keys = _required_keys(ai_result.get("present", []), ordered_required)

    if present_keys:
        return [doc for doc in ordered_required if _document_key(doc) not in present_keys]

    missing_keys = _required_keys(ai_result.get("missing", []), ordered_required)
    return [doc for doc in ordered_required if _document_key(doc) in missing_keys]


def _required_only_list(values: Any, required_documents: Sequence[str]) -> list[str]:
    value_keys = _required_keys(values, required_documents)
    return [doc for doc in required_documents if _document_key(doc) in value_keys]


def _required_keys(values: Any, required_documents: Sequence[str]) -> set[str]:
    if not isinstance(values, list):
        return set()

    allowed = {_document_key(doc) for doc in required_documents}
    keys = {_document_key(str(item)) for item in values}
    return keys & allowed


def _merge_actions(actions: Any, defaults: Sequence[str]) -> list[str]:
    ordered: list[str] = []
    for action in [*(actions if isinstance(actions, list) else []), *defaults]:
        if isinstance(action, str) and action not in ordered:
            ordered.append(action)
    return ordered


def _document_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        stripped = stripped.removesuffix("```").strip()
    return stripped


def _openai_error_message(exc: urllib.error.HTTPError) -> str:
    try:
        payload = exc.read().decode("utf-8")
        data = json.loads(payload)
        return data.get("error", {}).get("message") or f"OpenAI request failed ({exc.code})"
    except Exception:
        return f"OpenAI request failed ({exc.code})"
