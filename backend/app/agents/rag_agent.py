import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from app.db.session import SessionLocal
from app.rag.retrieval.hybrid import HybridRetriever
from app.services.ingestion_service import ensure_bm25_loaded
from app.services.llm_service import get_chat_model

AGENT_SYSTEM_PROMPT = """你是个人知识库 AgentRAG，可以调用工具完成任务。
工具：
- knowledge_base_search：在指定知识库中检索资料。
- summarize：总结给定文本。
最终回答必须使用中文，并给出来源编号引用。
"""


class RAGAgent:
    async def run(self, knowledge_base_id: int, query: str, history: list[dict]) -> dict:
        sources: list[dict] = []

        async def knowledge_base_search(query_text: str) -> str:
            """在知识库中检索与问题相关的资料。"""
            async with SessionLocal() as session:
                await ensure_bm25_loaded(session, knowledge_base_id)
            retriever = HybridRetriever()
            results = await retriever.retrieve(knowledge_base_id, query_text, top_k=5)
            for item in results:
                sources.append(item)
            return json.dumps(
                [{"content": item["content"], "metadata": item["metadata"], "score": item["score"]} for item in results],
                ensure_ascii=False,
            )

        search_tool = tool(knowledge_base_search)

        async def summarize(text: str) -> str:
            """总结给定文本。"""
            llm = get_chat_model()
            response = await llm.ainvoke(
                [
                    SystemMessage(content="请用中文简洁总结用户提供的文本，保留关键信息。"),
                    HumanMessage(content=text),
                ]
            )
            return str(response.content)

        summarize_tool = tool(summarize)

        llm = get_chat_model()
        agent = create_react_agent(llm, [search_tool, summarize_tool])

        messages: list = [SystemMessage(content=AGENT_SYSTEM_PROMPT)]
        for item in history:
            if item.get("role") == "user":
                messages.append(HumanMessage(content=item.get("content", "")))
            else:
                messages.append(SystemMessage(content=item.get("content", "")))
        messages.append(HumanMessage(content=query))

        result = await agent.ainvoke({"messages": messages})
        final_message = result["messages"][-1]
        answer = str(final_message.content) if hasattr(final_message, "content") else str(final_message)
        steps = [message.type for message in result["messages"] if message.type in {"ai", "tool"}]
        return {"answer": answer, "citations": sources, "steps": steps}