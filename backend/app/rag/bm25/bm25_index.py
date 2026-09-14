import re

from rank_bm25 import BM25Okapi

from app.rag.splitter.splitter import ChunkInput


class BM25Manager:
    def __init__(self) -> None:
        self._indexes: dict[int, dict] = {}

    def rebuild(self, knowledge_base_id: int, chunks: list[ChunkInput]) -> None:
        tokenized = [self._tokenize(chunk.content) for chunk in chunks]
        if not tokenized:
            self._indexes.pop(knowledge_base_id, None)
            return
        self._indexes[knowledge_base_id] = {
            "model": BM25Okapi(tokenized),
            "chunks": chunks,
            "tokenized": tokenized,
        }

    def search(self, knowledge_base_id: int, query: str, limit: int = 20) -> list[dict]:
        entry = self._indexes.get(knowledge_base_id)
        if not entry:
            return []
        scores = entry["model"].get_scores(self._tokenize(query))
        ranked = sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)[:limit]
        results = []
        for index in ranked:
            chunk = entry["chunks"][index]
            results.append(
                {
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                    "bm25_score": float(scores[index]),
                }
            )
        return results

    def drop(self, knowledge_base_id: int) -> None:
        self._indexes.pop(knowledge_base_id, None)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [token.lower() for token in re.findall(r"\w+", text)]


bm25_manager = BM25Manager()