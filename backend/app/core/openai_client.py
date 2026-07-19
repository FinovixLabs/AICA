"""Thin OpenAI chat-completions transport, shared by every AI call in the app.

Each AI feature — chat streaming, filing edits, register-command planning
(services/chat_assistant.py) and recon column mapping (recon/ai_mapping.py) —
was a POST to {base}/chat/completions with a bearer key wrapped in the same
HTTPError/URLError/TimeoutError handling. This centralizes that one HTTP path so
it lives in exactly one place.

Two entry points, differing only in how failure is surfaced:
  post_chat()   raises LLMError — for callers that need a value or nothing.
  stream_chat() yields a human-readable error string — for callers piping
                straight to a client SSE stream, where raising mid-generator
                would break the response.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Iterable, Iterator

from app.core.config import get_settings


class LLMError(RuntimeError):
    """Transport or protocol failure talking to the chat-completions endpoint."""


def _request(payload: dict[str, Any]) -> urllib.request.Request:
    settings = get_settings()
    return urllib.request.Request(
        f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )


def post_chat(payload: dict[str, Any], *, timeout: int) -> str:
    """POST a completion and return the raw response body. Raises LLMError.

    LLMError subclasses RuntimeError, so existing `except RuntimeError` callers
    keep catching it and the error text is unchanged.
    """
    try:
        with urllib.request.urlopen(_request(payload), timeout=timeout) as res:
            return res.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise LLMError(f"AI service error ({exc.code})") from exc
    except urllib.error.URLError as exc:
        raise LLMError(f"Network error: {exc.reason}") from exc
    except TimeoutError as exc:
        raise LLMError("Request timed out") from exc


def _sse_tokens(lines: Iterable[bytes]) -> Iterator[str]:
    """Extract assistant content tokens from an OpenAI SSE line stream.

    Pure over its input (no network) so it can be exercised directly — see the
    __main__ self-check.
    """
    for raw in lines:
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


def stream_chat(payload: dict[str, Any], *, timeout: int) -> Iterator[str]:
    """POST a streaming completion and yield content tokens.

    On transport failure, yields a single human-readable error string rather than
    raising — the caller pipes this straight to the client SSE stream.
    """
    try:
        with urllib.request.urlopen(_request({**payload, "stream": True}), timeout=timeout) as res:
            yield from _sse_tokens(res)
    except urllib.error.HTTPError as exc:
        yield f"\n[Error {exc.code}] Could not reach the AI service."
    except urllib.error.URLError as exc:
        yield f"\n[Error] Network error: {exc.reason}"
    except TimeoutError:
        yield "\n[Error] Request timed out."


if __name__ == "__main__":
    def _line(content: str) -> bytes:
        return f'data: {{"choices":[{{"delta":{{"content":"{content}"}}}}]}}'.encode()

    stream = [_line("Hel"), b"", b": comment", _line("lo"), b"data: [DONE]", _line("ignored")]
    assert list(_sse_tokens(stream)) == ["Hel", "lo"], list(_sse_tokens(stream))
    assert list(_sse_tokens([b'data: {"bad": true}'])) == []  # malformed shape -> skipped
    print("openai_client self-check ok")
