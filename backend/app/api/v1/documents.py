from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Document, KnowledgeBase, User
from app.schemas.document import DocumentOut
from app.services.ingestion_service import delete_document, index_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    knowledge_base_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Document]:
    knowledge_base = await db.get(KnowledgeBase, knowledge_base_id)
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if user.role != "admin" and knowledge_base.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问该知识库")
    result = await db.execute(
        select(Document)
        .where(Document.knowledge_base_id == knowledge_base_id, Document.is_deleted.is_(False))
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_document(
    document_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    document = await db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    knowledge_base = await db.get(KnowledgeBase, document.knowledge_base_id)
    if knowledge_base is None or (user.role != "admin" and knowledge_base.owner_id != user.id):
        raise HTTPException(status_code=403, detail="无权删除该文档")
    await delete_document(db, document.id)


@router.post("/{document_id}/reindex", response_model=DocumentOut)
async def reindex_document(
    document_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Document:
    document = await db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    knowledge_base = await db.get(KnowledgeBase, document.knowledge_base_id)
    if knowledge_base is None or (user.role != "admin" and knowledge_base.owner_id != user.id):
        raise HTTPException(status_code=403, detail="无权操作该文档")
    await index_document(db, document.id)
    await db.refresh(document)
    return document