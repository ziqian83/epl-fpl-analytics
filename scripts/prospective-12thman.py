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
by builder 'signal'; decisions from GW10.

FORWARD DECISION FREEZE (docs/13/16): `freeze --gw K` runs BEFORE GW K's deadline and
persists each policy's actual decisions (starting squad at start_gw, transfers, XI,
bench order, captain/vice) into 12th-man/v2/data/frozen/decisions/gw<K>-<version>.json
with frozen_at, input hashes and code pins; frozen files are never overwritten.
Decision inputs are strictly pre-outcome: played rows with gw < K, the fixture SCHEDULE
at K (opponents), bootstrap now_cost at frozen_at, and prior frozen decision files.
`score-gw --gw K` later applies official actuals to the frozen decisions only.
`replay` (formerly `run`) reconstructs choices AFTER outcome rows exist and is a
DIAGNOSTIC: its outputs land in prospective-2026-27-replay*.json, never in the
prospective record (prospective-2026-27-results*.json, written by score-gw only).
Transfer decisions use the SAME code path as the replay: bt.transfer_week.

Panel versions (docs/15/16): spec field "panel_version" selects the frozen panel SQL -
"v1" (default; fit-12thman-model.py PANEL_SQL) or "v2" (fit-12thman-model-v2.py
PANEL_SQL_V2: fixture-deduped conceded, shared player-GW grid, blank/missing semantics).
Each version scores under its own label: results land in
prospective-2026-27-results.json (v1) and prospective-2026-27-results-v2.json (v2);
the two never overwrite each other.

Usage:
  python3 scripts/prospective-12thman.py refresh-data   # pull API -> cache CSVs + provenance
  python3 scripts/prospective-12thman.py build-db       # rebuild /tmp/epl12_prospective.duckdb
  python3 scripts/prospective-12thman.py freeze --gw 10 --spec <spec.json>   # BEFORE the GW10 deadline
  python3 scripts/prospective-12thman.py score-gw --gw 10 --spec <spec.json> # AFTER GW10 is final
  python3 scripts/prospective-12thman.py replay --spec <spec.json>           # diagnostic only
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

def results_path_for(version):
    """The official prospective record per version (written by score-gw ONLY, from
    frozen pre-deadline decisions); v1 keeps the original path."""
    suffix = '' if version == 'v1' else f'-{version}'
    return os.path.join(ROOT, '12th-man', 'v2', 'data', 'frozen', f'prospective-2026-27-results{suffix}.json')

def replay_path_for(version):
    """Replay diagnostics (post-outcome reconstruction) - never the prospective record."""
    suffix = '' if version == 'v1' else f'-{version}'
    return os.path.join(ROOT, '12th-man', 'v2', 'data', 'frozen', f'prospective-2026-27-replay{suffix}.json')

def panel_sql_for(version):
    """Frozen panel SQL for a version; the train-season tuple is extended to include 2026-27."""
    if version == 'v1':
        src = open(os.path.join(HERE, 'fit-12thman-model.py')).read()
        sql = re.search(r'PANEL_SQL = """(.*?)"""', src, re.S).group(1)
    elif version == 'v2':
        src = open(os.path.join(HERE, 'fit-12thman-model-v2.py')).read()
        sql = re.search(r'PANEL_SQL_V2 = """(.*?)"""', src, re.S).group(1)
    else:
        raise ValueError(f'unknown panel_version {version!r}')
    sql = sql.replace("('2021-22','2022-23','2023-24','2024-25','2025-26')",
                      "('2021-22','2022-23','2023-24','2024-25','2025-26','2026-27')")
    assert "'2026-27'" in sql, 'season-list replacement failed'
    return sql


# ---------------------------------------------------------------------------
# FORWARD DECISION VIEW (docs/16). decision_sql_for(version, K) reproduces the
# frozen panel's feature semantics for a FUTURE or in-progress GW K WITHOUT any
# GW-K outcome data: player features come from played rows with gw < K, the
# GW-K opponent mapping comes from the fixture SCHEDULE (epl_schedule, known
# pre-deadline), and anchor rows give every registered player a row at K.
# Equivalence with the replay panel on completed GWs is enforced by
# tests/test_prospective_decisions.py.
# ---------------------------------------------------------------------------
_DEC_GRID = """
  SELECT season, gw::INT AS gw, player_id,
         MAX(CASE WHEN position='GK' THEN 'GKP' ELSE position END) AS position, MAX(team) AS team,
         SUM(minutes)::DOUBLE AS mins, SUM(total_points)::DOUBLE AS pts,
         SUM(COALESCE(expected_goal_involvements,0)) AS xgi
  FROM epl_fpl_gameweeks
  WHERE season = '{season}' AND gw::INT < {K}
    AND position IN ('GKP','GK','DEF','MID','FWD')
  GROUP BY season, gw, player_id
"""

