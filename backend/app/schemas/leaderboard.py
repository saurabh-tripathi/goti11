import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: uuid.UUID
    username: str
    total_points: Decimal
    prize_awarded: Decimal
    captain_name: str
    vice_captain_name: str


class SeriesLeaderboardEntry(BaseModel):
    rank: int
    user_id: uuid.UUID
    username: str
    fantasy_points: Decimal   # SUM of user_teams.total_points for this series
    prize_awarded: Decimal    # SUM of prize money won across matches in this series
    matches_played: int


class UserMatchHistory(BaseModel):
    """One row per match the user participated in within a series."""
    match_id: uuid.UUID
    match_name: str
    scheduled_at: datetime | None
    match_status: str
    total_points: Decimal
    rank: int | None
    prize_awarded: Decimal
    captain_name: str
    vice_captain_name: str
