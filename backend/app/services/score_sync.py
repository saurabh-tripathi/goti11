"""Sync scorecard from CricAPI → player_match_scores → user team points."""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import settings
from app.models.match import Match
from app.models.player import Player
from app.models.scoring import PlayerMatchScore
from app.models.team import UserTeam, UserTeamPlayer


def _parse_batting(innings: list) -> dict[str, dict]:
    """Extract batting stats keyed by player name (best-effort)."""
    stats: dict[str, dict] = {}
    for inn in innings:
        for batter in inn.get("batting", []):
            name = batter.get("batsman", {}).get("name", "")
            if not name:
                continue
            runs = int(batter.get("r", 0))
            balls = int(batter.get("b", 0))
            fours = int(batter.get("4s", 0))
            sixes = int(batter.get("6s", 0))
            dismissal = batter.get("dismissal", "")
            is_duck = runs == 0 and balls > 0 and "not out" not in dismissal.lower()
            stats[name] = {
                "runs": runs,
                "balls_faced": balls,
                "fours": fours,
                "sixes": sixes,
                "is_duck": is_duck,
            }
    return stats


def _parse_bowling(innings: list) -> dict[str, dict]:
    """Extract bowling stats keyed by player name."""
    stats: dict[str, dict] = {}
    for inn in innings:
        for bowler in inn.get("bowling", []):
            name = bowler.get("bowler", {}).get("name", "")
            if not name:
                continue
            overs_str = str(bowler.get("o", "0"))
            try:
                overs = Decimal(overs_str)
            except Exception:
                overs = Decimal("0")
            stats[name] = {
                "wickets": int(bowler.get("w", 0)),
                "overs_bowled": overs,
                "maiden_overs": int(bowler.get("m", 0)),
                "runs_conceded": int(bowler.get("r", 0)),
            }
    return stats


def _parse_fielding(innings: list) -> dict[str, dict]:
    """Extract fielding stats from dismissal descriptions."""
    stats: dict[str, dict] = {}
    for inn in innings:
        for batter in inn.get("batting", []):
            dismissal = batter.get("dismissal", "")
            low = dismissal.lower()
            if "caught" in low:
                # "c PlayerName b BowlerName"
                parts = dismissal.split(" ")
                if len(parts) >= 2:
                    fielder = parts[1]
                    d = stats.setdefault(fielder, {"catches": 0, "stumpings": 0, "run_outs": 0})
                    d["catches"] += 1
            elif "stumped" in low:
                parts = dismissal.split(" ")
                if len(parts) >= 2:
                    fielder = parts[1]
                    d = stats.setdefault(fielder, {"catches": 0, "stumpings": 0, "run_outs": 0})
                    d["stumpings"] += 1
            elif "run out" in low:
                # Best-effort: extract fielder name between ()
                import re
                match = re.search(r"\(([^)]+)\)", dismissal)
                if match:
                    fielder = match.group(1).strip()
                    d = stats.setdefault(fielder, {"catches": 0, "stumpings": 0, "run_outs": 0})
                    d["run_outs"] += 1
    return stats


def sync_match_score(db: Session, match: Match) -> dict:
    """
    1. Check cooldown
    2. Fetch scorecard from CricAPI (or use cached)
    3. Parse stats → upsert player_match_scores
    4. Compute raw_points via rules engine
    5. Propagate to user_teams
    """
    from app.services.cricket_api import get_match_scorecard
    from app.services.rules_engine import compute_player_points, apply_multipliers_and_total
    from app.models.rules import PointRule, SeriesRuleSet

    # Cooldown check
    now = datetime.now(timezone.utc)
    if match.scorecard_updated_at:
        elapsed = (now - match.scorecard_updated_at).total_seconds()
        if elapsed < settings.SCORE_SYNC_COOLDOWN_SECONDS:
            remaining = int(settings.SCORE_SYNC_COOLDOWN_SECONDS - elapsed)
            return {"message": f"Cooldown active, retry in {remaining}s", "updated": False}

    if not match.cricapi_match_id:
        return {"message": "No cricapi_match_id set", "updated": False}

    # Fetch scorecard
    scorecard_data = get_match_scorecard(match.cricapi_match_id)
    match.raw_scorecard = scorecard_data
    match.scorecard_updated_at = now

    innings = scorecard_data.get("data", {}).get("scorecard", [])
    batting_stats = _parse_batting(innings)
    bowling_stats = _parse_bowling(innings)
    fielding_stats = _parse_fielding(innings)

    # Load point rules
    series_rule_set = (
        db.query(SeriesRuleSet)
        .filter(SeriesRuleSet.series_id == match.series_id)
        .first()
    )
    point_rules = []
    if series_rule_set:
        point_rules = (
            db.query(PointRule)
            .filter(PointRule.rule_set_id == series_rule_set.rule_set_id)
            .all()
        )

    # Load match players
    from app.models.player import MatchPlayer
    match_players = db.query(MatchPlayer).filter(MatchPlayer.match_id == match.id).all()

    updated_count = 0
    for mp in match_players:
        player = mp.player
        name = player.name

        batting = batting_stats.get(name, {})
        bowling = bowling_stats.get(name, {})
        fielding = fielding_stats.get(name, {})

        score = (
            db.query(PlayerMatchScore)
            .filter(PlayerMatchScore.match_id == match.id, PlayerMatchScore.player_id == player.id)
            .first()
        )
        if not score:
            score = PlayerMatchScore(match_id=match.id, player_id=player.id)
            db.add(score)

        score.runs = batting.get("runs", 0)
        score.balls_faced = batting.get("balls_faced", 0)
        score.fours = batting.get("fours", 0)
        score.sixes = batting.get("sixes", 0)
        score.is_duck = batting.get("is_duck", False)
        score.wickets = bowling.get("wickets", 0)
        score.overs_bowled = bowling.get("overs_bowled", Decimal("0"))
        score.maiden_overs = bowling.get("maiden_overs", 0)
        score.runs_conceded = bowling.get("runs_conceded", 0)
        score.catches = fielding.get("catches", 0)
        score.stumpings = fielding.get("stumpings", 0)
        score.run_outs = fielding.get("run_outs", 0)
        score.updated_at = now

        if point_rules:
            score.raw_points = compute_player_points(score, point_rules, player.role)

        updated_count += 1

    db.flush()

    # Propagate to user teams
    user_teams = db.query(UserTeam).filter(UserTeam.match_id == match.id).all()
    for team in user_teams:
        for utp in team.players:
            score = (
                db.query(PlayerMatchScore)
                .filter(
                    PlayerMatchScore.match_id == match.id,
                    PlayerMatchScore.player_id == utp.player_id,
                )
                .first()
            )
            if score:
                utp.points_earned = score.effective_points

        apply_multipliers_and_total(team)

    match.status = "scoring"
    db.commit()

    return {"message": f"Score synced for {updated_count} players", "updated": True}
