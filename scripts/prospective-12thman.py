#!/usr/bin/env python3
"""The 12th Man - PROSPECTIVE frozen-policy runner (2026-27, GW10 onward).

This is the pre-registered outer test promised in docs/13: three policies frozen BEFORE
the GW10 deadline (2026-11-06T18:30Z, official bootstrap-static), scored GW by GW as
official results land, with no spec edits after the freeze.

  - hold          (builder 'signal', never transfers)
  - persistence   (f_pts4, margin>0, builder 'signal')
  - model         (pred, margin>1, builder 'signal')

Data: official FPL API (bootstrap-static, element-summary, fixtures). Vaastav's repo
cannot supply 2026-27 on the freeze timeline: its pinned master d7b05b51d137 (22 Oct
2026) covers only through GW6, and GW7-9 are required for GW10 features. The API pull is
snapshotted to .fit-cache/2026-27-merged_gw.csv in vaastav merged_gw column format with
recorded pull time and sha256; that hash goes into the spec JSON at the data freeze.

Simulation: the corrected pre-outcome scorer from backtest-12thman-constrained.py
(pick_team + score_gw: legal XI/bench/captain/vice from as-of signal only, official
auto-subs and vice-captain on realized minutes, full-data scoring). Squad built at GW10
by builder 'signal'; decisions from GW10. Per-GW points are obtained by deterministic
replay: cumulative(K) - cumulative(K-1) over completed GWs K >= 10.

Usage:
  python3 scripts/prospective-12thman.py refresh-data   # pull API -> cache CSV + provenance
  python3 scripts/prospective-12thman.py build-db       # rebuild /tmp/epl12_prospective.duckdb
  python3 scripts/prospective-12thman.py run --spec 12th-man/v2/data/frozen/prospective-2026-27-spec.json
"""
import argparse, csv, hashlib, importlib.util, json, os, re, sys, time, urllib.request
import duckdb, numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
CACHE = os.path.join(ROOT, '.fit-cache')
DB = '/tmp/epl12_prospective.duckdb'
SEASON = '2026-27'
TRAIN = ['2021-22', '2022-23', '2023-24', '2024-25', '2025-26']
RESULTS = os.path.join(ROOT, '12th-man', 'v2', 'data', 'frozen', 'prospective-2026-27-results.json')

spec_loader = importlib.util.spec_from_file_location('bt', os.path.join(HERE, 'backtest-12thman-constrained.py'))
bt = importlib.util.module_from_spec(spec_loader); spec_loader.loader.exec_module(bt)

def api(path):
    req = urllib.request.Request('https://fantasy.premierleague.com/api/' + path,
                                 headers={'User-Agent': '12thman-prospective-research'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))

