# The 12th Man - fresh model, v0 method and validation

Written 25 Oct 2026. This model is built fresh for The 12th Man. It inherits nothing from the Boot Room picker: no code, no scoring rules, no constants. Coefficients below are fitted on this warehouse's historical data and nothing else.

## What it predicts

Expected FPL points for one player in one gameweek (xP), predicted as of that gameweek's deadline using only information available at that moment.

## Features (all available pre-deadline)

- Trailing 4-gameweek mean total points (`f_pts4`)
- Trailing 4-GW mean expected goal involvements, FPL's own xG+xA (`f_xgi4`)
- Trailing 4-GW mean minutes share, minutes/90 (`f_minshare4`)
- Opponent strength: the upcoming opponent's mean goals conceded per match over the prior 4 GWs (`opp_strength_k`), averaged across double-fixture weeks
- Position (GKP/DEF/MID/FWD; source labels `GK` and `GKP` are the same population and are normalized; stray `AM`/blank labels, 322 rows in five seasons, are excluded)

Data hygiene: a canonical player-gameweek grid sums double-gameweek fixture rows (374 duplicate player-GW cases in 2024-25 alone), so "trailing 4" means four gameweeks, never four rows. Zero-minute rows exist for every player every GW, so benchings count as zeros rather than vanishing.

## Fitting

Ordinary least squares, one configuration, features chosen a priori, no tuning and no feature search. Eligibility: four prior GW rows and at least 180 trailing minutes (45/GW average).

## Validation (rolling origin, strictly out-of-sample)

| Held-out season | Train rows | Test rows | Naive MAE* | Model MAE | Naive corr | Model corr |
| --- | --- | --- | --- | --- | --- | --- |
| 2024-25 | 17,465 | 7,002 | 2.380 | 2.200 (-7.6%) | 0.212 | 0.251 |
| 2025-26 | 24,467 | 6,962 | 2.578 | 2.301 (-10.8%) | 0.138 | 0.188 |

*Naive = repeat the trailing-4 mean points (persistence baseline).

Coefficients are stable across the two fits: persistence ~0.24-0.26, xGI ~0.87-1.12, minutes share ~1.33-1.48, opponent strength ~0.005 (near zero at GW level - kept, but honest: the fixture adjustment barely moves single-GW predictions), GKP +0.13-0.14, DEF -0.35/-0.38, FWD +0.08/+0.17 relative to MID.

## Calibration (2025-26 holdout)