_DEC_ANCHORS = """
latest AS (
  SELECT player_id, position, team FROM (
    SELECT player_id, position, team,
           ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY gw DESC) AS rn
    FROM grid) t WHERE rn = 1
),
anchors AS (  -- every known player at the decision GW; target unknown (NULL)
  SELECT '{season}' AS season, {K} AS gw, player_id, position, team,
         CAST(NULL AS DOUBLE) AS mins, CAST(NULL AS DOUBLE) AS pts, CAST(NULL AS DOUBLE) AS xgi
  FROM latest
),
grid2 AS (SELECT * FROM grid UNION ALL SELECT * FROM anchors)
"""

_DEC_FIXK = """
  SELECT sch.season, sch.gw::INT AS k, sch.team, AVG(s.opp_gc4) AS opp_strength_k
  FROM epl_schedule sch
  JOIN epl_teams tn ON tn.season=sch.season AND tn.team_id=sch.opponent_team_id
  JOIN teamstr s ON s.season=sch.season AND s.gw=sch.gw AND s.opp_team=tn.name
  WHERE sch.gw::INT = {K}
  GROUP BY sch.season, sch.gw, sch.team
"""

_DECISION_SQL_V1 = """
WITH grid AS (""" + _DEC_GRID + """),
""" + _DEC_ANCHORS + """,
teamgw AS (  -- v1 semantics preserved verbatim (row-scaled conceded; the documented v1 defect)
  SELECT season, gw::INT AS gw, team,
         SUM(CASE WHEN was_home THEN team_a_score ELSE team_h_score END)::DOUBLE AS conceded,
         COUNT(DISTINCT opponent_team_id) AS nfix
  FROM epl_fpl_gameweeks WHERE season = '{season}' AND gw::INT < {K}
  GROUP BY season, gw, team
  UNION ALL
  SELECT DISTINCT season, {K} AS gw, team, CAST(NULL AS DOUBLE), CAST(NULL AS BIGINT)
  FROM epl_schedule WHERE season = '{season}' AND gw::INT = {K}
),
teamstr AS (
  SELECT season, gw, team AS opp_team,
         AVG(conceded/nfix) OVER (PARTITION BY season, team ORDER BY gw RANGE BETWEEN 4 PRECEDING AND 1 PRECEDING) AS opp_gc4
  FROM teamgw
),
fixk AS (""" + _DEC_FIXK + """),
feat AS (  -- windows computed BEFORE the schedule join (the join is k=K-only)
  SELECT g.season, g.gw AS k, g.player_id, g.position, g.team,
         AVG(g.pts)  OVER w AS f_pts4,
         AVG(g.xgi)  OVER w AS f_xgi4,
         AVG(g.mins/90) OVER w AS f_minshare4,
         COUNT(*)    OVER w AS nrows4,
         g.pts AS target_pts
  FROM grid2 g
  WINDOW w AS (PARTITION BY g.season, g.player_id ORDER BY g.gw RANGE BETWEEN 4 PRECEDING AND 1 PRECEDING)
),
panel AS (
  SELECT g.*, f.opp_strength_k
  FROM feat g
  JOIN fixk f ON f.season=g.season AND f.k=g.k AND f.team=g.team
)
SELECT season, k, player_id, position, team, f_pts4, f_xgi4, f_minshare4, opp_strength_k, target_pts
FROM panel
WHERE k = {K} AND nrows4 = 4 AND f_minshare4*4*90 >= 180 AND opp_strength_k IS NOT NULL
ORDER BY season, k, position, player_id
"""