def refresh_data():
    """Pull the official API and snapshot 2026-27 player-GW rows in vaastav merged_gw format."""
    boot = api('bootstrap-static/')
    teams = {t['id']: t['name'] for t in boot['teams']}
    posmap = {1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD'}
    fixtures = {f['id']: f for f in api('fixtures/')}
    elems = boot['elements']
    rows = []
    for i, e in enumerate(elems):
        s = api(f"element-summary/{e['id']}/")
        for h in s['history']:
            fx = fixtures.get(h['fixture'])
            if fx is None: continue
            team_id = fx['team_h'] if h['was_home'] else fx['team_a']
            rows.append({
                'GW': h['round'], 'element': e['id'], 'position': posmap[e['element_type']],
                'team': teams[team_id], 'minutes': h['minutes'], 'total_points': h['total_points'],
                'expected_goal_involvements': h['expected_goal_involvements'],
                'was_home': h['was_home'], 'team_h_score': h['team_h_score'],
                'team_a_score': h['team_a_score'], 'opponent_team': h['opponent_team'],
                'value': h['value']})
        if (i + 1) % 100 == 0: print(f'  pulled {i+1}/{len(elems)} players', flush=True)
        time.sleep(0.05)
    cols = ['GW', 'element', 'position', 'team', 'minutes', 'total_points',
            'expected_goal_involvements', 'was_home', 'team_h_score', 'team_a_score',
            'opponent_team', 'value']
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f'{SEASON}-merged_gw.csv')
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    sha = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    with open(os.path.join(CACHE, f'{SEASON}-teams.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['id', 'name'])
        for tid, name in sorted(teams.items()): w.writerow([tid, name])
    bygw = {}
    for fx in fixtures.values():
        if fx.get('event'): bygw.setdefault(fx['event'], []).append(bool(fx.get('finished')))
    completed = sorted(g for g, v in bygw.items() if all(v))
    prov = {'source': 'official FPL API (bootstrap-static, element-summary, fixtures)',
            'pulled_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'csv_sha256': sha, 'rows': len(rows), 'players': len(elems),
            'completed_gws': completed}
    with open(os.path.join(CACHE, f'{SEASON}-provenance.json'), 'w') as f:
        json.dump(prov, f, indent=2)
    print(json.dumps(prov, indent=2))

def build_db():
    """Build the prospective warehouse: vaastav cache for train seasons + API snapshot for 2026-27."""
    if os.path.exists(DB): os.remove(DB)
    con = duckdb.connect(DB)
    frames, teams = [], []
    for s in TRAIN + [SEASON]:
        gw = pd.read_csv(os.path.join(CACHE, f'{s}-merged_gw.csv'), low_memory=False)
        gw['season'] = s
        frames.append(gw)
        t = pd.read_csv(os.path.join(CACHE, f'{s}-teams.csv'))
        t['season'] = s
        teams.append(t[['season', 'id', 'name']].rename(columns={'id': 'team_id'}))
    gw = pd.concat(frames, ignore_index=True)
    gw = gw.rename(columns={'GW': 'gw', 'element': 'player_id', 'opponent_team': 'opponent_team_id'})
    keep = ['season', 'gw', 'player_id', 'position', 'team', 'minutes', 'total_points',
            'expected_goal_involvements', 'was_home', 'team_a_score', 'team_h_score', 'opponent_team_id']
    con.register('gw_stage', gw[keep])
    con.execute('CREATE TABLE epl_fpl_gameweeks AS SELECT * FROM gw_stage')
    con.register('teams_stage', pd.concat(teams, ignore_index=True))
    con.execute('CREATE TABLE epl_teams AS SELECT * FROM teams_stage')
    con.close()
    print('db built:', DB)

def run(spec_path):
    specj = json.load(open(spec_path))
    start_gw = specj['start_gw']
    assert specj['season'] == SEASON and specj['ft_cap'] == bt.FT_CAP
    if not os.path.exists(DB): build_db()
    fit_src = open(os.path.join(HERE, 'fit-12thman-model.py')).read()
    panel_sql = re.search(r'PANEL_SQL = """(.*?)"""', fit_src, re.S).group(1)
    panel_sql = panel_sql.replace("('2021-22','2022-23','2023-24','2024-25','2025-26')",
                                  "('2021-22','2022-23','2023-24','2024-25','2025-26','2026-27')")
    assert "'2026-27'" in panel_sql
    con = duckdb.connect(DB, read_only=True)
    df = con.execute(panel_sql).fetchdf()
    full = con.execute("""SELECT season, gw::INT AS k, player_id,
                          SUM(total_points)::DOUBLE AS pts, SUM(minutes)::DOUBLE AS mins
                          FROM epl_fpl_gameweeks GROUP BY season, gw, player_id""").fetchdf()
    con.close()
    act = {}
    for s, k, p, pts, mins in full.itertuples(index=False):
        act.setdefault(s, {}).setdefault(k, {})[p] = (pts, mins)
    bt.SEASONS = TRAIN + [SEASON]
    prices = bt.load_prices()
    prov = json.load(open(os.path.join(CACHE, f'{SEASON}-provenance.json')))
    complete = [g for g in prov['completed_gws'] if g >= start_gw]
    te_full = bt.fit_and_prep(df, TRAIN, SEASON, prices)
    te_full = te_full[te_full.k >= start_gw]
    act_s = act.get(SEASON, {})
    results = {'spec': os.path.basename(spec_path),
               'scored_through_gw': max(complete) if complete else None,
               'provenance': prov, 'policies': {}}
    for pol in specj['policies']:
        weekly, cum = {}, (0.0, 0, 0)
        for K in complete:
            te = te_full[te_full.k <= K]
            if pol['key'] == 'hold':
                r = bt.simulate_hold(te, prices, act_s, start=specj['builder'])
            else:
                r = bt.simulate(te, prices, act_s, pol['margin'], key=pol['key'], start=specj['builder'])
            if r is None: continue
            total, tr, hits, _ = r
            weekly[str(K)] = {'pts': round(total - cum[0], 1), 'transfers': tr - cum[1], 'hits': hits - cum[2]}
            cum = (total, tr, hits)
        results['policies'][pol['name']] = {
            'weekly': weekly, 'total': round(cum[0], 1), 'transfers': cum[1], 'hits': cum[2]}
        print(f"  {pol['name']}: total {cum[0]:.1f} ({cum[1]} tr, {cum[2]} hits) through GW {max(complete) if complete else '-'}")
    os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    with open(RESULTS, 'w') as f:
        json.dump(results, f, indent=2)
    print('wrote', RESULTS)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['refresh-data', 'build-db', 'run'])
    ap.add_argument('--spec', default=os.path.join(ROOT, '12th-man', 'v2', 'data', 'frozen', 'prospective-2026-27-spec.json'))
    a = ap.parse_args()
    {'refresh-data': refresh_data, 'build-db': build_db, 'run': lambda: run(a.spec)}[a.cmd]()
