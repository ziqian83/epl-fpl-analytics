# The 12th Man v2 - decision design (fresh brief, 31 Oct 2026)

Written 31 Oct 2026. This is the concrete design for the rebuild he asked for at
09:13 ("start from scratch to revisit what is truly the build that should be the
12th man"). It answers his two data-design questions (09:08, 09:10), states what
v1 could not do, and pins down every judgement line v2 draws so the lines can be
challenged. v1 stays live and untouched; v2 ships alongside it under
`12th-man/v2/`. No Boot Room code, scoring rules or constants are carried over -
the concepts he asked for are rebuilt fresh and defined in this document.

## The brief (his words, 31 Oct 2026, WhatsApp)

1. "I need to first determine if my team is good enough for that gameweek or if
   I need to make decisions to fix it."
2. "I have a free transfer each gameweek but I can choose to make more if the
   numbers back it up."
3. "There are chips to use based on the rules of the game and I need the 12th Man
   to decide if it is the best option to use it that week."
4. "The 12th Man should make all its decisions based on data, ie. whether a
   player is on form consistent or just a one week wonder."
5. Two horizons, confirmed 09:19: this gameweek AND the next 5-6, each compared
   against holding, with expected benefit, points cost, uncertainty and
   opportunity cost. Recommendations allowed; the final risk choice is his,
   situational, every week.
6. 09:21-09:22: personal tool AND a data-analytics show-and-tell. He chose his
   own squad for the walkthrough: "You can publish the squad but keep the ID
   private."

## Where the data comes from (his 09:08 question)

The 12th Man does not need MotherDuck to *run*. Three layers, each replaceable:

- **Live player data** - the official FPL API (bootstrap-static, element
  summaries, fixtures). Public, read-only, no login. A GitHub Action pulls it
  daily and commits a generic player pool (`v2/data/pool.json`): every player's
  recent per-gameweek record, projections, fixtures, price, ownership, status.
  No team IDs, no squads - publishable by construction.
- **His squad** - the same public API, keyed by his team ID, fetched in the
  browser through one named read-only relay when he taps Load. The ID lives in
  his browser's localStorage only. What the ID reveals and what it cannot see is
  stated on the page itself.
- **The warehouse (MotherDuck/local DuckDB)** - used OFFLINE, for one job:
  fitting and validating the projection model on 10 seasons of history. The
  shipped model is a small set of coefficients in the repo; the running app
  never queries the warehouse. If MotherDuck's free tier vanished tomorrow, the
  app would not notice.

Cost: S$0. Public API + free relays + GitHub Pages/Actions free tier.

## What got lost between the Boot Room and the 12th Man (his 09:10 question)

The audit (31 Oct) compared the two codebases. Four Boot Room capabilities were
never rebuilt for the 12th Man; v2 restores each as a fresh implementation:

1. **Consistency signal.** Boot Room scored how reliably a player returns, not
   just his average. v1 carried only averages. -> v2 evidence module, below.
2. **"Who else should I have considered."** His standing ask (17 Oct): a squad
   review that only looks at his 15 misses the point. -> v2 outsiders module.
3. **Chip timing per week.** Boot Room treated chips as decisions with windows;
   v1 showed chip state only and said "timing judgement is yours". -> v2 chip
   verdicts, below.
4. **Accountability loop.** Frozen calls scored after the deadline. -> v2 design
   includes it; implementation is a later milestone (named, not silent).

## The decision room (page structure)

1. **The verdict** - one card: "Good enough for GWn?" Projected XI points,
   flagged concerns, the best available fix and its expected gain. Three honest
   classes (thresholds are judgement lines over a weak signal, shown with their
   numbers):
   - *Good enough* - best legal 1-FT fix this GW gains < 0.75 xP and no starter
     is news-flagged: no fix worth a certain cost.
   - *One fix worth judging* - gain 0.75-2.0 xP, or one flagged starter.
   - *Surgery worth modelling* - gain >= 2.0 xP, or 2+ flagged starters.
2. **What I would do** - the feasible plays side by side: Hold / one fix / two
   moves (hit if no FTs) / chip plays. Each card shows BOTH lenses - this GW and
   GWn..n+4 - with certain costs, expected benefit, and the opportunity cost of
   each path. When the two lenses disagree the card says so. One card carries
   the "engine lean - weak signal" badge; the risk choice stays with him.
3. **Chips this week** - every live chip with its official window, its expiry,
   and a this-week verdict with evidence. Expiring first-half chips (Bench
   boost, Triple captain, Free hit are lost after GW19 if unplayed) get named
   warnings.
4. **Squad with evidence** - his 15, each with a tap-open evidence drawer:
   last six gameweeks (points, minutes, xGI), form, consistency, spike and
   rotation flags, price, ownership, fixtures.
5. **Who else was considered** - the strongest outsiders per position inside his
   budget and the club cap, so "who should I have considered" is answered every
   week without asking.
6. **Method and honesty** - validation numbers, known limits, data as-of stamps.

## Form, consistency, one-week wonder (his requirement 4) - v2 definitions

All computed from the last six completed gameweeks, per player, from the
official per-GW record. A *played* week = 45+ minutes. A *return* = 5+ FPL
points (appearance points alone never reach 5; a return means attacking
involvement, a clean sheet, or bonus).

- **Form**: mean points over the last 4 GWs (`form4`) and last 2 (`form2`), next
  to each other so a recent surge or dip inside the average is visible.
- **Consistency**: returns / played over the last 6 GWs, shown as "4 of 5 starts
  returned 5+". High form with low consistency is a streaky player, not a
  reliable one.
- **One-week-wonder flag**: last-GW points >= 8 AND last-GW xGI <= 0.5 AND
  last-GW points at least 5 above his prior form4. Points without underlying
  involvement - the exact signature of a haul that does not repeat.
- **Quiet-runner flag (the reverse)**: last-2-GW xGI >= 1.5 with <= 4 total
  points. Involvement without returns - the positive-regression candidate the
  crowd is ignoring. This is where differentials come from.
- **Rotation flag**: mean minutes over the last 3 GWs under 60.
- **News flag**: FPL status and news carried verbatim (injury, doubt,
  suspension).

These are definitions, not claims of predictive power; each is shown with its
raw numbers so he can overrule any flag.

## Chip verdicts (his requirement 3)

Windows come from the official rules data in the FPL API (each chip's valid
gameweek range), crossed with his used-chips history. Current state (31 Oct):
wildcard spent GW7 (second-half wildcard unlocks GW20); Bench boost, Triple
captain, Free hit live, first-half copies expire after GW19.

Each live chip gets a weekly verdict with its evidence:

- **Bench boost**: sum of the bench's projected xP this GW. >= 12: strong
  candidate week. 9-12: plausible - check the horizon for a better bench week
  (doubles). < 9: weak bench week, hold. Always shown with the horizon check.
- **Triple captain**: the XI's best projected score this GW. >= 7 xP: as good a
  week as this model can see (a double gameweek is better - the horizon check
  looks for one). Otherwise hold.
- **Free hit**: starters projecting 0 xP (blank, or news-flagged out). >= 3:
  candidate week - compare against the alternative of taking hits. Otherwise
  hold for a blank gameweek later in the season.
- **Wildcard**: the unconstrained restructure's horizon gain over holding. >= 8
  horizon xP: worth modelling seriously. Plus the standing note: the second-half
  wildcard unlocks GW20.

Every verdict is labelled a heuristic over a weak projection. The chip play is
his call; the page's job is that he never plays one blind.

## Two lenses, conflicts explicit (his requirement 5)

Every play shows this-GW gain and horizon gain side by side. A transfer that
wins this week but loses the horizon (a one-week fixture swing) is flagged as a
conflict, not averaged away. The engine lean picks the best horizon net after
certain costs and says so; the card for the this-GW lens stays visible because
his risk choice is situational (his 09:19 ruling).

## Validation and honesty protocol

- Labelling decision (31 Oct, after review): the verdict, every chip badge and the
  engine lean carry their experimental status in the primary label itself
  ("Experimental - not validated advice", "Heuristic candidate/hold"), not only in
  surrounding caveats. A class name like "surgery" or "candidate" must never read as
  a recommendation to act.

- The projection model stays the v1 OLS (method: docs/09) until a refit beats it
  on the same protocol - and the fit script ships in the repo this time
  (milestone below), so coefficients are reproducible from public data.
- Rolling-origin holdouts, pairwise swap ordering vs naive persistence as the
  decision-relevant metric. Current honest numbers: pair accuracy 0.501/0.503
  vs 0.486/0.490 naive on the 2024-25/2025-26 holdouts; MAE a wash; correlation
  up on both. A weak signal - enough to sort a shortlist, never enough to
  justify a move alone. That sentence appears wherever xP is shown.
- Uncertainty is presented as ranges and classes, never decimals-as-truth:
  mean error per player-GW is ~2.3 points, so single-GW gaps under ~1 point are
  labelled noise.
- No captaincy model, no price-change prediction, no news scraping in v2 -
  named as limits, not faked.

## Build milestones

1. v2 pool (daily refresh, per-GW history rows, chip windows) - this commit.
2. v2 engine (verdict, plays, chips, evidence, outsiders) + tests - this commit.
3. v2 page at /12th-man/v2/ - this commit. v1 untouched at /12th-man/.
4. Committed, reproducible fit script for the model (audit gap) - next.
5. Frozen-calls accountability log (calls scored after each deadline) - next.
6. LLM surface over the MCP connection (his "best of both worlds") - parked
   until the warehouse's read-only AI credential is restored.
