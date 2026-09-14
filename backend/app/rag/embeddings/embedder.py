import asyncio

import httpx

from app.core.config import get_settings


class Embedder:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._local_model = None

    @property
    def dimension(self) -> int:
        if self.settings.embedding_provider == "local" and self._local_model is not None:
            return self._local_model.get_sentence_embedding_dimension()
        return 1024

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if self.settings.embedding_provider == "cloud":
            return await self._embed_cloud(texts)
        return await self._embed_local(texts)

    async def _embed_local(self, texts: list[str]) -> list[list[float]]:
        model = self._get_local_model()
        vectors = await asyncio.to_thread(
            model.encode,
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return [vector.tolist() for vector in vectors]

    def _get_local_model(self):
        if self._local_model is None:
            from sentence_transformers import SentenceTransformer

            self._local_model = SentenceTransformer(self.settings.embedding_model)
        return self._local_model

    async def _embed_cloud(self, texts: list[str]) -> list[list[float]]:
        if not self.settings.cloud_embedding_api_key:
            raise RuntimeError("云端 embedding 未配置 API Key")
        model = self.settings.cloud_embedding_model or "text-embedding-3-small"
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                self.settings.llm_base_url or "https://api.openai.com/v1",
                headers={"Authorization": f"Bearer {self.settings.cloud_embedding_api_key}"},
                json={"model": model, "input": texts},
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]