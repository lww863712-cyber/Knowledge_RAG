from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.config import get_settings
from app.db.session import get_db
from app.models import ModelConfig, User
from app.schemas.settings import ModelConfigIn, SettingsOut

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/models", response_model=SettingsOut)
async def get_model_settings(_: User = Depends(require_admin)) -> SettingsOut:
    settings = get_settings()
    return SettingsOut(
        app_name=settings.app_name,
        llm_provider=settings.llm_provider,
        llm_base_url=settings.llm_base_url,
        llm_model=settings.llm_model,
        llm_temperature=settings.llm_temperature,
        embedding_provider=settings.embedding_provider,
        embedding_model=settings.embedding_model,
        embedding_use_int8=settings.embedding_use_int8,
        reranker_model=settings.reranker_model,
    )


@router.post("/models", response_model=ModelConfigIn, status_code=status.HTTP_201_CREATED)
async def create_model_config(
    payload: ModelConfigIn,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> ModelConfigIn:
    if payload.is_active:
        result = await db.execute(
            select(ModelConfig).where(ModelConfig.provider == payload.provider, ModelConfig.model_name == payload.model_name)
        )
        config = result.scalar_one_or_none()
        if config:
            config.base_url = payload.base_url
            config.api_key_ref = payload.api_key_ref
            config.unit_price_input = payload.unit_price_input
            config.unit_price_output = payload.unit_price_output
            config.is_active = True
            await db.commit()
            return payload
        db.add(
            ModelConfig(
                provider=payload.provider,
                model_name=payload.model_name,
                base_url=payload.base_url,
                api_key_ref=payload.api_key_ref,
                unit_price_input=payload.unit_price_input,
                unit_price_output=payload.unit_price_output,
                is_active=True,
            )
        )
        await db.commit()
    return payload