import uuid
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class SeriesCreate(BaseModel):
    name: str
    cricapi_series_id: str | None = None
    status: str = "upcoming"
    start_date: date | None = None
    end_date: date | None = None
    prize_pool: Decimal = Decimal("0")


class SeriesPatch(BaseModel):
    name: str | None = None
    cricapi_series_id: str | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    prize_pool: Decimal | None = None


class SeriesResponse(BaseModel):
    id: uuid.UUID
    name: str
    cricapi_series_id: str | None
    status: str
    start_date: date | None
    end_date: date | None
    prize_pool: Decimal

    model_config = {"from_attributes": True}
