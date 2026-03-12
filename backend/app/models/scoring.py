import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PlayerMatchScore(Base):
    __tablename__ = "player_match_scores"
    __table_args__ = (UniqueConstraint("match_id", "player_id", name="uq_match_player_score"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False, index=True)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)

    # Batting
    runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    balls_faced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fours: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sixes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_duck: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Bowling
    wickets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overs_bowled: Mapped[Decimal] = mapped_column(Numeric(4, 1), default=0, nullable=False)
    maiden_overs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    runs_conceded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Fielding
    catches: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stumpings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    run_outs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    raw_points: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    override_points: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    match: Mapped["Match"] = relationship("Match", back_populates="player_scores")
    player: Mapped["Player"] = relationship("Player", back_populates="match_scores")

    @property
    def effective_points(self) -> Decimal:
        return self.override_points if self.override_points is not None else self.raw_points
