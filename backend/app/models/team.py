import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserTeam(Base):
    __tablename__ = "user_teams"
    __table_args__ = (UniqueConstraint("user_id", "match_id", name="uq_user_match_team"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    match_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False, index=True)
    captain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    vice_captain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    total_points: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prize_awarded: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="teams")
    match: Mapped["Match"] = relationship("Match", back_populates="user_teams")
    captain: Mapped["Player"] = relationship("Player", foreign_keys=[captain_id])
    vice_captain: Mapped["Player"] = relationship("Player", foreign_keys=[vice_captain_id])
    players: Mapped[list["UserTeamPlayer"]] = relationship("UserTeamPlayer", back_populates="team", cascade="all, delete-orphan")


class UserTeamPlayer(Base):
    __tablename__ = "user_team_players"

    user_team_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_teams.id"), primary_key=True)
    player_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("players.id"), primary_key=True)
    points_earned: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(3, 1), default=1.0, nullable=False)  # 2.0/1.5/1.0
    final_points: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    team: Mapped["UserTeam"] = relationship("UserTeam", back_populates="players")
    player: Mapped["Player"] = relationship("Player", back_populates="team_players")
