from pydantic import BaseModel, Field


class SettingsOut(BaseModel):
    app_name: str
    llm_provider: str
    llm_base_url: str
    llm_model: str
    llm_temperature: float
    embedding_provider: str
    embedding_model: str
    embedding_use_int8: bool
    reranker_model: str


class ModelConfigIn(BaseModel):
    provider: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    base_url: str | None = None
    api_key_ref: str | None = None
    unit_price_input: float = Field(default=0, ge=0)
    unit_price_output: float = Field(default=0, ge=0)
    is_active: bool = True