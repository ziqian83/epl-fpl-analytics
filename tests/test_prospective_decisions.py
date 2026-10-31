#!/usr/bin/env python3
"""Checks for the forward decision freeze (docs/16):
A. decision_sql_for(version, K) == replay panel features on COMPLETED GWs
   (real prospective DB; skipped when absent) - the no-leakage/equivalence gate.
B. End-to-end freeze + score on a synthetic league (no network, monkeypatched
   bootstrap): builder path, prior-state path, immutability, hash verification,
   scoring from frozen decisions only.
Run: python3 tests/test_prospective_decisions.py [--db /tmp/epl12_prospective.duckdb]
"""
import importlib.util, json, os, sys, tempfile
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
spec = importlib.util.spec_from_file_location('prosp', os.path.join(ROOT, 'scripts', 'prospective-12thman.py'))
prosp = importlib.util.module_from_spec(spec); spec.loader.exec_module(prosp)

fails = []
def check(name, cond, detail=''):
    print(('PASS' if cond else 'FAIL'), name, detail)
    if not cond: fails.append(name)

# ---- A. equivalence on completed GWs (real data)
db = sys.argv[sys.argv.index('--db') + 1] if '--db' in sys.argv else '/tmp/epl12_prospective.duckdb'
if os.path.exists(db):
    import duckdb
    con = duckdb.connect(db, read_only=True)
    p1 = con.execute(prosp.panel_sql_for('v1')).fetchdf()
    p2 = con.execute(prosp.panel_sql_for('v2')).fetchdf()
    p2e = p2[(p2.nrows4 == 4) & (p2.f_minshare4*4*90 >= 180)].copy()
    for K in (5, 6, 7, 8):
        d1 = con.execute(prosp.decision_sql_for('v1', K)).fetchdf()
        r1 = p1[(p1.season == '2026-27') & (p1.k == K)]
        m = d1.merge(r1, on='player_id', suffixes=('_d', '_p'))
        check(f'A v1 K={K}: membership identical', len(m) == len(d1) == len(r1),
              f'dec={len(d1)} panel={len(r1)}')
        for c in ('f_pts4', 'f_xgi4', 'f_minshare4', 'opp_strength_k'):
            ok = len(m) > 0 and (m[f'{c}_d'] - m[f'{c}_p']).abs().max() < 1e-9
            check(f'A v1 K={K}: {c} equal', ok)
        d2 = con.execute(prosp.decision_sql_for('v2', K)).fetchdf()
        d2 = d2[(d2.nrows4 == 4) & (d2.f_minshare4*4*90 >= 180)].copy()
        r2 = p2e[(p2e.season == '2026-27') & (p2e.k == K)]
        m2 = d2.merge(r2, on='player_id', suffixes=('_d', '_p'))
        check(f'A v2 K={K}: membership identical', len(m2) == len(d2) == len(r2),
              f'dec={len(d2)} panel={len(r2)}')
        for c in ('f_pts4', 'f_xgi4', 'f_minshare4', 'opp_strength_k', 'team_gws4', 'n_blank4', 'n_missing4'):
            ok = len(m2) > 0 and (m2[f'{c}_d'] - m2[f'{c}_p']).abs().max() < 1e-9
            check(f'A v2 K={K}: {c} equal', ok)
    # leak guard: decision SQL reads no played rows at/after K
    sql = prosp.decision_sql_for('v2', 6)
    check('A leak guard: features bound gw < K', sql.count('gw::INT < 6') >= 2 and 'gw::INT = 6' in sql)
    con.close()
else:
    print('SKIP part A: no prospective db at', db)

# ---- B. synthetic end-to-end freeze + score
SEASONS = ['2021-22', '2022-23', '2023-24', '2024-25', '2025-26', '2026-27']
TEAMS = [(1, 'ALPHA'), (2, 'BETA'), (3, 'GAMMA'), (4, 'DELTA'), (5, 'ECHO'), (6, 'FOXTROT')]
POSSEQ = ['GKP', 'GKP', 'DEF', 'DEF', 'MID', 'MID', 'FWD', 'FWD']  # per team: 8 players (club-cap-3 headroom for a 15-man squad from 6 teams)
def pid_of(ti, pi): return ti * 100 + pi

tmp = tempfile.mkdtemp()
cache = os.path.join(tmp, 'cache'); os.makedirs(cache)
for s in SEASONS:
    rows = []
    for gw in range(1, 9):
        pairs = [((1, 'ALPHA'), (2, 'BETA')), ((3, 'GAMMA'), (4, 'DELTA')), ((5, 'ECHO'), (6, 'FOXTROT'))]
        for fi, ((htid, hnm), (atid, anm)) in enumerate(pairs):
            home, away = ((htid, hnm), (atid, anm)) if gw % 2 else ((atid, anm), (htid, hnm))
            fid = gw * 100 + fi
            for side, (tid, tnm), (otid, onm), hs, as_ in [
                    ('h', home, away, 2, 1), ('a', away, home, 2, 1)]:
                for pi, pos in enumerate(POSSEQ):
                    rows.append({'GW': gw, 'fixture': fid, 'element': pid_of(tid, pi),
                                 'position': pos, 'team': tnm, 'minutes': 90, 'total_points': 5,
                                 'expected_goal_involvements': 0.5, 'was_home': side == 'h',
                                 'team_h_score': hs, 'team_a_score': as_, 'opponent_team': otid,
                                 'value': 50})
    pd.DataFrame(rows).to_csv(os.path.join(cache, f'{s}-merged_gw.csv'), index=False)
    pd.DataFrame([{'id': t, 'name': n} for t, n in TEAMS]).to_csv(os.path.join(cache, f'{s}-teams.csv'), index=False)
