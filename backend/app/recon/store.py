"""Persistence for the recon module (schema `recon`, migration 004).

Raw psycopg2 against a caller-supplied cursor, matching the rest of the app's
route style (api/routes/*.py). Every function takes an open cursor and never
commits — the get_db dependency commits on success and rolls back on error.

jsonb columns are written with psycopg2.extras.Json so Python dicts/lists round
trip without manual json.dumps and ::jsonb casting.
"""
from __future__ import annotations

from typing import Any

from psycopg2.extras import Json

__all__ = [
    "create_run",
    "accept_matched_inward_results",
    "get_document",
    "get_result",
    "get_run",
    "insert_results",
    "list_documents_by_type",
    "list_results",
    "list_runs",
    "set_result_ignored",
    "set_result_ims_action",
    "set_result_message",
    "reset_run_ims_actions",
]


# ── documents (source files, stored via the Documents workspace) ──────────────
def get_document(cur, document_id: str, client_id: str) -> dict[str, Any] | None:
    """One document from the base `documents` table, scoped to the client."""
    cur.execute(
        """
        SELECT id::text, doc_type::text, file_name, storage_path, tax_period
        FROM documents WHERE id = %s AND client_id = %s
        """,
        (document_id, client_id),
    )
    row = cur.fetchone()
    if row is None:
        return None
    return {
        "id": row[0], "doc_type": row[1], "file_name": row[2],
        "storage_path": row[3], "tax_period": row[4],
    }


def list_documents_by_type(cur, client_id: str, doc_types: list[str]) -> list[dict[str, Any]]:
    """Selectable documents of the given type(s) for a client, newest first."""
    cur.execute(
        """
        SELECT id::text, doc_type::text, file_name, tax_period, uploaded_at
        FROM documents
        WHERE client_id = %s AND doc_type::text = ANY(%s)
        ORDER BY uploaded_at DESC
        """,
        (client_id, doc_types),
    )
    return [
        {
            "id": r[0], "doc_type": r[1], "file_name": r[2], "tax_period": r[3],
            "uploaded_at": r[4].isoformat() if r[4] else None,
        }
        for r in cur.fetchall()
    ]


# ── runs ──────────────────────────────────────────────────────────────────────
def create_run(
    cur,
    *,
    client_id: str,
    module: str,
    period: str | None,
    pr_document_id: str | None,
    cp_document_id: str | None,
    config: dict[str, Any],
    totals: dict[str, Any],
    excluded: list[dict[str, Any]],
    engine_version: str | None,
) -> str:
    cur.execute(
        """
        INSERT INTO recon.runs
            (client_id, module, period, pr_document_id, cp_document_id,
             config, totals, excluded, engine_version)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id::text
        """,
        (
            client_id, module, period, pr_document_id, cp_document_id,
            Json(config), Json(totals), Json(excluded), engine_version,
        ),
    )
    return cur.fetchone()[0]


def get_run(cur, run_id: str, client_id: str) -> dict[str, Any] | None:
    cur.execute(
        """
        SELECT id::text, module, period, config, totals, excluded, engine_version, created_at
        FROM recon.runs WHERE id = %s AND client_id = %s
        """,
        (run_id, client_id),
    )
    row = cur.fetchone()
    if row is None:
        return None
    return {
        "id": row[0], "module": row[1], "period": row[2], "config": row[3],
        "totals": row[4], "excluded": row[5], "engine_version": row[6],
        "created_at": row[7].isoformat() if row[7] else None,
    }


def list_runs(cur, client_id: str, module: str, limit: int = 25) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT id::text, period, totals, created_at
        FROM recon.runs WHERE client_id = %s AND module = %s
        ORDER BY created_at DESC LIMIT %s
        """,
        (client_id, module, limit),
    )
    return [
        {
            "id": r[0], "period": r[1], "totals": r[2],
            "created_at": r[3].isoformat() if r[3] else None,
        }
        for r in cur.fetchall()
    ]


# ── results ───────────────────────────────────────────────────────────────────
def insert_results(cur, run_id: str, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Persist each reconciliation-list row, returning the rows with their db ids
    injected under 'id' (the frontend needs the id for ignore / message)."""
    out: list[dict[str, Any]] = []
    for result in results:
        cur.execute(
            """
            INSERT INTO recon.results
                (run_id, seq, status, status_code, match_key, payload, ims_action)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id::text, ims_action, ims_action_at
            """,
            (
                run_id, result.get("seq", 0), result["status"], result["status_code"],
                result.get("key"), Json(result), result.get("ims_action", "not_actioned"),
            ),
        )
        inserted = cur.fetchone()
        out.append({
            **result,
            "id": inserted[0],
            "ims_action": inserted[1],
            "ims_action_at": inserted[2].isoformat() if inserted[2] else None,
            "ignored": False,
            "message": None,
        })
    return out


