"""CricAPI client with local JSONB caching."""
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings

ROLE_MAP = {
    "wk-batsman": "wicketkeeper",
    "wicket-keeper batsman": "wicketkeeper",
    "wicketkeeper": "wicketkeeper",
    "batsman": "batsman",
    "top order batter": "batsman",
    "middle order batter": "batsman",
    "opening batter": "batsman",
    "batter": "batsman",
    "bowling allrounder": "allrounder",
    "batting allrounder": "allrounder",
    "allrounder": "allrounder",
    "all-rounder": "allrounder",
    "bowler": "bowler",
    "medium": "bowler",
    "fast medium": "bowler",
    "pace bowler": "bowler",
    "spin bowler": "bowler",
}


def normalize_role(raw_role: str) -> str:
    """Map CricAPI role strings to canonical set."""
    normalized = raw_role.lower().strip()
    for key, canonical in ROLE_MAP.items():
        if key in normalized:
            return canonical
    # Default fallback
    if "wk" in normalized or "keeper" in normalized:
        return "wicketkeeper"
    if "bowl" in normalized:
        return "bowler"
    if "bat" in normalized:
        return "batsman"
    if "all" in normalized:
        return "allrounder"
    return "batsman"


def _get(endpoint: str, params: dict | None = None) -> dict:
    url = f"{settings.CRICAPI_BASE_URL}/{endpoint}"
    p = {"apikey": settings.CRICAPI_KEY, **(params or {})}
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(url, params=p)
        resp.raise_for_status()
        return resp.json()


def get_current_matches() -> list[dict]:
    """Fetch current IPL matches from CricAPI."""
    data = _get("cricScore")
    return data.get("data", [])


def get_match_squad(cricapi_match_id: str) -> dict:
    """Fetch squad/players for a match."""
    return _get("match_squad", {"id": cricapi_match_id})


def get_match_scorecard(cricapi_match_id: str) -> dict:
    """Fetch full scorecard for a match."""
    return _get("match_scorecard", {"id": cricapi_match_id})


def get_match_points(cricapi_match_id: str) -> dict:
    """Fetch fantasy points for a match (paid tier)."""
    return _get("match_points", {"id": cricapi_match_id})


def sync_match_squad(db, match) -> int:
    """Pull squad from CricAPI and upsert players + match_players."""
    from app.models.player import MatchPlayer, Player

    if not match.cricapi_match_id:
        raise ValueError("Match has no cricapi_match_id set")

    data = get_match_squad(match.cricapi_match_id)
    squad_data = data.get("data", {})

    count = 0
    teams = squad_data.get("squad", [])
    if not teams:
        # Try alternate structure
        teams = []
        for key in ("teamInfo", "teams"):
            if key in squad_data:
                teams = squad_data[key]
                break

    for team_entry in teams:
        team_name = team_entry.get("name", "Unknown")
        players_list = team_entry.get("players", [])
        for p_data in players_list:
            cricapi_id = str(p_data.get("id", ""))
            if not cricapi_id:
                continue

            raw_role = p_data.get("role", "batsman")
            canonical_role = normalize_role(raw_role)

            # Upsert player
            player = db.query(Player).filter(Player.cricapi_player_id == cricapi_id).first()
            if not player:
                player = Player(
                    cricapi_player_id=cricapi_id,
                    name=p_data.get("name", "Unknown"),
                    role=canonical_role,
                    ipl_team=team_name,
                )
                db.add(player)
                db.flush()
            else:
                player.name = p_data.get("name", player.name)
                player.role = canonical_role
                player.ipl_team = team_name
                player.last_synced_at = datetime.now(timezone.utc)

            # Upsert match_player
            mp = (
                db.query(MatchPlayer)
                .filter(MatchPlayer.match_id == match.id, MatchPlayer.player_id == player.id)
                .first()
            )
            credit = float(p_data.get("fantasyCredit", 8.0))
            if not mp:
                mp = MatchPlayer(
                    match_id=match.id,
                    player_id=player.id,
                    team_name=team_name,
                    credit_value=credit,
                )
                db.add(mp)
            else:
                mp.credit_value = credit
                mp.team_name = team_name

            count += 1

    match.status = "squad_synced"
    db.commit()
    return count
