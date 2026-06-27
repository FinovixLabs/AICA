from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO
import json
import os
import re
from typing import Any

from flask import Blueprint, Response, g, jsonify, request, stream_with_context
from werkzeug.utils import secure_filename

from chat_assistant import edit_filing_output, stream_chat, stream_edit_filing_output
from filing.prerequisites import check as check_prerequisites, SUPPORTED_FILING_TYPES
from requirement_checking import (
    RequirementCheckError,
    build_gstr1_filing_start_payload,
    run_gstr1_requirement_check,
)
from uploading import extract_and_clean

# GSTIN format enforced by the DB CHECK constraint (chk_clients_gstin_format).
GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z]$")

# Local disk root for uploaded client documents (storage_path is relative to this).
UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

_default_ca_id: str | None = None


api_bp = Blueprint("api", __name__,url_prefix="/api")
# routes/auth.py
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# routes/clients.py
client_bp = Blueprint("clients", __name__, url_prefix="/api/clients")

# routes/filing.py
filing_bp = Blueprint("filing", __name__, url_prefix="/api/filing")

# routes/notices.py
notice_bp = Blueprint("notices", __name__, url_prefix="/api/notices")


def _json(data: Any, status: int = 200):
    return jsonify(data), status


def _body() -> dict[str, Any]:
    return request.get_json(silent=True) or {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _filing_frequency(scheme: str) -> str:
    """Normalize a free-text scheme label to the filing_frequency enum."""
    s = (scheme or "").strip().lower()
    if any(k in s for k in ("quarter", "qrmp", "cmp")):
        return "quarterly"
    return "monthly"


def _default_ca(cur) -> str:
    """Return the id of a default CA, creating one if none exists.

    Clients require a ca_id FK. Until real auth is wired up, every client is
    attached to a single default CA so inserts/selects work end-to-end.
    """
    global _default_ca_id
    if _default_ca_id is not None:
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


def _client_id(cur, ca_id: str, gstin: str) -> str | None:
    """Resolve a client's UUID from its GSTIN for the given CA."""
    cur.execute(
        "SELECT id FROM clients WHERE ca_id = %s AND gstin = %s",
        (ca_id, gstin),
    )
    row = cur.fetchone()
    return str(row[0]) if row else None


def _human_size(n: int | None) -> str:
    """Format a byte count as a short human-readable string."""
    if not n:
        return ""
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


# Column projection shared by GET and POST. Every column it references is
# present both on `clients` and in an `INSERT ... RETURNING *` row.
_CLIENT_COLS = """
    gstin,
    legal_name                 AS name,
    state_code                 AS state,
    reg_type                   AS type,
    reg_scheme                 AS scheme,
    status::text               AS status,
    UPPER(LEFT(legal_name, 1)) AS init
"""


@auth_bp.post("/login")
def login():
    data = _body()
    if not data.get("email") or not data.get("password"):
        return _json({"error": "email and password are required"}, 400)

    # TODO: replace with your real auth lookup and token issuing.
    user = {
        "name": data["email"].split("@")[0],
        "frn": "",
        "initials": data["email"][:2].upper(),
        "firm": "",
    }
    return _json({"token": "", "user": user})


@auth_bp.post("/logout")
def logout():
    # TODO: clear/revoke the real auth session if you use server-side sessions.
    return _json({"ok": True})


@auth_bp.get("/me")
def me():
    # TODO: return the authenticated user from token/cookie context.
    return _json({"user": None})


@api_bp.get("/dashboard")
def dashboard():

    return _json(
        {
            "stats": {
                "filings": {"done": 0, "total": 0, "delta": 0},
                "openNotices": 0,
                "approved": 0,
                "itcReconciled": "0",
                "sparks": {
                    "filings": [],
                    "notices": [],
                    "approved": [],
                    "itc": [],
                },
            },
            "liability": [],
            "deadlines": [],
            "activity": [],
            "riskWatch": [],
        }
    )


@client_bp.route("", methods=["GET", "POST"])
def clients():
    cur = g.db.cursor()
    ca_id = _default_ca(cur)

    if request.method == "GET":
        cur.execute(
            f"SELECT {_CLIENT_COLS} FROM clients WHERE ca_id = %s ORDER BY legal_name",
            (ca_id,),
        )
        cols = [d[0] for d in cur.description]
        return _json([dict(zip(cols, r)) for r in cur.fetchall()])

    data = _body()
    if not isinstance(data, dict):
        return _json({"error": "request body must be an object"}, 400)

    client = data.get("client")
    if not isinstance(client, dict):
        client = data

    gstin = str(client.get("gstin", "")).strip().upper()
    name = str(client.get("name", "")).strip()
    if not gstin:
        return _json({"error": "GSTIN is required"}, 400)
    if not name:
        return _json({"error": "Name is required"}, 400)
    if not GSTIN_RE.match(gstin):
        return _json({"error": "GSTIN format is invalid"}, 400)

    reg_type = (str(client.get("type", "")).strip() or None)
    reg_scheme = (str(client.get("scheme", "")).strip() or None)

    cur.execute(
        f"""
        WITH ins AS (
            INSERT INTO clients
                (ca_id, gstin, legal_name, state_code,
                 reg_type, reg_scheme, filing_frequency)
            VALUES
                (%(ca_id)s, %(gstin)s, %(name)s, %(state)s,
                 %(reg_type)s, %(reg_scheme)s, %(filing_frequency)s)
            ON CONFLICT (ca_id, gstin) DO NOTHING
            RETURNING *
        )
        SELECT {_CLIENT_COLS} FROM ins
        """,
        {
            "ca_id": ca_id,
            "gstin": gstin,
            "name": name,
            "state": (str(client.get("state", "")).strip() or None),
            "reg_type": reg_type,
            "reg_scheme": reg_scheme,
            "filing_frequency": _filing_frequency(reg_scheme or ""),
        },
    )
    row = cur.fetchone()
    g.db.commit()
    if row is None:
        return _json({"error": "A client with this GSTIN already exists"}, 409)
    cols = [d[0] for d in cur.description]
    return _json({"client": dict(zip(cols, row))}, 201)


@client_bp.get("/<gstin>")
def client(gstin: str):
    # TODO: load this GSTIN from your database.
    return _json(
        {
            "gstin": gstin,
            "stats": {"returns": "0/0", "itcMatch": 0, "openNotices": 0},
            "signals": [],
            "documents": [],
            "filings": [],
            "notices": [],
        }
    )

def _doc_row(name: str, doc_type: str, size: int | None, period: str | None = None) -> dict:
    """Shape a documents row for the frontend (dDoc / handleFiles renderers)."""
    return {
        "name": name,
        "type": doc_type.replace("_", " ").title(),
        "route": period or "",
        "extracted": _human_size(size),
        "status": "stored",
    }


@client_bp.route("/<gstin>/documents", methods=["GET", "POST"])
def documents(gstin: str):
    cur = g.db.cursor()
    ca_id = _default_ca(cur)
    gstin = gstin.strip().upper()
    client_id = _client_id(cur, ca_id, gstin)
    if client_id is None:
        return _json({"error": "client not found"}, 404)

    if request.method == "GET":
        cur.execute(
            """
            SELECT file_name, doc_type::text, file_size_bytes, tax_period
            FROM documents
            WHERE client_id = %s
            ORDER BY uploaded_at DESC
            """,
            (client_id,),
        )
        return _json([_doc_row(n, t, s, p) for (n, t, s, p) in cur.fetchall()])

    uploaded = request.files.get("file")
    if uploaded is None or not uploaded.filename:
        return _json({"error": "file is required"}, 400)

    # The frontend "type" field is a format hint (text_pdf/csv/...), not a
    # document_type category, so persist the default category for now.
    doc_type = "other"
    file_name = uploaded.filename

    dest_dir = os.path.join(UPLOAD_ROOT, client_id)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, secure_filename(file_name) or "upload")
    uploaded.save(dest_path)
    size = os.path.getsize(dest_path)
    storage_path = os.path.relpath(dest_path, UPLOAD_ROOT)
    file_text = extract_and_clean(dest_path)

    cur.execute(
        """
        INSERT INTO documents
            (client_id, doc_type, file_name, storage_path, file_size_bytes, file_text)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING file_name, doc_type::text, file_size_bytes, tax_period
        """,
        (client_id, doc_type, file_name, storage_path, size, file_text),
    )
    row = cur.fetchone()
    g.db.commit()
    doc = _doc_row(row[0], row[1], row[2], row[3])
    return _json({**doc, "doc": doc}, 201)


