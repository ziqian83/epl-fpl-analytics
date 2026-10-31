# 14 - Low-minutes (gated-out) players: measured outcome distributions (31 Oct 2026)

Question: when the engine gives a squad player no projection (the 180-trailing-minute
gate; docs/13), how wrong is the silent zero? Measured, not estimated.

Data: /tmp/epl.duckdb `epl_fpl_gameweeks` (vaastav lineage), seasons 2021-22..2025-26,
player-GWs with gw >= 5. Gate proxy: trailing-4-GW minutes < 180 (matches the panel rule;
no status/news fields exist in this dataset, so injury-driven absence is proxied by the
minutes pattern, not observed directly).

## Conditional-on-playing (size of the blind spot, NOT a decision-time number)

Gated-out player-GWs where the player actually plays 45+ minutes:
n=10,958, mean 3.09 pts, P(>=5)=24.0%, P(>=8)=9.3%.
Over-gate comparison (45+ min): n=30,586, mean 3.44, P(>=5)=28.3%.
So a gated-out starter scores about 90% of a rated starter. Treating such a player as 0
loses ~3 points on the weeks he plays. Minutes-played is post-outcome information; this
conditions on it, so it cannot be used as a projection.

## Decision-time view (what a usable treatment could be built from)

Among gated-out player-GWs, before knowing whether the player plays:

| trailing 4-GW minutes | n | P(plays) | P(45+) | E[pts given 45+] | unconditional E[pts] |
|---|---|---|---|---|---|
| 0 (true cold start) | 60,022 | 4% | 2% | 2.60 | 0.10 |
| 1-89 | 16,362 | 47% | 19% | 3.01 | 0.92 |
| 90-179 | 12,064 | 63% | 41% | 3.15 | 1.57 |

By position (all gated-out): DEF E=0.38, MID 0.52, FWD 0.59, GK 0.10 unconditional;
E[pts|45+] ranges DEF 2.76 to FWD 3.67.

Returning-from-absence pattern (45+ min 2-4 GWs ago, 0 min last GW; the injury-return
shape): n=531, P(plays)=26%, unconditional E[pts]=0.38.

## Caveats (read before using any number above)

- A low aggregate mean does NOT establish that a silent zero is right for an individual
  player or for a six-week horizon decision. These are group averages over loosely
  matching players; no individual's expected points (e.g. João Pedro's) can be read off
  them, and the unconditional numbers are one-week figures - they say nothing about
  horizon sums.
- FPL status / chance_next is an INPUT TO EVALUATE, not an established calibrated
  P(plays). Whether chance_next is empirically calibrated has not been tested here.
- A two-part P(plays) x E[pts|plays] estimator is a HYPOTHESIS TO TEST, not a concluded
  design. Open questions before it could be tested: consistent handling of points
  scoring paths across minute bands (cameos, cards, bonus), scoring-rule consistency
  between the vaastav totals and official FPL scoring, and interaction with the
  engine's XI/bench interlock.
