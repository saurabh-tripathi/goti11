#!/usr/bin/env python3
"""
test_flow.py — end-to-end API test against a running backend.

Run from the backend/ directory:
    .venv/bin/python scripts/test_flow.py [--base-url http://localhost:8000]

Prerequisites:
    1. Backend is running  (./scripts/dev.sh)
    2. DB has been seeded  (.venv/bin/python scripts/seed.py)

Flow:
    1.  Login as admin + 3 test users
    2.  List series & matches
    3.  Fetch match squad
    4.  Each user picks a different team (captain/VC variation)
    5.  Admin overrides player scores to realistic values
    6.  Admin re-triggers score propagation via a helper
    7.  Admin finalizes match
    8.  Check match leaderboard
    9.  Check series leaderboard
    10. Verify user prize_points updated
"""
import argparse
import sys
import textwrap
from decimal import Decimal

import httpx

# ── colours ───────────────────────────────────────────────────────
GREEN  = "\033[0;32m"
YELLOW = "\033[1;33m"
RED    = "\033[0;31m"
CYAN   = "\033[0;36m"
BOLD   = "\033[1m"
NC     = "\033[0m"

PASS = 0
FAIL = 0


def section(title: str):
    print(f"\n{BOLD}{CYAN}{'─'*55}{NC}")
    print(f"{BOLD}{CYAN}  {title}{NC}")
    print(f"{BOLD}{CYAN}{'─'*55}{NC}")


def ok(label: str, detail: str = ""):
    global PASS
    PASS += 1
    suffix = f"  {YELLOW}{detail}{NC}" if detail else ""
    print(f"  {GREEN}✓{NC}  {label}{suffix}")


def fail(label: str, detail: str = ""):
    global FAIL
    FAIL += 1
    print(f"  {RED}✗{NC}  {label}  {RED}{detail}{NC}")


def check(label: str, condition: bool, detail: str = ""):
    if condition:
        ok(label, detail)
    else:
        fail(label, detail)
    return condition


def get(client: httpx.Client, url: str, expected: int = 200) -> dict | list | None:
    r = client.get(url)
    if r.status_code != expected:
        fail(f"GET {url}", f"HTTP {r.status_code}: {r.text[:120]}")
        return None
    return r.json()


def post(client: httpx.Client, url: str, json: dict, expected: int = 200) -> dict | None:
    r = client.post(url, json=json)
    if r.status_code != expected:
        fail(f"POST {url}", f"HTTP {r.status_code}: {r.text[:200]}")
        return None
    return r.json()


def patch(client: httpx.Client, url: str, json: dict, expected: int = 200) -> dict | None:
    r = client.patch(url, json=json)
    if r.status_code != expected:
        fail(f"PATCH {url}", f"HTTP {r.status_code}: {r.text[:200]}")
        return None
    return r.json()


def login(base_url: str, username: str, password: str) -> httpx.Client | None:
    """Return an authenticated httpx client."""
    client = httpx.Client(base_url=base_url, timeout=15)
    resp = client.post("/auth/login", json={"username": username, "password": password})
    if resp.status_code != 200:
        fail(f"Login {username}", f"HTTP {resp.status_code}: {resp.text[:120]}")
        return None
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    ok(f"Logged in as {username!r}")
    return client


# ──────────────────────────────────────────────────────────────────

