import uuid
from decimal import Decimal
from pydantic import BaseModel


class PlayerScoreResponse(BaseModel):
    player_id: uuid.UUID
    player_name: str
    role: str
    runs: int
    fours: int
    sixes: int
    wickets: int
    maiden_overs: int
    catches: int
    stumpings: int
    run_outs: int
    raw_points: Decimal
    override_points: Decimal | None
    effective_points: Decimal
