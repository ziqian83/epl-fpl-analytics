#!/usr/bin/env python3
"""Signal inspection: coefficient drift across rolling fit windows (diagnostic, no validation).

The constrained backtest (docs/12) found the model's inner-validation edge did not
generalize. Before changing anything, measure: do the fitted coefficients move across
expanding training windows? Instability here is a candidate explanation. This script only
prints the coefficients per window; it makes no out-of-sample claim.

Run: python3 scripts/inspect-12thman-signals.py [--db /tmp/epl12_fit.duckdb]
"""
import argparse, os, re
import duckdb, numpy as np

fit_src = open(os.path.join(os.path.dirname(__file__), 'fit-12thman-model.py')).read()
PANEL_SQL = re.search(r'PANEL_SQL = """(.*?)"""', fit_src, re.S).group(1)
SEASONS = ['2021-22', '2022-23', '2023-24', '2024-25', '2025-26']
NAMES = ['intercept', 'f_pts4', 'f_xgi4', 'f_minshare4', 'opp_strength_k', 'is_GKP', 'is_DEF', 'is_FWD']

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
    print('feature        ' + ''.join(f'{"thru " + s:>11}' for s in SEASONS[1:]))
    coefs = []
    for i in range(1, len(SEASONS)):
        tr = df[df.season.isin(SEASONS[:i + 1])]
        coef, *_ = np.linalg.lstsq(design(tr), tr.target_pts.values, rcond=None)
        coefs.append(coef)
    coefs = np.array(coefs)
    for j, n in enumerate(NAMES):
        print(f'{n:<15}' + ''.join(f'{c:>11.3f}' for c in coefs[:, j]))
    print('\nmax |drift| (last window - first window):')
    for j, n in enumerate(NAMES):
        print(f'  {n:<15} {coefs[-1, j] - coefs[0, j]:+.3f}')

if __name__ == '__main__':
    main()
