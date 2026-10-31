#!/usr/bin/env python3
"""Deterministic grain probe for the 12th Man pipeline (docs/15_grain_audit.md).

Builds a tiny in-memory DuckDB with known blank/double-GW structure and runs the
SHARED PANEL_SQL (extracted verbatim from scripts/fit-12thman-model.py, the same
string used by the backtests and the prospective runner) plus the row-window rule
used by the docs/14 low-minutes evaluation. Prints intended vs actual side by
side. This probe DOCUMENTS current behavior; it is not a pass/fail gate and
changes nothing.

Mini league (season 2025-26): ALPHA (3 players: 1,2,3), BETA (player 11),
GAMMA (player 21). Every fixture: home team wins 2-1 (each team concedes 1 per
fixture). All players play 90 minutes in every fixture, 5 points each.
  GW1: ALPHA(H) vs BETA
  GW2: ALPHA(H) vs BETA  AND  ALPHA(A) vs GAMMA   <- ALPHA double GW
  GW3: ALPHA(H) vs BETA
  GW4: ALPHA blank (no fixture; ALPHA players absent) ; BETA(H) vs GAMMA
  GW5: ALPHA(H) vs BETA
  GW6: ALPHA(H) vs BETA   <- evaluation GW
Run: python3 tests/grain_probe.py
"""
import re, duckdb, os

HERE = os.path.dirname(os.path.abspath(__file__))
fit_src = open(os.path.join(HERE, '..', 'scripts', 'fit-12thman-model.py')).read()
PANEL_SQL = re.search(r'PANEL_SQL = """(.*?)"""', fit_src, re.S).group(1)
assert "2025-26" in PANEL_SQL  # mini league uses that season label; no patch needed

con = duckdb.connect()
con.execute("""CREATE TABLE epl_fpl_gameweeks(season VARCHAR, gw BIGINT, player_id BIGINT,
  position VARCHAR, team VARCHAR, minutes BIGINT, total_points BIGINT,
  expected_goal_involvements DOUBLE, was_home BOOLEAN, team_a_score BIGINT,
  team_h_score BIGINT, opponent_team_id BIGINT)""")
con.execute("CREATE TABLE epl_teams(season VARCHAR, team_id BIGINT, name VARCHAR)")
for tid, nm in [(1, 'ALPHA'), (2, 'BETA'), (3, 'GAMMA')]:
    con.execute("INSERT INTO epl_teams VALUES ('2025-26', ?, ?)", [tid, nm])

ALPHA = [1, 2, 3]
def fixture(gw, home_tid, home_nm, away_tid, away_nm, home_players, away_players):
    hs, as_ = 2, 1  # home 2-1 away: each side concedes a known number
    for pid in home_players:
        con.execute("INSERT INTO epl_fpl_gameweeks VALUES ('2025-26',?,?,?,?,?,?,?,?,?,?,?)",
                    [gw, pid, 'MID', home_nm, 90, 5, 0.5, True, as_, hs, away_tid])
    for pid in away_players:
        con.execute("INSERT INTO epl_fpl_gameweeks VALUES ('2025-26',?,?,?,?,?,?,?,?,?,?,?)",
                    [gw, pid, 'MID', away_nm, 90, 5, 0.5, False, as_, hs, home_tid])

fixture(1, 1, 'ALPHA', 2, 'BETA', ALPHA, [11])
fixture(2, 1, 'ALPHA', 2, 'BETA', ALPHA, [11])   # ALPHA double GW, fixture 1
fixture(2, 3, 'GAMMA', 1, 'ALPHA', [21], ALPHA)  # ALPHA double GW, fixture 2 (away)
fixture(3, 1, 'ALPHA', 2, 'BETA', ALPHA, [11])
# GW4: ALPHA blank - no ALPHA rows. BETA(H) vs GAMMA still plays.
fixture(4, 2, 'BETA', 3, 'GAMMA', [11], [21])
fixture(5, 1, 'ALPHA', 2, 'BETA', ALPHA, [11])
fixture(6, 1, 'ALPHA', 2, 'BETA', ALPHA, [11])

print("=== raw rows for ALPHA player 1 ===")
for r in con.execute("SELECT gw, minutes, total_points FROM epl_fpl_gameweeks WHERE player_id=1 ORDER BY gw").fetchall():
    print("  gw", r[0], "mins", r[1], "pts", r[2])
