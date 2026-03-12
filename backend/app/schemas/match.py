import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class MatchCreate(BaseModel):
    series_id: uuid.UUID
    name: str
    team_a: str
    team_b: str
    cricapi_match_id: str | None = None
    scheduled_at: datetime | None = None
    lock_time: datetime | None = None
    prize_pool: Decimal = Decimal("0")


class MatchPatch(BaseModel):
    name: str | None = None
    team_a: str | None = None
    team_b: str | None = None
    cricapi_match_id: str | None = None
    scheduled_at: datetime | None = None
    lock_time: datetime | None = None
    status: str | None = None
    prize_pool: Decimal | None = None


class MatchResponse(BaseModel):
    id: uuid.UUID
    series_id: uuid.UUID
    cricapi_match_id: str | None
    name: str
    team_a: str
    team_b: str
    scheduled_at: datetime | None
    lock_time: datetime | None
    status: str
    prize_pool: Decimal
    scorecard_updated_at: datetime | None

    model_config = {"from_attributes": True}


class OverrideScoreRequest(BaseModel):
    player_id: uuid.UUID
    override_points: Decimal
