"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("prize_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "series",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("cricapi_series_id", sa.String(100), nullable=True, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="upcoming"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("prize_pool", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("series_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("series.id"), nullable=False),
        sa.Column("cricapi_match_id", sa.String(100), nullable=True, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("team_a", sa.String(100), nullable=False),
        sa.Column("team_b", sa.String(100), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lock_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="upcoming"),
        sa.Column("prize_pool", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("raw_scorecard", postgresql.JSONB(), nullable=True),
        sa.Column("scorecard_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "players",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cricapi_player_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("ipl_team", sa.String(100), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_players_cricapi_player_id", "players", ["cricapi_player_id"])

    op.create_table(
        "match_players",
        sa.Column("match_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matches.id"), primary_key=True),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("players.id"), primary_key=True),
        sa.Column("team_name", sa.String(100), nullable=False),
        sa.Column("credit_value", sa.Numeric(5, 1), nullable=False, server_default="8.0"),
        sa.Column("is_playing", sa.Boolean(), nullable=False, server_default="true"),
        sa.UniqueConstraint("match_id", "player_id", name="uq_match_player"),
    )

    op.create_table(
        "user_teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("captain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("vice_captain_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("total_points", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("prize_awarded", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "match_id", name="uq_user_match_team"),
    )
    op.create_index("ix_user_teams_user_id", "user_teams", ["user_id"])
    op.create_index("ix_user_teams_match_id", "user_teams", ["match_id"])

    op.create_table(
        "user_team_players",
        sa.Column("user_team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user_teams.id"), primary_key=True),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("players.id"), primary_key=True),
        sa.Column("points_earned", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("multiplier", sa.Numeric(3, 1), nullable=False, server_default="1.0"),
        sa.Column("final_points", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )

    op.create_table(
        "player_match_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("player_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("runs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("balls_faced", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fours", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sixes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_duck", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("wickets", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overs_bowled", sa.Numeric(4, 1), nullable=False, server_default="0"),
        sa.Column("maiden_overs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("runs_conceded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("catches", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stumpings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("run_outs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("raw_points", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("override_points", sa.Numeric(10, 2), nullable=True),
        sa.Column("extra_data", postgresql.JSONB(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("match_id", "player_id", name="uq_match_player_score"),
    )
    op.create_index("ix_player_match_scores_match_id", "player_match_scores", ["match_id"])
    op.create_index("ix_player_match_scores_player_id", "player_match_scores", ["player_id"])

    op.create_table(
        "rule_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "point_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_set_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rule_sets.id"), nullable=False),
        sa.Column("event_key", sa.String(50), nullable=False),
        sa.Column("role_filter", sa.String(50), nullable=True),
        sa.Column("points", sa.Numeric(6, 2), nullable=False),
    )

    op.create_table(
        "selection_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_set_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rule_sets.id"), nullable=False),
        sa.Column("constraint_key", sa.String(50), nullable=False),
        sa.Column("value_int", sa.Integer(), nullable=True),
        sa.Column("value_decimal", sa.Numeric(10, 2), nullable=True),
    )

    op.create_table(
        "series_rule_sets",
        sa.Column("series_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("series.id"), primary_key=True),
        sa.Column("rule_set_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rule_sets.id"), primary_key=True),
    )

    op.create_table(
        "prize_distributions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("match_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matches.id"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("prize_awarded", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_prize_distributions_match_id", "prize_distributions", ["match_id"])


def downgrade() -> None:
    op.drop_table("prize_distributions")
    op.drop_table("series_rule_sets")
    op.drop_table("selection_rules")
    op.drop_table("point_rules")
    op.drop_table("rule_sets")
    op.drop_table("player_match_scores")
    op.drop_table("user_team_players")
    op.drop_table("user_teams")
    op.drop_table("match_players")
    op.drop_table("players")
    op.drop_table("matches")
    op.drop_table("series")
    op.drop_table("users")
