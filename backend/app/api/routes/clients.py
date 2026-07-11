from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from app.core.db import get_db
from app.api.deps import get_or_create_default_ca, get_client_id, require_client, human_size, filing_frequency
from app.models.schemas import ClientCreate

router = APIRouter(prefix="/clients", tags=["clients"])

_CLIENT_COLS = """
    gstin,
    legal_name                 AS name,
    state_code                 AS state,
    reg_type                   AS type,
    reg_scheme                 AS scheme,
    status::text               AS status,
    UPPER(LEFT(legal_name, 1)) AS init
"""


@router.get("")
async def list_clients(db=Depends(get_db)):
    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    cur.execute(
        f"SELECT {_CLIENT_COLS} FROM clients WHERE ca_id = %s ORDER BY legal_name",
        (ca_id,),
    )
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


@router.post("", status_code=201)
async def create_client(body: ClientCreate, db=Depends(get_db)):
    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)

    cur.execute(
        f"""
        WITH ins AS (
            INSERT INTO clients
                (ca_id, gstin, legal_name, state_code, reg_type, reg_scheme, filing_frequency)
            VALUES
                (%(ca_id)s, %(gstin)s, %(name)s, %(state)s, %(type)s, %(scheme)s, %(freq)s)
            ON CONFLICT (ca_id, gstin) DO NOTHING
            RETURNING *
        )
        SELECT {_CLIENT_COLS} FROM ins
        """,
        {
            "ca_id": ca_id,
            "gstin": body.gstin,
            "name": body.name,
            "state": body.state,
            "type": body.type,
            "scheme": body.scheme,
            "freq": filing_frequency(body.scheme or ""),
        },
    )
    row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=409, detail="A client with this GSTIN already exists")
    cols = [d[0] for d in cur.description]
    return {"client": dict(zip(cols, row))}


@router.get("/{gstin}")
async def get_client(gstin: str, db=Depends(get_db)):
    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    client_id = get_client_id(cur, ca_id, gstin.upper())

    # fetch basic info
    cur.execute(
        f"SELECT {_CLIENT_COLS} FROM clients WHERE ca_id = %s AND gstin = %s",
        (ca_id, gstin.upper()),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    cols = [d[0] for d in cur.description]
    client = dict(zip(cols, row))

    return {
        **client,
        "stats": {"returns": "0/0", "itcMatch": 0, "openNotices": 0},
        "signals": [],
        "documents": [],
        "filings": [],
        "notices": [],
    }