_DECISION_SQL_V2 = """
WITH grid AS (""" + _DEC_GRID + """),
""" + _DEC_ANCHORS + """,
fx AS (  -- one row per (fixture, team): fixture identity from the source fixture id
  SELECT DISTINCT season, gw::INT AS gw, fixture, team, was_home, team_h_score, team_a_score
  FROM epl_fpl_gameweeks
  WHERE season = '{season}' AND gw::INT < {K}
),
fxc AS (
  SELECT season, gw, fixture, team,
         (CASE WHEN was_home THEN team_a_score ELSE team_h_score END)::DOUBLE AS conceded
  FROM fx
),
teamgw AS (
  SELECT season, gw, team, AVG(conceded) AS conceded_per_fx, COUNT(*) AS nfix
  FROM fxc GROUP BY season, gw, team
  UNION ALL
  SELECT DISTINCT season, {K} AS gw, team, CAST(NULL AS DOUBLE), CAST(NULL AS BIGINT)
  FROM epl_schedule WHERE season = '{season}' AND gw::INT = {K}
),
teamstr AS (
  SELECT season, gw, team AS opp_team,
         AVG(conceded_per_fx) OVER w AS opp_gc4,
         COUNT(*) OVER w AS n_gws4
  FROM teamgw
  WINDOW w AS (PARTITION BY season, team ORDER BY gw RANGE BETWEEN 4 PRECEDING AND 1 PRECEDING)
),
fixk AS (""" + _DEC_FIXK + """),
teamwin AS (  -- trailing calendar GWs in which the team had ANY fixture (played only)
  SELECT t1.season, t1.gw::INT AS k, t1.team, COUNT(t2.gw) AS team_gws4
  FROM (SELECT DISTINCT season, gw, team FROM epl_schedule WHERE season='{season}' AND gw::INT={K}) t1
  LEFT JOIN (SELECT DISTINCT season, gw, team FROM fx) t2
    ON t2.season=t1.season AND t2.team=t1.team AND t2.gw BETWEEN t1.gw-4 AND t1.gw-1
  GROUP BY t1.season, t1.gw, t1.team
),
feat AS (  -- windows computed BEFORE the schedule join (the join is k=K-only)
  SELECT g.season, g.gw AS k, g.player_id, g.position, g.team,
         AVG(g.pts)  OVER w AS f_pts4,
         AVG(g.xgi)  OVER w AS f_xgi4,
         AVG(g.mins/90) OVER w AS f_minshare4,
         COUNT(*)    OVER w AS nrows4,
         g.pts AS target_pts
  FROM grid2 g
  WINDOW w AS (PARTITION BY g.season, g.player_id ORDER BY g.gw RANGE BETWEEN 4 PRECEDING AND 1 PRECEDING)
),
panel AS (
  SELECT g.*, f.opp_strength_k, tw.team_gws4
  FROM feat g
  JOIN fixk f ON f.season=g.season AND f.k=g.k AND f.team=g.team
  JOIN teamwin tw ON tw.season=g.season AND tw.k=g.k AND tw.team=g.team
)
SELECT season, k, player_id, position, team, f_pts4, f_xgi4, f_minshare4, opp_strength_k,
       nrows4, team_gws4,
       LEAST(4, k-1) - team_gws4 AS n_blank4,
       team_gws4 - nrows4 AS n_missing4,
       target_pts
FROM panel
WHERE k = {K} AND opp_strength_k IS NOT NULL
ORDER BY season, k, position, player_id
"""

def decision_sql_for(version, K):
    tpl = {'v1': _DECISION_SQL_V1, 'v2': _DECISION_SQL_V2}.get(version)
    if tpl is None: raise ValueError(f'unknown panel_version {version!r}')
    return tpl.format(season=SEASON, K=int(K))

def decision_file_path(gw, version):
    return os.path.join(ROOT, '12th-man', 'v2', 'data', 'frozen', 'decisions',
                        f'gw{int(gw):02d}-{version}.json')

def _decision_hash(d):
    body = {k: v for k, v in d.items() if k != 'content_sha256'}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()

def verify_decision_file(d):
    """Integrity check on a frozen decision file (hash self-consistency)."""
    return 'content_sha256' in d and _decision_hash(d) == d['content_sha256']

def _load_prior_state(gw, version, specj):
    """Rebuild per-policy state entering GW gw from the frozen decision files
    gw=start_gw..gw-1. State evolution needs no outcomes: squads/banks/FTs change
    only through the frozen transfers."""
    start_gw = specj['start_gw']
    state = {}
    for K in range(start_gw, gw):
        d = json.load(open(decision_file_path(K, version)))
        assert verify_decision_file(d), f'frozen decision file failed hash check: gw{K:02d}-{version}'
        assert d['gw'] == K and d['panel_version'] == version
        for name, p in d['policies'].items():
            state[name] = {
                'squad': {e['pid']: {'pos': e['pos'], 'buy': e['buy'], 'team': e['team']} for e in p['squad']},
                'bank': p['bank_after'], 'fts': p['fts_after'],
                'transfers_total': p['transfers_total_after'], 'hits_total': p['hits_total_after']}
    return state

