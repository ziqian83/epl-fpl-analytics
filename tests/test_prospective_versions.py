#!/usr/bin/env python3
"""Checks for the prospective version wiring (docs/16): panel-source selection,
separate version labels, fixture-column plumbing, v2 spec pins, and a functional
build_db pass on a synthetic cache (incl. the fixture-integrity assert).

Run: python3 tests/test_prospective_versions.py
Exits nonzero on failure. No network; the synthetic cache lives in a temp dir.
"""
import importlib.util, json, os, subprocess, sys, tempfile
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
spec = importlib.util.spec_from_file_location('prosp', os.path.join(ROOT, 'scripts', 'prospective-12thman.py'))
prosp = importlib.util.module_from_spec(spec); spec.loader.exec_module(prosp)

fails = []
def check(name, cond, detail=''):
    print(('PASS' if cond else 'FAIL'), name, detail)
    if not cond: fails.append(name)

# 1. panel selection
v1 = prosp.panel_sql_for('v1'); v2 = prosp.panel_sql_for('v2')
check('v1 SQL selected + 2026-27 added', 'nrows4' in v1 and "'2026-27'" in v1)
check('v2 SQL selected + 2026-27 added', 'n_blank4' in v2 and "'2026-27'" in v2)
check('SQLs differ (versioned)', v1 != v2)
try:
    prosp.panel_sql_for('v9'); check('unknown version rejected', False)
except ValueError:
    check('unknown version rejected', True)

# 2. separate version labels
check('v1 results path unchanged', prosp.results_path_for('v1').endswith('prospective-2026-27-results.json'))
check('v2 results path labelled', prosp.results_path_for('v2').endswith('prospective-2026-27-results-v2.json'))
check('v1 path constant preserved', prosp.RESULTS.endswith('prospective-2026-27-results.json'))

# 3. fixture plumbing (static)
src = open(os.path.join(ROOT, 'scripts', 'prospective-12thman.py')).read()
check('refresh-data writes fixture', "'fixture': h['fixture']" in src)
check('build-db integrity assert', 'fixture integrity violated' in src)
check('v2 run requires fixture ids', 'lack fixture ids' in src)
check('v2 eligibility applied in run()', 'df.nrows4 == 4' in src and 'f_minshare4*4*90 >= 180' in src)

# 4. v2 spec pins
specj = json.load(open(os.path.join(ROOT, '12th-man', 'v2', 'data', 'frozen', 'prospective-2026-27-spec-v2.json')))
check('spec panel_version v2', specj.get('panel_version') == 'v2')
check('spec start GW10', specj['start_gw'] == 10)
def blob(p):
    return subprocess.run(['git', 'hash-object', p], capture_output=True, text=True, cwd=ROOT).stdout.strip()
check('runner pin matches HEAD content', specj['code']['runner_blob_sha1'] == blob('scripts/prospective-12thman.py'))
check('v2 panel-source pin matches', specj['code']['fit_panel_source_blob_sha1'] == blob('scripts/fit-12thman-model-v2.py'))
check('backtest pin matches v1 spec pin', specj['code']['backtest_blob_sha1'] == blob('scripts/backtest-12thman-constrained.py') == '7f3b412bd69aaec354f546870f4e62b846be829f')
check('csv_sha256 fill-at-freeze slot', 'csv_sha256' in specj['panel'])
check('source gaps recorded', len(specj.get('source_gaps', [])) >= 2)
check('intended start recorded', 'intended_start' in specj)
check('v1 spec untouched by v2 wiring', json.load(open(os.path.join(ROOT, '12th-man', 'v2', 'data', 'frozen', 'prospective-2026-27-spec.json')))['code']['fit_panel_source_blob_sha1'] == '35034548ded19e56d8b83460f409fd994e267b02')

# 5. functional build_db on a synthetic cache
SEASONS = ['2021-22', '2022-23', '2023-24', '2024-25', '2025-26', '2026-27']
def write_cache(cache, corrupt=False):
    os.makedirs(cache, exist_ok=True)
    for s in SEASONS:
        rows = []
        for gw in range(1, 9):
            fid = gw * 10
            for pid, team, home, opp in [(1, 'ALPHA', True, 2), (2, 'ALPHA', True, 2), (11, 'BETA', False, 1), (12, 'BETA', False, 1)]:
                hs, as_ = (2, 1)
                if corrupt and s == '2026-27' and gw == 3 and pid == 1:
                    hs = 5  # inconsistent score within fixture -> assert must fire
                rows.append({'GW': gw, 'fixture': fid, 'element': pid, 'position': 'MID', 'team': team,
                             'minutes': 90, 'total_points': 5, 'expected_goal_involvements': 0.5,
                             'was_home': home, 'team_h_score': hs, 'team_a_score': as_, 'opponent_team': opp})
        pd.DataFrame(rows).to_csv(os.path.join(cache, f'{s}-merged_gw.csv'), index=False)
        pd.DataFrame([{'id': 1, 'name': 'ALPHA'}, {'id': 2, 'name': 'BETA'}]).to_csv(os.path.join(cache, f'{s}-teams.csv'), index=False)

tmp = tempfile.mkdtemp()
write_cache(os.path.join(tmp, 'cache'))
prosp.CACHE = os.path.join(tmp, 'cache')
prosp.DB = os.path.join(tmp, 'test.duckdb')
prosp.build_db()
import duckdb
con = duckdb.connect(prosp.DB, read_only=True)
cols = [c[1] for c in con.execute('PRAGMA table_info(epl_fpl_gameweeks)').fetchall()]
check('fixture column in prospective DB', 'fixture' in cols)
nnull = con.execute('SELECT COUNT(*) FROM epl_fpl_gameweeks WHERE fixture IS NULL').fetchone()[0]
check('no null fixtures in synthetic DB', nnull == 0)
df = con.execute(prosp.panel_sql_for('v2')).fetchdf()
check('v2 panel SQL executes on prospective DB', True)
check('v2 panel carries diagnostics', 'n_blank4' in df.columns and 'n_missing4' in df.columns)
df1 = con.execute(prosp.panel_sql_for('v1')).fetchdf()
check('v1 panel SQL executes on prospective DB', True)
con.close()
# 5c. fit_and_prep works after the run()-level v2 eligibility filter (the v1 SQL
# filters in-query; the raw v2 panel carries ineligible/NULL-feature rows)
dfe = df[(df.nrows4 == 4) & (df.f_minshare4*4*90 >= 180)].copy()
te = prosp.bt.fit_and_prep(dfe, prosp.TRAIN, '2026-27', {})
check('fit_and_prep runs on filtered v2 panel', te.pred.notna().all())

# 5b. corrupted fixture must trip the assert
tmp2 = tempfile.mkdtemp()
write_cache(os.path.join(tmp2, 'cache'), corrupt=True)
prosp.CACHE = os.path.join(tmp2, 'cache')
prosp.DB = os.path.join(tmp2, 'test2.duckdb')
try:
    prosp.build_db()
    check('corrupt fixture rejected', False)
except AssertionError as e:
    check('corrupt fixture rejected', 'fixture integrity violated' in str(e), str(e))

print('FAILURES:', len(fails))
sys.exit(1 if fails else 0)
