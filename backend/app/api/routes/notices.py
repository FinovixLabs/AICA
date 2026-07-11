from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from app.core.db import get_db
from app.api.deps import get_or_create_default_ca, require_client
from app.models.schemas import ApproveReplyRequest

router = APIRouter(prefix="/notices", tags=["notices"])


@router.post("/classify")
async def classify_notice(
    gstin: str = Form(...),
    file: UploadFile = File(...),
    db=Depends(get_db),
):
    cur = db.cursor()
    ca_id = get_or_create_default_ca(cur)
    require_client(cur, ca_id, gstin.upper())

    return {
        "meta": {
            "id": "",
            "type": "",
            "template": "",
            "section": "",
            "demand": "",
            "issue": "",
            "due": "",
            "fileName": file.filename,
        }
    }


@router.post("/draft-reply")
async def draft_reply(body: dict, db=Depends(get_db)):
    gstin = body.get("gstin")
    notice_id = body.get("noticeId")
    if not gstin or not notice_id:
        raise HTTPException(status_code=400, detail="gstin and noticeId are required")
    return {"meta": {}, "draftHtml": "", "refs": []}


@router.post("/approve")
async def approve_reply(body: ApproveReplyRequest):
    return {
        "version": body.version,
        "savedAt": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/knowledge")
async def knowledge(q: str = ""):
    return {
        "stats": {"chunks": 0, "templates": 0, "forms": 0, "updated": ""},
        "templates": [],
        "q": q,
    }
