# 15 - Data-grain audit: blanks, doubles and window rules (31 Oct 2026)

Bounded audit of intended vs actual data grain across the pipeline, triggered by
the docs/14 reconstruction work. Method: reading the committed code plus
tests/grain_probe.py (a tiny deterministic fixture league with one double GW and
one blank GW, run against the SHARED PANEL_SQL). No estimator experiments were
run; nothing here changes a shipped number. Evidence: tests/grain_probe.py
output is deterministic and re-runnable.

## Source data grain (established)

- vaastav merged_gw.csv (fit DB) and the official element-summary pull
  (prospective DB) are RAW FIXTURE ROWS: a double GW is two rows for the same
  player-GW (5,541 such player-GWs in the fit DB; 9,163 in the 11-season
  warehouse), a blank GW is NO rows for that team's players (verified on the
  fit DB: no all-zero team-GWs exist; disrupted GWs simply contain fewer teams,
  e.g. 2021-22 GW18 and GW30 hold 8 of 20 teams).
- The model docstring's stated intent (fit-12thman-model.py): "Canonical
  player-GW grid sums double-gameweek rows. Eligibility: 4 prior GW rows and
  >=180 trailing minutes."

## Path-by-path: intended vs actual

1. Model panel (PANEL_SQL, shared verbatim by the fit, both backtests and the
   prospective runner via regex extraction): the grid CTE aggregates to
   player-GW (SUM minutes/points/xgi per season-gw-player) BEFORE windowing, so
   features, labels and nrows4 are player-GW-grain, and RANGE BETWEEN
   4 PRECEDING AND 1 PRECEDING on gw is a calendar-GW window. This MATCHES the
   stated intent. (An earlier interim claim that nrows4 counts fixture rows was
   wrong; it counts aggregated grid rows, i.e. distinct GWs.)
2. Blank-GW eligibility QUIRK in that same panel: because blanks leave no rows,
   a player whose team blanks in the trailing 4 GWs has at most 3 grid rows in
   the window and is panel-ineligible for up to 4 weeks even when playing every
   available fixture (probe: ALPHA player excluded at GW6 with 360 trailing
   minutes, nrows4 = 3). Whether this exclusion is intended is unrecorded.
3. Opponent-strength feature DEFECT in that same panel: teamgw computes
   SUM(per-row conceded) / COUNT(DISTINCT opponent) from RAW rows, so the
   feature is scaled by how many of the team's players have rows in the dataset
   (probe: ALPHA 3 vs intended 1; BETA 1 vs intended 2... see probe), double GWs
   average only via the distinct-opponent count, and blank GWs silently shorten
   the trailing average (AVG skips the missing GW instead of shortening the
   divisor deliberately). OLS absorbs a constant scale factor, but squad-size
   variation and blank/double mixing make the scaling non-constant. Affects the
   fit, both backtests and the prospective runner equally (shared SQL), so
   relative comparisons inside one panel are less distorted than the raw
   numbers suggest, but the feature is not "opponent trailing-4 goals
   conceded" in the intended units.
4. Backtest and prospective ACTUALS: FULL_SQL / the prospective equivalent do
   GROUP BY season, gw, player_id with SUM - correct player-GW grain for
   scoring, including doubles.
5. Prospective DB build: raw fixture rows (one per element-summary history
   entry, each tied to a fixture id); consumed only through the aggregated grid
   and the aggregated actuals - downstream grain correct, DB itself raw.
6. Live pool gate (12thman2-refresh.mjs): perGw map keyed by round sums double
   fixtures into one GW (code comment: "double fixtures summed into one GW"),
   then slice(-4) and a 4-entry requirement. Calendar-consistent for doubles.
   For blanks: if FPL history omits blank rounds, the last-4-entries slice
   stretches across the blank and the 4-entry rule excludes the player - same
   effect as item 2; if history includes 0-minute blank rows, it does not.
   UNVERIFIED which; no blank GW has occurred yet in 2026-27 GW1-8.
7. docs/14 low-minutes evaluation (original interactive run AND the committed
   reconstruction scripts/low-minutes-eval.py): RAW fixture-row grain with a
   ROWS window - a double GW counts as 2 of the 4 trailing "rows". Differs
   from the canonical panel in BOTH grain (fixture vs player-GW) and window
   (rows vs calendar). Its numbers are not computed on the population the
   model, backtests or live gate use. Scope measured on the fit DB (gw>=5,
   126,353 raw fixture rows): 1,683 gate flips vs the calendar rule (542
   rows-gated-only, 1,141 calendar-gated-only), concentrated in the disrupted
   2021-22 season (3.06% of its rows) and 78 flips (0.29%) in the 2025-26 test
   season; 1,712 band flips among 87,918 commonly gated rows.
8. Engine/page (engine.js on pool.json): consumes the refresh output, already
   aggregated per round - consistent.

## What this does and does not explain

- The docs/14 original-vs-reconstruction last-digit gaps are NOT explained by
  the rows-vs-calendar mismatch: both runs used row windows. Candidate
  contributors are the unknown tie handling among same-player-GW fixture rows
  and other unpersisted implementation details; no causal attribution is
  established (the reconstruction pins ties by opponent_team_id).
- The 2021-22 concentration of definition flips coincides with that season's
  heavy blank/double disruption (2,217 double player-GWs; GWs with 8 teams),
  which is consistent with the grain mechanism but is not proof for any
  specific metric gap.

## Proposed corrections (decision for the maintainer, NOT implemented)

C1. Extract the canonical player-GW grid into one shared definition used by
    every consumer, including any future low-minutes evaluation.
C2. Fix teamgw: dedupe to one row per fixture BEFORE summing conceded, average
    per fixture, and make blank-GW handling in the trailing average explicit
    (shorten window by blanks vs count them as no-data), recorded in docs/13.
C3. Decide and record blank-GW eligibility semantics for the panel and the
    live gate: "4 calendar GWs with fixtures" (current de-facto) vs "4
    calendar GWs regardless of blanks, blanks contribute 0 minutes".
C4. If the low-minutes evaluation is ever re-run, do it under a NEW frozen
    spec on the canonical grid; the 31 Oct run stays as-is (spec frozen,
    results exploratory).
C5. Verify live FPL history blank behavior at the first natural blank GW, then
    align the live gate with the C3 decision.

Until C1-C3 land, the prospective freeze spec and setup are PROVISIONAL: they
inherit the panel semantics above. Frozen artifacts (gw09.json, pool.json
snapshots, prospective spec/results files) are unchanged; all scored results
remain exploratory per docs/13.
