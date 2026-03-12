import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.match import Match
from app.models.team import UserTeam
from app.models.user import User
from app.models.player import Player
from app.schemas.leaderboard import LeaderboardEntry, SeriesLeaderboardEntry, UserMatchHistory

router = APIRouter(tags=["leaderboard"])


@router.get("/matches/{match_id}/leaderboard", response_model=list[LeaderboardEntry])
def match_leaderboard(match_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    teams = (
        db.query(UserTeam)
        .filter(UserTeam.match_id == match_id)
        .order_by(UserTeam.total_points.desc(), UserTeam.created_at.asc())
        .all()
    )
    result = []
    for rank, team in enumerate(teams, start=1):
        captain_player = db.query(Player).filter(Player.id == team.captain_id).first()
        vc_player = db.query(Player).filter(Player.id == team.vice_captain_id).first()
        result.append(
            LeaderboardEntry(
                rank=rank,
                user_id=team.user_id,
                username=team.user.username,
                total_points=team.total_points,
                prize_awarded=team.prize_awarded,
                captain_name=captain_player.name if captain_player else "",
                vice_captain_name=vc_player.name if vc_player else "",
            )
        )
    return result


@router.get("/series/{series_id}/leaderboard", response_model=list[SeriesLeaderboardEntry])
def series_leaderboard(series_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    # Subquery: aggregate per-user stats for matches in this series only
    series_stats = (
        db.query(
            UserTeam.user_id,
            func.sum(UserTeam.total_points).label("fantasy_points"),
            func.sum(UserTeam.prize_awarded).label("prize_awarded"),
            func.count(UserTeam.id).label("matches_played"),
        )
        .join(Match, Match.id == UserTeam.match_id)
        .filter(Match.series_id == series_id)
        .group_by(UserTeam.user_id)
        .subquery()
    )

    # Outer-join so users with 0 matches still appear with zeros
    rows = (
        db.query(
            User,
            func.coalesce(series_stats.c.fantasy_points, 0).label("fantasy_points"),
            func.coalesce(series_stats.c.prize_awarded, 0).label("prize_awarded"),
            func.coalesce(series_stats.c.matches_played, 0).label("matches_played"),
        )
        .outerjoin(series_stats, series_stats.c.user_id == User.id)
        .filter(User.is_active == True)
        .order_by(func.coalesce(series_stats.c.fantasy_points, 0).desc())
        .all()
    )

    return [
        SeriesLeaderboardEntry(
            rank=rank,
            user_id=user.id,
            username=user.username,
            fantasy_points=fantasy_points,
            prize_awarded=prize_awarded,
            matches_played=matches_played,
        )
        for rank, (user, fantasy_points, prize_awarded, matches_played) in enumerate(rows, start=1)
    ]


@router.get("/series/{series_id}/my-history", response_model=list[UserMatchHistory])
def my_series_history(
    series_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Match-by-match breakdown for the logged-in user within a series."""
    teams = (
        db.query(UserTeam)
        .join(Match, Match.id == UserTeam.match_id)
        .filter(Match.series_id == series_id, UserTeam.user_id == current_user.id)
        .order_by(Match.scheduled_at.asc())
        .all()
    )

    result = []
    for team in teams:
        captain_player = db.query(Player).filter(Player.id == team.captain_id).first()
        vc_player = db.query(Player).filter(Player.id == team.vice_captain_id).first()
        result.append(
            UserMatchHistory(
                match_id=team.match_id,
                match_name=team.match.name,
                scheduled_at=team.match.scheduled_at,
                match_status=team.match.status,
                total_points=team.total_points,
                rank=team.rank,
                prize_awarded=team.prize_awarded,
                captain_name=captain_player.name if captain_player else "",
                vice_captain_name=vc_player.name if vc_player else "",
            )
        )
    return result
