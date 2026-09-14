import asyncio

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import IngestionJob, KnowledgeBase, User
from app.schemas.ingestion import BatchImportRequest, IngestionJobOut, ScanRequest, UrlImportRequest
from app.services import ingestion_service

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/upload", response_model=IngestionJobOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    knowledge_base_id: int = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IngestionJob:
    await _check_knowledge_base(db, knowledge_base_id, user)
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="上传文件为空")
    document = await ingestion_service.save_upload(db, knowledge_base_id, file.filename or "unnamed", data)
    job = await ingestion_service.create_job(db, knowledge_base_id, "upload", [document.id])
    asyncio.create_task(ingestion_service.run_ingestion_job(job.id))
    return job


@router.post("/scan", response_model=IngestionJobOut, status_code=status.HTTP_201_CREATED)
async def scan_directory(
    payload: ScanRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IngestionJob:
    await _check_knowledge_base(db, payload.knowledge_base_id, user)
    try:
        return await ingestion_service.scan_directory(db, payload.knowledge_base_id, payload.directory)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/url", response_model=IngestionJobOut, status_code=status.HTTP_201_CREATED)
async def import_url(
    payload: UrlImportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IngestionJob:
    await _check_knowledge_base(db, payload.knowledge_base_id, user)
    try:
        return await ingestion_service.import_url(db, payload.knowledge_base_id, payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/batch", response_model=IngestionJobOut, status_code=status.HTTP_201_CREATED)
async def batch_import(
    payload: BatchImportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IngestionJob:
    await _check_knowledge_base(db, payload.knowledge_base_id, user)
    return await ingestion_service.batch_import_paths(db, payload.knowledge_base_id, payload.paths)


@router.get("/jobs", response_model=list[IngestionJobOut])
async def list_jobs(
    knowledge_base_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[IngestionJob]:
    await _check_knowledge_base(db, knowledge_base_id, user)
    result = await db.execute(
        select(IngestionJob)
        .where(IngestionJob.knowledge_base_id == knowledge_base_id)
        .order_by(IngestionJob.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


async def _check_knowledge_base(db: AsyncSession, knowledge_base_id: int, user: User) -> None:
    knowledge_base = await db.get(KnowledgeBase, knowledge_base_id)
    if knowledge_base is None or knowledge_base.is_deleted:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if user.role != "admin" and knowledge_base.owner_id != user.id:
        raise HTTPException(status_code=403, detail="无权访问该知识库")