# schedule through GW9 (beyond played data), prices, provenance
with open(os.path.join(cache, '2026-27-schedule.csv'), 'w') as f:
    f.write('gw,team,opponent_team_id\n')
    for gw in range(1, 10):
        pairs = [((1, 'ALPHA'), (2, 'BETA')), ((3, 'GAMMA'), (4, 'DELTA')), ((5, 'ECHO'), (6, 'FOXTROT'))]
        for (htid, hnm), (atid, anm) in pairs:
            f.write(f'{gw},{hnm},{atid}\n'); f.write(f'{gw},{anm},{htid}\n')
with open(os.path.join(cache, '2026-27-prices.csv'), 'w') as f:
    f.write('element,now_cost\n')
    for tid, _ in TEAMS:
        for pi in range(len(POSSEQ)): f.write(f'{pid_of(tid, pi)},50\n')
json.dump({'source': 'synthetic', 'pulled_at': '2026-10-31T00:00:00Z', 'csv_sha256': 'syn',
           'rows': -1, 'players': 48, 'schedule_rows': 54, 'completed_gws': [1, 2, 3, 4, 5, 6]},
          open(os.path.join(cache, '2026-27-provenance.json'), 'w'))

prosp.CACHE = cache
prosp.DB = os.path.join(tmp, 'syn.duckdb')
prosp.ROOT = tmp  # decision/results files land in tmp
os.makedirs(os.path.join(tmp, '12th-man', 'v2', 'data', 'frozen', 'decisions'))
prosp._blob = lambda p: 'testblob'
prosp.api = lambda path: {'elements': [{'id': pid_of(t, pi), 'now_cost': 50}
                                       for t, _ in TEAMS for pi in range(len(POSSEQ))]}
prosp.build_db()

specj = {'season': '2026-27', 'start_gw': 6, 'gw10_deadline': '2026-11-06T18:30:00Z',
         'ft_cap': 5, 'builder': 'signal',
         'policies': [{'name': 'hold', 'key': 'hold', 'margin': None, 'builder': 'signal'},
                      {'name': 'persistence_m0', 'key': 'f_pts4', 'margin': 0.0, 'builder': 'signal'},
                      {'name': 'model_m1', 'key': 'pred', 'margin': 1.0, 'builder': 'signal'}]}
spec_path = os.path.join(tmp, 'spec.json'); json.dump(specj, open(spec_path, 'w'))

prosp.freeze(6, spec_path)
d6 = json.load(open(prosp.decision_file_path(6, 'v1')))

check('B freeze file hash verifies', prosp.verify_decision_file(d6))
check('B version recorded', d6['panel_version'] == 'v1')
for name, p in d6['policies'].items():
    check(f'B {name}: 15-man squad', len(p['squad']) == 15)
    check(f'B {name}: XI 11 + bench 4', len(p['xi']) == 11 and len(p['bench']) == 4)
    check(f'B {name}: cap/vice in XI', p['captain'] in p['xi'] and p['vice'] in p['xi'])
    check(f'B {name}: no transfers at start GW', p['transfers'] == [] and p['fts_after'] == 0)
    check(f'B {name}: positions recorded', all(e['pos'] in ('GKP', 'DEF', 'MID', 'FWD') for e in p['squad']))
check('B hold/model share builder squad', [e['pid'] for e in d6['policies']['hold']['squad']] ==
      [e['pid'] for e in d6['policies']['model_m1']['squad']])

# immutability
try:
    prosp.freeze(6, spec_path)
    check('B freeze refuses overwrite', False)
except SystemExit:
    check('B freeze refuses overwrite', True)

# tamper detection
import copy
d6bad = copy.deepcopy(d6); d6bad['policies']['hold']['xi'][0] = 999999
check('B tamper detected', not prosp.verify_decision_file(d6bad))

# prior-state path (GW7): FT banks to 1, uniform signals -> no transfers
prosp.freeze(7, spec_path)
d7 = json.load(open(prosp.decision_file_path(7, 'v1')))
check('B GW7 file hash verifies', prosp.verify_decision_file(d7))
for name, p in d7['policies'].items():
    check(f'B GW7 {name}: squad carried over', [e['pid'] for e in p['squad']] ==
          [e['pid'] for e in d6['policies'][name]['squad']])
    check(f'B GW7 {name}: fts banked to 1, no moves', p['fts_after'] == 1 and p['transfers'] == [])

# scoring from frozen decisions: every squad player recorded 90 min / 5 pts
prosp.score_frozen(6, spec_path)
res = json.load(open(prosp.results_path_for('v1')))
check('B results labelled v1 + frozen source', res['panel_version'] == 'v1' and 'frozen' in res['decision_source'])
for name, pol in res['policies'].items():
    check(f'B {name}: GW6 scored 60.0 (11x5 + captain 5)', pol['weekly']['6']['pts'] == 60.0,
          f"got {pol['weekly']['6']['pts']}")
try:
    prosp.score_frozen(6, spec_path)
    check('B score refuses rescore', False)
except SystemExit:
    check('B score refuses rescore', True)
try:
    prosp.score_frozen(7, spec_path)  # GW7 not complete in provenance
    check('B score requires completion', False)
except AssertionError:
    check('B score requires completion', True)

print('FAILURES:', len(fails))
sys.exit(1 if fails else 0)
