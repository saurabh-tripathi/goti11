import uuid
from decimal import Decimal
from pydantic import BaseModel


class PlayerResponse(BaseModel):
    id: uuid.UUID
    cricapi_player_id: str
    name: str
    role: str
    ipl_team: str | None

    model_config = {"from_attributes": True}


class MatchPlayerResponse(BaseModel):
    player_id: uuid.UUID
    match_id: uuid.UUID
    team_name: str
    credit_value: Decimal
    is_playing: bool
    player: PlayerResponse

    model_config = {"from_attributes": True}
