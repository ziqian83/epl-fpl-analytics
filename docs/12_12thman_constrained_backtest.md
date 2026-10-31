# 12 - Squad-constrained decision backtest (budget, FT banking, hits)

`scripts/backtest-12thman-constrained.py` — 31 Oct 2026. Companion to the unrestricted
diagnostic in `scripts/backtest-12thman-policies.py`; this version replays the weekly
transfer question under real FPL constraints, so it is the evidence base for (or against)
any recommendation-reliability claim.

## Method

- Same leakage-safe panel and rolling-origin lstsq fit as `fit-12thman-model.py`;
  held-out seasons 2024-25 (train 2021-22..2023-24) and 2025-26 (train 2021-22..2024-25),
  GW5-GW38 (the panel needs 4 trailing GWs).
- Prices: pinned vaastav `merged_gw.csv` snapshots (`value`, tenths of GBPm), joined by
  (season, gw, element). Buys pay the target-GW deadline price; sells credit
  buy + floor(profit/2), or current price if it fell. Price coverage 100% both seasons.
- Starting squad: reserve-aware greedy under the GBP 100.0m budget, position quotas,
  club cap 3. Identical builder for every policy, so differences are the transfer policy.
- Free transfers bank week to week, cap 5 (the rule in force for both held-out seasons).
  Extra transfers cost -4 and are taken only when the predicted edge clears margin + 4.
- Scoring: realized best-XI points (no captain doubling, no chips). Squad members missing
  from a GW's panel rows still occupy their slot and score 0 — a real squad keeps an
  injured/benched player; excluding them collapses the formation picker and under-credits
  hold (bug found and fixed during this audit, 31 Oct).
- Comparators: hold (never transfer), persistence heuristic (f_pts4 form, no model),
  random legal swaps (5 seeds). Policies decide on predictions only; realized points are
  used exclusively for scoring.

## Results (points vs hold, after -4 hit costs)

| policy | 2024-25 | 2025-26 |
| --- | --- | --- |
| hold (constrained start) | 1230 | 1177 |
| model margin>0 | +237 (33 tr, 0 hits) | +287 (33 tr, 0 hits) |
| model margin>1 | +132 (33 tr, 0 hits) | +301 (32 tr, 0 hits) |
| model margin>2 | +128 (19 tr, 0 hits) | +340 (21 tr, 0 hits) |
| persistence (form, no model) | +333 (63 tr, 30 hits) | +412 (60 tr, 27 hits) |
| random legal swaps | -242 (33 tr) | -66 (33 tr) |

## What this does and does not support

- Supported: model-driven transfers beat holding and beat random activity by a wide,
  consistent margin under budget/FT/hit constraints in both held-out seasons. Acting on
  the model is better than not acting.
- NOT supported: any calibrated margin bar. The margin curve falls in 2024-25
  (+237/+132/+128) and rises in 2025-26 (+287/+301/+340) — no stable cutoff across seasons.
- NOT supported: superiority over form-chasing. The persistence heuristic with aggressive
  hits beat the model in both seasons. The engine's evidence layer (consistency,
  one-week-wonder flags) exists to discipline exactly this; the backtest says the raw
  projection alone does not dominate a naive form signal.
- Known limitations: no captain doubling, no chips/wildcards, buys pay deadline price,
  panel-missing players score 0 (biases against holding injury-prone players, applies to
  all policies), starting squad is a greedy heuristic, two held-out seasons only.
