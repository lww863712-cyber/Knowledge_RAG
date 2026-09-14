from datetime import datetime

from pydantic import BaseModel


class UsageSummaryItem(BaseModel):
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float


class UsageDayItem(BaseModel):
    date: str
    input_tokens: int
    output_tokens: int
    cost: float


class UsageSummary(BaseModel):
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    by_provider: list[UsageSummaryItem]
    by_day: list[UsageDayItem]