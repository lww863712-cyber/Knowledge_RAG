from datetime import datetime

from pydantic import BaseModel, Field


class IngestionJobOut(BaseModel):
    id: int
    knowledge_base_id: int
    job_type: str
    status: str
    progress: float
    error_message: str | None
    details_json: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScanRequest(BaseModel):
    knowledge_base_id: int
    directory: str


class UrlImportRequest(BaseModel):
    knowledge_base_id: int
    url: str


class BatchImportRequest(BaseModel):
    knowledge_base_id: int
    paths: list[str] = Field(default_factory=list)