from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ModelConfig, UsageRecord


async def record_usage(
    db: AsyncSession,
    user_id: int | None,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    duration_ms: int,
    usage_type: str = "chat",
    metadata: dict | None = None,
) -> None:
    result = await db.execute(
        select(ModelConfig).where(
            ModelConfig.provider == provider,
            ModelConfig.model_name == model,
            ModelConfig.is_active.is_(True),
        )
    )
    config = result.scalar_one_or_none()
    unit_input = config.unit_price_input if config else 0
    unit_output = config.unit_price_output if config else 0
    cost = (input_tokens / 1_000_000) * unit_input + (output_tokens / 1_000_000) * unit_output

    db.add(
        UsageRecord(
            user_id=user_id,
            provider=provider,
            model=model,
            usage_type=usage_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            duration_ms=duration_ms,
            metadata_json=metadata or {},
        )
    )
    await db.commit()


async def get_usage_summary(db: AsyncSession, days: int = 30) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(select(UsageRecord).where(UsageRecord.created_at >= cutoff))
    records = list(result.scalars().all())

    total_input = 0
    total_output = 0
    total_cost = 0.0
    by_provider: dict[tuple[str, str], dict] = {}
    by_day: dict[str, dict] = {}

    for record in records:
        total_input += record.input_tokens
        total_output += record.output_tokens
        total_cost += record.cost

        key = (record.provider, record.model)
        item = by_provider.setdefault(key, {"provider": record.provider, "model": record.model, "input_tokens": 0, "output_tokens": 0, "cost": 0.0})
        item["input_tokens"] += record.input_tokens
        item["output_tokens"] += record.output_tokens
        item["cost"] += record.cost

        day_key = record.created_at.date().isoformat()
        day_item = by_day.setdefault(day_key, {"date": day_key, "input_tokens": 0, "output_tokens": 0, "cost": 0.0})
        day_item["input_tokens"] += record.input_tokens
        day_item["output_tokens"] += record.output_tokens
        day_item["cost"] += record.cost

    return {
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cost": round(total_cost, 6),
        "by_provider": list(by_provider.values()),
        "by_day": list(by_day.values()),
    }