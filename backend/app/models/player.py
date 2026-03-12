import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cricapi_player_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # wicketkeeper/batsman/bowler/allrounder
    ipl_team: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    match_players: Mapped[list["MatchPlayer"]] = relationship("MatchPlayer", back_populates="player")
    team_players: Mapped[list["UserTeamPlayer"]] = relationship("UserTeamPlayer", back_populates="player")
    match_scores: Mapped[list["PlayerMatchScore"]] = relationship("PlayerMatchScore", back_populates="player")


class MatchPlayer(Base):
    __tablename__ = "match_players"
    __table_args__ = (UniqueConstraint("match_id", "player_id", name="uq_match_player"),)

    match_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matches.id"), primary_key=True)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), primary_key=True)
    team_name: Mapped[str] = mapped_column(String(100), nullable=False)
    credit_value: Mapped[Decimal] = mapped_column(Numeric(5, 1), default=8.0, nullable=False)
    is_playing: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    match: Mapped["Match"] = relationship("Match", back_populates="match_players")
    player: Mapped["Player"] = relationship("Player", back_populates="match_players")