print("  note: GW2 appears TWICE (double), GW4 absent (blank)")

print("\n=== PANEL_SQL output at GW6 (k=6) ===")
df = con.execute(PANEL_SQL).fetchdf()
print(df[df.k == 6].to_string(index=False))

a1 = df[(df.k == 6) & (df.player_id == 1)]
print("\n--- intended vs actual, ALPHA player 1 at GW6 ---")
print("intended: eligible. Trailing calendar GWs 2,3,4,5: played 3 (double in GW2, blank GW4),")
print("  trailing minutes 360 (4 fixtures x 90), trailing mean pts 5.0.")
if len(a1) == 0:
    print("actual: EXCLUDED from panel (no row at k=6). Reason below.")
else:
    print("actual:", a1.iloc[0].to_dict())
nrows = con.execute("""
  WITH grid AS (SELECT season, gw::INT AS gw, player_id, SUM(minutes) mins
    FROM epl_fpl_gameweeks GROUP BY season, gw, player_id),
  w AS (SELECT gw, COUNT(*) OVER (PARTITION BY player_id ORDER BY gw
      RANGE BETWEEN 4 PRECEDING AND 1 PRECEDING) AS n4
    FROM grid WHERE player_id=1)
  SELECT n4 FROM w WHERE gw=6""").fetchone()[0]
print(f"  nrows4 (aggregated grid, calendar window) = {nrows} -> panel requires 4, has {nrows}: "
      "a BLANK GW in the trailing 4 makes the player panel-ineligible even though he played 3 of 4 GWs.")

print("\n--- opponent-strength units (teamgw conceded) ---")
row = con.execute("""
  SELECT team, gw, SUM(CASE WHEN was_home THEN team_a_score ELSE team_h_score END) AS conceded_rowsum,
         COUNT(DISTINCT opponent_team_id) AS nfix, COUNT(*) AS n_player_rows
  FROM epl_fpl_gameweeks WHERE gw=1 GROUP BY team, gw ORDER BY team""").fetchall()
for t in row:
    print(f"  {t[0]} GW1: row-sum conceded={t[2]}, nfix={t[3]}, player_rows={t[4]}")
print("  intended: goals conceded per fixture (ALPHA GW1: 1).")
print("  actual PANEL_SQL: conceded/nfix = row-sum / nfix = player_rows x goals / nfix")
print("  (ALPHA GW1: 3/1 = 3; BETA GW1: 1/1 = 1) - the feature is scaled by how many")
print("  of the team's players have rows, and by fixture count only via DISTINCT opponents.")

print("\n--- row-window (docs/14 eval rule) vs calendar window on raw rows ---")
r = con.execute("""
  SELECT gw, minutes,
    COALESCE(SUM(minutes) OVER (PARTITION BY player_id ORDER BY gw, opponent_team_id
      ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING),0) AS trail_rows,
    COALESCE(SUM(minutes) OVER (PARTITION BY player_id ORDER BY gw
      RANGE BETWEEN 4 PRECEDING AND 1 PRECEDING),0) AS trail_cal
  FROM epl_fpl_gameweeks WHERE player_id=1 ORDER BY gw, opponent_team_id""").fetchall()
print("  gw | mins | trail_4_rows | trail_4_calendar_GWs")
for g, m, tr, tc in r:
    print(f"  {g}  |  {m:3d} |     {tr:3d}      |      {tc:3d}")
print("  note: at GW3 the row-window spans only GWs 1-2 (double counted as 2 of the 4);")
print("  the calendar window over raw rows sums ALL rows in GWs gw-4..gw-1.")
print("\n--- blank GW grain ---")
print("  ALPHA players have NO row at GW4 (blank). This matches the vaastav/fit-DB")
print("  grain: in the real fit DB no team-GW has all-zero minutes, and disrupted GWs")
print("  simply contain fewer teams (2021-22 GW18 and GW30 have 8 of 20 teams).")
print("  Whether the live FPL element-summary history also omits blank rounds is")
print("  UNVERIFIED here; if it does, the live gate's last-4-entries slice stretches")
print("  across blanks exactly like this fixture.")
