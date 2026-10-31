# 13 - Evaluation protocol, methodological audit, and evidence-led plan (31 Oct 2026)

Status of all numbers in docs/12: RETROSPECTIVE-EXPLORATORY. Both held-out seasons have
been inspected across multiple variants (margins, gates, starts, captain on/off, and two
scorer generations). They are no longer untouched test sets; spec choices informed by
them are not independent validation.

## Simulator sanity review (independent pass over scripts/backtest-12thman-constrained.py)

- ORACLE XI: FOUND and FIXED (31 Oct, second pass). The first scorer's `best_xi_points`
  selected the XI and formation by REALIZED points after the fact. The corrected scorer
  (`pick_team` + `score_gw`) fixes XI, bench order, captain and vice BEFORE outcomes from
  the policy's as-of signal only, then applies official auto-subs (bench order, formation
  stays legal, GK for GK) and the vice-captain rule on realized minutes. 35 unit checks
  in tests/test_simulator_rules.py cover selection, sub legality/order, captain/vice,
  GK sub, missing-data handling, sell rounding, quotas and budget.
- PANEL ZEROING: FOUND and FIXED (same pass). The first scorer gave panel-missing owned
  players 0 points even when they played. Scoring now reads FULL player-GW data
  (epl_fpl_gameweeks unfiltered: 27,605 rows / 804 players for 2024-25), so every owned
  player scores real points and real minutes; panel membership only limits BUY
  candidates and as-of signals.
- No realized points in DECISIONS: confirmed. Transfers, XI/bench/captain, and the spec
  grid use predictions/form only; realized points and minutes enter only scoring.
- Feature leakage: panel features are trailing-4-GW (RANGE 4 PRECEDING..1 PRECEDING) and
  opponent strength is trailing; training is rolling-origin by season. No current-GW
  feature use found.
- Eligibility: panel requires 4 trailing GW rows AND >=180 minutes over them, so new
  signings/youth are absent until their 5th GW; buy candidates must be panel-present.
  This biases the universe toward established regulars (selection-side only, post-fix).
- Prices: buys pay the target-GW deadline price; intra-week moves unmodelled. Sells:
  buy + floor(profit/2), current price if down (sell_price, unit-tested).
- FT/hits: bank cap 5 (rule from 2024/25, verified), hits -4, runtime asserts bank >= 0
  and squad size 15.
- Approximation bias is NOT established as policy-neutral: captain rule and price rules
  interact with each policy's squad path. Accordingly NO numerical noise threshold is
  claimed; the measured start-sensitivity spread (selected spec: -20..+557 on 2024-25,
  +20..+273 on 2025-26) demonstrates fragility larger than the model-vs-form gap.

## What the retrospective experiment supports - precisely (corrected scorer)

- Inside THIS simulator: the model beat form-chasing on 2025-26 (selected +246 vs +213)
  and lost on 2024-25 (selected -20 vs +50). The inner 2023-24 validation still prefers
  the model (+443 vs persistence best +349). The earlier "model loses on both holdouts"
  finding was partly an oracle-scorer/panel-zeroing artifact and is RETRACTED.
- The mixed result, plus start sensitivity larger than any policy gap, means NO policy
  ranking is established. It is NOT grounds to switch the live product's advice in
  either direction. Live engine copy and caveats stay as-is.

## docs/12 audit trail (resolved 31 Oct)

- First-pass selected-spec anomaly (+64 vs raw m>1 +97 on 2024-25, oracle scorer): stage-1
  tied across gates and broke to gate>=0.8, which bound on 2024-25 (7 weeks). Tiebreak fix
  (6a4712e) breaks ties toward the simplest spec. SUPERSEDED by the corrected-scorer
  rerun: with the legal scorer the inner selection is model gate>=0.0 margin>1 and the
  2024-25 selected result is -20.
- Second-pass correction (31 Oct): oracle XI and panel zeroing replaced as above; all
  stage-1/stage-2 numbers regenerated; selection re-derived (unchanged family: model
  margin>1; gate now 0.0 by the simplest-spec tiebreak).

## Prospective outer-test protocol

- 2026-27 GW1-8 are elapsed and GW9 is mid-flight: NOT untouched. The only clean
  prospective window is GW10 onward, frozen before the GW10 deadline (2026-11-06T18:30Z,
  official bootstrap-static).
- Freeze (spec + code + data hashes recorded in the repo) BEFORE the GW10 deadline:
  {hold, raw persistence m>0, raw model m>1}, builder 'signal', pre-outcome
  XI/bench/captain rule as coded, FT cap 5, panel extended with 2026-27 (vaastav pinned
  commit recorded at build time). Score each completed GW without editing specs; any spec
  change restarts the clock.
- The engine's frozen weekly calls (12th-man/v2/data/frozen/, from GW9) are PRODUCT
  diagnostics - pre-deadline snapshots scored against actuals. They are not the same
  evidence class as an executable-policy simulation and are reported separately.

## Evidence-led plan (no tuning toward an outcome)

- No policy recommendation changes anywhere (product, docs, user copy) until a
  prospective, pre-registered result exists.
- Diagnostic work on model/generalization questions: coefficient drift across rolling
  fits, per-feature contribution by season, regime comparison. Inspection and
  measurement, not score tweaks.
- Build movement without validation claims: provenance fixtures (panel hash locked in
  tests/fixtures/), signal-inspection tooling, engine rule fixtures (legal XI, pricing
  edge cases - now landed as tests/test_simulator_rules.py), and the GW10 freeze when
  its deadline approaches.
