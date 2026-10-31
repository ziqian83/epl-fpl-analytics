#!/usr/bin/env python3
"""The 12th Man - PANEL V2: corrected grain and opponent-strength units (docs/16).

Versioned correction of the defects found in the 31 Oct grain audit (docs/15).
v1 (fit-12thman-model.py) is frozen and unchanged; this v2 exists alongside it.
Per docs/16, v2 does NOT feed live advice without its own prospective evidence.

Corrections vs v1:
 1. Fixture-level conceded: v1's teamgw summed per-PLAYER-row fixture scores and
    divided by COUNT(DISTINCT opponent), scaling the feature by how many of the
    team's players had rows. v2 dedupes to one row per (season, fixture, team)
    FIRST - fixture identity from the vaastav `fixture` column (verified: scores
    consistent within fixture, 2 teams per fixture, ids never span GWs, max 2
    fixtures per team-GW, all 5 cached seasons) - then averages per fixture.
    NOTE: team_h_score/team_a_score are fixture final scores; the per-player
    `goals_conceded` column is a different, player-on-pitch stat and is NOT used.
 2. Explicit blank/missing semantics: trailing windows are CALENDAR GWs
    (RANGE 4 PRECEDING..1 PRECEDING) over the canonical player-GW grid.
    n_blank4 = trailing calendar GWs (of the expected 4, pro-rated before GW5)
    where the player's TEAM had no fixture (true scheduled blank, from the
    fixture table). n_missing4 = GWs where the team had a fixture but the
    player has no record (vaastav 2025-26: 371/841 players have such in-span
    gaps). Eligibility is UNCHANGED in outcome from v1 (nrows4 = 4 distinct GWs
    with a player record AND >= 180 trailing minutes), but the exclusion reason
    is now recorded. Opponent trailing conceded averages over the opponent's
    GWs WITH a fixture (true blanks shorten the divisor, n_gws4 recorded).
 3. Shared aggregation: the grid + fixture CTEs below are the single canonical
    definition for future consumers (docs/16, C1).

Invariant vs v1 (checked by tests/test_grain_v2.py on real data): identical
panel membership and identical f_pts4/f_xgi4/f_minshare4/target_pts; ONLY
opp_strength_k values change.

Data: same cached vaastav CSVs as v1 (.fit-cache, hashes printed by
print_freeze), keeping the `fixture` column v1 dropped. DB built at
/tmp/epl12_fit_v2.duckdb (v1's /tmp/epl12_fit.duckdb untouched).

Run: python3 scripts/fit-12thman-model-v2.py [--db /tmp/epl12_fit_v2.duckdb]
"""
import argparse, os
import duckdb, numpy as np, pandas as pd

SEASONS = ['2021-22', '2022-23', '2023-24', '2024-25', '2025-26']

def build_db(dbpath, cache='./.fit-cache'):
    con = duckdb.connect(dbpath)
    done = con.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='epl_fpl_gameweeks'").fetchone()[0]
    if done:
        con.close(); return
    frames, teams = [], []
    for s in SEASONS:
        gw = pd.read_csv(f'{cache}/{s}-merged_gw.csv', low_memory=False)
        gw['season'] = s
        frames.append(gw)
        t = pd.read_csv(f'{cache}/{s}-teams.csv')
        t['season'] = s
        teams.append(t[['season', 'id', 'name']].rename(columns={'id': 'team_id'}))
    gw = pd.concat(frames, ignore_index=True)
    gw = gw.rename(columns={'GW': 'gw', 'element': 'player_id', 'opponent_team': 'opponent_team_id'})
    keep = ['season', 'gw', 'fixture', 'player_id', 'position', 'team', 'minutes', 'total_points',
            'expected_goal_involvements', 'was_home', 'team_a_score', 'team_h_score', 'opponent_team_id']
    con.register('gw_stage', gw[keep])
    con.execute('CREATE TABLE epl_fpl_gameweeks AS SELECT * FROM gw_stage')
    con.register('teams_stage', pd.concat(teams, ignore_index=True))
    con.execute('CREATE TABLE epl_teams AS SELECT * FROM teams_stage')
    # build-time fixture integrity assertions (fail loudly, not silently)
    bad = con.execute("""SELECT COUNT(*) FROM (SELECT season, fixture FROM epl_fpl_gameweeks
        GROUP BY season, fixture HAVING COUNT(DISTINCT (team_h_score, team_a_score)) > 1
        OR COUNT(DISTINCT team) <> 2)""").fetchone()[0]
    assert bad == 0, f'fixture integrity violated in {bad} fixtures'
    con.close()
    print('db built:', dbpath)

