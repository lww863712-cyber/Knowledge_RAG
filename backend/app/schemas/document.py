from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    knowledge_base_id: int
    collection_id: int | None
    name: str
    file_type: str
    source: str
    status: str
    size: int
    metadata_json: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}