@filing_bp.post("/prerequisites")
def prerequisites():
    data = _body()
    gstin = str(data.get("gstin", "")).strip().upper()
    filing_type = str(data.get("filing_type", "")).strip().upper()

    if not gstin:
        return _json({"error": "gstin is required"}, 400)
    if not filing_type:
        return _json({"error": "filing_type is required"}, 400)
    if filing_type not in SUPPORTED_FILING_TYPES:
        return _json({"error": f"unsupported filing_type; supported: {SUPPORTED_FILING_TYPES}"}, 400)

    cur = g.db.cursor()
    ca_id = _default_ca(cur)
    client_id = _client_id(cur, ca_id, gstin)
    if client_id is None:
        return _json({"error": "client not found"}, 404)

    result = check_prerequisites(cur, client_id, filing_type)
    status_code = 200 if result.get("status") == "ready" else 422
    return _json(result, status_code)


@filing_bp.post("/reconcile")
def reconcile():
    data = _body()
    if not data.get("gstin") or not data.get("period"):
        return _json({"error": "gstin and period are required"}, 400)

    # TODO: run your deterministic reconciliation pipeline.
    return _json({"rows": [], "output": {"rows": []}, "status": "pending"})


@filing_bp.post("/requirements-check")
def requirements_check():
    data = _body()
    gstin = str(data.get("gstin", "")).strip().upper()
    period = str(data.get("period", "")).strip() or None

    if not gstin:
        return _json({"error": "gstin is required"}, 400)

    cur = g.db.cursor()
    ca_id = _default_ca(cur)
    client_id = _client_id(cur, ca_id, gstin)
    if client_id is None:
        return _json({"error": "client not found"}, 404)

    try:
        result = run_gstr1_requirement_check(
            g.db,
            client_id=client_id,
            gstin=gstin,
            period=period,
        )
    except RequirementCheckError as exc:
        return _json({"error": str(exc)}, 502)

    return _json(result)


