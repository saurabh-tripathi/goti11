#!/usr/bin/env python3
"""
seed.py — populate the DB with realistic test data.

Run from the backend/ directory:
    .venv/bin/python scripts/seed.py [--reset]

--reset  drops all seeded rows first (safe: only deletes rows created by
          this script, identified by a known prefix/value).
"""
import argparse
import sys
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

# ── path setup ────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.match import Match
from app.models.player import MatchPlayer, Player
from app.models.prize import PrizeDistribution
from app.models.rules import PointRule, RuleSet, SelectionRule, SeriesRuleSet
from app.models.scoring import PlayerMatchScore
from app.models.series import Series
from app.models.team import UserTeam, UserTeamPlayer
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── constants ─────────────────────────────────────────────────────
SEED_TAG = "SEED"   # prefix used in cricapi_player_id to find/delete seeded rows

GREEN = "\033[0;32m"; YELLOW = "\033[1;33m"; RED = "\033[0;31m"; NC = "\033[0m"
def ok(msg):   print(f"{GREEN}✓{NC}  {msg}")
def info(msg): print(f"{YELLOW}→{NC}  {msg}")
def err(msg):  print(f"{RED}✗{NC}  {msg}", file=sys.stderr)


# ─────────────────────────────────────────────────────────────────
# Reset helpers
# ─────────────────────────────────────────────────────────────────

def reset(db: Session):
    info("Resetting seeded data...")

    # Find seeded players
    seeded_players = db.query(Player).filter(Player.cricapi_player_id.like(f"{SEED_TAG}%")).all()
    seeded_pids = [p.id for p in seeded_players]

    # Cascade: user_team_players → user_teams → player_match_scores → match_players → players
    if seeded_pids:
        db.query(UserTeamPlayer).filter(UserTeamPlayer.player_id.in_(seeded_pids)).delete(synchronize_session=False)
        db.query(PlayerMatchScore).filter(PlayerMatchScore.player_id.in_(seeded_pids)).delete(synchronize_session=False)
        db.query(MatchPlayer).filter(MatchPlayer.player_id.in_(seeded_pids)).delete(synchronize_session=False)
        for p in seeded_players:
            db.delete(p)

    # Find seeded series (by name prefix)
    seeded_series = db.query(Series).filter(Series.name.like(f"[{SEED_TAG}]%")).all()
    seeded_sids = [s.id for s in seeded_series]

    if seeded_sids:
        seeded_matches = db.query(Match).filter(Match.series_id.in_(seeded_sids)).all()
        seeded_mids = [m.id for m in seeded_matches]
        if seeded_mids:
            db.query(UserTeam).filter(UserTeam.match_id.in_(seeded_mids)).delete(synchronize_session=False)
            db.query(PrizeDistribution).filter(PrizeDistribution.match_id.in_(seeded_mids)).delete(synchronize_session=False)
            for m in seeded_matches:
                db.delete(m)
        db.query(SeriesRuleSet).filter(SeriesRuleSet.series_id.in_(seeded_sids)).delete(synchronize_session=False)
        for s in seeded_series:
            db.delete(s)

    # Rule sets
    seeded_rs = db.query(RuleSet).filter(RuleSet.name.like(f"[{SEED_TAG}]%")).all()
    for rs in seeded_rs:
        db.delete(rs)

    # Users
    seeded_users = db.query(User).filter(User.username.like("testuser%")).all()
    for u in seeded_users:
        db.delete(u)

    db.commit()
    ok("Reset done.")


# ─────────────────────────────────────────────────────────────────
# Main seed
# ─────────────────────────────────────────────────────────────────

