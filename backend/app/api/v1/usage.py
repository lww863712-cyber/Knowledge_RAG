from fastapi import APIRouter, Depends, Query

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import User
from app.schemas.usage import UsageSummary
from app.services.usage_service import get_usage_summary
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/summary", response_model=UsageSummary)
async def usage_summary(
    days: int = Query(default=30, ge=1, le=365),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UsageSummary:
    data = await get_usage_summary(db, days)
    return UsageSummary(**data)