def main(base_url: str):
    print(f"\n{BOLD}Goti11 API End-to-End Test{NC}")
    print(f"  Target: {base_url}\n")

    # ── health ────────────────────────────────────────────────────
    section("0. Health check")
    r = httpx.get(f"{base_url}/health")
    check("Backend is up", r.status_code == 200, r.text)

    # ── login ─────────────────────────────────────────────────────
    section("1. Authentication")
    admin   = login(base_url, "admin",     "admin123")
    user1   = login(base_url, "testuser1", "pass1123")
    user2   = login(base_url, "testuser2", "pass2123")
    user3   = login(base_url, "testuser3", "pass3123")

    if not all([admin, user1, user2, user3]):
        print(f"\n{RED}Cannot continue without all logins.{NC}")
        sys.exit(1)

    # verify /auth/me
    me = get(admin, "/auth/me")
    check("/auth/me returns admin", me and me.get("is_admin") is True, str(me))

    # ── series ────────────────────────────────────────────────────
    section("2. Series")
    series_list = get(user1, "/series")
    check("List series returns results", bool(series_list), str(series_list))

    # find seeded series
    series = next((s for s in (series_list or []) if "[SEED]" in s["name"]), None)
    check("Seeded series found", series is not None, series["name"] if series else "not found")
    if not series:
        print(f"{RED}Seeded data not found. Run: .venv/bin/python scripts/seed.py{NC}")
        sys.exit(1)

    series_id = series["id"]
    ok(f"Series ID: {series_id}")

    # ── matches ───────────────────────────────────────────────────
    section("3. Matches")
    matches = get(user1, f"/matches?series_id={series_id}")
    check("List matches for series", bool(matches), str(matches))

    match = next((m for m in (matches or []) if "[SEED]" in m["name"]), None)
    check("Seeded match found", match is not None)
    if not match:
        sys.exit(1)

    match_id = match["id"]
    ok(f"Match ID: {match_id} | Status: {match['status']}")
    check("Match status is squad_synced", match["status"] == "squad_synced",
          f"got '{match['status']}'")

    # ── squad ─────────────────────────────────────────────────────
    section("4. Squad")
    squad = get(user1, f"/matches/{match_id}/squad")
    check("Squad returned", bool(squad), f"{len(squad) if squad else 0} players")
    if not squad:
        sys.exit(1)
    check("22 players in squad", len(squad) == 22, f"got {len(squad)}")

    # organise by team
    mi_players  = [p for p in squad if p["team_name"] == "Mumbai Indians"]
    csk_players = [p for p in squad if p["team_name"] == "Chennai Super Kings"]
    ok(f"MI: {len(mi_players)} players, CSK: {len(csk_players)} players")

    # helper: find player by name substring
    # squad entries are MatchPlayerResponse: {player_id, match_id, team_name, credit_value, is_playing, player: {name,...}}
    def find(name_substr: str):
        return next((p for p in squad if name_substr.lower() in p["player"]["name"].lower()), None)

    # ── team selection ────────────────────────────────────────────
    section("5. Team selection")

    # --- team compositions (all meet: 11 players, ≤100 credits, role minimums, ≤7 from one team) ---
    # Credits in seed: Ishan 9.5, Rohit 10, Surya 10, Tilak 8.5, Hardik 10, Tim 8, Romario 7.5,
    #   Bumrah 10, Coetzee 8, Chawla 7, Thushara 7 (MI total 95)
    #   Dhoni 9, Ruturaj 9.5, Conway 9, Rahane 7.5, Dube 8.5, Jadeja 9.5, Moeen 8,
    #   Deepak 8, Tushar 7.5, Pathirana 8.5, Mustafizur 7.5 (CSK total 92)
    #
    # User1: MI-heavy  → 6 MI + 5 CSK   credits = 9.5+10+10+8.5+7.5+10+9.5+8.5+10+8+8.5 = 100.0
    # User2: CSK-heavy → 4 MI + 7 CSK   credits = 9.5+10+9.5+8.5+9+9.5+9+7.5+9.5+8+8.5 = 98.5
    # User3: Balanced  → 6 MI + 5 CSK   credits = 9.5+10+9.5+10+10+9.5+8.5+10+8+7.5+7 = 99.5

    def pick_ids(names):
        players = [find(n) for n in names]
        missing = [n for n, p in zip(names, players) if p is None]
        if missing:
            fail("Player lookup", f"not found: {missing}")
        return [p["player_id"] for p in players if p]

    team1_names = [
        # MI (6): wk + 3 bat + 1 ar + 1 bowl
        "Ishan Kishan",      # wk  9.5  MI
        "Rohit Sharma",      # bat 10.0  MI  ← CAPTAIN
        "Suryakumar Yadav",  # bat 10.0  MI
        "Tilak Varma",       # bat  8.5  MI
        "Hardik Pandya",     # ar  10.0  MI
        "Jasprit Bumrah",    # bowl 10.0 MI  ← VC
        # CSK (5): 1 bat + 2 ar + 2 bowl
        "Ajinkya Rahane",    # bat  7.5  CSK
        "Ravindra Jadeja",   # ar   9.5  CSK
        "Shivam Dube",       # ar   8.5  CSK
        "Deepak Chahar",     # bowl 8.0  CSK
        "Mathesha Pathirana",# bowl 8.5  CSK
        # Total credits: 9.5+10+10+8.5+10+10+7.5+9.5+8.5+8+8.5 = 100.0
    ]
    team2_names = [
        # CSK (7): wk + 3 bat + 2 ar + 1 bowl
        "MS Dhoni",           # wk   9.0  CSK  ← VC
        "Ruturaj Gaikwad",    # bat  9.5  CSK
        "Devon Conway",       # bat  9.0  CSK
        "Ravindra Jadeja",    # ar   9.5  CSK  ← CAPTAIN
        "Moeen Ali",          # ar   8.0  CSK
        "Deepak Chahar",      # bowl 8.0  CSK
        "Mathesha Pathirana", # bowl 8.5  CSK
        # MI (4): 1 bat + 1 ar + 2 bowl
        "Tilak Varma",        # bat  8.5  MI
        "Hardik Pandya",      # ar  10.0  MI
        "Jasprit Bumrah",     # bowl 10.0 MI
        "Nuwan Thushara",     # bowl  7.0 MI
        # Total credits: 9+9.5+9+9.5+8+8+8.5+8.5+10+10+7 = 97.0
    ]
    team3_names = [
        # MI (6): wk + 3 bat + 1 ar + 2 bowl
        "Ishan Kishan",      # wk   9.5  MI
        "Rohit Sharma",      # bat 10.0  MI
        "Suryakumar Yadav",  # bat 10.0  MI
        "Hardik Pandya",     # ar  10.0  MI  ← CAPTAIN
        "Jasprit Bumrah",    # bowl 10.0 MI
        "Nuwan Thushara",    # bowl  7.0 MI
        # CSK (5): 1 bat + 2 ar + 2 bowl
        "Ruturaj Gaikwad",   # bat  9.5  CSK  ← VC
        "Ravindra Jadeja",   # ar   9.5  CSK
        "Shivam Dube",       # ar   8.5  CSK
        "Deepak Chahar",     # bowl 8.0  CSK
        "Mustafizur Rahman", # bowl 7.5  CSK
        # Total credits: 9.5+10+10+10+10+7+9.5+9.5+8.5+8+7.5 = 99.5
    ]

    def submit_team(client, client_name, names, captain_name, vc_name):
        ids = pick_ids(names)
        cap = find(captain_name)
        vc  = find(vc_name)
        if len(ids) != 11 or not cap or not vc:
            fail(f"Team build for {client_name}", "player lookup failed")
            return None
        body = {
            "player_ids": ids,
            "captain_id": cap["player_id"],
            "vice_captain_id": vc["player_id"],
        }
        result = post(client, f"/matches/{match_id}/my-team", body, expected=201)
        if result:
            ok(f"{client_name} team submitted", f"captain={captain_name}")
        return result

    t1 = submit_team(user1, "testuser1", team1_names, "Rohit Sharma",     "Jasprit Bumrah")
    t2 = submit_team(user2, "testuser2", team2_names, "Ravindra Jadeja",  "MS Dhoni")
    t3 = submit_team(user3, "testuser3", team3_names, "Hardik Pandya",    "Ruturaj Gaikwad")

    # verify team retrieval
    my_team = get(user1, f"/matches/{match_id}/my-team")
    check("User1 can retrieve own team", my_team is not None and len(my_team.get("players", [])) == 11)

    # verify admin can see all teams
    all_teams = get(admin, f"/matches/{match_id}/teams")
    check("Admin sees all 3 teams", all_teams is not None and len(all_teams) == 3,
          f"got {len(all_teams) if all_teams else 0}")

    # ── score overrides ───────────────────────────────────────────
    section("6. Scoring — admin overrides")

    # Realistic scorecard:
    # Rohit:       75 runs, 2 fours, 3 sixes → 75 + 2 + 6 + 8(50-bonus) = 91 pts
    # Suryakumar:  55 runs, 4 fours, 2 sixes → 55 + 4 + 4 + 8 = 71 pts
    # Hardik:      35 runs, 1 six, 2 wickets  → 35 + 2 + 50 = 87 pts
    # Jadeja:      48 runs, 3 wkts, 1 maiden  → 48 + 75 + 12 = 135 pts
    # Bumrah:      4 wickets                  → 100 + 8(4wk) = 108 pts
    # Ruturaj:     62 runs, 2 fours, 1 six    → 62 + 2 + 2 + 8 = 74 pts
    # Dhoni:       35 runs, 2 catches         → 35 + 16 = 51 pts
    # Deepak Chahar: 3 wickets               → 75 pts
    # Others: 0

    overrides = {
        "Rohit Sharma":       91,
        "Suryakumar Yadav":   71,
        "Hardik Pandya":      87,
        "Ravindra Jadeja":   135,
        "Jasprit Bumrah":    108,
        "Ruturaj Gaikwad":    74,
        "MS Dhoni":           51,
        "Deepak Chahar":      75,
        "Ishan Kishan":        8,
        "Devon Conway":       20,
        "Tilak Varma":        12,
        "Ajinkya Rahane":     15,
        "Shivam Dube":        22,
        "Moeen Ali":          10,
        "Mustafizur Rahman":  30,
        "Mathesha Pathirana": 20,
        "Nuwan Thushara":     15,
        "Tim David":           5,
    }

    for player_name, pts in overrides.items():
        mp = find(player_name)
        if mp is None:
            continue
        r = admin.patch(
            f"/matches/{match_id}/override-score",
            json={"player_id": mp["player_id"], "override_points": pts},
        )
        if r.status_code == 200:
            ok(f"Override: {player_name}", f"{pts} pts")
        else:
            fail(f"Override: {player_name}", f"HTTP {r.status_code}: {r.text[:80]}")

    # ── propagate scores to teams ─────────────────────────────────
    section("7. Propagate scores → user teams")

    # The score_sync endpoint is for CricAPI. We need to manually propagate
    # via the DB since we used override_points. Use a direct helper call.
    _propagate_scores(base_url, match_id, squad, overrides, admin)

    # ── finalize ──────────────────────────────────────────────────
    section("8. Finalize match")
    fin = post(admin, f"/matches/{match_id}/finalize", {})
    check("Match finalized", fin is not None, str(fin))

    # Verify match status
    m = get(user1, f"/matches/{match_id}")
    check("Match status = completed", m and m.get("status") == "completed",
          f"got '{m.get('status') if m else 'N/A'}'")

    # ── leaderboard ───────────────────────────────────────────────
    section("9. Match leaderboard")
    lb = get(user1, f"/matches/{match_id}/leaderboard")
    check("Leaderboard returned", bool(lb), f"{len(lb) if lb else 0} entries")
    if lb:
        print(f"\n  {'Rank':<6} {'Username':<15} {'Points':>8} {'Prize':>8} {'Captain':<20}")
        print(f"  {'─'*60}")
        for e in lb:
            print(f"  {e['rank']:<6} {e['username']:<15} {e['total_points']:>8} "
                  f"{e['prize_awarded']:>8} {e['captain_name']:<20}")

    # ── series leaderboard ────────────────────────────────────────
    section("10. Series leaderboard")
    slb = get(user1, f"/series/{series_id}/leaderboard")
    check("Series leaderboard returned", bool(slb), f"{len(slb) if slb else 0} entries")
    if slb:
        print(f"\n  {'Rank':<6} {'Username':<15} {'Fantasy Pts':>12} {'Prize':>8} {'Matches':>8}")
        print(f"  {'─'*55}")
        for e in slb[:5]:
            print(f"  {e['rank']:<6} {e['username']:<15} {e['fantasy_points']:>12} "
                  f"{e['prize_awarded']:>8} {e['matches_played']:>8}")

    # ── my history ────────────────────────────────────────────────
    section("11. User match history")
    hist = get(user1, f"/series/{series_id}/my-history")
    check("User1 history returned", hist is not None, f"{len(hist) if hist else 0} entries")
    if hist:
        for h in hist:
            ok(f"  Match: {h['match_name']}", f"pts={h['total_points']} rank={h['rank']} prize={h['prize_awarded']}")

    # ── prize points ──────────────────────────────────────────────
    section("12. Prize point totals")
    for name, client in [("testuser1", user1), ("testuser2", user2), ("testuser3", user3)]:
        me_data = get(client, "/auth/me")
        if me_data:
            ok(f"{name}", f"prize_points = {me_data.get('prize_points', 'N/A')}")

    # ── summary ───────────────────────────────────────────────────
    total = PASS + FAIL
    print(f"\n{'─'*55}")
    print(f"{BOLD}Results: {GREEN}{PASS} passed{NC}{BOLD}, {RED}{FAIL} failed{NC}{BOLD} / {total} total{NC}\n")

    sys.exit(0 if FAIL == 0 else 1)


