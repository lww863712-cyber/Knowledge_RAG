import pytest

pytest.importorskip("rank_bm25")

from app.rag.bm25.bm25_index import BM25Manager
from app.rag.splitter.splitter import ChunkInput


def test_bm25_search() -> None:
    manager = BM25Manager()
    manager.rebuild(
        1,
        [
            ChunkInput(content="Python FastAPI 后端开发", metadata={"chunk_key": "1:1"}),
            ChunkInput(content="RAG 向量检索与重排", metadata={"chunk_key": "1:2"}),
        ],
    )

    results = manager.search(1, "Python 后端", limit=5)

    assert results
    assert results[0]["content"].startswith("Python FastAPI")