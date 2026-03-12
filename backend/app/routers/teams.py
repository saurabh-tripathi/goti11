import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin_user, get_current_user, get_db
from app.models.match import Match
from app.models.player import MatchPlayer, Player
from app.models.team import UserTeam, UserTeamPlayer
from app.models.user import User
from app.schemas.team import TeamCreate, TeamPlayerDetail, TeamResponse

router = APIRouter(tags=["teams"])


def build_team_response(team: UserTeam) -> TeamResponse:
    players = []
    for utp in team.players:
        mp = next((mp for mp in utp.player.match_players if mp.match_id == team.match_id), None)
        players.append(
            TeamPlayerDetail(
                player_id=utp.player_id,
                name=utp.player.name,
                role=utp.player.role,
                ipl_team=utp.player.ipl_team,
                credit_value=mp.credit_value if mp else 0,
                team_name=mp.team_name if mp else "",
                is_captain=(utp.player_id == team.captain_id),
                is_vice_captain=(utp.player_id == team.vice_captain_id),
                points_earned=utp.points_earned,
                multiplier=utp.multiplier,
                final_points=utp.final_points,
            )
        )
    return TeamResponse(
        id=team.id,
        user_id=team.user_id,
        match_id=team.match_id,
        captain_id=team.captain_id,
        vice_captain_id=team.vice_captain_id,
        total_points=team.total_points,
        rank=team.rank,
        prize_awarded=team.prize_awarded,
        is_locked=team.is_locked,
        players=players,
    )


@router.get("/matches/{match_id}/my-team", response_model=TeamResponse)
def get_my_team(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = (
        db.query(UserTeam)
        .filter(UserTeam.match_id == match_id, UserTeam.user_id == current_user.id)
        .first()
    )
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return build_team_response(team)


@router.post("/matches/{match_id}/my-team", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_team(
    match_id: uuid.UUID,
    body: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Check lock
    now = datetime.now(timezone.utc)
    if match.lock_time and now >= match.lock_time:
        raise HTTPException(status_code=400, detail="Team selection is locked")
    if match.status not in ("upcoming", "squad_synced"):
        raise HTTPException(status_code=400, detail="Cannot pick team for this match")

    # Validate via rules engine
    from app.services.rules_engine import validate_team_selection
    match_players = db.query(MatchPlayer).filter(MatchPlayer.match_id == match_id).all()
    selected_players = [mp for mp in match_players if mp.player_id in body.player_ids]

    if len(selected_players) != len(body.player_ids):
        raise HTTPException(status_code=400, detail="Some selected players are not in this match's squad")

    errors = validate_team_selection(db, match, body.player_ids, selected_players)
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    # Upsert team
    existing = (
        db.query(UserTeam)
        .filter(UserTeam.match_id == match_id, UserTeam.user_id == current_user.id)
        .first()
    )
    if existing:
        if existing.is_locked:
            raise HTTPException(status_code=400, detail="Team is locked")
        # Delete old players
        db.query(UserTeamPlayer).filter(UserTeamPlayer.user_team_id == existing.id).delete()
        existing.captain_id = body.captain_id
        existing.vice_captain_id = body.vice_captain_id
        team = existing
    else:
        team = UserTeam(
            user_id=current_user.id,
            match_id=match_id,
            captain_id=body.captain_id,
            vice_captain_id=body.vice_captain_id,
        )
        db.add(team)
        db.flush()

    for player_id in body.player_ids:
        multiplier = 2.0 if player_id == body.captain_id else (1.5 if player_id == body.vice_captain_id else 1.0)
        utp = UserTeamPlayer(
            user_team_id=team.id,
            player_id=player_id,
            multiplier=multiplier,
        )
        db.add(utp)

    db.commit()
    db.refresh(team)
    return build_team_response(team)


@router.get("/matches/{match_id}/teams", response_model=list[TeamResponse])
def list_match_teams(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    teams = db.query(UserTeam).filter(UserTeam.match_id == match_id).all()
    return [build_team_response(t) for t in teams]