PANEL_SQL_V2 = """
WITH grid AS (
  SELECT season, gw::INT AS gw, player_id,
         MAX(CASE WHEN position='GK' THEN 'GKP' ELSE position END) AS position, MAX(team) AS team,
         SUM(minutes)::DOUBLE AS mins, SUM(total_points)::DOUBLE AS pts,
         SUM(COALESCE(expected_goal_involvements,0)) AS xgi,
         COUNT(DISTINCT fixture) AS nfix
  FROM epl_fpl_gameweeks
  WHERE season IN ('2021-22','2022-23','2023-24','2024-25','2025-26')
    AND position IN ('GKP','GK','DEF','MID','FWD')
  GROUP BY season, gw, player_id
),
fx AS (  -- one row per (fixture, team): fixture identity from the source fixture id
  SELECT DISTINCT season, gw::INT AS gw, fixture, team, was_home, team_h_score, team_a_score
  FROM epl_fpl_gameweeks
  WHERE season IN ('2021-22','2022-23','2023-24','2024-25','2025-26')
),
fxc AS (  -- conceded from the fixture's final score, not from any player stat
  SELECT season, gw, fixture, team,
         (CASE WHEN was_home THEN team_a_score ELSE team_h_score END)::DOUBLE AS conceded
  FROM fx
),
teamgw AS (  -- per calendar GW: mean conceded across the team's fixtures (1 or 2)
  SELECT season, gw, team, AVG(conceded) AS conceded_per_fx, COUNT(*) AS nfix
  FROM fxc GROUP BY season, gw, team
),
teamstr AS (  -- trailing calendar-4-GW mean over the opponent's GWs WITH a fixture
  SELECT season, gw, team AS opp_team,
         AVG(conceded_per_fx) OVER w AS opp_gc4,
         COUNT(*) OVER w AS n_gws4
  FROM teamgw
  WINDOW w AS (PARTITION BY season, team ORDER BY gw RANGE BETWEEN 4 PRECEDING AND 1 PRECEDING)
),
fixk AS (
  SELECT g.season, g.gw::INT AS k, g.team, AVG(s.opp_gc4) AS opp_strength_k
  FROM (SELECT DISTINCT season, gw, team, opponent_team_id FROM epl_fpl_gameweeks) g
  JOIN epl_teams tn ON tn.season=g.season AND tn.team_id=g.opponent_team_id
  JOIN teamstr s ON s.season=g.season AND s.gw=g.gw AND s.opp_team=tn.name
  GROUP BY g.season, g.gw, g.team
),
teamwin AS (  -- trailing calendar GWs in which the team had ANY fixture
  SELECT t1.season, t1.gw::INT AS k, t1.team, COUNT(t2.gw) AS team_gws4
  FROM (SELECT DISTINCT season, gw, team FROM fx) t1
  LEFT JOIN (SELECT DISTINCT season, gw, team FROM fx) t2
    ON t2.season=t1.season AND t2.team=t1.team AND t2.gw BETWEEN t1.gw-4 AND t1.gw-1
  GROUP BY t1.season, t1.gw, t1.team
),
panel AS (
  SELECT g.season, g.gw AS k, g.player_id, g.position, g.team,
         AVG(g.pts)  OVER w AS f_pts4,
         AVG(g.xgi)  OVER w AS f_xgi4,
         AVG(g.mins/90) OVER w AS f_minshare4,
         COUNT(*)    OVER w AS nrows4,
         g.pts AS target_pts,
         f.opp_strength_k, tw.team_gws4
  FROM grid g
  JOIN fixk f ON f.season=g.season AND f.k=g.gw AND f.team=g.team
  JOIN teamwin tw ON tw.season=g.season AND tw.k=g.gw AND tw.team=g.team
  WINDOW w AS (PARTITION BY g.season, g.player_id ORDER BY g.gw RANGE BETWEEN 4 PRECEDING AND 1 PRECEDING)
)
SELECT season, k, player_id, position, team, f_pts4, f_xgi4, f_minshare4, opp_strength_k,
       nrows4, team_gws4,
       LEAST(4, k-1) - team_gws4 AS n_blank4,   -- true scheduled blanks in window
       team_gws4 - nrows4 AS n_missing4,        -- team played, player record absent
       target_pts
FROM panel
WHERE opp_strength_k IS NOT NULL
ORDER BY season, k, position, player_id
"""