def list_results(cur, run_id: str, client_id: str) -> list[dict[str, Any]] | None:
    # Confirm the run belongs to the client before returning any rows.
    cur.execute(
        "SELECT 1 FROM recon.runs WHERE id = %s AND client_id = %s",
        (run_id, client_id),
    )
    if cur.fetchone() is None:
        return None
    cur.execute(
        """
        SELECT id::text, payload, ignored, message, ims_action, ims_action_at
        FROM recon.results WHERE run_id = %s
        ORDER BY status_code, seq
        """,
        (run_id,),
    )
    return [
        {
            **r[1], "id": r[0], "ignored": r[2], "message": r[3],
            "ims_action": r[4], "ims_action_at": r[5].isoformat() if r[5] else None,
        }
        for r in cur.fetchall()
    ]


def get_result(cur, result_id: str, client_id: str) -> dict[str, Any] | None:
    cur.execute(
        """
        SELECT r.id::text, r.payload, r.ignored, r.message, r.run_id::text, run.module,
               r.ims_action, r.ims_action_at
        FROM recon.results r
        JOIN recon.runs run ON run.id = r.run_id
        WHERE r.id = %s AND run.client_id = %s
        """,
        (result_id, client_id),
    )
    row = cur.fetchone()
    if row is None:
        return None
    return {
        "id": row[0], "payload": row[1], "ignored": row[2],
        "message": row[3], "run_id": row[4], "module": row[5],
        "ims_action": row[6],
        "ims_action_at": row[7].isoformat() if row[7] else None,
    }


def set_result_ignored(cur, result_id: str, client_id: str, ignored: bool) -> bool:
    cur.execute(
        """
        UPDATE recon.results r SET ignored = %s
        FROM recon.runs run
        WHERE r.id = %s AND r.run_id = run.id AND run.client_id = %s
        """,
        (ignored, result_id, client_id),
    )
    return cur.rowcount > 0


def set_result_message(cur, result_id: str, client_id: str, message: str) -> bool:
    cur.execute(
        """
        UPDATE recon.results r SET message = %s
        FROM recon.runs run
        WHERE r.id = %s AND r.run_id = run.id AND run.client_id = %s
        """,
        (message, result_id, client_id),
    )
    return cur.rowcount > 0


def set_result_ims_action(
    cur, result_id: str, client_id: str, action: str
) -> dict[str, Any] | None:
    """Persist a local IMS Inward action, scoped to its owning client and module."""
    cur.execute(
        """
        UPDATE recon.results result
        SET ims_action = %s,
            ims_action_at = now()
        FROM recon.runs run
        WHERE result.id = %s
          AND result.run_id = run.id
          AND run.client_id = %s
          AND run.module = 'ims_inward'
        RETURNING result.id::text, result.ims_action, result.ims_action_at
        """,
        (action, result_id, client_id),
    )
    row = cur.fetchone()
    if row is None:
        return None
    return {"id": row[0], "ims_action": row[1], "ims_action_at": row[2].isoformat()}


def reset_run_ims_actions(cur, run_id: str, client_id: str) -> int | None:
    """Reset every action in one IMS Inward run to its default value."""
    cur.execute(
        "SELECT 1 FROM recon.runs WHERE id = %s AND client_id = %s AND module = 'ims_inward'",
        (run_id, client_id),
    )
    if cur.fetchone() is None:
        return None
    cur.execute(
        """
        UPDATE recon.results
        SET ims_action = 'not_actioned', ims_action_at = NULL,
            ignored = FALSE, message = NULL
        WHERE run_id = %s
        """,
        (run_id,),
    )
    return cur.rowcount


def accept_matched_inward_results(
    cur, run_id: str, client_id: str
) -> list[str] | None:
    """Accept pending matched rows without overwriting manual Reject/Hold choices."""
    cur.execute(
        "SELECT 1 FROM recon.runs WHERE id = %s AND client_id = %s AND module = 'ims_inward'",
        (run_id, client_id),
    )
    if cur.fetchone() is None:
        return None
    cur.execute(
        """
        UPDATE recon.results
        SET ims_action = 'accept', ims_action_at = now()
        WHERE run_id = %s
          AND status = 'matched'
          AND ims_action = 'not_actioned'
        RETURNING id::text
        """,
        (run_id,),
    )
    return [row[0] for row in cur.fetchall()]
