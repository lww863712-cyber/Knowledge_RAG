from sqlalchemy import JSON, Boolean, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ModelConfig(Base, TimestampMixin):
    __tablename__ = "model_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    base_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_key_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parameters_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    unit_price_input: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    unit_price_output: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)