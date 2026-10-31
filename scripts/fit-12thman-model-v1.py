# The 12th Man - v1 runtime-model fit (the fit that produced the live coefficients)
# Original run: 26 Oct 2026, on an 11-season warehouse built by
# sql/epl_duckdb_load.sql from vaastav/Fantasy-Premier-League CSVs.
# This fit's 2025-26 holdout beta vector is exactly the live model in
# scripts/12thman2-refresh.mjs: COEF {const,pts4,pts2,xgi4,xgi2,minshare4,home,
# ogcAtt,ogcDef,ogsAtt,ogsDef} + POS_OFFSET {GKP .623, DEF .058, FWD .148}.
# Holdout results of the original run: 2024-25 MAE 2.242, corr 0.262,
# pair-acc 0.501 (n=12351); 2025-26 MAE 2.299, corr 0.212, pair-acc 0.503
# (n=12376). Naive MAE 2.430 / 2.601.
# Requires: warehouse at /tmp/epl.duckdb (build: duckdb /tmp/epl.duckdb
#   then run sql/epl_duckdb_load.sql, or python3 with the duckdb package).
# Note: pair sampling has no fixed ORDER BY upstream, so pair-acc varies
# ~+/-0.003 between identical runs; MAE/corr are stable.
# ---------------------------------------------------------------------------

import duckdb, numpy as np, pandas as pd

con = duckdb.connect('/tmp/epl.duckdb', read_only=True)

# ---- canonical player-GW grid (doubles summed), 2020-21 onward ----
gw = con.execute("""
SELECT season, player_id, position, round AS gw,
       SUM(minutes)::DOUBLE AS mins, SUM(total_points)::DOUBLE AS pts,
       SUM(expected_goal_involvements) AS xgi
FROM epl_fpl_gameweeks
WHERE season >= '2020-21'
GROUP BY 1,2,3,4
""").df()

# ---- per player-GW fixture rows: opponents + home flags ----
fx = con.execute("""
SELECT g.season, g.player_id, g.round AS gw, g.opponent_team_id AS opp, (g.was_home)::INT AS home
FROM epl_fpl_gameweeks g WHERE g.season >= '2020-21'
""").df()

# ---- player team id per GW (via team name -> epl_teams) ----
tm = con.execute("""
SELECT DISTINCT g.season, g.team AS team_name, t.team_id
FROM epl_fpl_gameweeks g JOIN epl_teams t ON t.season=g.season AND t.name=g.team
WHERE g.season >= '2020-21'
""").df()
team_id_of = {(r.season, r.team_name): r.team_id for r in tm.itertuples()}

# ---- team-match rows, then team-GW aggregates ----
rows = con.execute("""
SELECT season, team, round AS gw, opponent_team_id AS opp, was_home, team_h_score, team_a_score
FROM epl_fpl_gameweeks
WHERE season >= '2020-21' AND team_h_score IS NOT NULL
""").df()
rows['tid'] = [team_id_of.get((s, t)) for s, t in zip(rows.season, rows.team)]
rows = rows.dropna(subset=['tid'])
rows['tid'] = rows.tid.astype(int)
rows['conceded'] = np.where(rows.was_home, rows.team_a_score, rows.team_h_score)
rows['scored'] = np.where(rows.was_home, rows.team_h_score, rows.team_a_score)
match = rows.groupby(['season','tid','gw','opp','was_home'], as_index=False).agg(conceded=('conceded','max'), scored=('scored','max'))
tgw = match.groupby(['season','tid','gw'], as_index=False).agg(gc=('conceded','sum'), gs=('scored','sum'), n=('conceded','size'))

# team trailing-4 per-match conceded/scored entering each GW
tgw = tgw.sort_values(['season','tid','gw'])
for col in ['gc','gs','n']:
    tgw['t4_'+col] = tgw.groupby(['season','tid'])[col].transform(lambda s: s.shift(1).rolling(4, min_periods=4).sum())
tgw['t4_gc_pm'] = tgw.t4_gc / tgw.t4_n
tgw['t4_gs_pm'] = tgw.t4_gs / tgw.t4_n
teamkey = tgw.set_index(['season','tid','gw'])

# player trailing features
gw = gw.sort_values(['season','player_id','gw'])
gw['pos'] = gw.position.replace({'GK':'GKP'})
gw = gw[gw.pos.isin(['GKP','DEF','MID','FWD'])]
grp = gw.groupby(['season','player_id'])
for col in ['pts','xgi','mins']:
    gw['t4_'+col] = grp[col].transform(lambda s: s.shift(1).rolling(4, min_periods=4).sum())
gw['t2_pts'] = grp['pts'].transform(lambda s: s.shift(1).rolling(2, min_periods=2).sum())
gw['t2_xgi'] = grp['xgi'].transform(lambda s: s.shift(1).rolling(2, min_periods=2).sum())

