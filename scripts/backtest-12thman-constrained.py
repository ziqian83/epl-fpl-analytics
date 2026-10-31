#!/usr/bin/env python3
"""The 12th Man - SQUAD-CONSTRAINED decision backtest (budget, sell values, FT banking, hits).

The unrestricted dynamic comparison in backtest-12thman-policies.py answers "does acting
beat holding" in a diagnostic frame. This script replays the same question under real FPL
constraints so the numbers can support (or kill) a recommendation-reliability claim:

  - 15-man squad under the GBP 100.0m starting budget, club cap 3, position quotas.
  - Prices from the pinned vaastav merged_gw snapshots (value, tenths of GBPm).
  - Sell value = buy price + floor(profit / 2) (current price if it fell).
  - Free transfers bank week to week, capped at 5 (the rule in force for the held-out
    seasons 2024-25 and 2025-26); extra transfers cost -4 each and are only taken when
    the predicted edge clears the margin PLUS the certain 4-point cost.
  - Buys use the price at the target GW's row (price at that deadline) - a documented
    approximation, identical across all policies and comparators.

Policies: hold (never transfer), model-driven at margins 0/1/2, persistence heuristic
(f_pts4, no model), random legal swap (5 seeds). All share the same greedy starting-squad
builder, so differences are the transfer policy, not the start. Leakage-safe: predictions
come from the same rolling-origin lstsq fit as fit-12thman-model.py; decisions for GW k+1
use only as-of features and prices no later than that deadline.

Run after fit-12thman-model.py has built the DB:  python3 scripts/backtest-12thman-constrained.py [--db /tmp/epl12_fit.duckdb]
"""
import argparse, os, re, csv
import duckdb, numpy as np

fit_src = open(os.path.join(os.path.dirname(__file__), 'fit-12thman-model.py')).read()
PANEL_SQL = re.search(r'PANEL_SQL = """(.*?)"""', fit_src, re.S).group(1)
SEASONS = ['2021-22', '2022-23', '2023-24', '2024-25', '2025-26']
CACHE = os.path.join(os.path.dirname(__file__), '..', '.fit-cache')

def design(d):
    pos = d.position.map({'GKP': 0, 'DEF': 1, 'MID': 2, 'FWD': 3}).fillna(2).values
    return np.column_stack([np.ones(len(d)), d.f_pts4, d.f_xgi4, d.f_minshare4, d.opp_strength_k,
                            (pos == 0), (pos == 1), (pos == 3)]).astype(float)

QUOTA = {'GKP': 2, 'DEF': 5, 'MID': 5, 'FWD': 3}
FORMATIONS = [(3, 4, 3), (3, 5, 2), (4, 4, 2), (4, 3, 3), (4, 5, 1), (5, 3, 2), (5, 4, 1), (5, 2, 3)]
FT_CAP = 5
BUDGET = 1000  # tenths of GBPm

def best_xi_points(rows, cap_pts=None):
    """Max realized XI points from squad rows (position, points). Captain (as-of chosen)
    doubles: pass his realized points as cap_pts and the best XI including him adds them once more."""
    by = {p: sorted((a for pos, a in rows if pos == p), reverse=True) for p in QUOTA}
    if not by['GKP']: return 0.0
    best = by['GKP'][0]
    top = 0.0
    for d, m, f in FORMATIONS:
        if len(by['DEF']) >= d and len(by['MID']) >= m and len(by['FWD']) >= f:
            top = max(top, sum(by['DEF'][:d]) + sum(by['MID'][:m]) + sum(by['FWD'][:f]))
    return best + top + (cap_pts or 0.0)

def load_prices():
    """{(season, gw, player_id): value} from the pinned cache snapshots. DGW rows deduped."""
    out = {}
    for s in SEASONS:
        path = os.path.join(CACHE, f'{s}-merged_gw.csv')
        with open(path, encoding='latin-1') as fh:
            for row in csv.DictReader(fh):
                key = (s, int(row['GW']), int(row['element']))
                out[key] = int(row['value'])  # later DGW row overwrites; same value
    return out

