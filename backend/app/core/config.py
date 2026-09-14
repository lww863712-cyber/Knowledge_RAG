from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "one_RAG"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 1440
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"

    database_url: str = "postgresql+asyncpg://rag:rag_password@localhost:5432/rag"
    qdrant_url: str = "http://localhost:6333"
    file_storage_dir: str = "./data/files"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    llm_provider: str = "deepseek"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""
    llm_temperature: float = 0.2

    embedding_provider: str = "local"
    embedding_model: str = "BAAI/bge-m3"
    embedding_use_int8: bool = False
    cloud_embedding_model: str = ""
    cloud_embedding_api_key: str = ""

    reranker_model: str = "BAAI/bge-reranker-v2-m3"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()