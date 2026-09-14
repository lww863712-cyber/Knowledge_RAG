from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    knowledge_base_id: int
    query: str = Field(min_length=1)
    top_k: int = Field(default=6, ge=1, le=50)


class RetrievalItem(BaseModel):
    content: str
    metadata: dict
    score: float
    dense_score: float | None = None
    bm25_score: float | None = None


class RetrievalResponse(BaseModel):
    results: list[RetrievalItem]