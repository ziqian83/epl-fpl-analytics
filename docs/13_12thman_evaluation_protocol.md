# 13 - Evaluation protocol and evidence-led plan (31 Oct 2026)

Status of all numbers in docs/12: RETROSPECTIVE-EXPLORATORY. Both held-out seasons have
now been inspected across multiple variants (margins, gates, starts, captain on/off).
They are no longer untouched test sets, and future spec choices informed by them cannot
be called independently validated.

## Methodological audit of docs/12 (prompted by review, resolved 31 Oct)

- Selected-spec anomaly (+64 vs raw m>1 +97 on 2024-25): NOT a bug. The stage-1 grid tied
  at +508 across ALL gate values on the inner 2023-24 season (the minshare gate never
  binds on model picks there), and the tie was broken by sort order to gate>=0.8. On
  2024-25 the gate DID bind: 7 weeks where the model's best buy had minshare4 < 0.8
  (instrumented count), diverging the transfer path and costing 33 pts. Binding is
  season-dependent; "the gate never binds" was true only of the inner season. Protocol
  fix applied: ties now break toward the simplest spec (lowest gate, lowest margin),
  which would have selected raw model m>1 (gate 0.0) - its holdout numbers (+97/+252)
  were already in the table, and the headline (loses to raw persistence +304/+358) is
  unchanged.
- Captain approximation: captain = weekly top-signal squad member, not a human choice;
  this inflates all policies roughly equally and flattens between-policy differences.
- Best-legal-XI approximates auto-subs generously (real auto-subs only replace
  non-players in strict bench order); same generosity for every policy.
- Price availability: buys pay the target-GW deadline price; intra-week price movement
  is not modelled. Sell rounding: floor(profit/2), current price when down. Both
  documented in docs/12 and identical across policies.
- Interpretation bound: differences under ~30 pts/season across policies are inside
  start-builder and approximation noise (start sensitivity showed +64..+536 on the same
  holdout); only the large, consistent persistence-over-model gap carries signal.

## Prospective outer-test protocol (the only path to a validated claim)

1. Freeze specs NOW, before any 2026-27 evaluation: {hold, raw persistence m>0,
   raw model m>1} with fixed builder 'signal', captain rule as coded, FT cap 5.
2. Extend the panel with the current season (vaastav 2026-27, pinned commit recorded)
   and evaluate week by week as GWs complete, WITHOUT re-inspecting intermediate results
   to adjust specs. Each scored GW is appended to a results log with its data hash.
3. The engine's own weekly frozen calls (12th-man/v2/data/frozen/, starting GW9) are the
   parallel prospective test for the shipped product; scored post-deadline per artifact.
4. Any spec change after a 2026-27 evaluation restarts the clock: new spec, new freeze,
   evaluation only on GWs completed after the change.

## Evidence-led plan (grounded in the findings, not tuned toward an outcome)

- The simple baseline is the one to beat and currently the best-supported policy:
  form-chasing with hit discipline. The user's original ask is consistency of the data
  and decisions, not a fancy estimator. If the product recommends anything today, the
  honest reference is the form baseline with the engine's evidence layer as
  DISCIPLINE (fewer, better-sourced transfers), presented as judgement, not as a
  validated edge.
- The model's job is now diagnostic: where its inner-season edge came from (fixture
  strength? xGI signal?) and why it failed to generalize (regime shift? coefficient
  instability across fits?). That is inspection work (coefficient drift, per-feature
  contribution by season), not score tuning.
- Build movement that does not require new validation: provenance locking (panel hash
  fixture), signal inspection tooling, test fixtures for the engine's legal-XI and
  pricing rules against official edge cases, and the prospective protocol above.
