import uuid
from decimal import Decimal
from pydantic import BaseModel, model_validator


class TeamCreate(BaseModel):
    player_ids: list[uuid.UUID]
    captain_id: uuid.UUID
    vice_captain_id: uuid.UUID

    @model_validator(mode="after")
    def validate_captain_in_team(self) -> "TeamCreate":
        if self.captain_id not in self.player_ids:
            raise ValueError("captain_id must be in player_ids")
        if self.vice_captain_id not in self.player_ids:
            raise ValueError("vice_captain_id must be in player_ids")
        if self.captain_id == self.vice_captain_id:
            raise ValueError("captain and vice_captain must be different players")
        return self


class TeamPlayerDetail(BaseModel):
    player_id: uuid.UUID
    name: str
    role: str
    ipl_team: str | None
    credit_value: Decimal
    team_name: str
    is_captain: bool
    is_vice_captain: bool
    points_earned: Decimal
    multiplier: Decimal
    final_points: Decimal

    model_config = {"from_attributes": True}


class TeamResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    match_id: uuid.UUID
    captain_id: uuid.UUID
    vice_captain_id: uuid.UUID
    total_points: Decimal
    rank: int | None
    prize_awarded: Decimal
    is_locked: bool
    players: list[TeamPlayerDetail]

    model_config = {"from_attributes": True}
