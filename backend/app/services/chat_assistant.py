from __future__ import annotations
import json
import logging
import urllib.error
import urllib.request
from typing import Iterator
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPTS: dict[str, str] = {
    "filing": (
        "You are AICA, an expert GST filing assistant for Indian Chartered Accountants. "
        "You help with GSTR-1, GSTR-3B, GSTR-2A/2B, ITC reconciliation, reversals, "
        "interest and late fee calculations, and general GST compliance queries. "
        "Be concise, cite the GST Act section or CBIC circular number when relevant, "
        "and never invent or estimate tax figures."
    ),
    "notice": (
        "You are AICA, an expert GST notice reply assistant for Indian Chartered Accountants. "
        "You help interpret GST show-cause notices, demands under Section 73/74/75, "
        "and draft legally grounded reply letters citing the GST Act, rules, and CBIC circulars. "
        "Structure replies point-by-point, include specific citations, and never fabricate "
        "legal references or case law."
    ),
}

_EDIT_STREAM_DELIMITER = "===FILING_JSON==="

_EDIT_STREAM_SYSTEM = (
    "You edit generated GSTR filing outputs for Indian Chartered Accountants. "
    "Apply only the user's requested change to the supplied current CSV and JSON. "
    "Stream your answer in exactly two parts and nothing else:\n"
    "1. First, the complete updated CSV file (raw CSV text, headers included, no markdown fences).\n"
    f"2. Then a single line containing exactly {_EDIT_STREAM_DELIMITER}\n"
    "3. Then the complete updated filing_json as a single compact JSON object.\n"
    "Do not emit any prose, explanation, or message before, between, or after these parts. "
    "Do not invent new tax figures unless the user explicitly provides them. "
    "If the requested change is ambiguous or unsafe, return the current CSV and JSON unchanged."
)


def _get_model() -> str:
    return get_settings().OPENAI_CHAT_MODEL


def _get_base_url() -> str:
    return get_settings().OPENAI_BASE_URL.rstrip("/")


def _get_api_key() -> str:
    return get_settings().OPENAI_API_KEY


def _retrieve_filing_context(query: str) -> str:
    try:
        from app.services.hybrid_search import filing_search_engine
        if filing_search_engine is None:
            return ""
        return filing_search_engine.search_as_context(query)
    except Exception as exc:
        logger.warning("RAG retrieval failed: %s", exc)
        return ""


def _build_filing_system_prompt(gstin: str | None, rag_context: str) -> str:
    base = _SYSTEM_PROMPTS["filing"]
    parts = []
    if gstin:
        parts.append(f"Client GSTIN: {gstin}")
    if rag_context:
        parts.append(
            "Use the following GST knowledge base excerpts to ground your answer. "
            "Cite the relevant section or circular when applicable.\n\n"
            f"--- GST KNOWLEDGE BASE ---\n{rag_context}\n--- END KNOWLEDGE BASE ---"
        )
    parts.append(base)
    return "\n\n".join(parts)


def stream_chat(
    messages: list[dict],
    gstin: str | None = None,
    context: str = "filing",
) -> Iterator[str]:
    api_key = _get_api_key()
    if not api_key:
        yield "OPENAI_API_KEY is not configured."
        return

    user_query = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_query = str(msg.get("content", ""))
            break

    if context == "filing" and user_query:
        rag_context = _retrieve_filing_context(user_query)
        system = _build_filing_system_prompt(gstin, rag_context)
    else:
        system = _SYSTEM_PROMPTS.get(context, _SYSTEM_PROMPTS["filing"])
        if gstin:
            system = f"Client GSTIN: {gstin}\n\n{system}"

    payload = {
        "model": _get_model(),
        "stream": True,
        "messages": [{"role": "system", "content": system}, *messages],
    }

    req = urllib.request.Request(
        f"{_get_base_url()}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            for raw in res:
                line = raw.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    return
                try:
                    chunk = json.loads(data)
                    token = chunk["choices"][0]["delta"].get("content") or ""
                    if token:
                        yield token
                except (KeyError, IndexError, json.JSONDecodeError):
                    continue
    except urllib.error.HTTPError as exc:
        yield f"\n[Error {exc.code}] Could not reach the AI service."
    except urllib.error.URLError as exc:
        yield f"\n[Error] Network error: {exc.reason}"
    except TimeoutError:
        yield "\n[Error] Request timed out."


def stream_edit_filing_output(
    *,
    instruction: str,
    filing_json: dict,
    filing_csv: str,
    gstin: str | None = None,
    period: str | None = None,
) -> Iterator[str]:
    api_key = _get_api_key()
    if not api_key:
        yield "OPENAI_API_KEY is not configured."
        return

    payload = {
        "model": _get_model(),
        "stream": True,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": _EDIT_STREAM_SYSTEM},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "gstin": gstin,
                        "period": period,
                        "instruction": instruction,
                        "current_filing_csv": filing_csv,
                        "current_filing_json": filing_json,
                    },
                    default=str,
                ),
            },
        ],
    }

    req = urllib.request.Request(
        f"{_get_base_url()}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            for raw in res:
                line = raw.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    return
                try:
                    chunk = json.loads(data)
                    token = chunk["choices"][0]["delta"].get("content") or ""
                    if token:
                        yield token
                except (KeyError, IndexError, json.JSONDecodeError):
                    continue
    except urllib.error.HTTPError as exc:
        yield f"\n[Error {exc.code}] Could not reach the AI service."
    except urllib.error.URLError as exc:
        yield f"\n[Error] Network error: {exc.reason}"
    except TimeoutError:
        yield "\n[Error] Request timed out."


def edit_filing_output(
    *,
    instruction: str,
    filing_json: dict,
    filing_csv: str,
    gstin: str | None = None,
    period: str | None = None,
) -> dict:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    system = (
        "You edit generated GSTR filing outputs for Indian Chartered Accountants. "
        "Apply only the user's requested change to the supplied current CSV and JSON. "
        "Return compact JSON only with keys: message, filing_csv, filing_json. "
        "filing_csv must be a complete CSV file, not markdown. "
        "filing_json must be the complete updated JSON object. "
        "Do not invent new tax figures unless the user explicitly provides them."
    )

    payload = {
        "model": _get_model(),
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "gstin": gstin, "period": period, "instruction": instruction,
                        "current_filing_csv": filing_csv, "current_filing_json": filing_json,
                    },
                    default=str,
                ),
            },
        ],
    }

    req = urllib.request.Request(
        f"{_get_base_url()}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            body = res.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"AI service error ({exc.code})") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError("Request timed out") from exc

    try:
        content = json.loads(body)["choices"][0]["message"]["content"]
        parsed = json.loads(_strip_json_fence(content))
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("AI returned unexpected response") from exc

    edited_csv = parsed.get("filing_csv")
    edited_json = parsed.get("filing_json")
    if not isinstance(edited_csv, str) or not isinstance(edited_json, dict):
        raise RuntimeError("AI edit response missing filing_csv or filing_json")

    return {
        "message": str(parsed.get("message") or "Filing output updated."),
        "filing_csv": edited_csv,
        "filing_json": edited_json,
    }


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        stripped = stripped.removesuffix("```").strip()
    return stripped
