"""Atomic prize distribution for a finalized match."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.prize import PrizeDistribution
from app.models.team import UserTeam
from app.models.user import User


def distribute_prizes(db: Session, match: Match) -> dict:
    """
    Atomically:
    1. Rank user_teams by total_points (tie-break: earlier submission)
    2. For each prize_distributions row: calculate prize = match.prize_pool × pct/100
    3. Write prize_awarded to user_teams and prize_distributions
    4. Increment users.prize_points
    5. Set match.status = 'completed'
    """
    if match.status == "completed":
        return {"message": "Match already finalized"}

    try:
        # 1. Rank teams
        teams = (
            db.query(UserTeam)
            .filter(UserTeam.match_id == match.id)
            .order_by(UserTeam.total_points.desc(), UserTeam.created_at.asc())
            .all()
        )

        for rank, team in enumerate(teams, start=1):
            team.rank = rank

        # 2. Load prize template for this match
        prize_rows = (
            db.query(PrizeDistribution)
            .filter(PrizeDistribution.match_id == match.id, PrizeDistribution.user_id == None)
            .order_by(PrizeDistribution.rank.asc())
            .all()
        )

        if not prize_rows:
            # Fallback default: rank1=70%, rank2=30%
            prize_rows = []
            for rank, pct in [(1, Decimal("70")), (2, Decimal("30"))]:
                pd = PrizeDistribution(
                    match_id=match.id,
                    rank=rank,
                    percentage=pct,
                )
                db.add(pd)
                prize_rows.append(pd)
            db.flush()

        # 3. Distribute prizes
        rank_to_team = {t.rank: t for t in teams}

        for prize_row in prize_rows:
            award = (match.prize_pool * prize_row.percentage / Decimal("100")).quantize(Decimal("0.01"))
            prize_row.prize_awarded = award

            winning_team = rank_to_team.get(prize_row.rank)
            if winning_team:
                prize_row.user_id = winning_team.user_id
                winning_team.prize_awarded = award

                # 4. Increment user.prize_points (integer points, floor of award)
                user = db.query(User).filter(User.id == winning_team.user_id).first()
                if user:
                    user.prize_points += int(award)

        # 5. Finalize
        match.status = "completed"
        db.commit()

        return {
            "message": "Match finalized",
            "teams_ranked": len(teams),
            "prizes_distributed": len(prize_rows),
        }
    except Exception as e:
        db.rollback()
        raise e
