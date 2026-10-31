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

## What this supports and what it does not

- The silent zero is approximately right for true cold starts (0.10) and for
  injury-return shapes (0.38). It is most wrong for the 90-179 trailing-minute band
  (~1.6 pts/GW understatement): rotation and short-term absence, exactly the players
  who re-enter XIs.
- Any future estimator must be two-part and measurable: P(plays) x E[pts|plays], by
  trailing band and position, with FPL status/chance_next as the live P(plays) input
  (João Pedro GW9: chance_next=0% dominates his band base rate). No single discount
  coefficient is supported by this data.
- ep_next as a fill-in remains an UNVALIDATED external baseline: validating it against
  our weak model tests agreement, not accuracy. Validate against as-of recorded outcomes
  only if a historical as-of source is recoverable; the official API does not expose
  historic ep_next snapshots, so recoverability is doubtful.
- These distributions describe the pool-wide average. Nothing here changes a shipped
  number today; the page discloses missing projections instead of imputing them.
