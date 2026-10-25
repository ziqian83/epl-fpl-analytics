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

## What this is good for, and what it is not

Good: ranking transfer candidates against each other - the error mostly cancels in out-vs-in comparisons. Not good: point-precise claims, captaincy certainty, or "expected 6.2 points" headlines. Any surface that shows xP links here; numbers never appear without the method and the holdout sizes.

No odds input. No market data. v0 inputs are FPL's own public xG/xA, minutes, points and fixtures only.
