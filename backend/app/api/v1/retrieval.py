from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import KnowledgeBase, User
from app.rag.retrieval.hybrid import HybridRetriever
from app.schemas.retrieval import RetrievalRequest, RetrievalResponse
from app.services.ingestion_service import ensure_bm25_loaded

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=RetrievalResponse)
async def search(
    payload: RetrievalRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RetrievalResponse:
    knowledge_base = await db.get(KnowledgeBase, payload.knowledge_base_id)
    if knowledge_base is None or knowledge_base.is_deleted:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if user.role != "admin" and knowledge_base.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问该知识库")

    try:
        await ensure_bm25_loaded(db, payload.knowledge_base_id)
        retriever = HybridRetriever()
        results = await retriever.retrieve(payload.knowledge_base_id, payload.query, payload.top_k)
    except Exception as exc:
        import logging
        logging.exception("retrieval search failed")
        raise HTTPException(status_code=500, detail=f"检索失败: {exc}") from exc
    return RetrievalResponse(results=results)