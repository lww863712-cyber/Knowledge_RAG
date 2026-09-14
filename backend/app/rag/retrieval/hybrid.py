from app.rag.bm25.bm25_index import bm25_manager
from app.rag.embeddings.embedder import Embedder
from app.rag.reranker.reranker import Reranker
from app.rag.vector_store import VectorStore


class HybridRetriever:
    def __init__(self) -> None:
        self.embedder = Embedder()
        self.reranker = Reranker()
        self.vector_store = VectorStore()

    async def retrieve(self, knowledge_base_id: int, query: str, top_k: int = 6) -> list[dict]:
        query_vector = (await self.embedder.embed([query]))[0]
        try:
            dense_results = await self.vector_store.search(knowledge_base_id, query_vector, limit=max(top_k * 3, 12))
        except Exception:
            dense_results = []
        lexical_results = bm25_manager.search(knowledge_base_id, query, limit=max(top_k * 3, 12))

        merged = self._rrf_merge(dense_results, lexical_results)
        candidates = merged[: max(top_k * 2, 10)]
        texts = [item["content"] for item in candidates]
        try:
            rerank_scores = await self.reranker.rerank(query, texts)
        except Exception:
            rerank_scores = [float(item.get("rrf", 0)) for item in candidates]

        ranked = sorted(
            zip(candidates, rerank_scores),
            key=lambda pair: pair[1],
            reverse=True,
        )
        return [
            {
                "content": item["content"],
                "metadata": item["metadata"],
                "score": round(score, 6),
                "dense_score": item.get("dense_score"),
                "bm25_score": item.get("bm25_score"),
            }
            for item, score in ranked[:top_k]
        ]

    @staticmethod
    def _rrf_merge(dense_results: list[dict], lexical_results: list[dict], k: int = 60) -> list[dict]:
        index: dict[str, dict] = {}

        for rank, item in enumerate(dense_results, start=1):
            payload = item.get("payload", {})
            key = payload.get("chunk_key") or str(item.get("id"))
            entry = index.setdefault(key, {
                "content": payload.get("content", ""),
                "metadata": payload.get("metadata", {}),
                "dense_score": item.get("score", 0),
                "bm25_score": 0,
                "rrf": 0,
                "chunk_key": key,
            })
            entry["rrf"] += 1 / (k + rank)

        for rank, item in enumerate(lexical_results, start=1):
            metadata = item.get("metadata", {})
            key = str(metadata.get("chunk_key") or item.get("content"))
            entry = index.setdefault(key, {
                "content": item.get("content", ""),
                "metadata": metadata,
                "dense_score": 0,
                "bm25_score": item.get("bm25_score", 0),
                "rrf": 0,
                "chunk_key": key,
            })
            entry["rrf"] += 1 / (k + rank)

        return sorted(index.values(), key=lambda entry: entry["rrf"], reverse=True)