> STATUS (31 Oct, post-review): RETROSPECTIVE-EXPLORATORY. The holdout seasons below have
> been inspected across multiple variants and no longer constitute an untouched test set.
> See docs/13 for the methodological audit (incl. the +64 vs +97 selected-spec anomaly,
> resolved as season-dependent gate binding after an arbitrary tie) and the prospective
> outer-test protocol that replaces holdout reuse.

# 12 - Squad-constrained decision backtest (budget, FT banking, hits, captain)

`scripts/backtest-12thman-constrained.py` — 31 Oct 2026. Replays weekly transfer decisions
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
  edge > margin + 4. Captain: each GW's highest-signal squad member (policy's own key),
  realized points doubled. Best legal XI from the 15 (approximates auto-subs; documented).
- Squad members missing from a GW's panel rows keep their slot and score 0.
- Stage 1 (train-only spec selection): fit 2021-22+2022-23, validate on 2023-24. Grid:
  {model, persistence} x gate {0,.5,.6,.7,.8} x margin {0,1}.
- Stage 2 (true holdouts): 2024-25 (train 2021-22..2023-24), 2025-26 (train ..2024-25),
  GW5-GW38. Baselines: hold, raw model margins 0/1/2, raw persistence, random (seeds 0-4).
- Repro: panel sha256[:16]=e5c5f580073d8ecb (31,429 rows), python 3.10.12, numpy 2.2.6,
  duckdb 1.5.6, random seeds 0-4, DB /tmp/epl12_fit.duckdb (vaastav pinned master
  d7b05b51d137, cache .fit-cache/). Runtime asserts: bank never negative, squad always 15.

## Stage 1 (inner validation on 2023-24, hold=1135) - selection uses ONLY this

- Model: +487 (margin>0) / +508 (margin>1); the minshare gate never binds on model picks.
- Persistence: +289..+433 across the grid (best: gate>=0.8 margin>0).
- SELECTED SPEC: model, margin>1 (gate irrelevant - tied across gate values).

## Stage 2 (true holdouts) - hit-adjusted points vs hold

| policy | 2024-25 (hold 1457) | 2025-26 (hold 1382) |
| --- | --- | --- |
| raw model margin>0 | +165 | +224 |
| raw model margin>1 | +97 | +252 |
| raw model margin>2 | +162 | +306 |
| raw persistence (form) | +304 (63 tr, 30 hits) | +358 (60 tr, 27 hits) |
| random legal swaps | -313 | -93 |
| train-selected spec (model m>1) | +64 | +252 |

Starting-squad sensitivity (selected spec vs the SAME builder's hold):

| start builder | 2024-25 | 2025-26 |
| --- | --- | --- |
| signal | +64 (hold 1457) | +252 (hold 1382) |
| signal-per-price | +536 (hold 1083) | +303 (hold 1420) |
| form | +345 (hold 1341) | +140 (hold 1587) |

## Conclusions (bounded to exactly this experiment)

1. The raw projection model LOSES to the simple form-chasing baseline on both true
   holdouts (+64..+306 vs +304/+358 depending on margin), even though the model won
   clearly on the 2023-24 inner validation (+508 vs +377). The inner-validation edge did
   not generalize. This is the main finding.
2. Form-chasing pays for 27-30 hits and still nets more than any model variant tested.
   Hits were not the deciding factor; the raw persistence edge exceeds its hit costs.
3. Results are highly sensitive to the starting squad (selected spec: +64 to +536 on the
   same holdout across builders). Two holdout seasons and a greedy start heuristic are
   not enough to rank policies with confidence beyond "persistence >= raw model here".
4. What this does NOT establish: any calibrated transfer bar; any superiority claim for
   the model; any claim that the engine's evidence layer (consistency, one-week-wonder
   flags) closes the gap - that layer is untested here and is the next experiment, with
   its spec again designed on training-era data only.
5. Known simplifications: best-legal-XI approximates auto-subs; captain is the weekly
   top-signal pick, not a human's choice; buys pay deadline price; two holdout seasons.
