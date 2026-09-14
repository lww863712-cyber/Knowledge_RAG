import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.agents.rag_agent import RAGAgent
from app.api.deps import get_current_user
from app.models import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import answer_with_rag, stream_answer_with_rag

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
) -> ChatResponse:
    history = [item.model_dump() for item in payload.history]
    try:
        result = await RAGAgent().run(payload.knowledge_base_id, payload.message, history)
    except Exception as exc:
        import logging
        logging.exception("agent chat failed")
        raise HTTPException(status_code=500, detail=f"Agent 执行失败: {exc}") from exc
    return ChatResponse(**result)


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    history = [item.model_dump() for item in payload.history]
    async def event_generator():
        async for event in stream_answer_with_rag(payload.knowledge_base_id, payload.message, history, user):
            yield event
    return StreamingResponse(event_generator(), media_type="text/event-stream")