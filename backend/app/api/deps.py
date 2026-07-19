from __future__ import annotations
from fastapi import HTTPException
from app.core.db import get_db  # re-export for convenience

_default_ca_id: str | None = None


def get_or_create_default_ca(cur) -> str:
    global _default_ca_id
    if _default_ca_id:
        return _default_ca_id
    cur.execute("SELECT id FROM cas ORDER BY created_at LIMIT 1")
    row = cur.fetchone()
    if row is None:
        cur.execute(
            "INSERT INTO cas (full_name, firm_name) VALUES (%s, %s) RETURNING id",
            ("Default CA", "AICA"),
        )
        row = cur.fetchone()
    _default_ca_id = str(row[0])
    return _default_ca_id


def get_client_id(cur, ca_id: str, gstin: str) -> str | None:
    cur.execute(
        "SELECT id FROM clients WHERE ca_id = %s AND gstin = %s",
        (ca_id, gstin),
    )
    row = cur.fetchone()
    return str(row[0]) if row else None


def require_client(cur, ca_id: str, gstin: str) -> str:
    client_id = get_client_id(cur, ca_id, gstin)
    if client_id is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client_id


def human_size(n: int | None) -> str:
    if not n:
        return ""
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def filing_frequency(scheme: str) -> str:
    s = (scheme or "").strip().lower()
    if any(k in s for k in ("quarter", "qrmp", "cmp")):
        return "quarterly"
    return "monthly"
