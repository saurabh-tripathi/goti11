"""
Wipe all seed/test data from the database and recreate the admin user.
Run as a one-off ECS task when you want a clean production state.

Usage:
    python scripts/reset_prod.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User
from app.models.series import Series
from app.models.match import Match
from app.models.player import Player, MatchPlayer
from app.models.team import UserTeam, UserTeamPlayer
from app.models.scoring import PlayerMatchScore
from app.models.rules import RuleSet, PointRule, SelectionRule, SeriesRuleSet
from app.models.prize import PrizeDistribution
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def reset(db):
    print("Wiping all data...")

    # Delete in dependency order
    db.query(PlayerMatchScore).delete()
    db.query(UserTeamPlayer).delete()
    db.query(UserTeam).delete()
    db.query(MatchPlayer).delete()
    db.query(Player).delete()
    db.query(PrizeDistribution).delete()
    db.query(SeriesRuleSet).delete()
    db.query(PointRule).delete()
    db.query(SelectionRule).delete()
    db.query(RuleSet).delete()
    db.query(Match).delete()
    db.query(Series).delete()
    db.query(User).delete()
    db.flush()
    print("  All tables cleared.")

    # Recreate admin user
    admin = User(
        username="admin",
        email="admin@goti11.local",
        hashed_password=pwd_context.hash("admin123"),
        is_admin=True,
    )
    db.add(admin)
    db.commit()
    print("  Admin user recreated (admin / admin123).")
    print("Done. Production DB is clean.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        reset(db)
    finally:
        db.close()
