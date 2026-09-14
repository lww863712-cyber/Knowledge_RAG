from uuid import uuid4

from qdrant_client import AsyncQdrantClient, models

from app.core.config import get_settings


class VectorStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncQdrantClient(url=settings.qdrant_url)

    def collection_name(self, knowledge_base_id: int) -> str:
        return f"kb_{knowledge_base_id}"

    async def ensure_collection(self, knowledge_base_id: int, dimension: int) -> None:
        name = self.collection_name(knowledge_base_id)
        if not await self.client.collection_exists(name):
            await self.client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
            )

    async def upsert(self, knowledge_base_id: int, vectors: list[list[float]], payloads: list[dict]) -> None:
        points = [
            models.PointStruct(id=str(uuid4()), vector=vector, payload=payload)
            for vector, payload in zip(vectors, payloads)
        ]
        await self.client.upsert(collection_name=self.collection_name(knowledge_base_id), points=points)

    async def search(self, knowledge_base_id: int, vector: list[float], limit: int = 20) -> list[dict]:
        name = self.collection_name(knowledge_base_id)
        if not await self.client.collection_exists(name):
            return []
        response = await self.client.query_points(
            collection_name=name,
            query=vector,
            limit=limit,
            with_payload=True,
        )
        return [
            {
                "id": point.id,
                "score": float(point.score),
                "payload": point.payload or {},
            }
            for point in response.points
        ]

    async def delete_document(self, knowledge_base_id: int, document_id: int) -> None:
        await self.client.delete(
            collection_name=self.collection_name(knowledge_base_id),
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id))]
                )
            ),
        )

    async def delete_collection(self, knowledge_base_id: int) -> None:
        await self.client.delete_collection(collection_name=self.collection_name(knowledge_base_id))