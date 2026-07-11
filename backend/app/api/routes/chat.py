from __future__ import annotations
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest
from app.services.chat_assistant import stream_chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(body: ChatRequest, stream: bool = False):
    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    if stream:
        def event_stream():
            for token in stream_chat(messages, gstin=body.gstin, context=body.context):
                if token:
                    yield f"data: {json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    reply = "".join(stream_chat(messages, gstin=body.gstin, context=body.context))
    return {"reply": reply}
