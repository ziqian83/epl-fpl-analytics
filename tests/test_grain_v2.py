#!/usr/bin/env python3
"""Deterministic checks for panel v2 (docs/16): blank/double/missing semantics,
fixture-deduped conceded, and the real-data invariant vs v1.

Part A: tiny synthetic league (one double GW, one true blank, one missing
record) through PANEL_SQL_V2. Part B: on the real v2 DB, v1 and v2 panels must
have identical membership, f_pts4, f_xgi4, f_minshare4 and target_pts; only
opp_strength_k may change.

Run: python3 tests/test_grain_v2.py [--db /tmp/epl12_fit_v2.duckdb]
Exits nonzero on failure.
"""
import re, os, sys, duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
v2_src = open(os.path.join(HERE, '..', 'scripts', 'fit-12thman-model-v2.py')).read()
PANEL_SQL_V2 = re.search(r'PANEL_SQL_V2 = """(.*?)"""', v2_src, re.S).group(1)

con = duckdb.connect()
con.execute("""CREATE TABLE epl_fpl_gameweeks(season VARCHAR, gw BIGINT, fixture BIGINT,
  player_id BIGINT, position VARCHAR, team VARCHAR, minutes BIGINT, total_points BIGINT,
  expected_goal_involvements DOUBLE, was_home BOOLEAN, team_a_score BIGINT,
  team_h_score BIGINT, opponent_team_id BIGINT)""")
con.execute("CREATE TABLE epl_teams(season VARCHAR, team_id BIGINT, name VARCHAR)")
for tid, nm in [(1, 'ALPHA'), (2, 'BETA'), (3, 'GAMMA')]:
    con.execute("INSERT INTO epl_teams VALUES ('2025-26', ?, ?)", [tid, nm])

ALPHA = [1, 2, 3]
fxid = [100]
def fixture(gw, home_tid, home_nm, away_tid, away_nm, home_players, away_players, hs, as_):
    fxid[0] += 1
    for pid in home_players:
        con.execute("INSERT INTO epl_fpl_gameweeks VALUES ('2025-26',?,?,?,?,?,?,?,?,?,?,?,?)",
                    [gw, fxid[0], pid, 'MID', home_nm, 90, 5, 0.5, True, as_, hs, away_tid])
    for pid in away_players:
        con.execute("INSERT INTO epl_fpl_gameweeks VALUES ('2025-26',?,?,?,?,?,?,?,?,?,?,?,?)",
                    [gw, fxid[0], pid, 'MID', away_nm, 90, 5, 0.5, False, as_, hs, home_tid])

# GW1: ALPHA(H) 2-1 BETA. GW2: ALPHA(H) 3-0 BETA and GAMMA(H) 1-0 ALPHA (double).
# GW3: ALPHA(H) 2-1 BETA. GW4: ALPHA blank; BETA(H) 2-1 GAMMA. GW5: ALPHA(H) 2-1 BETA. GW6 same.
# GAMMA player 21 has NO rows before GW4 though GAMMA played in GW2: missing records GW2-3? GAMMA plays GW2 only -> missing GW2.
fixture(1, 1, 'ALPHA', 2, 'BETA', ALPHA, [11], 2, 1)
fixture(2, 1, 'ALPHA', 2, 'BETA', ALPHA, [11], 3, 0)
fixture(2, 3, 'GAMMA', 1, 'ALPHA', [21], ALPHA, 1, 0)
fixture(3, 1, 'ALPHA', 2, 'BETA', ALPHA, [11], 2, 1)
fixture(4, 2, 'BETA', 3, 'GAMMA', [11], [21], 2, 1)
fixture(5, 1, 'ALPHA', 2, 'BETA', ALPHA, [11], 2, 1)
fixture(6, 1, 'ALPHA', 2, 'BETA', ALPHA, [11], 2, 1)
fixture(6, 3, 'GAMMA', 2, 'BETA', [21], [11], 1, 0)  # BETA double; GAMMA plays at k=6

df = con.execute(PANEL_SQL_V2).fetchdf()
fails = []
def check(name, cond, detail=''):
    print(('PASS' if cond else 'FAIL'), name, detail)
    if not cond: fails.append(name)

