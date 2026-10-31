#!/usr/bin/env python3
"""The 12th Man - reproducible model fit + validation.

Recovered and consolidated 31 Oct 2026 from the 25 Oct 2026 build session, where
the fit ran as inline scripts that were never committed (audit gap). The SQL and
statistics below are the recovered final versions, unchanged; this file adds a
documented, repeatable data path so anyone can rebuild the input and re-run.

Data: public vaastav/Fantasy-Premier-League dataset (official FPL per-player
per-gameweek dumps), fetched from raw.githubusercontent.com. No secrets, no
personal data, no team IDs.

Method (docs/09_12thman_model.md is the narrative):
  OLS, features chosen a priori, no tuning: trailing-4-GW mean points, trailing
  xGI, trailing minutes share, opponent trailing-4 goals conceded, position
  dummies. Canonical player-GW grid sums double-gameweek rows. Eligibility: 4
  prior GW rows and >=180 trailing minutes. Validation: rolling origin by season
  (train on prior seasons, test on the held-out season) plus a same-position
  pairwise ranking test against the persistence baseline.

Run:  python3 scripts/fit-12thman-model.py [--db /tmp/epl12.duckdb]
Deps: duckdb, numpy, pandas.
"""
import argparse, os, sys, urllib.request
import duckdb, numpy as np, pandas as pd

SEASONS = ['2021-22', '2022-23', '2023-24', '2024-25', '2025-26']
RAW = 'https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{season}/{name}'

