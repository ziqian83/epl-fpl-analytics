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
