"""Rules engine: team validation + points computation.

All constraints and point values are data-driven from the DB.
Add new constraint types by adding entries to CONSTRAINT_HANDLERS.
"""
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Constraint handlers
# ---------------------------------------------------------------------------

def validate_total_count(player_ids: list, match_players: list, rule, **_) -> str | None:
    expected = rule.value_int
    if expected and len(player_ids) != expected:
        return f"Team must have exactly {expected} players (got {len(player_ids)})"
    return None


def validate_credits(player_ids: list, match_players: list, rule, **_) -> str | None:
    cap = rule.value_decimal or Decimal(rule.value_int or 100)
    total = sum(mp.credit_value for mp in match_players if mp.player_id in set(player_ids))
    if total > cap:
        return f"Total credits {total} exceeds cap {cap}"
    return None


_ROLE_KEY_MAP = {
    "min_batsmen":      "batsman",
    "min_bowlers":      "bowler",
    "min_allrounders":  "allrounder",
    "min_wicketkeepers":"wicketkeeper",
}


def validate_min_role(player_ids: list, match_players: list, rule, **_) -> str | None:
    key = rule.constraint_key
    min_count = rule.value_int or 0
    role = _ROLE_KEY_MAP.get(key, key.replace("min_", ""))
    pid_set = set(player_ids)
    count = sum(
        1 for mp in match_players
        if mp.player_id in pid_set and mp.player.role == role
    )
    if count < min_count:
        return f"Need at least {min_count} {role}(s) (have {count})"
    return None


def validate_max_team(player_ids: list, match_players: list, rule, **_) -> str | None:
    max_count = rule.value_int or 7
    pid_set = set(player_ids)
    team_counts: dict[str, int] = {}
    for mp in match_players:
        if mp.player_id in pid_set:
            team_counts[mp.team_name] = team_counts.get(mp.team_name, 0) + 1
    for team, count in team_counts.items():
        if count > max_count:
            return f"Max {max_count} players from one team (have {count} from {team})"
    return None


CONSTRAINT_HANDLERS = {
    "total_players": validate_total_count,
    "credit_cap": validate_credits,
    "min_wicketkeepers": validate_min_role,
    "min_batsmen": validate_min_role,
    "min_bowlers": validate_min_role,
    "min_allrounders": validate_min_role,
    "max_from_one_team": validate_max_team,
}


# ---------------------------------------------------------------------------
# Validation entry point
# ---------------------------------------------------------------------------

def validate_team_selection(
    db: Session,
    match,
    player_ids: list[uuid.UUID],
    selected_match_players: list,
) -> list[str]:
    """Return list of validation errors (empty = valid)."""
    from app.models.rules import SelectionRule, SeriesRuleSet

    # Load selection rules for this series
    series_rule_set = (
        db.query(SeriesRuleSet)
        .filter(SeriesRuleSet.series_id == match.series_id)
        .first()
    )
    if not series_rule_set:
        # No rules configured — only enforce total_players = 11 as default
        if len(player_ids) != 11:
            return [f"Team must have exactly 11 players"]
        return []

    rules = (
        db.query(SelectionRule)
        .filter(SelectionRule.rule_set_id == series_rule_set.rule_set_id)
        .all()
    )

    errors = []
    for rule in rules:
        handler = CONSTRAINT_HANDLERS.get(rule.constraint_key)
        if handler:
            err = handler(
                player_ids=player_ids,
                match_players=selected_match_players,
                rule=rule,
            )
            if err:
                errors.append(err)
    return errors


# ---------------------------------------------------------------------------
# Points computation
# ---------------------------------------------------------------------------

def compute_player_points(score, point_rules: list, player_role: str) -> Decimal:
    """Compute raw fantasy points for a player based on their scorecard stats."""
    total = Decimal("0")

    for rule in point_rules:
        # Skip if role filter doesn't match
        if rule.role_filter and rule.role_filter != player_role:
            continue

        pts = Decimal(str(rule.points))
        key = rule.event_key

        match key:
            case "run":
                total += pts * score.runs
            case "four":
                total += pts * score.fours
            case "six":
                total += pts * score.sixes
            case "wicket":
                total += pts * score.wickets
            case "maiden_over":
                total += pts * score.maiden_overs
            case "catch":
                total += pts * score.catches
            case "stumping":
                total += pts * score.stumpings
            case "run_out":
                total += pts * score.run_outs
            case "duck_penalty":
                if score.is_duck:
                    total += pts  # pts should be negative
            case "half_century_bonus":
                if score.runs >= 50:
                    total += pts
            case "century_bonus":
                if score.runs >= 100:
                    total += pts
            case "five_wicket_bonus":
                if score.wickets >= 5:
                    total += pts
            case "four_wicket_bonus":
                if score.wickets >= 4:
                    total += pts
            case _:
                # Unknown key — skip silently; add new cases as needed
                pass

    return total


def apply_multipliers_and_total(team) -> Decimal:
    """Compute total_points for a UserTeam after scores are set."""
    total = Decimal("0")
    for utp in team.players:
        # utp.points_earned should already be set by score_sync
        utp.final_points = utp.points_earned * utp.multiplier
        total += utp.final_points
    team.total_points = total
    return total
