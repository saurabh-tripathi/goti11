import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_admin_user, get_current_user, get_db
from app.models.match import Match
from app.models.scoring import PlayerMatchScore
from app.models.user import User
from app.schemas.match import MatchCreate, MatchPatch, MatchResponse, OverrideScoreRequest
from app.schemas.player import MatchPlayerResponse
from app.schemas.scoring import PlayerScoreResponse
from app.models.player import Player

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchResponse])
def list_matches(
    series_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Match)
    if series_id:
        q = q.filter(Match.series_id == series_id)
    return q.order_by(Match.scheduled_at.desc()).all()


@router.get("/{match_id}", response_model=MatchResponse)
def get_match(match_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    m = db.query(Match).filter(Match.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    return m


@router.post("", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
def create_match(
    body: MatchCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    m = Match(**body.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.patch("/{match_id}", response_model=MatchResponse)
def patch_match(
    match_id: uuid.UUID,
    body: MatchPatch,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    m = db.query(Match).filter(Match.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(m, field, value)
    db.commit()
    db.refresh(m)
    return m


@router.get("/{match_id}/squad", response_model=list[MatchPlayerResponse])
def get_match_squad(match_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    from app.models.player import MatchPlayer
    players = (
        db.query(MatchPlayer)
        .filter(MatchPlayer.match_id == match_id)
        .all()
    )
    return players


@router.post("/{match_id}/sync-squad", status_code=status.HTTP_200_OK)
def sync_squad(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    from app.services.cricket_api import sync_match_squad
    m = db.query(Match).filter(Match.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    count = sync_match_squad(db, m)
    return {"message": f"Synced {count} players"}


@router.post("/{match_id}/sync-score", status_code=status.HTTP_200_OK)
def sync_score(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    from app.services.score_sync import sync_match_score
    m = db.query(Match).filter(Match.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    result = sync_match_score(db, m)
    return result


@router.post("/{match_id}/finalize", status_code=status.HTTP_200_OK)
def finalize_match(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    from app.services.prize_service import distribute_prizes
    m = db.query(Match).filter(Match.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    result = distribute_prizes(db, m)
    return result


@router.get("/{match_id}/scores", response_model=list[PlayerScoreResponse])
def get_match_scores(
    match_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
):
    scores = (
        db.query(PlayerMatchScore)
        .filter(PlayerMatchScore.match_id == match_id)
        .all()
    )
    result = []
    for s in scores:
        player = db.query(Player).filter(Player.id == s.player_id).first()
        effective = s.override_points if s.override_points is not None else s.raw_points
        result.append(PlayerScoreResponse(
            player_id=s.player_id,
            player_name=player.name if player else str(s.player_id),
            role=player.role if player else "",
            runs=s.runs,
            fours=s.fours,
            sixes=s.sixes,
            wickets=s.wickets,
            maiden_overs=s.maiden_overs,
            catches=s.catches,
            stumpings=s.stumpings,
            run_outs=s.run_outs,
            raw_points=s.raw_points,
            override_points=s.override_points,
            effective_points=effective,
        ))
    return result


@router.patch("/{match_id}/override-score", status_code=status.HTTP_200_OK)
def override_score(
    match_id: uuid.UUID,
    body: OverrideScoreRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    score = (
        db.query(PlayerMatchScore)
        .filter(PlayerMatchScore.match_id == match_id, PlayerMatchScore.player_id == body.player_id)
        .first()
    )
    if not score:
        # Create a blank score record if one doesn't exist yet (e.g. before sync-score has run)
        score = PlayerMatchScore(match_id=match_id, player_id=body.player_id)
        db.add(score)
    score.override_points = body.override_points
    db.commit()
    return {"message": "Override applied"}