@filing_bp.post("/start")
def filing_start():
    data = _body()
    gstin = str(data.get("gstin", "")).strip().upper()
    period = str(data.get("period", "")).strip() or None

    if not gstin:
        return _json({"error": "gstin is required"}, 400)

    cur = g.db.cursor()
    ca_id = _default_ca(cur)
    client_id = _client_id(cur, ca_id, gstin)
    if client_id is None:
        return _json({"error": "client not found"}, 404)

    result = build_gstr1_filing_start_payload(
        g.db,
        client_id=client_id,
        gstin=gstin,
        period=period,
    )
    return _json(result)


@filing_bp.post("/edit-output")
def edit_filing_output_route():
    data = _body()
    gstin = str(data.get("gstin", "")).strip().upper()
    period = str(data.get("period", "")).strip() or None
    instruction = str(data.get("instruction", "")).strip()
    filing_csv = data.get("filing_csv")
    filing_json = data.get("filing_json")

    if not gstin:
        return _json({"error": "gstin is required"}, 400)
    if not instruction:
        return _json({"error": "instruction is required"}, 400)
    if not isinstance(filing_csv, str) or not isinstance(filing_json, dict):
        return _json({"error": "filing_csv and filing_json are required"}, 400)

    cur = g.db.cursor()
    ca_id = _default_ca(cur)
    if _client_id(cur, ca_id, gstin) is None:
        return _json({"error": "client not found"}, 404)

    try:
        result = edit_filing_output(
            instruction=instruction,
            filing_json=filing_json,
            filing_csv=filing_csv,
            gstin=gstin,
            period=period,
        )
    except RuntimeError as exc:
        return _json({"error": str(exc)}, 502)

    return _json({"status": "updated", **result})


