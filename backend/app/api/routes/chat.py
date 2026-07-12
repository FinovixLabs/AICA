from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.api.deps import get_or_create_default_ca, require_client
from app.core.db import get_db
from app.models.schemas import ChatRequest
from app.services.chat_assistant import stream_chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(body: ChatRequest, stream: bool = False, db=Depends(get_db)):
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    client_documents: list[dict] = []

    if body.context == "filing" and body.gstin:
        output_gstin = str((body.filing_output or {}).get("gstin") or "").strip().upper()
        if output_gstin and output_gstin != body.gstin.strip().upper():
            raise HTTPException(status_code=422, detail="Filing output does not belong to the selected client")
        cur = db.cursor()
        ca_id = get_or_create_default_ca(cur)
        client_id = require_client(cur, ca_id, body.gstin.strip().upper())
        cur.execute(
            """
            SELECT file_name, doc_type::text, tax_period, file_text
            FROM documents
            WHERE client_id = %s
            ORDER BY uploaded_at DESC
            """,
            (client_id,),
        )
        client_documents = [
            {
                "file_name": row[0],
                "doc_type": row[1],
                "tax_period": row[2],
                "file_text": row[3] or "",
            }
            for row in cur.fetchall()
        ]

    if stream:
        def event_stream():
            for token in stream_chat(
                messages,
                gstin=body.gstin,
                context=body.context,
                filing_output=body.filing_output,
                client_documents=client_documents,
            ):
                if token:
                    yield f"data: {json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    reply = "".join(stream_chat(
        messages,
        gstin=body.gstin,
        context=body.context,
        filing_output=body.filing_output,
        client_documents=client_documents,
    ))
    return {"reply": reply}
