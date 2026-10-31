# 13 - Evaluation protocol, methodological audit, and evidence-led plan (31 Oct 2026)

Status of all numbers in docs/12: RETROSPECTIVE-EXPLORATORY. Both held-out seasons have
been inspected across multiple variants (margins, gates, starts, captain on/off). They
are no longer untouched test sets; spec choices informed by them are not independent
validation.

## Simulator sanity review (independent pass over scripts/backtest-12thman-constrained.py)

- ORACLE XI: yes. `best_xi_points` selects the XI and formation by REALIZED points after
  the fact. A real manager sets the XI before matches. Captain is chosen pre-outcome
  (top as-of signal), but the XI itself is oracle. All policy comparisons inherit this.
- No realized points in DECISIONS: confirmed. Transfers, captain, and the spec grid use
  predictions/form only; realized points enter only scoring (including the oracle XI).
- Feature leakage: panel features are trailing-4-GW (RANGE 4 PRECEDING..1 PRECEDING) and
  opponent strength is trailing; training is rolling-origin by season. No current-GW
  feature use found.
- Eligibility: panel requires 4 trailing GW rows AND >=180 minutes over them, so new
  signings/youth are absent until their 5th GW; buy candidates must be panel-present;
  squad members missing from a GW's rows keep their slot and score 0. This biases the
  universe toward established regulars.
- Prices: buys pay the target-GW deadline price; intra-week moves unmodelled. Sells:
  buy + floor(profit/2), current price if down.
- FT/hits: bank cap 5 (rule from 2024/25, verified), hits -4, runtime asserts bank >= 0
  and squad size 15.
- Approximation bias is NOT established as policy-neutral: the oracle XI, captain rule,
  and price rules interact with each policy's squad path (e.g. hit-heavy paths field
  different XIs). Equal rules do not imply equal bias, and no measurement here separates
  that bias from real policy differences. Accordingly NO numerical noise threshold is
  claimed; the start-sensitivity spread (+64..+536 on one holdout) demonstrates
  fragility, not a quantified noise band.

## What the retrospective experiment supports - precisely

- Inside THIS simulator, on two retrospectively inspected seasons, raw form-chasing with
  hit discipline outscored the raw projection model across all tested margins, while the
  model had won the inner 2023-24 validation. That is a simulator finding about
  generalization failure, not a result about real FPL play today.
- It does NOT establish that form-chasing is the best real-money policy, and it is NOT
  grounds to switch the live product's advice. Live engine copy and caveats stay as-is.

## docs/12 audit trail (resolved 31 Oct)

- Selected-spec anomaly (+64 vs raw m>1 +97 on 2024-25): not a bug. Stage-1 tied at +508
  across all gate values (gate never binds on inner 2023-24 model picks); the tie broke
  by sort order to gate>=0.8, which then bound on 2024-25 (7 weeks, instrumented) and
  cost 33 pts. Fix (6a4712e): ties break toward the simplest spec - that would have
  selected raw model m>1, whose numbers were already reported; headline unchanged.

## Prospective outer-test protocol

- 2026-27 GW1-8 are elapsed and GW9 is mid-flight: NOT untouched. The only clean
  prospective window is GW10 onward, frozen before the GW10 deadline.
- Freeze (spec + code + data hashes recorded in the repo) BEFORE the GW10 deadline:
  {hold, raw persistence m>0, raw model m>1}, builder 'signal', captain rule as coded,
  FT cap 5, panel extended with 2026-27 (vaastav pinned commit recorded at build time).
  Score each completed GW without editing specs; any spec change restarts the clock.
- The engine's frozen weekly calls (12th-man/v2/data/frozen/, from GW9) are PRODUCT
  diagnostics - pre-deadline snapshots scored against actuals. They are not the same
  evidence class as an executable-policy simulation and are reported separately.

## Evidence-led plan (no tuning toward an outcome)

- No policy recommendation changes anywhere (product, docs, user copy) until a
  prospective, pre-registered result exists.
- Diagnostic work on the model's generalization failure: coefficient drift across
  rolling fits, per-feature contribution by season, regime comparison. Inspection and
  measurement, not score tweaks.
- Build movement without validation claims: provenance fixtures (panel hash locked in
  tests/fixtures/), signal-inspection tooling, engine rule fixtures (legal XI, pricing
  edge cases), and the GW10 freeze when its deadline approaches.