# opponent terms + home share per player-GW
fxagg = fx.groupby(['season','player_id','gw']).agg(opps=('opp', list), home=('home','mean')).reset_index()
gw = gw.merge(fxagg, on=['season','player_id','gw'], how='left')

def opp_terms(r):
    gcs, gss = [], []
    for o in r.opps:
        k = (r.season, o, r.gw)
        if k in teamkey.index:
            v = teamkey.loc[k]
            if pd.notna(v.t4_gc_pm): gcs.append(v.t4_gc_pm)
            if pd.notna(v.t4_gs_pm): gss.append(v.t4_gs_pm)
    return (np.mean(gcs) if gcs else np.nan, np.mean(gss) if gss else np.nan)

ot = gw.apply(opp_terms, axis=1, result_type='expand')
gw['opp_gc'] = ot[0]; gw['opp_gs'] = ot[1]

# eligible rows: 4 prior GW rows (trailing sums non-null) + >=180 trailing mins + target + opponent data
d = gw.dropna(subset=['t4_pts','t4_xgi','t4_mins','t2_pts','t2_xgi','opp_gc','opp_gs','pts']).copy()
d = d[d.t4_mins >= 180]
d['pts4'] = d.t4_pts/4; d['xgi4'] = d.t4_xgi/4; d['minshare4'] = d.t4_mins/360
d['pts2'] = d.t2_pts/2; d['xgi2'] = d.t2_xgi/2
d['att'] = d.pos.isin(['MID','FWD']).astype(int)
print('eligible rows by season:'); print(d.groupby('season').size())

POS = ['GKP','DEF','FWD']  # MID base
def design(df, model):
    n = len(df); X = [np.ones(n)]
    if model == 'v0':
        X += [df.pts4.values, df.xgi4.values, df.minshare4.values, df.opp_gc.values]
        X += [(df.pos==p).astype(float).values for p in POS]
    else:
        X += [df.pts4.values, df.pts2.values, df.xgi4.values, df.xgi2.values, df.minshare4.values,
              df.home.values,
              (df.opp_gc*df.att).values, (df.opp_gc*(1-df.att)).values,
              (df.opp_gs*df.att).values, (df.opp_gs*(1-df.att)).values]
        X += [(df.pos==p).astype(float).values for p in POS]
    return np.column_stack(X)

def fit_eval(train_seasons, test_season, seed=7):
    tr = d[d.season.isin(train_seasons)]; te = d[d.season==test_season]
    out = {}
    for model in ['v0','v1']:
        Xtr = design(tr, model); Xte = design(te, model)
        beta, *_ = np.linalg.lstsq(Xtr, tr.pts.values, rcond=None)
        pred = Xte @ beta
        mae = np.mean(np.abs(pred - te.pts.values)); corr = np.corrcoef(pred, te.pts.values)[0,1]
        # pairwise same-position within GW, deterministic sample
        rng = np.random.default_rng(seed)
        te2 = te.assign(pred=pred)
        correct = tot = 0; gaps = []
        for (gwk, posk), gdf in te2.groupby(['gw','pos']):
            if len(gdf) < 2: continue
            idx = gdf.index.values
            if len(idx) > 14: idx = rng.choice(idx, 14, replace=False)
            sub = te2.loc[idx]
            for i in range(len(sub)):
                for j in range(i+1, len(sub)):
                    pi, pj = sub.pred.iloc[i], sub.pred.iloc[j]
                    ai, aj = sub.pts.iloc[i], sub.pts.iloc[j]
                    if pi == pj: continue
                    tot += 1
                    if (pi > pj and ai > aj) or (pi < pj and ai < aj): correct += 1; gaps.append(abs(ai-aj))
        out[model] = dict(mae=mae, corr=corr, pair=correct/tot, npair=tot, gap=float(np.mean(gaps)), beta=beta)
    naive_mae = np.mean(np.abs(te.pts4.values - te.pts.values))
    return out, naive_mae, len(tr), len(te)

for name, trs, tes in [('HOLDOUT 2024-25', ['2021-22','2022-23','2023-24'], '2024-25'),
                       ('HOLDOUT 2025-26', ['2021-22','2022-23','2023-24','2024-25'], '2025-26')]:
    out, nmae, ntr, nte = fit_eval(trs, tes)
    print(f'\n=== {name} (train {ntr} rows, test {nte}) ===')
    print(f'naive MAE {nmae:.3f}')
    for m, r in out.items():
        print(f'{m}: MAE {r["mae"]:.3f} corr {r["corr"]:.3f} pair {r["pair"]:.3f} (n={r["npair"]}) meangap {r["gap"]:.2f}')
        print('  beta', np.round(r['beta'],3))