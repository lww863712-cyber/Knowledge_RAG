import asyncio

from app.core.config import get_settings


class Reranker:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.settings.reranker_model)
        return self._model

    async def rerank(self, query: str, texts: list[str]) -> list[float]:
        if not texts:
            return []
        model = self._get_model()
        pairs = [(query, text) for text in texts]
        scores = await asyncio.to_thread(model.predict, pairs)
        return [float(score) for score in scores]