def fetch(url, path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print('fetch', url, flush=True)
        with urllib.request.urlopen(url, timeout=120) as r, open(path, 'wb') as f:
            f.write(r.read())
    return path

def build_db(dbpath, cache='./.fit-cache'):
    con = duckdb.connect(dbpath)
    done = con.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='epl_fpl_gameweeks'").fetchone()[0]
    if done:
        con.close(); return
    frames, teams = [], []
    for s in SEASONS:
        gw = pd.read_csv(fetch(RAW.format(season=s, name='gws/merged_gw.csv'), f'{cache}/{s}-merged_gw.csv'), low_memory=False)
        gw['season'] = s
        frames.append(gw)
        t = pd.read_csv(fetch(RAW.format(season=s, name='teams.csv'), f'{cache}/{s}-teams.csv'))
        t['season'] = s
        teams.append(t[['season', 'id', 'name']].rename(columns={'id': 'team_id', 'name': 'name'}))
    gw = pd.concat(frames, ignore_index=True)
    gw = gw.rename(columns={'GW': 'gw', 'element': 'player_id', 'opponent_team': 'opponent_team_id'})
    keep = ['season', 'gw', 'player_id', 'position', 'team', 'minutes', 'total_points',
            'expected_goal_involvements', 'was_home', 'team_a_score', 'team_h_score', 'opponent_team_id']
    con.register('gw_stage', gw[keep])
    con.execute('CREATE TABLE epl_fpl_gameweeks AS SELECT * FROM gw_stage')
    con.register('teams_stage', pd.concat(teams, ignore_index=True))
    con.execute('CREATE TABLE epl_teams AS SELECT * FROM teams_stage')
    con.close()
    print('db built:', dbpath)

PANEL_SQL = """
WITH grid AS (
  SELECT season, gw::INT AS gw, player_id,
         MAX(CASE WHEN position='GK' THEN 'GKP' ELSE position END) AS position, MAX(team) AS team,
         SUM(minutes)::DOUBLE AS mins, SUM(total_points)::DOUBLE AS pts, SUM(COALESCE(expected_goal_involvements,0)) AS xgi
  FROM epl_fpl_gameweeks
  WHERE season IN ('2021-22','2022-23','2023-24','2024-25','2025-26')
    AND position IN ('GKP','GK','DEF','MID','FWD')
  GROUP BY season, gw, player_id
),
teamgw AS (
  SELECT season, gw::INT AS gw, team,
         SUM(CASE WHEN was_home THEN team_a_score ELSE team_h_score END)::DOUBLE AS conceded,
         COUNT(DISTINCT opponent_team_id) AS nfix
  FROM epl_fpl_gameweeks GROUP BY season, gw, team
),
teamstr AS (
  SELECT season, gw, team AS opp_team,
         AVG(conceded/nfix) OVER (PARTITION BY season, team ORDER BY gw RANGE BETWEEN 4 PRECEDING AND 1 PRECEDING) AS opp_gc4
  FROM teamgw
),
fixk AS (
  SELECT g.season, g.gw::INT AS k, g.team, AVG(s.opp_gc4) AS opp_strength_k
  FROM (SELECT DISTINCT season, gw, team, opponent_team_id FROM epl_fpl_gameweeks) g
  JOIN epl_teams tn ON tn.season=g.season AND tn.team_id=g.opponent_team_id
  JOIN teamstr s ON s.season=g.season AND s.gw=g.gw AND s.opp_team=tn.name
  GROUP BY g.season, g.gw, g.team
),
panel AS (
  SELECT g.season, g.gw AS k, g.player_id, g.position, g.team,
         AVG(g.pts)  OVER w AS f_pts4,
         AVG(g.xgi)  OVER w AS f_xgi4,
         AVG(g.mins/90) OVER w AS f_minshare4,
         COUNT(*)    OVER w AS nrows4,
         g.pts AS target_pts,
         f.opp_strength_k
  FROM grid g
  JOIN fixk f ON f.season=g.season AND f.k=g.gw AND f.team=g.team
  WINDOW w AS (PARTITION BY g.season, g.player_id ORDER BY g.gw RANGE BETWEEN 4 PRECEDING AND 1 PRECEDING)
)
SELECT season, k, player_id, position, f_pts4, f_xgi4, f_minshare4, opp_strength_k, target_pts
FROM panel
WHERE nrows4 = 4 AND f_minshare4*4*90 >= 180 AND opp_strength_k IS NOT NULL
"""

def design(d):
    pos = d.position.map({'GKP': 0, 'DEF': 1, 'MID': 2, 'FWD': 3}).fillna(2).values
    return np.column_stack([np.ones(len(d)), d.f_pts4, d.f_xgi4, d.f_minshare4, d.opp_strength_k,
                            (pos == 0), (pos == 1), (pos == 3)]).astype(float)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='/tmp/epl12_fit.duckdb')
    args = ap.parse_args()
    build_db(args.db)
    con = duckdb.connect(args.db, read_only=True)
    df = con.execute(PANEL_SQL).fetchdf()
    con.close()
    print('panel rows:', len(df))
    rng = np.random.default_rng(7)
    for testseason, trainseasons in [('2024-25', SEASONS[:3]), ('2025-26', SEASONS[:4])]:
        tr = df[df.season.isin(trainseasons)]; te = df[df.season == testseason].copy()
        coef, *_ = np.linalg.lstsq(design(tr), tr.target_pts.values, rcond=None)
        pred = design(te) @ coef; base = te.f_pts4.values
        print(f'--- test {testseason} (train {len(tr)}, test {len(te)}) coef {np.round(coef, 3)}')
        print('baseline corr %.3f MAE %.3f | model corr %.3f MAE %.3f' % (
            np.corrcoef(base, te.target_pts)[0, 1], np.abs(base - te.target_pts).mean(),
            np.corrcoef(pred, te.target_pts)[0, 1], np.abs(pred - te.target_pts).mean()))
        # pairwise ranking: same-position pairs per GW, sign agreement on actual gap
        te['pred'] = pred
        tot_m = cor_m = tot_b = cor_b = 0; deltas = []
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
            deltas.append(np.mean(np.where(pi >= pj, ai - aj, aj - ai)))
        print(f'{testseason}: model pair-acc={cor_m / tot_m:.3f} (n={tot_m})  baseline pair-acc={cor_b / tot_b:.3f} (n={tot_b})  mean actual gap when model sides correctly ~{np.mean(deltas):.2f} pts')

if __name__ == '__main__':
    main()