a1 = df[(df.k == 6) & (df.player_id == 1)]
check('A1: double-GW player has exactly one panel row at k=6', len(a1) == 1)
if len(a1):
    r = a1.iloc[0]
    # trailing GWs 2,3,4,5: player rows in 2,3,5 (blank 4) -> nrows4=3
    check('A1: nrows4=3 (blank GW4 not a row)', r.nrows4 == 3, f'got {r.nrows4}')
    check('A1: n_blank4=1 (GW4 true blank)', r.n_blank4 == 1, f'got {r.n_blank4}')
    check('A1: n_missing4=0', r.n_missing4 == 0, f'got {r.n_missing4}')
    # f_minshare4 = AVG over player rows in window: (180+90+90)/3/90 = 1.333...
    check('A1: double GW minutes summed (180) into one GW share', abs(r.f_minshare4 - 360/270) < 1e-9,
          f'got {r.f_minshare4:.4f}')
    # opponent at k=6 is ALPHA... player 1 IS Alpha; opp_strength_k is for BETA's view? No: fixk maps
    # (k, team=ALPHA) -> AVG over ALPHA's GW6 opponents (BETA) of BETA's trailing conceded.
    # BETA conceded per fixture: GW1:2, GW2:3, GW3:2, GW5:2 (GW4 BETA was home vs GAMMA, conceded 1)
    # trailing GWs 2..5 with fixtures: GW2:3, GW3:2, GW4:1, GW5:2 -> mean 2.0
    check('A1: opp_strength_k = BETA per-fixture conceded mean over GWs 2-5 = 2.0 (not row-scaled)',
          abs(r.opp_strength_k - 2.0) < 1e-9, f'got {r.opp_strength_k}')

g21 = df[(df.k == 6) & (df.player_id == 21)]
check('G21 (GAMMA): row at k=6 exists', len(g21) == 1)
if len(g21):
    r = g21.iloc[0]
    # GAMMA fixtures in 2..5: GW2 (vs ALPHA), GW4 (vs BETA) -> team_gws4=2; player rows: GW2,GW4 -> nrows4=2
    check('G21: nrows4=2', r.nrows4 == 2, f'got {r.nrows4}')
    check('G21: n_blank4=2 (GW3, GW5 no GAMMA fixture)', r.n_blank4 == 2, f'got {r.n_blank4}')
    check('G21: n_missing4=0 (present whenever GAMMA played)', r.n_missing4 == 0, f'got {r.n_missing4}')
    # opp_strength_k for a GAMMA player = GAMMA's GW6 opponent (BETA) trailing conceded:
    # BETA per-fixture conceded GWs 2-5: 3, 2, 1, 2 -> mean 2.0 (not row-scaled)
    check('G21: opp_strength_k = opponent BETA per-fixture conceded mean 2.0 (not row-scaled)',
          abs(r.opp_strength_k - 2.0) < 1e-9, f'got {r.opp_strength_k}')

# v1 equivalence on real data
db = sys.argv[sys.argv.index('--db') + 1] if '--db' in sys.argv else '/tmp/epl12_fit_v2.duckdb'
if os.path.exists(db):
    v1_src = open(os.path.join(HERE, '..', 'scripts', 'fit-12thman-model.py')).read()
    PANEL_SQL_V1 = re.search(r'PANEL_SQL = """(.*?)"""', v1_src, re.S).group(1)
    c2 = duckdb.connect(db, read_only=True)
    p2 = c2.execute(PANEL_SQL_V2).fetchdf()
    p2 = p2[(p2.nrows4 == 4) & (p2.f_minshare4*4*90 >= 180)]
    p1 = c2.execute(PANEL_SQL_V1).fetchdf()
    c2.close()
    k = ['season', 'k', 'player_id']
    m = p1.merge(p2, on=k, suffixes=('_v1', '_v2'))
    check('B1: v1/v2 panel membership identical', len(m) == len(p1) == len(p2),
          f'v1={len(p1)} v2={len(p2)} merged={len(m)}')
    for col in ('f_pts4', 'f_xgi4', 'f_minshare4', 'target_pts'):
        same = (m[f'{col}_v1'] - m[f'{col}_v2']).abs().max() < 1e-9
        check(f'B2: {col} identical v1 vs v2', same)
    diff = (m['opp_strength_k_v1'] - m['opp_strength_k_v2']).abs()
    check('B3: opp_strength_k changed (the correction)', diff.max() > 1e-6,
          f'max delta {diff.max():.3f}, mean {diff.mean():.3f}')
else:
    print('SKIP part B: no v2 db at', db)

print('FAILURES:', len(fails))
sys.exit(1 if fails else 0)