def freeze(gw, spec_path):
    """Persist the actual pre-deadline policy decisions for GW gw. Never overwrites."""
    specj = json.load(open(spec_path))
    version = specj.get('panel_version', 'v1')
    start_gw = specj['start_gw']
    assert gw >= start_gw, f'freeze gw {gw} before start_gw {start_gw}'
    outpath = decision_file_path(gw, version)
    if os.path.exists(outpath):
        raise SystemExit(f'immutable: {outpath} already exists; frozen decisions are never overwritten')
    if not os.path.exists(DB): build_db()
    # fresh price snapshot at freeze time (the recorded deadline-price approximation)
    boot = api('bootstrap-static/')
    now_cost = {e['id']: int(e['now_cost']) for e in boot['elements']}
    prices_pulled_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    prices_sha = hashlib.sha256(json.dumps(now_cost, sort_keys=True).encode()).hexdigest()
    con = duckdb.connect(DB, read_only=True)
    nsched = con.execute(f'SELECT COUNT(*) FROM epl_schedule WHERE gw::INT = {int(gw)}').fetchone()[0]
    assert nsched > 0, f'no schedule rows for GW {gw}; run refresh-data first'
    dpan = con.execute(decision_sql_for(version, gw)).fetchdf()
    dtr = con.execute(panel_sql_for(version)).fetchdf()
    con.close()
    if version == 'v2':
        # identical eligibility outcome as v1's in-query filter (docs/16)
        dpan = dpan[(dpan.nrows4 == 4) & (dpan.f_minshare4*4*90 >= 180)].copy()
        dtr = dtr[(dtr.nrows4 == 4) & (dtr.f_minshare4*4*90 >= 180)].copy()
    bt.SEASONS = TRAIN + [SEASON]
    prices = bt.load_prices()
    dtr = dtr[dtr.season.isin(TRAIN)]  # fit rows only; the decision view owns SEASON rows
    df = pd.concat([dtr, dpan], ignore_index=True)
    te = bt.fit_and_prep(df, TRAIN, SEASON, prices)
    te = te[te.k == gw]  # decision rows only (fit_and_prep also passes played 2026-27 rows through)
    te['value'] = [now_cost.get(p) for p in te.player_id]  # freeze-time deadline prices
    byk = te.set_index('player_id')
    def price(k, pid):
        v = now_cost.get(pid)
        if v is not None: return v
        for kk in range(k - 1, 0, -1):
            v = prices.get((SEASON, kk, pid))
            if v is not None: return v
        return None
    prior = _load_prior_state(gw, version, specj) if gw > start_gw else {}
    prov = json.load(open(os.path.join(CACHE, f'{SEASON}-provenance.json')))
    out = {'kind': 'frozen pre-deadline policy decisions (docs/13/16)',
           'panel_version': version, 'season': SEASON, 'gw': int(gw),
           'frozen_at': prices_pulled_at,
           'gw_deadline': specj.get('gw10_deadline') if gw == specj['start_gw'] else None,
           'inputs': {'played_rows': f'gw < {int(gw)} from {SEASON}-merged_gw.csv',
                      'csv_sha256': prov['csv_sha256'], 'csv_pulled_at': prov['pulled_at'],
                      'schedule': f'{SEASON}-schedule.csv (epl_schedule, {nsched} rows at GW {gw})',
                      'prices': 'bootstrap-static now_cost', 'prices_pulled_at': prices_pulled_at,
                      'prices_sha256': prices_sha},
           'code': {'repo': 'ziqian83/epl-fpl-analytics',
                    'runner_blob_sha1': _blob('scripts/prospective-12thman.py'),
                    'backtest_blob_sha1': _blob('scripts/backtest-12thman-constrained.py'),
                    'fit_panel_source_blob_sha1': _blob('scripts/fit-12thman-model.py' if version == 'v1'
                                                        else 'scripts/fit-12thman-model-v2.py')},
           'policies': {}}
    for pol in specj['policies']:
        name, key = pol['name'], pol['key']
        sigkey = 'pred' if key == 'hold' else key
        if gw == start_gw:
            initkey = 'f_pts4' if specj['builder'] == 'form' else ('pred' if key in ('pred', 'random', 'hold') else key)
            squad, club, spent = bt.build_squad(byk, initkey, strategy=specj['builder'])
            if len(squad) < 15: raise SystemExit(f'{name}: cannot field 15 from the decision panel')
            bank, fts, moves, hits_w = bt.BUDGET - spent, 0, [], 0
            tr_total, hit_total = 0, 0
        else:
            st = prior[name]
            squad = {pid: {'pos': w['pos'], 'buy': w['buy']} for pid, w in st['squad'].items()}
            club = {}
            for pid, w in st['squad'].items(): club[w['team']] = club.get(w['team'], 0) + 1
            bank, fts = st['bank'], min(bt.FT_CAP, st['fts'] + 1)
            tr_total, hit_total = st['transfers_total'], st['hits_total']
            if key == 'hold':
                moves, hits_w = [], 0
            else:
                wk = bt.transfer_week(squad, club, bank, fts, byk, gw, price, pol['margin'], key)
                bank, fts, moves, hits_w = wk['bank'], wk['fts'], wk['moves'], wk['hits']
                tr_total += wk['transfers']; hit_total += hits_w
        sig = {pid: (float(byk.loc[pid][sigkey]) if pid in byk.index else 0.0) for pid in squad}
        rows = [(pid, squad[pid]['pos'], sig[pid]) for pid in squad]
        xi, bench, cap, vice = bt.pick_team(rows)
        out['policies'][name] = {
            'squad': [{'pid': pid, 'pos': w['pos'],
                       'team': (byk.loc[pid]['team'] if pid in byk.index else
                                prior[name]['squad'][pid]['team']),
                       'buy': w['buy']} for pid, w in squad.items()],
            'bank_after': int(bank), 'fts_before': int(fts + len([m for m in moves if m[4] == 'ft'])) if moves else int(fts),
            'fts_after': int(fts),
            'transfers': [{'out': m[0], 'in': m[1], 'sell': m[2], 'cost': m[3], 'kind': m[4]} for m in moves],
            'hits_this_gw': int(hits_w),
            'transfers_total_after': int(tr_total), 'hits_total_after': int(hit_total),
            'xi': [int(p) for p in xi], 'bench': [int(p) for p in bench],
            'captain': int(cap), 'vice': int(vice), 'signal_key': sigkey}
    out['content_sha256'] = _decision_hash(out)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, 'w') as f:
        json.dump(out, f, indent=2)
    for name, p in out['policies'].items():
        print(f"  {name}: {len(p['transfers'])} transfers, xi {p['xi']}, cap {p['captain']}")
    print('froze', outpath)