@filing_bp.post("/edit-output-stream")
def edit_filing_output_stream_route():
    data = _body()
    gstin = str(data.get("gstin", "")).strip().upper()
    period = str(data.get("period", "")).strip() or None
    instruction = str(data.get("instruction", "")).strip()
    filing_csv = data.get("filing_csv")
    filing_json = data.get("filing_json")

    if not gstin:
        return _json({"error": "gstin is required"}, 400)
    if not instruction:
        return _json({"error": "instruction is required"}, 400)
    if not isinstance(filing_csv, str) or not isinstance(filing_json, dict):
        return _json({"error": "filing_csv and filing_json are required"}, 400)

    cur = g.db.cursor()
    ca_id = _default_ca(cur)
    if _client_id(cur, ca_id, gstin) is None:
        return _json({"error": "client not found"}, 404)

    def event_stream():
        for token in stream_edit_filing_output(
            instruction=instruction,
            filing_json=filing_json,
            filing_csv=filing_csv,
            gstin=gstin,
            period=period,
        ):
            if token:
                yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")


@filing_bp.post("/output")
def filing_output():
    data = _body()
    gstin = data.get("gstin", "client")
    period = data.get("period", "period")

    # generate this CSV from the saved reconciliation output.
    csv = StringIO()
    csv.write("table,description,igst,cgst,sgst\n")

    headers = {
        "Content-Disposition": f"attachment; filename=GSTR3B_{gstin}_{period}.csv"
    }
    return Response(csv.getvalue(), mimetype="text/csv", headers=headers)


@notice_bp.post("/classify")
def classify_notice():
    gstin = request.form.get("gstin")
    uploaded = request.files.get("file")
    if not gstin or uploaded is None:
        return _json({"error": "gstin and file are required"}, 400)

    # TODO: save/classify notice and return extracted metadata.
    return _json(
        {
            "meta": {
                "id": "",
                "type": "",
                "template": "",
                "section": "",
                "demand": "",
                "issue": "",
                "due": "",
                "fileName": uploaded.filename,
            }
        }
    )


@notice_bp.post("/draft-reply")
def draft_reply():
    data = _body()
    if not data.get("gstin") or not data.get("noticeId"):
        return _json({"error": "gstin and noticeId are required"}, 400)

    # TODO: call your RAG/LLM drafting flow and return reviewed draft metadata.
    return _json({"meta": {}, "draftHtml": "", "refs": []})


@notice_bp.post("/approve")
def approve_reply():
    data = _body()
    required = {"gstin", "noticeId", "html", "version"}
    missing = [key for key in required if key not in data]
    if missing:
        return _json({"error": f"missing required fields: {', '.join(missing)}"}, 400)

    # persist final reply html/version against the notice record.
    return _json({"version": data["version"], "savedAt": _now_iso()})


@api_bp.post("/chat")
def chat():
    data = _body()
    raw_messages = data.get("messages")
    messages = raw_messages if isinstance(raw_messages, list) else []
    context = str(data.get("context") or "").strip()
    gstin = str(data.get("gstin") or "").strip()

    wants_stream = "text/event-stream" in request.headers.get("Accept", "")
    if not wants_stream:
        reply = "".join(stream_chat(messages, gstin=gstin or None, context=context or "filing"))
        return _json({"reply": reply})

    def event_stream():
        for token in stream_chat(messages, gstin=gstin or None, context=context or "filing"):
            if token:
                yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")


@api_bp.get("/knowledge")
def knowledge():
    query = request.args.get("q", "")

    # TODO: return metadata from the GST knowledge collection, filtered by q.
    return _json(
        {
            "stats": {"chunks": 0, "templates": 0, "forms": 0, "updated": ""},
            "templates": [],
            "q": query,
        }
    )


__all__ = ["api_bp", "client_bp", "auth_bp","filing_bp","notice_bp"]
