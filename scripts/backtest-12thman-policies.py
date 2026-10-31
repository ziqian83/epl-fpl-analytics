#!/usr/bin/env python3
"""The 12th Man - decision-level backtest: when is acting on a projected edge worth it?

The model's docs/09 validation shows individual-level fit (MAE ~2.3) and weak
pairwise lift. Neither answers the product question: does ACTING on a predicted
transfer edge beat holding, and at what bar? This script tests that directly on
held-out seasons with the same leakage-safe, rolling-origin fit as
fit-12thman-model.py.

Design: within each held-out GW and position, every ordered pair (sell i, buy j)
is a candidate swap. Predicted edge = pred_j - pred_i; realized edge =
actual_j - actual_i. Policies: "transfer when edge > k" for a grid of k, and
"take a hit when edge > 4" (hit cost 4 certain). We report n acted, mean
realized edge, and hit-policy net. No ownership or budget model - pairs are
unrestricted within position, so absolute levels are optimistic; the SHAPE of
the curve vs k is the decision-relevant output.

Run after fit-12thman-model.py has built the DB:  python3 scripts/backtest-12thman-policies.py [--db /tmp/epl12_fit.duckdb]
"""
import argparse
import duckdb, numpy as np

# Reuse the exact panel SQL from the fit script to guarantee identical features.
import re, os
fit_src = open(os.path.join(os.path.dirname(__file__), 'fit-12thman-model.py')).read()
PANEL_SQL = re.search(r'PANEL_SQL = """(.*?)"""', fit_src, re.S).group(1)
SEASONS = ['2021-22', '2022-23', '2023-24', '2024-25', '2025-26']

def design(d):
    pos = d.position.map({'GKP': 0, 'DEF': 1, 'MID': 2, 'FWD': 3}).fillna(2).values
    return np.column_stack([np.ones(len(d)), d.f_pts4, d.f_xgi4, d.f_minshare4, d.opp_strength_k,
                            (pos == 0), (pos == 1), (pos == 3)]).astype(float)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='/tmp/epl12_fit.duckdb')
    args = ap.parse_args()
    con = duckdb.connect(args.db, read_only=True)
    df = con.execute(PANEL_SQL).fetchdf()
    con.close()
    for testseason, trainseasons in [('2024-25', SEASONS[:3]), ('2025-26', SEASONS[:4])]:
        tr = df[df.season.isin(trainseasons)]; te = df[df.season == testseason].copy()
        coef, *_ = np.linalg.lstsq(design(tr), tr.target_pts.values, rcond=None)
        te['pred'] = design(te) @ coef
        # aggregate over all within-position pairs per GW, vectorized per group
        acted = {k: [] for k in [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]}
        hit = []
        for (k, pos), grp in te.groupby(['k', 'position']):
            p = grp.pred.values; a = grp.target_pts.values
            if len(grp) < 2: continue
            edge = p[None, :] - p[:, None]          # buy j, sell i
            real = a[None, :] - a[:, None]
            m = ~np.eye(len(grp), dtype=bool)
            for bar in acted:
                sel = (edge > bar) & m
                if sel.any(): acted[bar].append(real[sel].mean())
            sel = (edge > 4.0) & m
            if sel.any(): hit.append((real[sel] - 4.0).mean())
        print(f'--- {testseason}: mean realized edge (buy - sell) when acting at bar k')
        for bar, v in acted.items():
            print(f'  k>{bar:<4} gw-groups={len(v):<4} mean realized {np.mean(v):+.3f} pts')
        print(f'  hit policy (edge>4, cost 4): gw-groups={len(hit)} mean net {np.mean(hit):+.3f} pts')

if __name__ == '__main__':
    main()
