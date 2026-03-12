import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RuleSet(Base):
    __tablename__ = "rule_sets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    point_rules: Mapped[list["PointRule"]] = relationship("PointRule", back_populates="rule_set", cascade="all, delete-orphan")
    selection_rules: Mapped[list["SelectionRule"]] = relationship("SelectionRule", back_populates="rule_set", cascade="all, delete-orphan")
    series_rule_sets: Mapped[list["SeriesRuleSet"]] = relationship("SeriesRuleSet", back_populates="rule_set")


class PointRule(Base):
    __tablename__ = "point_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_set_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rule_sets.id"), nullable=False)
    event_key: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. run, four, six, wicket, maiden_over, catch, stumping, run_out,
    #      duck_penalty, half_century_bonus, century_bonus, five_wicket_bonus
    role_filter: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # optional: only applies to this role
    points: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)

    rule_set: Mapped["RuleSet"] = relationship("RuleSet", back_populates="point_rules")


class SelectionRule(Base):
    __tablename__ = "selection_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_set_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rule_sets.id"), nullable=False)
    constraint_key: Mapped[str] = mapped_column(String(50), nullable=False)
    # e.g. total_players, credit_cap, min_wicketkeepers, max_from_one_team,
    #      min_batsmen, min_bowlers, min_allrounders
    value_int: Mapped[int | None] = mapped_column(Integer, nullable=True)
    value_decimal: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    rule_set: Mapped["RuleSet"] = relationship("RuleSet", back_populates="selection_rules")


class SeriesRuleSet(Base):
    __tablename__ = "series_rule_sets"

    series_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("series.id"), primary_key=True)
    rule_set_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rule_sets.id"), primary_key=True)

    series: Mapped["Series"] = relationship("Series", back_populates="rule_sets")
    rule_set: Mapped["RuleSet"] = relationship("RuleSet", back_populates="series_rule_sets")