def build_squad(first, initkey, strategy='signal'):
    """Reserve-aware greedy: rank by the strategy's key, add a player only if the remaining
    budget can still cover the cheapest available player for every unfilled slot.
    Guarantees a full 15 under the budget whenever the pool allows it."""
    pool = first[first.value.notna()].copy()
    if strategy == 'signal_per_price':
        pool['_k'] = pool[initkey] / pool.value
    else:
        pool['_k'] = pool[initkey]
    order = pool.sort_values('_k', ascending=False)
    cheapest = {p: order[order.position == p].value.min() for p in QUOTA}
    squad, club, spent = {}, {}, 0
    for pid, r in order.iterrows():
        pos = r.position
        if sum(1 for v in squad.values() if v['pos'] == pos) >= QUOTA[pos]: continue
        if club.get(r.team, 0) >= 3: continue
        # reserve for the other slots still open after this pick
        need = 0
        for p, n in QUOTA.items():
            filled = sum(1 for v in squad.values() if v['pos'] == p) + (1 if p == pos else 0)
            need += max(0, n - filled) * (cheapest[p] if np.isfinite(cheapest[p]) else 0)
        if spent + r.value + need > BUDGET: continue
        squad[pid] = {'pos': pos, 'buy': int(r.value)}
        club[r.team] = club.get(r.team, 0) + 1
        spent += int(r.value)
        if len(squad) == 15: break
    return squad, club, spent

