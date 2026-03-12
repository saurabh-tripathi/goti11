import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("series.id"), nullable=False)
    cricapi_match_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    team_a: Mapped[str] = mapped_column(String(100), nullable=False)
    team_b: Mapped[str] = mapped_column(String(100), nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lock_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="upcoming", nullable=False)
    # upcoming / squad_synced / locked / scoring / completed
    prize_pool: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    raw_scorecard: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scorecard_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    series: Mapped["Series"] = relationship("Series", back_populates="matches")
    match_players: Mapped[list["MatchPlayer"]] = relationship("MatchPlayer", back_populates="match")
    user_teams: Mapped[list["UserTeam"]] = relationship("UserTeam", back_populates="match")
    player_scores: Mapped[list["PlayerMatchScore"]] = relationship("PlayerMatchScore", back_populates="match")
    prize_distributions: Mapped[list["PrizeDistribution"]] = relationship("PrizeDistribution", back_populates="match")
