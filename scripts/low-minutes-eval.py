#!/usr/bin/env python3
"""Frozen-spec low-minutes estimator retrospective evaluation (docs/14).

RECONSTRUCTED 31 Oct 2026 AFTER the original interactive run, from the frozen
spec (verbatim in docs/14_low_minutes_evidence.md, appendix). The original run
was executed interactively against /tmp/epl12_fit.duckdb and its code was not
persisted; the original numbers are NOT exactly recoverable. This script is a
reconstruction, not a reproduction of the original implementation.

Known discrepancies vs the docs/14 table (same DB, seed 20261031, deterministic
ORDER BY): C0 MAE-all (0.435 vs 0.436), C0 MAE-played (2.238 vs 2.239), C1
MAE-played (1.489 vs 1.491), C1 bias (+0.000 vs -0.001), C2 MAE-played (1.727
vs 1.729), C2 Spearman (0.142 vs 0.143), C3 MAE-all (0.510 vs 0.511), C3
MAE-played (1.482 vs 1.484), C3 bias (+0.003 vs +0.002), C3 Spearman (0.179
vs 0.178), C3 b90_179 calibration (1.54 vs 1.53), bootstrap CI lower bounds
(C2-C0 -0.012 vs -0.011; C3-C1 -0.011 vs -0.010; C2-C1 +0.237 [+0.215, +0.261]
vs +0.238 [+0.214, +0.261]). Everything else matches at printed precision,
including all band calibration actuals and the C1/C2 calibration rows. These
deltas are reported, not explained away: the original implementation differs
somewhere and where exactly is unknown. Matching confidence intervals would
not establish implementation equivalence. No causal attribution is
established. Candidate contributors, unproven: the original run's tie handling
among same-player-GW fixture rows (5,541 such doubles in this DB; pinned here
by opponent_team_id) and any other unpersisted implementation details. An
aggregated player-GW-grain variant diverges further (C0 0.440, C1 0.522,
C2 0.439, C3 0.521 overall MAE), consistent with - not proof of - the original
having run on raw fixture rows. The rows-vs-calendar limitation below cannot
explain these gaps: both runs used row windows. See docs/15_grain_audit.md.

POPULATION-DEFINITION LIMITATION (material): this script's trailing window is
the player's previous 4 ROWS within the season (missed GWs skipped). The frozen
spec says "trailing-4-GW minutes", and every other pipeline component uses
CALENDAR gameweeks: the model panel, both backtests and the prospective runner
all share one PANEL_SQL (RANGE BETWEEN 4 PRECEDING AND 1 PRECEDING on gw,
nrows4 = 4, >= 180 minutes), and the live gate (scripts/12thman2-refresh.mjs)
slices the last 4 rounds of FPL element-summary history. For players with an
absent trailing row (intermittent players, mid-season signings, data gaps) the
two rules assign different eligibility and bands. Measured scope on this DB
(gw>=5, 126,353 raw fixture rows): 1,683 gate flips (542 rows-gated-only, 1,141
calendar-gated-only), concentrated in 2021-22 (3.06% of that season's rows),
78 flips (0.29%) in the 2025-26 test season; 1,712 band flips among the 87,918
commonly gated rows; trailing minutes differ on 11,791 rows (median 90, max 270
where differing). Read the evaluation conclusions with this mismatch in mind.
Not patched: the spec for this eval was frozen, and the rest of the pipeline is
internally consistent on the calendar rule.

Population of this reconstruction: player-GW rows with gw>=5, trailing minutes =
SUM(minutes) over the player's previous 4 ROWS within the same season, gated-out
= trailing minutes < 180. Trailing form (C2) = AVG(total_points) over the same
previous 4 rows, 0 when no trailing rows.

DB: /tmp/epl12_fit.duckdb, built by scripts/fit-12thman-model.py
(seasons 2021-22..2025-26). Fit 2021-22..2024-25; test 2025-26 (retrospective
chronological; 2025-26 was already inspected in this rebuild - NOT untouched
validation).

Run: python3 scripts/low-minutes-eval.py [--db /tmp/epl12_fit.duckdb]
"""
import argparse, duckdb, math, random

ap = argparse.ArgumentParser()
ap.add_argument('--db', default='/tmp/epl12_fit.duckdb')
ap.add_argument('--seed', type=int, default=20261031)
ap.add_argument('--boot', type=int, default=5000)
args = ap.parse_args()