def simulate(te, prices, margin, key='pred', seed=None, always_one=False, gate=0.0, start='signal'):
    """Constrained weekly simulation. Returns (total, transfers, hits, end_value)."""
    rng = np.random.default_rng(seed if seed is not None else 11)
    gws = sorted(te.k.unique())
    byk = {k: g.set_index('player_id') for k, g in te.groupby('k')}
    def price(k, pid):
        # price at GW k's deadline; fall back to the most recent earlier price
        v = prices.get((te.season.iloc[0], k, pid))
        if v is None:
            for kk in range(k - 1, 0, -1):
                v = prices.get((te.season.iloc[0], kk, pid))
                if v is not None: break
        return v
    # --- starting squad: reserve-aware greedy under budget, quotas, club cap 3
    first = byk[gws[0]]
    initkey = 'f_pts4' if start == 'form' else ('pred' if key in ('pred', 'random') else key)
    squad, club, spent = build_squad(first, initkey, strategy=start)
    if len(squad) < 15:
        return None  # cannot field a squad - season data problem
    bank = BUDGET - spent
    max_fts_seen = 0
    total, transfers, hits, fts = 0.0, 0, 0, 0
    for i, k in enumerate(gws):
        cur = byk[k]
        # Panel-missing squad members still occupy their slot and score 0 (a real squad
        # keeps an injured/benched player; he does not vanish). Excluding them collapses
        # the formation picker and under-credits hold.
        rows = [(squad[pid]['pos'], float(cur.loc[pid].target_pts) if pid in cur.index else 0.0) for pid in squad]
        # captain: highest as-of signal in the squad this GW (policy's own key); realized points double.
        cappid, capsig = None, None
        for pid in squad:
            if pid in cur.index:
                sg = float(cur.loc[pid][key]) if key in cur.columns else 0.0
                if capsig is None or sg > capsig: cappid, capsig = pid, sg
        cap_pts = float(cur.loc[cappid].target_pts) if cappid is not None else 0.0
        total += best_xi_points(rows, cap_pts=cap_pts)
        if i + 1 >= len(gws): break
        fts = min(FT_CAP, fts + 1)
        max_fts_seen = max(max_fts_seen, fts)
        nk = gws[i + 1]
        nxt = byk[nk]
        while True:
            best = None
            cands = None
            if key == 'random': cands = []
            for pid_w, w in squad.items():
                if pid_w not in nxt.index: continue
                pw = price(nk, pid_w)
                if pw is None: continue
                sell_w = w['buy'] + max(0, (pw - w['buy']) // 2) if pw >= w['buy'] else pw
                row_w = nxt.loc[pid_w]
                for pid_b, row_b in nxt.iterrows():
                    if pid_b in squad or row_b.position != w['pos']: continue
                    pb = row_b.value
                    if not np.isfinite(pb): continue
                    if int(pb) > sell_w + bank: continue
                    if gate and row_b.f_minshare4 < gate: continue  # consistency gate: cameo form is not evidence
                    if club.get(row_b.team, 0) - (1 if row_b.team == row_w.team else 0) >= 3: continue
                    if key == 'random':
                        cands.append((0.0, pid_w, pid_b, sell_w, int(pb), row_w.team, row_b.team))
                    else:
                        gain = row_b[key] - row_w[key]
                        if best is None or gain > best[0]:
                            best = (gain, pid_w, pid_b, sell_w, int(pb), row_w.team, row_b.team)
            if key == 'random':
                if not cands or fts <= 0: break
                best = cands[rng.integers(len(cands))]
                gain, pid_w, pid_b, sell_w, cost_b, t_w, t_b = best
                fts -= 1
                bank += sell_w - cost_b
                assert bank >= 0, 'bank went negative'
                club[t_w] -= 1; club[t_b] = club.get(t_b, 0) + 1
                squad[pid_b] = {'pos': squad[pid_w]['pos'], 'buy': cost_b}
                del squad[pid_w]
                assert len(squad) == 15
                transfers += 1
                break  # random takes one swap per week
            if best is None: break
            gain, pid_w, pid_b, sell_w, cost_b, t_w, t_b = best
            if fts > 0 and gain > margin:
                fts -= 1
            elif gain > margin + 4:
                hits += 1
            else:
                break
            bank += sell_w - cost_b
            assert bank >= 0, 'bank went negative'
            club[t_w] -= 1; club[t_b] = club.get(t_b, 0) + 1
            squad[pid_b] = {'pos': squad[pid_w]['pos'], 'buy': cost_b}
            del squad[pid_w]
            assert len(squad) == 15
            transfers += 1
            if always_one: break
    lastk = gws[-1]
    end_value = bank + sum((lambda pw, w: (w['buy'] + max(0, (pw - w['buy']) // 2) if pw and pw >= w['buy'] else (pw or w['buy'])))(price(lastk, pid), w) for pid, w in squad.items())
    return total, transfers, hits, end_value

def simulate_hold(te, prices, start='signal'):
    gws = sorted(te.k.unique())
    byk = {k: g.set_index('player_id') for k, g in te.groupby('k')}
    first = byk[gws[0]]
    squad_d, club, spent = build_squad(first, 'f_pts4' if start == 'form' else 'pred', strategy=start)
    squad = {pid: v['pos'] for pid, v in squad_d.items()}
    total = 0.0
    for k in gws:
        cur = byk[k]
        rows = [(squad[pid], float(cur.loc[pid].target_pts) if pid in cur.index else 0.0) for pid in squad]
        cappid, capsig = None, None
        for pid in squad:
            if pid in cur.index:
                sg = float(cur.loc[pid].pred)
                if capsig is None or sg > capsig: cappid, capsig = pid, sg
        cap_pts = float(cur.loc[cappid].target_pts) if cappid is not None else 0.0
        total += best_xi_points(rows, cap_pts=cap_pts)
    return total

def fit_and_prep(df, trainseasons, testseason, prices):
    tr = df[df.season.isin(trainseasons)]
    te = df[df.season == testseason].copy()
    coef, *_ = np.linalg.lstsq(design(tr), tr.target_pts.values, rcond=None)
    te['pred'] = design(te) @ coef
    te['value'] = [prices.get((s, k, p)) for s, k, p in zip(te.season, te.k, te.player_id)]
    return te

def score(r, hold):
    if r is None: return None
    tot, ntr, nh, tv = r
    return tot - 4 * nh, tot - 4 * nh - hold, ntr, nh

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='/tmp/epl12_fit.duckdb')
    ap.add_argument('--stage', default='all')
    args = ap.parse_args()
    con = duckdb.connect(args.db, read_only=True)
    df = con.execute(PANEL_SQL).fetchdf()
    con.close()
    prices = load_prices()

    # ---- reproducibility block
    import hashlib, sys, duckdb as _d
    h = hashlib.sha256(df.to_csv(index=False).encode()).hexdigest()[:16]
    print(f'repro: panel sha256[:16]={h} rows={len(df)} | python {sys.version.split()[0]} numpy {np.__version__} duckdb {_d.__version__} | seeds: random policy 0-4 | FT_CAP={FT_CAP} (5 from 2024-25, premierleague.com 2024/25 rules)')

    # ---- STAGE 1 (train-only spec design): fit 2021-22+2022-23, validate on 2023-24.
    # The gate/margin/policy spec chosen HERE is the only thing later evaluated on the
    # 2024-25 and 2025-26 holdouts. Nothing from the holdouts influences the choice.
    if args.stage == '2':
        bp, bg, bm = 'model', 0.8, 1.0  # stage-1 selection (train-only): model gate>=0.8 margin>1.0
    if args.stage == '2':
        print(f'=== STAGE 1 skipped (--stage 2); using train-only selection: model gate>=0.8 margin>1.0')
        inner = None
    else:
        inner = fit_and_prep(df, SEASONS[:2], '2023-24', prices)
    hold_in = simulate_hold(inner, prices) if inner is not None else float('nan')
    print(f'=== STAGE 1 inner validation on 2023-24 (hold={hold_in:.1f}) - spec selection uses ONLY this')
    if args.stage != '2':
        grid = []
        for policy, kk in [('model', 'pred'), ('persistence', 'f_pts4')]:
            for gate in [0.0, 0.5, 0.6, 0.7, 0.8]:
                for margin in [0.0, 1.0]:
                    r = simulate(inner, prices, margin, key=kk, gate=gate)
                    sc = score(r, hold_in)
                    grid.append((sc[1], policy, gate, margin, sc))
                    print(f'  {policy} gate>={gate} margin>{margin}: vs hold {sc[1]:+.1f} ({sc[2]} tr, {sc[3]} hits)')
        grid.sort(reverse=True)
        _, bp, bg, bm, _ = grid[0]
        print(f'  SELECTED SPEC (train-only): {bp} gate>={bg} margin>{bm}')

    # ---- STAGE 2: true holdouts. Baselines + the single selected spec.
    if args.stage == '1': return
    for testseason, trainseasons in [('2024-25', SEASONS[:3]), ('2025-26', SEASONS[:4])]:
        te = fit_and_prep(df, trainseasons, testseason, prices)
        hold = simulate_hold(te, prices)
        print(f'=== STAGE 2 holdout {testseason} (hold={hold:.1f})')
        for m in [0.0, 1.0, 2.0]:
            sc = score(simulate(te, prices, m), hold)
            print(f'  raw model margin>{m}: vs hold {sc[1]:+.1f} ({sc[2]} tr, {sc[3]} hits)')
        sc = score(simulate(te, prices, 0.0, key='f_pts4'), hold)
        print(f'  raw persistence: vs hold {sc[1]:+.1f} ({sc[2]} tr, {sc[3]} hits)')
        rnd = [simulate(te, prices, 0.0, key='random', seed=sd) for sd in range(5)]
        mt = np.mean([x[0] - 4 * x[2] for x in rnd if x])
        print(f'  random (5 seeds): vs hold {mt - hold:+.1f}')
        sc = score(simulate(te, prices, bm, key='pred' if bp == 'model' else 'f_pts4', gate=bg), hold)
        print(f'  SELECTED {bp} gate>={bg} margin>{bm}: vs hold {sc[1]:+.1f} ({sc[2]} tr, {sc[3]} hits)')
        # starting-squad sensitivity: hold + selected spec across 3 builders
        for st in ['signal', 'signal_per_price', 'form']:
            h2 = simulate_hold(te, prices, start=st)
            sc2 = score(simulate(te, prices, bm, key='pred' if bp == 'model' else 'f_pts4', gate=bg, start=st), h2)
            print(f'  start={st}: hold={h2:.1f} selected {sc2[1]:+.1f}')

if __name__ == '__main__':
    main()
