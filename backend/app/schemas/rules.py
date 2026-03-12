import uuid
from decimal import Decimal
from pydantic import BaseModel


class PointRuleCreate(BaseModel):
    event_key: str
    role_filter: str | None = None
    points: Decimal


class PointRuleResponse(BaseModel):
    id: uuid.UUID
    event_key: str
    role_filter: str | None
    points: Decimal

    model_config = {"from_attributes": True}


class SelectionRuleCreate(BaseModel):
    constraint_key: str
    value_int: int | None = None
    value_decimal: Decimal | None = None


class SelectionRuleResponse(BaseModel):
    id: uuid.UUID
    constraint_key: str
    value_int: int | None
    value_decimal: Decimal | None

    model_config = {"from_attributes": True}


class RuleSetCreate(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True
    point_rules: list[PointRuleCreate] = []
    selection_rules: list[SelectionRuleCreate] = []


class RuleSetResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    point_rules: list[PointRuleResponse]
    selection_rules: list[SelectionRuleResponse]

    model_config = {"from_attributes": True}
