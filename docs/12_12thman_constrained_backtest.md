> STATUS (31 Oct, post-review, corrected scorer): RETROSPECTIVE-EXPLORATORY. The holdout
> seasons below have been inspected across multiple variants and no longer constitute an
> untouched test set. This revision replaces the earlier oracle-XI scorer with a
> pre-outcome legal-XI/auto-sub scorer; all numbers changed. See docs/13 for the audit.

# 12 - Squad-constrained decision backtest (budget, FT banking, hits, captain)

`scripts/backtest-12thman-constrained.py` - 31 Oct 2026. Replays weekly transfer decisions
under real FPL constraints. Two-stage protocol: the policy/gate/margin spec is selected on
an inner validation season using ONLY training-era data, then evaluated once on each true
holdout. Nothing from the holdouts influences the spec choice.

## Method

- Panel and rolling-origin lstsq fit identical to `fit-12thman-model.py`; features are
  trailing-4-GW, as-of only. Decisions use predictions; realized points only score.
- Constraints: GBP 100.0m start budget, position quotas, club cap 3, real vaastav prices
  per GW (tenths), sell = buy + floor(profit/2) (current price if it fell), FT banking
  capped at 5 (rule in force for both holdout seasons - introduced 2024/25, confirmed
  against premierleague.com 31 Oct 2026), extra transfers -4 taken only when
  edge > margin + 4.
- Team selection is PRE-OUTCOME: each GW the XI, bench order, captain and vice are chosen
  from the policy's as-of signal only (formation maximizing signal over the legal set;
  bench by signal, GK last; captain = top-signal starter, vice = second). Scoring then
  applies the official auto-sub rule (non-playing starters replaced by bench in order
  while the formation stays legal, GK for GK) and the vice-captain rule, using FULL
  player-GW data (all 804 players in 2024-25, not the filtered panel) - owned players
  always score their real points and real minutes, whatever the panel says.
- Squad members missing from a GW's panel rows get as-of signal 0 (the picker benches
  them) but still score their real points via the full-data matrix.
- Stage 1 (train-only spec selection): fit 2021-22+2022-23, validate on 2023-24. Grid:
  {model, persistence} x gate {0,.5,.6,.7,.8} x margin {0,1}. Ties break to simplest spec.
- Stage 2 (held-out seasons): 2024-25 (train 2021-22..2023-24), 2025-26 (train ..2024-25),
  GW5-GW38. Baselines: hold, raw model margins 0/1/2, raw persistence, random (seeds 0-4).
- Repro: panel sha256[:16]=e5c5f580073d8ecb (31,429 rows), python 3.10.12, numpy 2.2.6,
  duckdb 1.5.6, random seeds 0-4, DB /tmp/epl12_fit.duckdb (vaastav pinned master
  d7b05b51d137, cache .fit-cache/). Runtime asserts: bank never negative, squad always 15.
- Rule unit tests: tests/test_simulator_rules.py (35 checks: sell rounding, formation
  legality, FT cap, XI/bench/captain selection, auto-sub order and legality, vice-captain,
  GK-for-GK, missing-data scoring, squad quotas/budget/club cap).

## Stage 1 (inner validation on 2023-24, hold=1397) - selection uses ONLY this

- Model: +413 (margin>0) / +443 (margin>1), 33 tr, 0 hits; the minshare gate never binds
  on model picks (identical at every gate value).
- Persistence: +209..+349 across the grid (best: gate>=0.8 margin>1, 47 tr, 14 hits).
- SELECTED SPEC: model, gate>=0.0, margin>1 (gates tied; simplest wins).

## Stage 2 (held-out seasons, retrospectively inspected) - hit-adjusted points vs hold

| policy | 2024-25 (hold 1660) | 2025-26 (hold 1536) |
| --- | --- | --- |
| raw model margin>0 | +10 | +232 |
| raw model margin>1 | -20 | +246 |
| raw model margin>2 | +122 | +169 |
| raw persistence (form) | +50 (63 tr, 30 hits) | +213 (60 tr, 27 hits) |
| random legal swaps | -346 | -116 |
| train-selected spec (model g0 m>1) | -20 (33 tr, 0 hits) | +246 (32 tr, 0 hits) |

Starting-squad sensitivity (selected spec vs the SAME builder's hold):

| start builder | 2024-25 | 2025-26 |
| --- | --- | --- |
| signal | -20 (hold 1660) | +246 (hold 1536) |
| signal-per-price | +557 (hold 1173) | +273 (hold 1445) |
| form | +266 (hold 1551) | +20 (hold 1735) |

## Conclusions (bounded to exactly this experiment)

1. MIXED holdout result, not a clean loss. On 2024-25 the model loses to form-chasing at
   the selected spec (-20 vs +50; raw margins +10/+122 bracket it). On 2025-26 the model
   BEATS form-chasing at margins 0 and 1 (+232/+246 vs +213) and loses at margin 2. The
   earlier finding "the model loses to form on both holdouts" was partly an artifact of
   the oracle-XI scorer and panel-zeroing; it does not survive the corrected simulator.
2. Starting-squad choice swings the outcome more than any policy difference measured here
   (selected spec on 2024-25: -20 to +557 across three builders; hold itself ranges
   1173-1660). Two holdout seasons and greedy start heuristics cannot rank policies
   beyond this fragility.
3. Form-chasing's 2024-25 edge came with 63 transfers and 30 hits; on 2025-26 the same
   policy with 27 hits no longer beats the model. Hit discipline alone does not explain
   the difference.
4. What this does NOT establish: any calibrated transfer bar; any superiority claim for
   the model OR for form-chasing; any grounds to change live advice; any claim about the
   engine's evidence layer (consistency, one-week-wonder flags), which is untested here.
5. Remaining simplifications: buys pay deadline price (intra-week moves unmodelled); two
   holdout seasons; buy candidates must be panel-present (eligibility bias toward
   established regulars); chips (WC/FH/BB/TC) are not modelled in this simulator.
