from fastapi import APIRouter, Depends
from app.core.db import get_db
from app.api.deps import get_or_create_default_ca

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def dashboard(db=Depends(get_db)):
    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)

    # Real client count
    cur.execute("SELECT COUNT(*) FROM clients WHERE ca_id = %s", (ca_id,))
    client_count = cur.fetchone()[0]

    return {
        "stats": {
            "clientCount": client_count,
            "filings": {"done": 0, "total": client_count, "delta": 0},
            "openNotices": 0,
            "approved": 0,
            "itcReconciled": "0",
            "sparks": {"filings": [], "notices": [], "approved": [], "itc": []},
        },
        "liability": [],
        "deadlines": [],
        "activity": [],
        "riskWatch": [],
    }
