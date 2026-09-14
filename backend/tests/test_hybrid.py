import pytest

pytest.importorskip("qdrant_client")
pytest.importorskip("rank_bm25")

from app.rag.retrieval.hybrid import HybridRetriever


def test_rrf_merge_combines_sources() -> None:
    dense = [
        {"id": "point-1", "score": 0.9, "payload": {"chunk_key": "1:1", "content": "A", "metadata": {}}},
    ]
    lexical = [
        {"content": "B", "metadata": {"chunk_key": "1:2"}, "bm25_score": 5.0},
    ]

    merged = HybridRetriever._rrf_merge(dense, lexical)

    assert len(merged) == 2
    assert {item["chunk_key"] for item in merged} == {"1:1", "1:2"}