con = duckdb.connect(args.db, read_only=True)
rows = con.execute("""
WITH r AS (
  -- raw fixture rows: a player-GW with two fixtures is TWO rows here, matching
  -- the original interactive run's grain. Window order among same-GW fixture
  -- rows is pinned by opponent_team_id so the run is deterministic; the
  -- original run's tie handling is unknown.
  SELECT season, gw, player_id, position, minutes, total_points,
    COALESCE(SUM(minutes) OVER (PARTITION BY season, player_id ORDER BY gw, opponent_team_id
      ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING),0) AS trail_min,
    COALESCE(AVG(total_points) OVER (PARTITION BY season, player_id ORDER BY gw, opponent_team_id
      ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING),0) AS trail_form
  FROM epl_fpl_gameweeks
)
SELECT season, gw, player_id, position, minutes, total_points, trail_min, trail_form
FROM r WHERE gw>=5 AND trail_min < 180
ORDER BY season, gw, player_id
""").fetchall()

def band(tm):
    return 'b0' if tm == 0 else ('b1_89' if tm < 90 else 'b90_179')

fit = [r for r in rows if r[0] < '2025-26']
test = [r for r in rows if r[0] == '2025-26']
BANDS = ('b0', 'b1_89', 'b90_179')

# C1: fit-period unconditional band mean (all gated-out rows incl. DNP)
c1 = {b: sum(r[5] for r in fit if band(r[6]) == b) / max(1, sum(1 for r in fit if band(r[6]) == b))
      for b in BANDS}
# C3 parts: P(plays>0|band); E[pts|plays, band x position]; E[pts|DNP] overall
pplay = {}
for b in BANDS:
    sub = [r for r in fit if band(r[6]) == b]
    pplay[b] = sum(1 for r in sub if r[4] > 0) / len(sub)
eplay = {}
for b in BANDS:
    for pos in set(r[3] for r in fit):
        vals = [r[5] for r in fit if band(r[6]) == b and r[3] == pos and r[4] > 0]
        if vals:
            eplay[(b, pos)] = sum(vals) / len(vals)
dnp = [r[5] for r in fit if r[4] == 0]
ednp = sum(dnp) / len(dnp) if dnp else 0.0

P = {c: [] for c in ('C0', 'C1', 'C2', 'C3')}
for r in test:
    b = band(r[6])
    P['C0'].append(0.0)
    P['C1'].append(c1[b])
    P['C2'].append(r[7])
    P['C3'].append(pplay[b] * eplay.get((b, r[3]), c1[b]) + (1 - pplay[b]) * ednp)

act = [r[5] for r in test]
allidx = list(range(len(test)))
played = [i for i, r in enumerate(test) if r[4] > 0]

def mae(p, idx): return sum(abs(p[i] - act[i]) for i in idx) / len(idx)
def bias(p, idx): return sum(p[i] - act[i] for i in idx) / len(idx)

def spearman(p, idx):
    xs = [p[i] for i in idx]; ys = [act[i] for i in idx]
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v); i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            m = (i + j) / 2.0
            for k in range(i, j + 1):
                rk[order[k]] = m
            i = j + 1
        return rk
    rx, ry = ranks(xs), ranks(ys)
    n = len(rx); mx = sum(rx) / n; my = sum(ry) / n
    cov = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    vx = sum((rx[i] - mx) ** 2 for i in range(n)); vy = sum((ry[i] - my) ** 2 for i in range(n))
    return cov / math.sqrt(vx * vy) if vx > 0 and vy > 0 else float('nan')

print("candidate | MAE all | MAE played | bias all | Spearman played")
for c in ('C0', 'C1', 'C2', 'C3'):
    rho = spearman(P[c], played) if c != 'C0' else float('nan')
    print(f"{c}: {mae(P[c], allidx):.3f} | {mae(P[c], played):.3f} | "
          f"{bias(P[c], allidx):+.3f} | {rho:.3f}")

print("calibration per band (mean predicted vs mean actual):")
for b in BANDS:
    idx = [i for i, r in enumerate(test) if band(r[6]) == b]
    a = sum(act[i] for i in idx) / len(idx)
    print(b, "actual", f"{a:.2f}",
          " ".join(f"{c}={sum(P[c][i] for i in idx) / len(idx):.2f}" for c in ('C1', 'C2', 'C3')))

random.seed(args.seed)
players = {}
for i, r in enumerate(test):
    players.setdefault(r[2], []).append(i)
pl = list(players)
d20, d31, d21 = [], [], []
for _ in range(args.boot):
    idx = [i for p in (random.choice(pl) for _ in range(len(pl))) for i in players[p]]
    pidx = [i for i in idx if test[i][4] > 0]
    d20.append(mae(P['C2'], idx) - mae(P['C0'], idx))
    d31.append(mae(P['C3'], pidx) - mae(P['C1'], pidx))
    d21.append(mae(P['C2'], pidx) - mae(P['C1'], pidx))
B = args.boot
for nm, dd in (("C2-C0 all", d20), ("C3-C1 played", d31), ("C2-C1 played", d21)):
    dd.sort()
    print(nm, "median", f"{dd[B // 2]:+.3f}", "CI",
          f"[{dd[int(0.025 * B)]:+.3f}, {dd[int(0.975 * B)]:+.3f}]")