def score_frozen(gw, spec_path):
    """Score GW gw from the FROZEN decisions (never reconstructed) once official
    points including bonus are final. Appends to the version-labelled results file."""
    specj = json.load(open(spec_path))
    version = specj.get('panel_version', 'v1')
    dpath = decision_file_path(gw, version)
    if not os.path.exists(dpath):
        raise SystemExit(f'no frozen decisions at {dpath}: freeze --gw {int(gw)} must run before scoring')
    d = json.load(open(dpath))
    assert verify_decision_file(d), 'frozen decision file failed hash check'
    prov = json.load(open(os.path.join(CACHE, f'{SEASON}-provenance.json')))
    assert int(gw) in prov['completed_gws'], (f'GW {gw} not complete in the snapshot '
                                              f'(completed: {prov["completed_gws"]}); refresh-data once official points are final')
    con = duckdb.connect(DB, read_only=True)
    act = {p: (pts, mins) for p, pts, mins in con.execute(
        f"""SELECT player_id, SUM(total_points)::DOUBLE, SUM(minutes)::DOUBLE
            FROM epl_fpl_gameweeks WHERE season='{SEASON}' AND gw::INT={int(gw)}
            GROUP BY player_id""").fetchall()}
    con.close()
    rpath = results_path_for(version)
    if os.path.exists(rpath):
        res = json.load(open(rpath))
        assert res.get('panel_version') == version
    else:
        res = {'spec': os.path.basename(spec_path), 'panel_version': version,
               'decision_source': 'frozen pre-deadline decisions (12th-man/v2/data/frozen/decisions/)',
               'provenance': prov, 'policies': {}}
    for name, p in d['policies'].items():
        pol = res['policies'].setdefault(name, {'weekly': {}, 'total': 0.0, 'transfers': 0, 'hits': 0})
        if str(gw) in pol['weekly']:
            raise SystemExit(f'immutable: {name} already scored for GW {gw} in {rpath}')
        posmap = {e['pid']: e['pos'] for e in p['squad']}
        pts = bt.score_gw(p['xi'], p['bench'], p['captain'], p['vice'], posmap, act)
        pol['weekly'][str(gw)] = {'pts': round(pts, 1), 'transfers': len(p['transfers']),
                                  'hits': p['hits_this_gw']}
        pol['total'] = round(sum(w['pts'] for w in pol['weekly'].values()), 1)
        pol['transfers'] = p['transfers_total_after']
        pol['hits'] = p['hits_total_after']
        pol['net'] = round(pol['total'] - 4 * pol['hits'], 1)
        print(f"  {name}: GW{gw} {pts:.1f} pts (total {pol['total']}, net {pol['net']})")
    res['scored_through_gw'] = int(gw)
    with open(rpath, 'w') as f:
        json.dump(res, f, indent=2)
    print('scored ->', rpath)