- Predicted-decile vs actual means are monotone and close; mild under-prediction in deciles 1-5 (about -0.2 average bias), mild over-prediction in decile 10.
- By position: GKP pred 3.00 vs actual 2.90; DEF 2.52 vs 2.84 (under); MID 3.02 vs 3.11; FWD 3.39 vs 3.41.
- Known caveats: same players appear in train and test (inflates versus a true new-player test); FWD was under-predicted in 2024-25 (3.47 vs 3.71), so position bias is not fully stable season to season; single-GW variance dominates everything (FPL Review's published analysis puts even a perfect-information model near R2 0.15).

## Pairwise ranking validation (added after review, 25 Oct)

Individual-level MAE and correlation do NOT establish usefulness for transfer decisions, so the intended use (ranking out-vs-in swaps) was tested directly: same-position pairs within one gameweek, sampled per GW on the held-out seasons, scoring whether the higher-predicted player actually scored higher (actual-points ties count as wrong for both models):

| Held-out season | Model pair accuracy | Persistence baseline |
| --- | --- | --- |
| 2024-25 | 0.483 (n=20,591 pairs) | 0.472 |
| 2025-26 | 0.493 (n=20,431 pairs) | 0.480 |

Honest read: the model beats naive persistence on pairwise ranking by only about one percentage point, and absolute accuracy sits near half because next-GW points are mostly variance. When the model picks the better side of a pair, the mean actual gap is 0.6-0.7 points. Consequences for the product:

- xP is a WEAK signal. It can order a shortlist; it cannot justify a move on its own.
- Small projected transfer edges are noise-dominated - the mean correct-side gap in these tests was only 0.6-0.7 points, and no calibrated significance threshold is established. These pair results are diagnostic, not a significance claim. Edges must be shown with their uncertainty, never as decisive.
- Weak projections must not collapse the user's feasible strategies (hold, transfer, chip) into one conservative recommendation. The page compares feasible strategies side by side, labels estimates as unvalidated where they are, and never claims an optimal answer.
- "Errors cancel in out-vs-in comparisons" was asserted in the first draft of this doc and is NOT supported; removed.

## Intended use and limits (current state)

Intended use: one input among several for ordering transfer candidates, with uncertainty shown. Unvalidated for: captaincy, chip timing, multi-week sequences, hit justification.

Known coverage limits:

- Current scoring rules: training seasons 2021-22 to 2024-25 predate the 2025-26 defensive-contribution scoring. Only the 2025-26 holdout reflects current rules, and its fit was the weaker of the two. Coefficients may underweight defensive actions under current rules. A current-rules-only refit needs more 2025-26 gameweeks.
- Cold start: players with fewer than 4 completed GW rows or under 180 trailing minutes are invisible to v0 - new signings, promoted players, players back from injury or loan. The page must say who is NOT rated, not just who is.
- Mid-season transfers: a player's trailing features cross clubs unchanged; team context is not adjusted.
- Blank and double gameweeks: doubles are summed into one player-GW; blanks are excluded from prediction at runtime (no fixture, no xP).
- Zero-minute rows are real rows in the source data, so benchings count as zeros in trailing windows (verified on 2024-25: 661-666 distinct players per GW with ~356-362 zero-minute rows).

No odds input. No market data. v0 inputs are FPL's own public xG/xA, minutes, points and fixtures only.


## v1: home/away, short-form window, role-split opponent terms (26 Oct 2026)

v0's known gaps named three cheap fixes: no home/away term, one shared opponent
coefficient (~0.005-0.19 depending on scaling, near zero), and a flat 4-GW form
window. v1 adds exactly those, chosen a priori, no feature search:

- Trailing 2-GW mean points and xGI alongside the 4-GW means (recency without an
  arbitrary decay constant)
- Home share of the predicted GW's fixtures (1.0 home, 0.0 away, 0.5 for a split double)
- Opponent terms split by role: opponent's trailing goals CONCEDED per match for
  MID/FWD (attacking relevance), opponent's trailing goals SCORED per match for
  GKP/DEF (clean-sheet relevance)

Validation protocol: identical rolling-origin holdouts as v0, rebuilt from the
DuckDB warehouse (sql/epl_duckdb_load.sql). v0 was refit under this replication
protocol so the comparison is exact; replication eligibility differs slightly from
the original v0 run (train 14,582 vs 17,465 on the 2024-25 split; opponent trailing
data is now required), so the v0 column below is the refit, not the original table
above. Pairwise test: same-position pairs within one gameweek, deterministic
sample (max 14 players per GW-position cell, all pairs, seed fixed), prediction
ties skipped, actual-points ties count wrong.

| Held-out season | Model | MAE | Naive MAE | Corr | Pair accuracy | Pairs |
| --- | --- | --- | --- | --- | --- | --- |
| 2024-25 | naive persistence | 2.430 | - | - | 0.486 | 11,755 |
| 2024-25 | v0 refit | 2.238 | 2.430 | 0.260 | 0.495 | 12,344 |
| 2024-25 | v1 | 2.242 | 2.430 | 0.262 | 0.501 | 12,351 |
| 2025-26 | naive persistence | 2.601 | - | - | 0.490 | 11,795 |
| 2025-26 | v0 refit | 2.304 | 2.601 | 0.191 | 0.498 | 12,367 |
| 2025-26 | v1 | 2.299 | 2.601 | 0.212 | 0.503 | 12,376 |

Honest read:

- The decision-relevant metric (pairwise ordering of same-position swaps) improves
  about half a point on BOTH independent holdouts; correlation improves on both;
  MAE is a wash (+0.004 on one, -0.005 on the other). Pairs within a GW are not
  independent observations, so treat the edge as directional consistency, not a
  tight significance claim.
- The new coefficients are stable and correctly signed across both fits: home
  +0.45/+0.58 points, opponent-scored for defenders -0.31/-0.36, opponent-conceded
  for attackers +0.18/+0.24.
- Everything from the v0 read still stands: single-GW variance dominates, small
  projected edges are noise, xP orders shortlists and never justifies a move alone.

Shipped v1 coefficients (fit on 2021-22..2024-25, the 2025-26-holdout fit):
const 0.379, pts4 0.123, pts2 0.077, xgi4 1.084, xgi2 0.613, minshare4 1.542,
home 0.450, opp-conceded MID/FWD 0.182, opp-conceded GKP/DEF 0.104,
opp-scored MID/FWD -0.118, opp-scored GKP/DEF -0.305; position offsets vs MID:
GKP +0.623, DEF +0.058, FWD +0.148.

Still open (unchanged): current-rules fit has only the 2025-26 season (defensive
contribution scoring is not a feature - the warehouse load does not carry it yet);
cold start; mid-season club changes; horizon holds trailing features constant.
ep_next (FPL's own projection) is not benchmarked: its history is not archived in
the public sources this warehouse uses, so an honest season-long comparison is not
possible from these data.

## Decision-level validation (31 Oct 2026 addendum)

Aggregate MAE/correlation says how far projections are off on average; the
decision question is whether the model's *ranking of candidate swaps* earns
points. `scripts/backtest-12thman-policies.py` replays every feasible
same-position swap candidate each GW in the held-out seasons (rolling-origin
fits, never future data), pairs it against holding the current player, and
scores the realized points difference.

Results (unrestricted same-position pairs - the optimistic ceiling, ignoring
budget and legality):

| Holdout | Pred. edge bar | Mean realized edge | n gw-groups (hit policy) |
|---|---|---|---|
| 2024-25 | >0 / >1 / >2 | +0.60 / +1.25 / +2.28 pts | hit net +0.86 (22) |
| 2025-26 | >0 / >1 / >2 | +0.72 / +1.46 / +1.84 pts | hit net +1.82 (5 - thin) |

Realized edge rises monotonically with the predicted bar, which supports the
page's decision-margin framing: small predicted edges realize small average
gains, not zero. It does NOT establish any bar as a calibrated threshold -
per-swap variance is large and the hit-policy samples are thin, so the page
labels the ~1 xP line a chosen sensitivity/decision margin, never a measured
"noise band".

## Provenance and reproducibility (31 Oct 2026 addendum)

- The live v1 coefficients come from a 26 Oct fit on an 11-season warehouse
  (vaastav CSVs via `sql/epl_duckdb_load.sql`). The verbatim fit script was
  filed as `scripts/fit-12thman-model-v1.py`. Its holdout results: 2024-25 MAE 2.242 /
  corr 0.262 / pair-acc 0.501; 2025-26 MAE 2.299 / corr 0.212 / pair-acc 0.503
  (naive 2.430 / 2.601). Runtime COEF + POS_OFFSET match that fit's beta
  vector exactly.
- `scripts/fit-12thman-model.py` (v0 research fit) reproduces the numbers in
  the section above. Pair-sampling is now order-frozen (`ORDER BY` on the
  panel) and the script prints sha256 of each input CSV plus
  duckdb/numpy/pandas versions. Before the ORDER BY fix, pair-accuracy
  wandered ~+/-0.003 between identical runs (unstable DuckDB result order);
  MAE/corr were always stable. Residual differences vs the 25 Oct original-run
  numbers are attributable to that ordering, possibly plus upstream CSV edits
  (vaastav master last changed 22 Oct 2026).
