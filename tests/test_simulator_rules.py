"""Unit tests for the 12th Man constrained-backtest simulator rules (2026/27 FPL rules).
Run: python3 tests/test_simulator_rules.py  (from repo root; needs numpy/pandas/duckdb env)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import importlib.util
spec = importlib.util.spec_from_file_location('bt', os.path.join(os.path.dirname(__file__), '..', 'scripts', 'backtest-12thman-constrained.py'))
bt = importlib.util.module_from_spec(spec); spec.loader.exec_module(bt)

ok = 0
def chk(name, cond):
    global ok
    assert cond, f'FAIL: {name}'
    ok += 1; print(f'  ok: {name}')

# --- pricing: official sell-price rounding (profit halved, rounded down) ---
chk('sell rounds half-profit down', bt.sell_price(60, 75) == 67)   # 7.5 profit -> +7
chk('sell exact half-profit', bt.sell_price(60, 70) == 65)
chk('sell price fall passes through', bt.sell_price(60, 55) == 55)
chk('sell no change', bt.sell_price(60, 60) == 60)

# --- formation legality set matches official legal formations ---
for fm in [(3,4,3),(3,5,2),(4,4,2),(4,3,3),(4,5,1),(5,4,1),(5,3,2),(5,2,3)]:
    chk(f'formation {fm} legal', fm in bt.LEGAL_SET)
for fm in [(3,3,4),(2,4,4),(4,2,4),(3,6,1),(2,5,3)]:
    chk(f'formation {fm} illegal', fm not in bt.LEGAL_SET)
chk('FT storage cap is 5 (2024/25 rule)', bt.FT_CAP == 5)

# --- pick_team: legal XI, bench order, captain/vice from as-of signal only ---
def squad_rows(seed=1):
    import random; rng = random.Random(seed)
    rows = []
    for i in range(2): rows.append((1000+i, 'GKP', rng.random()))
    for i in range(5): rows.append((2000+i, 'DEF', rng.random()))
    for i in range(5): rows.append((3000+i, 'MID', rng.random()))
    for i in range(3): rows.append((4000+i, 'FWD', rng.random()))
    return rows

rows = squad_rows()
xi, bench, cap, vice = bt.pick_team(rows)
pos = {pid: p for pid, p, _ in rows}
chk('XI has 11, bench 4', len(xi) == 11 and len(bench) == 4)
chk('squad fully partitioned', sorted(xi + bench) == sorted(pid for pid, _, _ in rows))
chk('exactly one GK in XI, GK last on bench', sum(pos[p]=='GKP' for p in xi) == 1 and pos[bench[-1]] == 'GKP')
d = sum(pos[p]=='DEF' for p in xi); m = sum(pos[p]=='MID' for p in xi); f = sum(pos[p]=='FWD' for p in xi)
chk(f'picked formation ({d},{m},{f}) legal', (d,m,f) in bt.LEGAL_SET)
sig = {pid: s for pid, s, _ in [(r[0], r[1], r[2]) for r in rows]}
sig = {r[0]: r[2] for r in rows}
chk('captain is highest-signal starter', cap == max(xi, key=lambda p: sig[p]))
chk('vice is second-highest-signal starter', vice == sorted(xi, key=lambda p: -sig[p])[1])

# --- score_gw: real auto-subs, captain double, vice on captain absence ---
# XI: GKP 1, DEF 4, MID 4, FWD 2 (4-4-2). Bench: MID b1, DEF b2, FWD b3, GKP bgk.
xi = [1, 10, 11, 12, 13, 20, 21, 22, 23, 30, 31]
bench = [24, 14, 32, 2]
posmap = {1:'GKP', 2:'GKP', 10:'DEF', 11:'DEF', 12:'DEF', 13:'DEF', 14:'DEF',
          20:'MID', 21:'MID', 22:'MID', 23:'MID', 24:'MID', 30:'FWD', 31:'FWD', 32:'FWD'}
act = {p: (5.0, 90.0) for p in xi + bench}
act[10] = (0.0, 0.0)   # starter DEF 10 does not play
# bench order: MID 24 first -> subbing 24 in for DEF 10 gives (3,5,2) legal -> sub applies
t = bt.score_gw(xi, bench, 30, 31, posmap, act)
chk('auto-sub brings first legal bench player in', t == 11*5 + 5)  # 11 players *5 + captain 5 double
# captain misses -> vice doubles
act2 = dict(act); act2[30] = (0.0, 0.0); act2[31] = (6.0, 90.0)
# now both DEF 10 and FWD 30 miss; bench 24 (MID) covers 10 -> (3,5,2); then b2 DEF 14 covers 30 -> (4,5,1) legal
t2 = bt.score_gw(xi, bench, 30, 31, posmap, act2)
chk('vice-captain doubles when captain absent', t2 == sum(5.0 for _ in range(10)) + 6.0 + 6.0)
# GK auto-sub: starting GK out -> bench GK in
act3 = dict(act); act3[1] = (0.0, 0.0); act3[2] = (4.0, 90.0); act3[10] = (5.0, 90.0)
t3 = bt.score_gw(xi, bench, 30, 31, posmap, act3)
chk('bench GK subs for starting GK', t3 == 10*5 + 4 + 5)
# illegal sub blocked: make every bench player a MID with 0 minutes for DEF gap that would break d>=3
act4 = {p: (5.0, 90.0) for p in xi + bench}
act4[10] = (0.0, 0.0); act4[14] = (0.0, 0.0); act4[24] = (0.0, 0.0)  # no playing bench player for the DEF hole except FWD 32
act4[32] = (0.0, 0.0)
t4 = bt.score_gw(xi, bench, 30, 31, posmap, act4)
chk('no playing bench cover -> 10 men score', t4 == 10*5 + 5)
# minutes come from act, not panel membership: a player absent from act scores 0 and is subbed
act5 = {p: (5.0, 90.0) for p in xi + bench}; del act5[10]; act5[24] = (7.0, 60.0)
t5 = bt.score_gw(xi, bench, 30, 31, posmap, act5)
chk('player missing from data treated as 0 min and auto-subbed', t5 == 10*5 + 7 + 5)

# --- build_squad: 15 players, position quotas, budget respected ---
import pandas as pd
df = pd.DataFrame({
    'player_id': list(range(1, 61)),
    'position': ['GKP']*8 + ['DEF']*20 + ['MID']*20 + ['FWD']*12,
    'team': [f'T{i%7}' for i in range(60)],
    'value': [float(40 + (i % 10)) for i in range(60)],
    'pred': [float((i * 7) % 23) for i in range(60)],
    'f_pts4': [float((i * 5) % 19) for i in range(60)],
}).set_index('player_id')
for strat in ('signal', 'form', 'signal_per_price'):
    squad, club, spent = bt.build_squad(df, 'pred' if strat != 'form' else 'f_pts4', strategy=strat)
    counts = {}
    for v in squad.values(): counts[v['pos']] = counts.get(v['pos'], 0) + 1
    chk(f'build_squad[{strat}] quotas 2/5/5/3', counts == {'GKP':2, 'DEF':5, 'MID':5, 'FWD':3})
    chk(f'build_squad[{strat}] within 100.0m budget and club cap 3', spent <= 1000 and max(club.values()) <= 3)

print(f'ALL {ok} SIMULATOR RULE CHECKS PASSED')