def seed(db: Session):

    # ── admin ─────────────────────────────────────────────────────
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@goti11.local",
            hashed_password=pwd_context.hash("admin123"),
            is_admin=True,
        )
        db.add(admin)
        db.flush()
        ok("Created admin user (admin / admin123)")
    else:
        info("admin already exists, skipping")

    # ── test users ────────────────────────────────────────────────
    test_users = []
    for i in range(1, 4):
        u = db.query(User).filter(User.username == f"testuser{i}").first()
        if not u:
            u = User(
                username=f"testuser{i}",
                email=f"testuser{i}@goti11.local",
                hashed_password=pwd_context.hash(f"pass{i}123"),
            )
            db.add(u)
            db.flush()
            ok(f"Created testuser{i} (pass{i}123)")
        else:
            info(f"testuser{i} already exists")
        test_users.append(u)

    # ── rule set ──────────────────────────────────────────────────
    rs_name = f"[{SEED_TAG}] Standard IPL Rules"
    rs = db.query(RuleSet).filter(RuleSet.name == rs_name).first()
    if not rs:
        rs = RuleSet(name=rs_name, description="Standard point rules for testing")
        db.add(rs)
        db.flush()

        point_rules = [
            # batting
            ("run",                None,            Decimal("1")),
            ("four",               None,            Decimal("1")),
            ("six",                None,            Decimal("2")),
            ("duck_penalty",       "batsman",       Decimal("-2")),
            ("half_century_bonus", None,            Decimal("8")),
            ("century_bonus",      None,            Decimal("16")),
            # bowling
            ("wicket",             None,            Decimal("25")),
            ("maiden_over",        None,            Decimal("12")),
            ("four_wicket_bonus",  None,            Decimal("8")),
            ("five_wicket_bonus",  None,            Decimal("16")),
            # fielding
            ("catch",              None,            Decimal("8")),
            ("stumping",           None,            Decimal("12")),
            ("run_out",            None,            Decimal("6")),
        ]
        for event_key, role_filter, points in point_rules:
            db.add(PointRule(rule_set_id=rs.id, event_key=event_key, role_filter=role_filter, points=points))

        selection_rules = [
            ("total_players",      11,  None),
            ("credit_cap",         None, Decimal("100")),
            ("min_wicketkeepers",  1,   None),
            ("min_batsmen",        3,   None),
            ("min_bowlers",        3,   None),
            ("min_allrounders",    1,   None),
            ("max_from_one_team",  7,   None),
        ]
        for key, vi, vd in selection_rules:
            db.add(SelectionRule(rule_set_id=rs.id, constraint_key=key, value_int=vi, value_decimal=vd))

        db.flush()
        ok(f"Created rule set '{rs_name}'")
    else:
        info(f"Rule set already exists")

    # ── series ────────────────────────────────────────────────────
    series_name = f"[{SEED_TAG}] IPL 2025 Test Series"
    series = db.query(Series).filter(Series.name == series_name).first()
    if not series:
        series = Series(
            name=series_name,
            cricapi_series_id="seed-series-001",
            start_date=date(2025, 4, 1),
            end_date=date(2025, 5, 31),
            status="active",
        )
        db.add(series)
        db.flush()

        # Link rule set
        db.add(SeriesRuleSet(series_id=series.id, rule_set_id=rs.id))
        db.flush()
        ok(f"Created series '{series_name}'")
    else:
        info("Series already exists")

    # ── match ─────────────────────────────────────────────────────
    match_name = f"[{SEED_TAG}] MI vs CSK — Match 1"
    match = db.query(Match).filter(Match.name == match_name).first()
    if not match:
        now = datetime.now(timezone.utc)
        match = Match(
            series_id=series.id,
            name=match_name,
            team_a="Mumbai Indians",
            team_b="Chennai Super Kings",
            scheduled_at=now + timedelta(hours=2),
            lock_time=now + timedelta(hours=1, minutes=30),
            status="squad_synced",   # skipping 'upcoming' so team selection works
            prize_pool=Decimal("1000"),
        )
        db.add(match)
        db.flush()
        ok(f"Created match '{match_name}'")
    else:
        info("Match already exists")

    # ── players ───────────────────────────────────────────────────
    # 22 players: 11 per team, roles satisfying selection rules
    # team A: Mumbai Indians
    # team B: Chennai Super Kings
    players_data = [
        # (cricapi_id, name, role, ipl_team, credit)
        # --- Mumbai Indians ---
        (f"{SEED_TAG}_MI_01", "Ishan Kishan",      "wicketkeeper", "Mumbai Indians",    Decimal("9.5")),
        (f"{SEED_TAG}_MI_02", "Rohit Sharma",       "batsman",      "Mumbai Indians",    Decimal("10.0")),
        (f"{SEED_TAG}_MI_03", "Suryakumar Yadav",   "batsman",      "Mumbai Indians",    Decimal("10.0")),
        (f"{SEED_TAG}_MI_04", "Tilak Varma",        "batsman",      "Mumbai Indians",    Decimal("8.5")),
        (f"{SEED_TAG}_MI_05", "Hardik Pandya",      "allrounder",   "Mumbai Indians",    Decimal("10.0")),
        (f"{SEED_TAG}_MI_06", "Tim David",          "allrounder",   "Mumbai Indians",    Decimal("8.0")),
        (f"{SEED_TAG}_MI_07", "Romario Shepherd",   "allrounder",   "Mumbai Indians",    Decimal("7.5")),
        (f"{SEED_TAG}_MI_08", "Jasprit Bumrah",     "bowler",       "Mumbai Indians",    Decimal("10.0")),
        (f"{SEED_TAG}_MI_09", "Gerald Coetzee",     "bowler",       "Mumbai Indians",    Decimal("8.0")),
        (f"{SEED_TAG}_MI_10", "Piyush Chawla",      "bowler",       "Mumbai Indians",    Decimal("7.0")),
        (f"{SEED_TAG}_MI_11", "Nuwan Thushara",     "bowler",       "Mumbai Indians",    Decimal("7.0")),
        # --- Chennai Super Kings ---
        (f"{SEED_TAG}_CSK_01", "MS Dhoni",           "wicketkeeper", "Chennai Super Kings", Decimal("9.0")),
        (f"{SEED_TAG}_CSK_02", "Ruturaj Gaikwad",    "batsman",      "Chennai Super Kings", Decimal("9.5")),
        (f"{SEED_TAG}_CSK_03", "Devon Conway",       "batsman",      "Chennai Super Kings", Decimal("9.0")),
        (f"{SEED_TAG}_CSK_04", "Ajinkya Rahane",     "batsman",      "Chennai Super Kings", Decimal("7.5")),
        (f"{SEED_TAG}_CSK_05", "Shivam Dube",        "allrounder",   "Chennai Super Kings", Decimal("8.5")),
        (f"{SEED_TAG}_CSK_06", "Ravindra Jadeja",    "allrounder",   "Chennai Super Kings", Decimal("9.5")),
        (f"{SEED_TAG}_CSK_07", "Moeen Ali",          "allrounder",   "Chennai Super Kings", Decimal("8.0")),
        (f"{SEED_TAG}_CSK_08", "Deepak Chahar",      "bowler",       "Chennai Super Kings", Decimal("8.0")),
        (f"{SEED_TAG}_CSK_09", "Tushar Deshpande",   "bowler",       "Chennai Super Kings", Decimal("7.5")),
        (f"{SEED_TAG}_CSK_10", "Mathesha Pathirana", "bowler",       "Chennai Super Kings", Decimal("8.5")),
        (f"{SEED_TAG}_CSK_11", "Mustafizur Rahman",  "bowler",       "Chennai Super Kings", Decimal("7.5")),
    ]

    player_objs = {}
    for cid, name, role, ipl_team, credit in players_data:
        p = db.query(Player).filter(Player.cricapi_player_id == cid).first()
        if not p:
            p = Player(cricapi_player_id=cid, name=name, role=role, ipl_team=ipl_team)
            db.add(p)
            db.flush()
        player_objs[cid] = (p, ipl_team, credit)

    ok(f"Upserted {len(players_data)} players")

    # ── match_players ─────────────────────────────────────────────
    for cid, (player, team_name, credit) in player_objs.items():
        existing = (
            db.query(MatchPlayer)
            .filter(MatchPlayer.match_id == match.id, MatchPlayer.player_id == player.id)
            .first()
        )
        if not existing:
            db.add(MatchPlayer(
                match_id=match.id,
                player_id=player.id,
                team_name=team_name,
                credit_value=credit,
            ))
    db.flush()
    ok("Linked players to match")

    # ── prize distributions ───────────────────────────────────────
    existing_prize = (
        db.query(PrizeDistribution)
        .filter(PrizeDistribution.match_id == match.id, PrizeDistribution.user_id == None)
        .first()
    )
    if not existing_prize:
        for rank, pct in [(1, Decimal("50")), (2, Decimal("30")), (3, Decimal("20"))]:
            db.add(PrizeDistribution(match_id=match.id, rank=rank, percentage=pct))
        db.flush()
        ok("Created prize distribution template (50%/30%/20%)")
    else:
        info("Prize distribution already exists")

    # ── Match 2: About to start (squad synced, locks in ~10 min) ─────
    match2_name = f"[{SEED_TAG}] MI vs CSK — Match 2 (Starts Soon)"
    match2 = db.query(Match).filter(Match.name == match2_name).first()
    if not match2:
        now = datetime.now(timezone.utc)
        match2 = Match(
            series_id=series.id,
            name=match2_name,
            team_a="Mumbai Indians",
            team_b="Chennai Super Kings",
            scheduled_at=now + timedelta(minutes=25),
            lock_time=now + timedelta(minutes=10),
            status="squad_synced",
            prize_pool=Decimal("2000"),
        )
        db.add(match2)
        db.flush()
        for cid, (player, team_name, credit) in player_objs.items():
            existing = (
                db.query(MatchPlayer)
                .filter(MatchPlayer.match_id == match2.id, MatchPlayer.player_id == player.id)
                .first()
            )
            if not existing:
                db.add(MatchPlayer(
                    match_id=match2.id,
                    player_id=player.id,
                    team_name=team_name,
                    credit_value=credit,
                ))
        db.flush()
        ok(f"Created match '{match2_name}'")
    else:
        info("Match 2 already exists")
        match2 = db.query(Match).filter(Match.name == match2_name).first()

    # Always refresh lock_time so it stays 2 hours in the future from now
    now = datetime.now(timezone.utc)
    match2.lock_time = now + timedelta(hours=2)
    match2.scheduled_at = now + timedelta(hours=2, minutes=30)
    db.flush()
    ok("Refreshed Match 2 lock_time → 2 h from now")

    # ── Match 3: Live / Scoring (started 3 hrs ago, MI innings done) ─
    match3_name = f"[{SEED_TAG}] MI vs CSK — Match 3 (Live)"
    match3 = db.query(Match).filter(Match.name == match3_name).first()
    if not match3:
        now = datetime.now(timezone.utc)
        match3 = Match(
            series_id=series.id,
            name=match3_name,
            team_a="Mumbai Indians",
            team_b="Chennai Super Kings",
            scheduled_at=now - timedelta(hours=3),
            lock_time=now - timedelta(hours=3, minutes=30),
            status="scoring",
            prize_pool=Decimal("5000"),
        )
        db.add(match3)
        db.flush()

        # Link players
        for cid, (player, team_name, credit) in player_objs.items():
            existing = (
                db.query(MatchPlayer)
                .filter(MatchPlayer.match_id == match3.id, MatchPlayer.player_id == player.id)
                .first()
            )
            if not existing:
                db.add(MatchPlayer(
                    match_id=match3.id,
                    player_id=player.id,
                    team_name=team_name,
                    credit_value=credit,
                ))
        db.flush()

        # Seed scores — MI innings completed, CSK chasing (only bowling done for CSK)
        # (cid, runs, fours, sixes, wickets, maiden_overs, catches, stumpings, is_duck, raw_points)
        live_scores = [
            # MI batters
            (f"{SEED_TAG}_MI_01", 45,  4, 2, 0, 0, 0, 0, False, Decimal("57")),
            (f"{SEED_TAG}_MI_02", 72,  6, 3, 0, 0, 0, 0, False, Decimal("90")),
            (f"{SEED_TAG}_MI_03",  0,  0, 0, 0, 0, 0, 0, True,  Decimal("-2")),  # duck
            (f"{SEED_TAG}_MI_04", 28,  2, 1, 0, 0, 0, 0, False, Decimal("33")),
            (f"{SEED_TAG}_MI_05", 15,  1, 0, 2, 0, 1, 0, False, Decimal("67")),  # + 2 wkts + catch
            (f"{SEED_TAG}_MI_06", 35,  2, 2, 0, 0, 0, 0, False, Decimal("43")),
            (f"{SEED_TAG}_MI_07", 22,  1, 1, 1, 0, 0, 0, False, Decimal("49")),
            (f"{SEED_TAG}_MI_08",  2,  0, 0, 4, 1, 0, 0, False, Decimal("110")), # 4 wkts + maiden
            (f"{SEED_TAG}_MI_09",  0,  0, 0, 2, 0, 0, 0, False, Decimal("50")),
            (f"{SEED_TAG}_MI_10",  0,  0, 0, 1, 0, 1, 0, False, Decimal("33")),
            (f"{SEED_TAG}_MI_11",  0,  0, 0, 2, 1, 0, 0, False, Decimal("58")),
            # CSK — bowling done, yet to bat
            (f"{SEED_TAG}_CSK_01",  0, 0, 0, 0, 0, 2, 1, False, Decimal("24")),  # 2c + 1st
            (f"{SEED_TAG}_CSK_02",  0, 0, 0, 0, 0, 1, 0, False, Decimal("8")),
            (f"{SEED_TAG}_CSK_03",  0, 0, 0, 0, 0, 0, 0, False, Decimal("0")),
            (f"{SEED_TAG}_CSK_04",  0, 0, 0, 0, 0, 1, 0, False, Decimal("8")),
            (f"{SEED_TAG}_CSK_05",  0, 0, 0, 1, 0, 0, 0, False, Decimal("25")),
            (f"{SEED_TAG}_CSK_06",  0, 0, 0, 2, 1, 1, 0, False, Decimal("66")),  # 2wkts+maiden+catch
            (f"{SEED_TAG}_CSK_07",  0, 0, 0, 1, 0, 0, 0, False, Decimal("25")),
            (f"{SEED_TAG}_CSK_08",  0, 0, 0, 2, 0, 0, 0, False, Decimal("50")),
            (f"{SEED_TAG}_CSK_09",  0, 0, 0, 0, 0, 0, 0, False, Decimal("0")),
            (f"{SEED_TAG}_CSK_10",  0, 0, 0, 3, 0, 0, 0, False, Decimal("75")),
            (f"{SEED_TAG}_CSK_11",  0, 0, 0, 1, 0, 0, 0, False, Decimal("25")),
        ]
        for cid, runs, fours, sixes, wkts, maidens, catches, stumpings, is_duck, raw_pts in live_scores:
            if cid in player_objs:
                p = player_objs[cid][0]
                existing_score = (
                    db.query(PlayerMatchScore)
                    .filter(PlayerMatchScore.match_id == match3.id, PlayerMatchScore.player_id == p.id)
                    .first()
                )
                if not existing_score:
                    db.add(PlayerMatchScore(
                        match_id=match3.id,
                        player_id=p.id,
                        runs=runs,
                        fours=fours,
                        sixes=sixes,
                        wickets=wkts,
                        maiden_overs=maidens,
                        catches=catches,
                        stumpings=stumpings,
                        is_duck=is_duck,
                        raw_points=raw_pts,
                    ))
        db.flush()
        ok(f"Created match '{match3_name}' with live scores")
    else:
        info("Match 3 already exists")
        match3 = db.query(Match).filter(Match.name == match3_name).first()

    # ── Match 3: seed user teams (locked, with computed points) ───
    # Points per player (effective = raw_points; C=×2, VC=×1.5)
    pts = {
        f"{SEED_TAG}_MI_01": Decimal("57"),   # Ishan Kishan
        f"{SEED_TAG}_MI_02": Decimal("90"),   # Rohit Sharma
        f"{SEED_TAG}_MI_05": Decimal("67"),   # Hardik Pandya
        f"{SEED_TAG}_MI_06": Decimal("43"),   # Tim David
        f"{SEED_TAG}_MI_07": Decimal("49"),   # Romario Shepherd
        f"{SEED_TAG}_MI_08": Decimal("110"),  # Jasprit Bumrah
        f"{SEED_TAG}_MI_09": Decimal("50"),   # Gerald Coetzee
        f"{SEED_TAG}_MI_11": Decimal("58"),   # Nuwan Thushara
        f"{SEED_TAG}_CSK_01": Decimal("24"),  # MS Dhoni
        f"{SEED_TAG}_CSK_05": Decimal("25"),  # Shivam Dube
        f"{SEED_TAG}_CSK_06": Decimal("66"),  # Ravindra Jadeja
        f"{SEED_TAG}_CSK_07": Decimal("25"),  # Moeen Ali
        f"{SEED_TAG}_CSK_08": Decimal("50"),  # Deepak Chahar
        f"{SEED_TAG}_CSK_10": Decimal("75"),  # Mathesha Pathirana
    }

    # (user_index 0-2, captain_cid, vc_cid, [11 player cids])
    team_defs = [
        (0, f"{SEED_TAG}_MI_08", f"{SEED_TAG}_MI_02",  # user1: C=Bumrah, VC=Rohit
         [f"{SEED_TAG}_MI_08", f"{SEED_TAG}_MI_02", f"{SEED_TAG}_CSK_06", f"{SEED_TAG}_MI_05",
          f"{SEED_TAG}_CSK_10", f"{SEED_TAG}_MI_01", f"{SEED_TAG}_MI_11", f"{SEED_TAG}_MI_09",
          f"{SEED_TAG}_MI_06", f"{SEED_TAG}_CSK_01", f"{SEED_TAG}_CSK_08"]),
        (1, f"{SEED_TAG}_MI_02", f"{SEED_TAG}_CSK_10",  # user2: C=Rohit, VC=Pathirana
         [f"{SEED_TAG}_MI_02", f"{SEED_TAG}_CSK_10", f"{SEED_TAG}_MI_08", f"{SEED_TAG}_CSK_06",
          f"{SEED_TAG}_MI_05", f"{SEED_TAG}_MI_01", f"{SEED_TAG}_MI_11", f"{SEED_TAG}_MI_07",
          f"{SEED_TAG}_MI_06", f"{SEED_TAG}_CSK_01", f"{SEED_TAG}_CSK_08"]),
        (2, f"{SEED_TAG}_CSK_06", f"{SEED_TAG}_MI_08",  # user3: C=Jadeja, VC=Bumrah
         [f"{SEED_TAG}_CSK_06", f"{SEED_TAG}_MI_08", f"{SEED_TAG}_MI_02", f"{SEED_TAG}_MI_05",
          f"{SEED_TAG}_CSK_10", f"{SEED_TAG}_MI_01", f"{SEED_TAG}_MI_11", f"{SEED_TAG}_MI_09",
          f"{SEED_TAG}_MI_06", f"{SEED_TAG}_CSK_01", f"{SEED_TAG}_CSK_05"]),
    ]

    for user_idx, cap_cid, vc_cid, player_cids in team_defs:
        user = test_users[user_idx]
        cap_player = player_objs[cap_cid][0]
        vc_player = player_objs[vc_cid][0]

        existing_team = (
            db.query(UserTeam)
            .filter(UserTeam.user_id == user.id, UserTeam.match_id == match3.id)
            .first()
        )
        if existing_team:
            info(f"Team for {user.username} in match3 already exists")
            continue

        # Compute total points
        total = Decimal("0")
        for cid in player_cids:
            base = pts.get(cid, Decimal("0"))
            if cid == cap_cid:
                total += base * Decimal("2")
            elif cid == vc_cid:
                total += base * Decimal("1.5")
            else:
                total += base

        team = UserTeam(
            user_id=user.id,
            match_id=match3.id,
            captain_id=cap_player.id,
            vice_captain_id=vc_player.id,
            total_points=total,
            is_locked=True,
        )
        db.add(team)
        db.flush()

        for cid in player_cids:
            p = player_objs[cid][0]
            base = pts.get(cid, Decimal("0"))
            if cid == cap_cid:
                mult, final = Decimal("2"), base * Decimal("2")
            elif cid == vc_cid:
                mult, final = Decimal("1.5"), base * Decimal("1.5")
            else:
                mult, final = Decimal("1"), base
            db.add(UserTeamPlayer(
                user_team_id=team.id,
                player_id=p.id,
                points_earned=base,
                multiplier=mult,
                final_points=final,
            ))
        db.flush()
        ok(f"Seeded team for {user.username} in match3 — {total} pts")

    db.commit()

    print()
    print("─" * 50)
    print("Seed complete. Summary:")
    print(f"  Admin:      admin / admin123")
    for i, u in enumerate(test_users, 1):
        print(f"  User {i}:     {u.username} / pass{i}123")
    print(f"  Series ID:  {series.id}")
    print(f"  Match ID:   {match.id}")
    print(f"  Match 2 ID: {match2.id}  ← squad_synced / starts soon")
    print(f"  Match 3 ID: {match3.id}  ← scoring / live with scores")
    print(f"  Players:    {len(players_data)} (11 MI + 11 CSK)")
    print(f"  Prize pool: ₹{match.prize_pool} (50/30/20%)")
    print("─" * 50)


# ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Delete seeded rows before re-seeding")
    args = parser.parse_args()

    db: Session = SessionLocal()
    try:
        if args.reset:
            reset(db)
        seed(db)
    except Exception as e:
        db.rollback()
        err(f"Seed failed: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
