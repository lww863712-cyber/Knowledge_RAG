from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import User


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    settings = get_settings()
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.username == settings.default_admin_username))
        user = result.scalar_one_or_none()
        if user is None:
            session.add(
                User(
                    username=settings.default_admin_username,
                    hashed_password=hash_password(settings.default_admin_password),
                    role="admin",
                    is_active=True,
                )
            )
            await session.commit()