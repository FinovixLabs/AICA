from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Iterator

# Edit these to change the opening message the AI sees when each section loads.
CHAT_INIT: dict[str, str] = {
    "filing": "Greet me briefly and explain what you can help me with in the GST filing section.",
    "notice": "Greet me briefly and explain what you can help me with in the GST notice section.",
}

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


def stream_chat(
    messages: list[dict],
    gstin: str | None = None,
    context: str = "filing",
) -> Iterator[str]:
    """Yield text tokens from OpenAI streaming chat completion."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        yield "OPENAI_API_KEY is not configured — cannot reach the assistant."
        return

    system = _SYSTEM_PROMPTS.get(context, _SYSTEM_PROMPTS["filing"])
    if gstin:
        system = f"Client GSTIN: {gstin}\n\n{system}"

    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4-mini")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    payload = {
        "model": model,
        "stream": True,
        "messages": [{"role": "system", "content": system}, *messages],
    }

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
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


def edit_filing_output(
    *,
    instruction: str,
    filing_json: dict,
    filing_csv: str,
    gstin: str | None = None,
    period: str | None = None,
) -> dict:
    """Return an AI-edited filing JSON/CSV pair for assistant-requested changes."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4-mini")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    system = (
        "You edit generated GSTR filing outputs for Indian Chartered Accountants. "
        "Apply only the user's requested change to the supplied current CSV and JSON. "
        "Return compact JSON only with keys: message, filing_csv, filing_json. "
        "filing_csv must be a complete CSV file, not markdown. "
        "filing_json must be the complete updated JSON object. "
        "Do not invent new tax figures unless the user explicitly provides them. "
        "If the requested change is ambiguous or unsafe, leave the files unchanged "
        "and explain the exact missing detail in message."
    )

    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
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
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            body = res.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Could not reach the AI service ({exc.code})") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError("Request timed out") from exc

    try:
        content = json.loads(body)["choices"][0]["message"]["content"]
        parsed = json.loads(_strip_json_fence(content))
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("AI returned an unexpected filing edit response") from exc

    edited_csv = parsed.get("filing_csv")
    edited_json = parsed.get("filing_json")
    if not isinstance(edited_csv, str) or not isinstance(edited_json, dict):
        raise RuntimeError("AI edit response did not include filing_csv and filing_json")

    return {
        "message": str(parsed.get("message") or "Filing output updated."),
        "filing_csv": edited_csv,
        "filing_json": edited_json,
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


def stream_edit_filing_output(
    *,
    instruction: str,
    filing_json: dict,
    filing_csv: str,
    gstin: str | None = None,
    period: str | None = None,
) -> Iterator[str]:
    """Yield tokens of an AI-edited filing as: <CSV> ===FILING_JSON=== <JSON>.

    Mirrors stream_chat()'s OpenAI streaming/error handling. The strict two-part
    contract lets the client render the CSV live and parse the JSON at the end.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        yield "OPENAI_API_KEY is not configured — cannot reach the assistant."
        return

    model = os.getenv("OPENAI_CHAT_MODEL", "gpt-5.4-mini")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    payload = {
        "model": model,
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
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
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


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        stripped = stripped.removesuffix("```").strip()
    return stripped