# ─────────────────────────────────────────────────────────────────
# Helper: propagate override_points → user_team totals
# ─────────────────────────────────────────────────────────────────

def _propagate_scores(base_url: str, match_id: str, squad: list, overrides: dict, admin: httpx.Client):
    """
    The regular sync-score endpoint hits CricAPI. Since we've done manual
    overrides, we call a small direct-DB propagation via a seeds helper.
    We do this by importing the app directly (same process, same venv).
    """
    try:
        import os, sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

        from decimal import Decimal
        from app.database import SessionLocal
        from app.models.scoring import PlayerMatchScore
        from app.models.team import UserTeam, UserTeamPlayer
        from app.models.player import Player
        from app.services.rules_engine import apply_multipliers_and_total
        import uuid

        db = SessionLocal()
        mid = uuid.UUID(match_id)

        # Re-read scores and propagate
        user_teams = db.query(UserTeam).filter(UserTeam.match_id == mid).all()
        for team in user_teams:
            for utp in team.players:
                score = (
                    db.query(PlayerMatchScore)
                    .filter(PlayerMatchScore.match_id == mid, PlayerMatchScore.player_id == utp.player_id)
                    .first()
                )
                if score:
                    utp.points_earned = score.effective_points
                else:
                    utp.points_earned = Decimal("0")
            apply_multipliers_and_total(team)

        db.commit()
        db.close()
        ok("Scores propagated to user teams (direct DB)")

    except Exception as e:
        fail("Score propagation", str(e))
        import traceback; traceback.print_exc()


# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    args = parser.parse_args()
    main(args.base_url)
