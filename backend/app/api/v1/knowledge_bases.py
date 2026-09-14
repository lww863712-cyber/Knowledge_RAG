from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Chunk, Document, KnowledgeBase, User
from app.rag.bm25.bm25_index import bm25_manager
from app.rag.vector_store import VectorStore
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseOut

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.get("", response_model=list[KnowledgeBaseOut])
async def list_knowledge_bases(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[KnowledgeBase]:
    query = select(KnowledgeBase).where(KnowledgeBase.is_deleted.is_(False)).order_by(KnowledgeBase.created_at.desc())
    if user.role != "admin":
        query = query.where(KnowledgeBase.owner_id == user.id)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=KnowledgeBaseOut, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBase:
    knowledge_base = KnowledgeBase(
        name=payload.name,
        description=payload.description,
        owner_id=user.id,
    )
    db.add(knowledge_base)
    await db.commit()
    await db.refresh(knowledge_base)
    return knowledge_base


@router.delete("/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    knowledge_base_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    knowledge_base = await db.get(KnowledgeBase, knowledge_base_id)
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if user.role != "admin" and knowledge_base.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权删除该知识库")

    document_ids = list((await db.execute(select(Document.id).where(Document.knowledge_base_id == knowledge_base_id))).scalars().all())
    await db.execute(delete(Chunk).where(Chunk.knowledge_base_id == knowledge_base_id))
    await db.execute(delete(Document).where(Document.knowledge_base_id == knowledge_base_id))
    knowledge_base.is_deleted = True
    await db.commit()

    vector_store = VectorStore()
    await vector_store.delete_collection(knowledge_base_id)
    bm25_manager.drop(knowledge_base_id)