ELIGIBILITY = "nrows4 = 4 AND f_minshare4*4*90 >= 180"  # unchanged outcome vs v1

def design(d):
    pos = d.position.map({'GKP': 0, 'DEF': 1, 'MID': 2, 'FWD': 3}).fillna(2).values
    return np.column_stack([np.ones(len(d)), d.f_pts4, d.f_xgi4, d.f_minshare4, d.opp_strength_k,
                            (pos == 0), (pos == 1), (pos == 3)]).astype(float)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='/tmp/epl12_fit_v2.duckdb')
    args = ap.parse_args()
    build_db(args.db)
    con = duckdb.connect(args.db, read_only=True)
    df = con.execute(PANEL_SQL_V2).fetchdf()
    con.close()
    eligible = df[(df.nrows4 == 4) & (df.f_minshare4*4*90 >= 180)].copy()  # ELIGIBILITY
    print('panel rows (pre-eligibility):', len(df), '| eligible:', len(eligible))
    print('exclusion reasons among ineligible: blanks-only',
          int(((df.n_blank4 > 0) & (df.n_missing4 == 0) & (df.nrows4 < 4)).sum()),
          '| missing-records involved', int((df.n_missing4 > 0).sum()),
          '| minutes-only', int(((df.nrows4 == 4) & (df.f_minshare4*4*90 < 180)).sum()))
    df = eligible
    rng = np.random.default_rng(7)
    for testseason, trainseasons in [('2024-25', SEASONS[:3]), ('2025-26', SEASONS[:4])]:
        tr = df[df.season.isin(trainseasons)]; te = df[df.season == testseason].copy()
        coef, *_ = np.linalg.lstsq(design(tr), tr.target_pts.values, rcond=None)
        pred = design(te) @ coef; base = te.f_pts4.values
        print(f'--- V2 test {testseason} (train {len(tr)}, test {len(te)}) coef {np.round(coef, 3)}')
        print('baseline corr %.3f MAE %.3f | model corr %.3f MAE %.3f' % (
            np.corrcoef(base, te.target_pts)[0, 1], np.abs(base - te.target_pts).mean(),
            np.corrcoef(pred, te.target_pts)[0, 1], np.abs(pred - te.target_pts).mean()))
        te['pred'] = pred
        tot_m = cor_m = tot_b = cor_b = 0
        for (k, pos), grp in te.groupby(['k', 'position']):
            n = len(grp)
            if n < 3: continue
            reps = min(300, n * 3)
            a = rng.integers(0, n, reps); b = rng.integers(0, n, reps)
            m = a != b; a, b = a[m], b[m]
            g = grp.reset_index(drop=True)
            pi, pj = g.pred.values[a], g.pred.values[b]
            bi, bj = g.f_pts4.values[a], g.f_pts4.values[b]
            ai, aj = g.target_pts.values[a], g.target_pts.values[b]
            tm = pi != pj; tb = bi != bj
            tot_m += tm.sum(); cor_m += (np.sign(pi - pj)[tm] == np.sign(ai - aj)[tm]).sum()
            tot_b += tb.sum(); cor_b += (np.sign(bi - bj)[tb] == np.sign(ai - aj)[tb]).sum()
        print(f'{testseason}: model pair-acc={cor_m / tot_m:.3f} (n={tot_m})  baseline pair-acc={cor_b / tot_b:.3f} (n={tot_b})')

if __name__ == '__main__':
    main()