- The tipping-point sensitivity shipped in the engine is a scenario sweep (all other
  projections, prices and squad fixed; one player's this-week projection swept 0.5-10).
  A tipping point is not a calibrated probability or interval.

## What this supports and what it does not

- At GROUP level the silent zero loses least for cold starts and injury-return shapes
  and most for the 90-179 trailing-minute band (~1.6 pts/GW): rotation and short-term
  absence, exactly the players who re-enter XIs. This sizes the aggregate error; it
  does not validate the zero for any individual (see caveats).
- No single discount coefficient is supported by this data. The two-part shape
  P(plays) x E[pts|plays] with band/position splits and FPL status as a P(plays)
  input is a testable hypothesis, not a concluded estimator.
- ep_next as a fill-in remains an UNVALIDATED external baseline: validating it against
  our weak model tests agreement, not accuracy. Validate against as-of recorded outcomes
  only if a historical as-of source is recoverable; the official API does not expose
  historic ep_next snapshots, so recoverability is doubtful.
- These distributions describe the pool-wide average. Nothing here changes a shipped
  number today; the page discloses missing projections instead of imputing them.

## Frozen-spec retrospective evaluation (spec frozen 31 Oct before the run)

Spec: fit 2021-22..2024-25, test 2025-26 (retrospective chronological; 2025-26 had
already been inspected in this rebuild - not untouched validation). Candidates:
C0 silent zero; C1 fit-period unconditional band mean; C2 trailing-4-GW form;
C3 two-part P(plays|band) x E[pts|plays,band x position] + P(DNP) x E[pts|DNP].
Selection rule frozen: C3 must beat C0, C1 AND C2 on played-row MAE and not show
worse bias than C1 to count as supported.

| candidate | MAE all | MAE played rows | bias all | Spearman (played) |
|---|---|---|---|---|
| C0 zero | 0.436 | 2.239 | -0.432 | n/a |
| C1 band mean | 0.511 | 1.491 | -0.001 | 0.184 |
| C2 trailing form | 0.434 | 1.729 | -0.136 | 0.143 |
| C3 two-part | 0.511 | 1.484 | +0.002 | 0.178 |

Calibration per band (mean predicted vs actual 0.06 / 0.98 / 1.75):
C1 0.12 / 0.90 / 1.53; C2 -0.00 / 0.62 / 1.49; C3 0.12 / 0.93 / 1.53.

Significance of the gaps (cluster bootstrap by player, 5000 resamples, test season;
differences written as first-minus-second):
- C2 - C0 overall MAE: median -0.001, 95% CI [-0.011, +0.009]. The interval crosses
  zero, so this analysis does NOT distinguish the nominal form edge from no edge -
  it neither confirms a real edge nor proves it is noise.
- C3 - C1 on played rows: median -0.007, CI [-0.010, -0.004] - C3 lower (better) by
  a statistically clear but practically negligible margin (~0.5% relative).
- C2 - C1 on played rows: median +0.238, CI [+0.214, +0.261] - C2 higher (worse);
  the band mean beats trailing form on played rows by about 0.24 pts.

POPULATION-DEFINITION LIMITATION (material, applies to this whole evaluation):
the frozen spec says "trailing-4-GW minutes", but both the original interactive
run and the committed reconstruction (scripts/low-minutes-eval.py) implemented
the trailing window as the player's previous 4 ROWS within the season, skipping
missed GWs. Every other pipeline component uses CALENDAR gameweeks: the model
panel, both backtests and the prospective runner share one PANEL_SQL (RANGE
BETWEEN 4 PRECEDING AND 1 PRECEDING on gw, requiring a row in all 4 GWs,
>= 180 minutes), and the live gate (scripts/12thman2-refresh.mjs) takes the last
4 rounds of FPL element-summary history. For players with an absent trailing row
(intermittent players, mid-season signings, data gaps) the two rules assign
different eligibility and bands. Measured scope on the fit DB (gw>=5, 126,353
raw fixture rows): 1,683 gate flips (542 rows-gated-only, 1,141
calendar-gated-only), concentrated in 2021-22 (3.06% of that season's rows) and
declining to 78 flips (0.29%) in the 2025-26 test season; 1,712 band flips
among the 87,918 commonly gated rows; trailing minutes differ on 11,791 rows
(median 90, max 270 where differing). Consequences: the numbers in this evaluation are not computed on the
population the model, backtests, or live gate would use, and the spec's intent
is calendar; treat the evaluation as approximate at the eligibility margin,
especially for intermittent players. Not patched: the spec for this run was
frozen, and the rest of the pipeline is internally consistent on the calendar
rule for eligibility and features (see docs/15 for the full grain audit,
including two panel-side issues found during it: blank-GW eligibility and the
opponent-strength feature's units).

Outcome per the frozen rule: C3 is NOT supported - its played-row edge over the
trivial band-mean baseline is negligible, so its extra machinery buys nothing.
On overall MAE, no candidate shows an edge over silent zero that this analysis can
distinguish from no edge (most gated-out players do not play), which is why the page
discloses rather than imputes. What survives: on the rows that
matter for decisions (the player actually plays), a trivial band mean recovers most
of the orderable signal (rho 0.18 vs zero's none); cold starts carry no orderable
signal at all; and none of these one-week estimators address the six-week horizon.
Six-week dependence can instead be shown as explicit multi-week scenarios (e.g. the
missing player performs at his band mean, or at the played-row mean, across the
horizon) - dependence displayed without claiming probabilities.

## Multi-week scenario dependence (his squad, GW9-14 horizon, 31 Oct)

Explicit hypothetical paths for the missing player (João Pedro). These are NOT
forecasts: each path holds his xP flat across the horizon (fixtures ignored), all
other projections and prices fixed. P2 uses the played-45+ band mean, a POST-OUTCOME
average over weeks gated-out players happened to play - shown only as an upper-ish
"back and starting" path, never as a decision-time expectation. Engine re-run per
path (plans + assess machinery unchanged):

| path | GW9 xiXp | JP in XI | named fix | hold horizon | single horizon | aggr horizon | plan order |
|---|---|---|---|---|---|---|---|
| P0: 0/GW (page behavior) | 45.6 | no | Cherki->Tavernier +2.43 | 274.9 | 288.2 | 318.3 | aggr > single > hold |
| P1: band mean 1.57/GW | 45.6 | no | Cherki->Tavernier +2.43 | 274.9 | 288.2 | 318.3 | unchanged |
| P2: played-mean 3.15/GW | 46.1 | yes (flagged: injury news) | Cherki->Tavernier +1.92 | 277.6 | 288.6 | 318.3 | unchanged |
| P3: 5.0/GW | 47.9 | yes (flagged) | Groß->Tavernier +1.75 | 288.7 | 299.1 | 323.6 | unchanged, gaps narrow |

Read, with the scenario limits stated: within THESE four flat paths on THIS page
state (fixtures omitted, all other projections frozen), the verdict class does not
move; the named fix changes identity by P3 and its gain shrinks from P2; plan order
holds while horizon gaps move up to ~14 xP; and once rated, his injury news flags
him as a starter risk (starters flagged 1 -> 2). Nothing here establishes general
decision-inertness below ~3 xP/GW: a finite set of flat paths cannot show that, and
fixture variation alone could move any of these points. Nor is his return output
purely a fitness question: both his playing time and his points conditional on
returning remain uncertain, and both are partly modelling questions the current
model cannot answer.

## Appendix: frozen spec (verbatim, frozen 31 Oct 2026 before the run)

FROZEN SPEC - low-minutes estimator retrospective evaluation (31 Oct 2026, frozen before this run)
Population: epl_fpl_gameweeks, gw>=5, gated-out = trailing-4-GW minutes < 180.
Fit seasons 2021-22..2024-25; test season 2025-26 (retrospective chronological; 2025-26
was already inspected during this rebuild - NOT untouched validation).
Candidates:
  C0 silent zero
  C1 nonzero baseline: fit-period unconditional band mean (bands: 0 / 1-89 / 90-179 trailing min)
  C2 nonzero baseline: trailing form = mean total_points over trailing 4 GWs (0 when no trailing rows)
  C3 two-part hypothesis: P(plays>0 | band) x E[pts | plays, band x position] + P(DNP) x E[pts|DNP]
Metrics (all pre-registered): overall MAE; MAE on played rows (minutes>0); bias overall and
per band; calibration = mean predicted vs mean actual per band; decision sensitivity =
Spearman rank correlation of prediction vs actual on played rows (the buy-side ordering question).
Selection rule: no estimator is merged on one metric; C3 must beat C0, C1 AND C2 on played-row
MAE and not show worse bias than C1 to count as supported.

## Reconstruction (not a reproduction of the original)

The original evaluation run was interactive and its code was not persisted; the
original numbers are NOT exactly recoverable. scripts/low-minutes-eval.py
(committed 31 Oct) is a reconstruction from the frozen spec above. Against the
same DB (seed 20261031, deterministic ORDER BY) it matches the table at printed
precision except: C0 MAE-all (0.435 vs 0.436), C0 MAE-played (2.238 vs 2.239),
C1 MAE-played (1.489 vs 1.491), C1 bias (+0.000 vs -0.001), C2 MAE-played
(1.727 vs 1.729), C2 Spearman (0.142 vs 0.143), C3 MAE-all (0.510 vs 0.511),
C3 MAE-played (1.482 vs 1.484), C3 bias (+0.003 vs +0.002), C3 Spearman (0.179
vs 0.178), C3 b90_179 calibration (1.54 vs 1.53), and bootstrap CI lower bounds
(C2-C0 -0.012 vs -0.011; C3-C1 -0.011 vs -0.010; C2-C1 +0.237 [+0.215, +0.261]
vs +0.238 [+0.214, +0.261]). All band calibration actuals and the C1/C2
calibration rows match exactly. These are unexplained implementation
differences in the original run, reported as-is; matching confidence intervals
would not establish implementation equivalence and are not offered as
justification. No causal attribution for the remaining gaps is established.
Candidate contributors, unproven: the original run's tie handling among
same-player-GW fixture rows (the DB holds 5,541 such doubles; the
reconstruction pins ties by opponent_team_id) and any other unpersisted
implementation details. An aggregated player-GW-grain variant diverges further
(C0 0.440, C1 0.522, C2 0.439, C3 0.521 overall MAE), which is consistent with
the original having run on raw fixture rows but does not prove it. Note the
rows-vs-calendar mismatch above CANNOT explain these gaps: the original run and
this reconstruction both used row windows. See docs/15 for the full grain
audit. The reconstruction also inherits the population-definition
limitation above (previous 4 rows, not previous 4 calendar GWs).
DB: /tmp/epl12_fit.duckdb, built by scripts/fit-12thman-model.py.
