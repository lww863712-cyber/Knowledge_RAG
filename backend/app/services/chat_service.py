import asyncio
import json
import time
from collections.abc import AsyncGenerator

from langchain_core.messages import HumanMessage, SystemMessage

from app.db.session import SessionLocal
from app.models import User
from app.rag.retrieval.hybrid import HybridRetriever
from app.services.ingestion_service import ensure_bm25_loaded
from app.services.llm_service import current_provider_model, get_chat_model
from app.services.usage_service import record_usage

SYSTEM_PROMPT = """你是个人知识库 AgentRAG。请基于提供的知识片段回答问题。
要求：
1. 如果知识片段不足，明确说明无法从知识库确认。
2. 回答中使用 [1]、[2] 等编号标注引用来源。
3. 用中文回答，保持准确、简洁。
"""


async def retrieve_context(knowledge_base_id: int, query: str, top_k: int = 6) -> list[dict]:
    async with SessionLocal() as session:
        await ensure_bm25_loaded(session, knowledge_base_id)
    retriever = HybridRetriever()
    return await retriever.retrieve(knowledge_base_id, query, top_k)


def build_context(results: list[dict]) -> str:
    parts = []
    for index, item in enumerate(results, start=1):
        parts.append(f"[{index}] {item['content']}")
    return "\n\n".join(parts)


def build_messages(history: list[dict], context: str, query: str) -> list:
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for item in history:
        if item.get("role") == "user":
            messages.append(HumanMessage(content=item.get("content", "")))
        else:
            messages.append(SystemMessage(content=item.get("content", "")))
    messages.append(HumanMessage(content=f"知识片段：\n{context}\n\n问题：{query}"))
    return messages


async def answer_with_rag(
    knowledge_base_id: int,
    query: str,
    history: list[dict],
    user: User | None = None,
) -> dict:
    started = time.perf_counter()
    results = await retrieve_context(knowledge_base_id, query)
    context = build_context(results)
    messages = build_messages(history, context, query)
    llm = get_chat_model()
    response = await llm.ainvoke(messages)
    duration_ms = int((time.perf_counter() - started) * 1000)

    usage = getattr(response, "usage_metadata", None) or {}
    input_tokens = int(usage.get("input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    provider, model = current_provider_model()

    async with SessionLocal() as session:
        await record_usage(session, user.id if user else None, provider, model, input_tokens, output_tokens, duration_ms, "chat")

    return {
        "answer": str(response.content),
        "citations": results,
        "steps": ["retrieve", "generate"],
    }


async def stream_answer_with_rag(
    knowledge_base_id: int,
    query: str,
    history: list[dict],
    user: User | None = None,
) -> AsyncGenerator[str, None]:
    started = time.perf_counter()
    results = await retrieve_context(knowledge_base_id, query)
    context = build_context(results)
    messages = build_messages(history, context, query)
    llm = get_chat_model(stream_usage=True)

    yield f"data: {json.dumps({'type': 'citations', 'content': results}, ensure_ascii=False)}\n\n"

    answer_parts: list[str] = []
    input_tokens = 0
    output_tokens = 0
    async for chunk in llm.astream(messages):
        token = str(chunk.content or "")
        answer_parts.append(token)
        yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"
        usage = getattr(chunk, "usage_metadata", None) or {}
        input_tokens = int(usage.get("input_tokens", input_tokens))
        output_tokens = int(usage.get("output_tokens", output_tokens))

    duration_ms = int((time.perf_counter() - started) * 1000)
    provider, model = current_provider_model()
    async with SessionLocal() as session:
        await record_usage(session, user.id if user else None, provider, model, input_tokens, output_tokens, duration_ms, "chat")

    yield f"data: {json.dumps({'type': 'done', 'content': ''.join(answer_parts)}, ensure_ascii=False)}\n\n"