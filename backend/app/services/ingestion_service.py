import asyncio
import hashlib
from pathlib import Path
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import Chunk, Document, IngestionJob
from app.rag.bm25.bm25_index import bm25_manager
from app.rag.embeddings.embedder import Embedder
from app.rag.parser.parser import parse_file
from app.rag.splitter.splitter import ChunkInput, split_sections
from app.rag.vector_store import VectorStore

settings = get_settings()

SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".pptx", ".md", ".markdown", ".txt", ".html", ".htm",
    ".csv", ".xlsx", ".json", ".xml", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".go", ".rs", ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php",
    ".sh", ".sql", ".yml", ".yaml", ".toml",
}


def detect_file_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix == "markdown":
        return "md"
    if suffix == "htm":
        return "html"
    if suffix == "yaml":
        return "yml"
    if suffix == "hpp":
        return "hpp"
    return suffix or "txt"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def save_upload(
    db: AsyncSession,
    knowledge_base_id: int,
    filename: str,
    data: bytes,
) -> Document:
    file_type = detect_file_type(filename)
    relative = Path("uploads") / f"{uuid4().hex}{Path(filename).suffix}"
    target = Path(settings.file_storage_dir) / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)

    document = Document(
        knowledge_base_id=knowledge_base_id,
        name=filename,
        file_type=file_type,
        file_path=str(target),
        source="upload",
        status="pending",
        size=len(data),
        content_hash=_sha256(data),
        metadata_json={"original_filename": filename},
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


async def create_job(db: AsyncSession, knowledge_base_id: int, job_type: str, document_ids: list[int]) -> IngestionJob:
    job = IngestionJob(
        knowledge_base_id=knowledge_base_id,
        job_type=job_type,
        status="pending",
        progress=0,
        details_json={"document_ids": document_ids},
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


def schedule_ingestion(job_id: int) -> None:
    asyncio.create_task(run_ingestion_job(job_id))


async def run_ingestion_job(job_id: int) -> None:
    async with SessionLocal() as db:
        job = await db.get(IngestionJob, job_id)
        if job is None:
            return
        job.status = "running"
        job.progress = 0
        await db.commit()

        document_ids = job.details_json.get("document_ids", [])
        total = len(document_ids)
        try:
            for index, document_id in enumerate(document_ids, start=1):
                await index_document(db, document_id)
                job.progress = round(index / total * 100, 2)
                await db.commit()

            job.status = "completed"
            job.progress = 100
            await db.commit()
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            await db.commit()


async def index_document(db: AsyncSession, document_id: int) -> None:
    document = await db.get(Document, document_id)
    if document is None or document.is_deleted:
        return

    document.status = "processing"
    await db.commit()

    try:
        sections = await asyncio.to_thread(parse_file, document.file_path or document.name, document.file_type)
        chunks = await asyncio.to_thread(split_sections, sections, document.file_type)
        if not chunks:
            document.status = "completed"
            await db.commit()
            return

        embedder = Embedder()
        vectors = await embedder.embed([chunk.content for chunk in chunks])

        vector_store = VectorStore()
        await vector_store.ensure_collection(document.knowledge_base_id, embedder.dimension)
        await vector_store.delete_document(document.knowledge_base_id, document.id)

        await db.execute(delete(Chunk).where(Chunk.document_id == document.id))

        payloads: list[dict] = []
        for index, (chunk, vector) in enumerate(zip(chunks, vectors), start=1):
            chunk_key = f"{document.id}:{index}"
            metadata = {**chunk.metadata, "document_id": document.id, "document_name": document.name, "chunk_key": chunk_key}
            payloads.append({"document_id": document.id, "content": chunk.content, "metadata": metadata, "chunk_key": chunk_key})
            db.add(
                Chunk(
                    knowledge_base_id=document.knowledge_base_id,
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk.content,
                    metadata_json=metadata,
                )
            )

        await vector_store.upsert(document.knowledge_base_id, vectors, payloads)
        document.status = "completed"
        await db.commit()
        await rebuild_bm25(db, document.knowledge_base_id)
    except Exception:
        document.status = "failed"
        await db.commit()
        raise


async def rebuild_bm25(db: AsyncSession, knowledge_base_id: int) -> None:
    result = await db.execute(select(Chunk).where(Chunk.knowledge_base_id == knowledge_base_id))
    chunks = list(result.scalars().all())
    bm25_manager.rebuild(
        knowledge_base_id,
        [
            ChunkInput(content=chunk.content, metadata={**chunk.metadata_json, "chunk_key": f"{chunk.document_id}:{chunk.chunk_index}"})
            for chunk in chunks
        ],
    )


async def ensure_bm25_loaded(db: AsyncSession, knowledge_base_id: int) -> None:
    if knowledge_base_id not in bm25_manager._indexes:
        await rebuild_bm25(db, knowledge_base_id)


async def scan_directory(db: AsyncSession, knowledge_base_id: int, directory: str) -> IngestionJob:
    root = Path(directory)
    if not root.exists():
        raise ValueError("目录不存在或后端容器无法访问该路径")

    document_ids: list[int] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            document = Document(
                knowledge_base_id=knowledge_base_id,
                name=path.name,
                file_type=detect_file_type(path.name),
                file_path=str(path),
                source="scan",
                status="pending",
                size=path.stat().st_size,
                metadata_json={"source_directory": str(root)},
            )
            db.add(document)
            await db.flush()
            document_ids.append(document.id)

    await db.commit()
    job = await create_job(db, knowledge_base_id, "scan", document_ids)
    schedule_ingestion(job.id)
    return job


async def import_url(db: AsyncSession, knowledge_base_id: int, url: str) -> IngestionJob:
    import trafilatura

    downloaded = await asyncio.to_thread(trafilatura.fetch_url, url)
    if not downloaded:
        raise ValueError("网页抓取失败，请检查 URL 或网络")
    text = await asyncio.to_thread(trafilatura.extract, downloaded, include_links=False, include_images=False)
    text = text or ""

    target = Path(settings.file_storage_dir) / "urls" / f"{uuid4().hex}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")

    document = Document(
        knowledge_base_id=knowledge_base_id,
        name=url,
        file_type="md",
        file_path=str(target),
        source="url",
        status="pending",
        size=len(text.encode("utf-8")),
        content_hash=_sha256(text.encode("utf-8")),
        metadata_json={"url": url},
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    job = await create_job(db, knowledge_base_id, "url", [document.id])
    schedule_ingestion(job.id)
    return job


async def batch_import_paths(db: AsyncSession, knowledge_base_id: int, paths: list[str]) -> IngestionJob:
    document_ids: list[int] = []
    for item in paths:
        path = Path(item)
        if not path.exists() or not path.is_file():
            continue
        document = Document(
            knowledge_base_id=knowledge_base_id,
            name=path.name,
            file_type=detect_file_type(path.name),
            file_path=str(path),
            source="api",
            status="pending",
            size=path.stat().st_size,
            metadata_json={"imported_path": str(path)},
        )
        db.add(document)
        await db.flush()
        document_ids.append(document.id)

    await db.commit()
    job = await create_job(db, knowledge_base_id, "batch", document_ids)
    schedule_ingestion(job.id)
    return job


async def delete_document(db: AsyncSession, document_id: int) -> None:
    document = await db.get(Document, document_id)
    if document is None:
        return
    vector_store = VectorStore()
    await vector_store.delete_document(document.knowledge_base_id, document.id)
    await db.execute(delete(Chunk).where(Chunk.document_id == document.id))
    document.is_deleted = True
    document.status = "deleted"
    await db.commit()
    await rebuild_bm25(db, document.knowledge_base_id)