def _blob(path):
    import subprocess
    return subprocess.run(['git', 'hash-object', path], capture_output=True, text=True, cwd=ROOT).stdout.strip()

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
                'GW': h['round'], 'fixture': h['fixture'], 'element': e['id'], 'position': posmap[e['element_type']],
                'team': teams[team_id], 'minutes': h['minutes'], 'total_points': h['total_points'],
                'expected_goal_involvements': h['expected_goal_involvements'],
                'was_home': h['was_home'], 'team_h_score': h['team_h_score'],
                'team_a_score': h['team_a_score'], 'opponent_team': h['opponent_team'],
                'value': h['value']})
        if (i + 1) % 100 == 0: print(f'  pulled {i+1}/{len(elems)} players', flush=True)
        time.sleep(0.05)
    cols = ['GW', 'fixture', 'element', 'position', 'team', 'minutes', 'total_points',
            'expected_goal_involvements', 'was_home', 'team_h_score', 'team_a_score',
            'opponent_team', 'value']
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f'{SEASON}-merged_gw.csv')
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    sha = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    # schedule pairs (one row per team per fixture): the pre-deadline opponent mapping
    # for the forward decision view; includes future GWs
    with open(os.path.join(CACHE, f'{SEASON}-schedule.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['gw', 'team', 'opponent_team_id'])
        nsched = 0
        for fx in fixtures.values():
            if not fx.get('event'): continue
            w.writerow([fx['event'], teams[fx['team_h']], fx['team_a']])
            w.writerow([fx['event'], teams[fx['team_a']], fx['team_h']])
            nsched += 2
    # price snapshot at pull time (freeze re-pulls bootstrap for its own snapshot)
    with open(os.path.join(CACHE, f'{SEASON}-prices.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['element', 'now_cost'])
        for e in elems: w.writerow([e['id'], e['now_cost']])
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
            'schedule_rows': nsched,
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
    if 'fixture' not in gw.columns:
        # snapshot predates the fixture column (e.g. the 31 Oct 2026 2026-27 pull);
        # v1 runs tolerate this, v2 refuses at run() below
        gw['fixture'] = None
        print('WARNING: cache lacks fixture ids; panel v2 will refuse to run until refresh-data')
    keep = ['season', 'gw', 'fixture', 'player_id', 'position', 'team', 'minutes', 'total_points',
            'expected_goal_involvements', 'was_home', 'team_a_score', 'team_h_score', 'opponent_team_id']
    con.register('gw_stage', gw[keep])
    con.execute('CREATE TABLE epl_fpl_gameweeks AS SELECT * FROM gw_stage')
    con.register('teams_stage', pd.concat(teams, ignore_index=True))
    con.execute('CREATE TABLE epl_teams AS SELECT * FROM teams_stage')
    sched_path = os.path.join(CACHE, f'{SEASON}-schedule.csv')
    if os.path.exists(sched_path):
        sch = pd.read_csv(sched_path)
        sch['season'] = SEASON
        con.register('sched_stage', sch[['season', 'gw', 'team', 'opponent_team_id']])
        con.execute('CREATE TABLE epl_schedule AS SELECT * FROM sched_stage')
    else:
        con.execute('CREATE TABLE epl_schedule(season VARCHAR, gw BIGINT, team VARCHAR, opponent_team_id BIGINT)')
        print('WARNING: no schedule snapshot; freeze cannot run until refresh-data')
    # build-time fixture integrity assertions (fail loudly, not silently); same check as fit v2
    bad = con.execute("""SELECT COUNT(*) FROM (SELECT season, fixture FROM epl_fpl_gameweeks
        WHERE fixture IS NOT NULL
        GROUP BY season, fixture HAVING COUNT(DISTINCT (team_h_score, team_a_score)) > 1
        OR COUNT(DISTINCT team) <> 2)""").fetchone()[0]
    assert bad == 0, f'fixture integrity violated in {bad} fixtures'
    con.close()
    print('db built:', DB)

def replay(spec_path):
    """DIAGNOSTIC replay: reconstructs decisions after outcome rows exist. Outputs go
    to prospective-2026-27-replay*.json and are NOT the prospective record; the record
    comes from freeze (pre-deadline) + score-gw (post-completion)."""
    specj = json.load(open(spec_path))
    version = specj.get('panel_version', 'v1')
    start_gw = specj['start_gw']
    assert specj['season'] == SEASON and specj['ft_cap'] == bt.FT_CAP
    if not os.path.exists(DB): build_db()
    panel_sql = panel_sql_for(version)
    con = duckdb.connect(DB, read_only=True)
    if version == 'v2':
        nnull = con.execute('SELECT COUNT(*) FROM epl_fpl_gameweeks WHERE fixture IS NULL').fetchone()[0]
        assert nnull == 0, (f'{nnull} rows lack fixture ids; re-run refresh-data '
                            '(the cached snapshot predates the fixture column)')
    df = con.execute(panel_sql).fetchdf()
    if version == 'v2':
        # v1's SQL applies eligibility in-query; v2 keeps the full panel for its
        # diagnostics columns, so apply the identical outcome here (docs/16)
        df = df[(df.nrows4 == 4) & (df.f_minshare4*4*90 >= 180)].copy()
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
    results = {'spec': os.path.basename(spec_path), 'panel_version': version,
               'kind': 'REPLAY DIAGNOSTIC (post-outcome reconstruction; not the prospective record)',
               'scored_through_gw': max(complete) if complete else None,
               'provenance': prov, 'policies': {}}
    for pol in specj['policies']:
        weekly, cum = {}, (0.0, 0, 0)
        for K in complete:
            te = te_full[te_full.k <= K]
            if pol['key'] == 'hold':
                t = bt.simulate_hold(te, prices, act_s, start=specj['builder'])
                r = None if t is None else (t, 0, 0, None)
            else:
                r = bt.simulate(te, prices, act_s, pol['margin'], key=pol['key'], start=specj['builder'])
            if r is None: continue
            total, tr, hits, _ = r
            weekly[str(K)] = {'pts': round(total - cum[0], 1), 'transfers': tr - cum[1], 'hits': hits - cum[2]}
            cum = (total, tr, hits)
        results['policies'][pol['name']] = {
            'weekly': weekly, 'total': round(cum[0], 1), 'transfers': cum[1], 'hits': cum[2]}
        print(f"  {pol['name']}: total {cum[0]:.1f} ({cum[1]} tr, {cum[2]} hits) through GW {max(complete) if complete else '-'}")
    out = replay_path_for(version)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as f:
        json.dump(results, f, indent=2)
    print('wrote', out)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['refresh-data', 'build-db', 'replay', 'run', 'freeze', 'score-gw'])
    ap.add_argument('--spec', default=os.path.join(ROOT, '12th-man', 'v2', 'data', 'frozen', 'prospective-2026-27-spec.json'))
    ap.add_argument('--gw', type=int)
    a = ap.parse_args()
    if a.cmd == 'run':
        print("NOTE: 'run' is renamed 'replay' (post-outcome diagnostic); use freeze/score-gw for the record", file=sys.stderr)
    cmds = {'refresh-data': refresh_data, 'build-db': build_db,
            'replay': lambda: replay(a.spec), 'run': lambda: replay(a.spec),
            'freeze': lambda: freeze(a.gw, a.spec), 'score-gw': lambda: score_frozen(a.gw, a.spec)}
    if a.cmd in ('freeze', 'score-gw'):
        assert a.gw, f'{a.cmd} needs --gw'
    cmds[a.cmd]()
