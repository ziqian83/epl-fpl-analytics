# 16 - Panel v2 spec (FROZEN 31 Oct 2026) - versioned correction of docs/15 defects

Versioned correction authorized for the confirmed grain/feature defects. v1
(scripts/fit-12thman-model.py, docs/09) is FROZEN and unchanged; v2 lives in
scripts/fit-12thman-model-v2.py with checks in tests/test_grain_v2.py. v2 does
NOT feed live advice or the page without its own prospective evidence; a refit
alone promotes nothing. Its prospective start must be pinned before the first
deadline it affects (separate artifact, not the existing GW10 freeze, which
stays provisional per docs/13).

## Source facts (verified 31 Oct on the cached CSVs, all 5 seasons)

- vaastav merged_gw.csv: raw fixture rows; `fixture` = official fixture id;
  380 fixtures/season; scores consistent within fixture; exactly 2 teams per
  fixture; fixture ids never span GWs; max 2 fixtures per team-GW; double
  team-GWs per season: 61/42/23/10/10; blank GWs enumerated (teams < 20).
- team_h_score/team_a_score are the FIXTURE's final score (constant across the
  fixture's player rows). The per-player `goals_conceded` column is a different
  player-on-pitch stat and is NOT used anywhere in v2.
- Official element-summary history (prospective 2026-27 pull): one row per
  round per registered player INCLUDING 0-minute rounds (669/669 players
  contiguous GW1-8); per-fixture rows by construction (no doubles yet in
  GW1-8). Blank-round shape UNVERIFIED (no blank so far in 2026-27): whether a
  future blank round yields a 0-minute row or no row is an open source question.
- vaastav vs API difference: 371/841 vaastav 2025-26 players have in-span gaps
  (absent records while their team played; reason unestablished), versus 0/669
  for the API pull. v2 records these as n_missing4, distinct from true blanks.

## Canonical definitions (the shared grain, docs/15 C1-C3)

- GRID: one row per (season, gw, player_id): mins/pts/xgi summed across the
  GW's fixtures; nfix = distinct fixtures (1 or 2); position/team via MAX
  (consistent within a GW).
- FIXTURE: one row per (season, fixture, team): conceded = opponent's goals
  from the fixture's final score (home team concedes team_a_score, away
  concedes team_h_score).
- TEAM-GW conceded: mean conceded across the team's fixtures that GW. A GW
  where the team has no fixture is a TRUE SCHEDULED BLANK: no team-GW row.
- Trailing windows: calendar GWs, RANGE BETWEEN 4 PRECEDING AND 1 PRECEDING.
- Player features: f_pts4/f_xgi4 = per-GW means over the player's grid rows in
  the window; f_minshare4 = mean(mins/90) (a double GW can contribute up to
  2.0 - intended: minutes per calendar GW); nrows4 = distinct GWs with a
  player record; target_pts = the GW's summed points.
- Opponent strength: for (k, team), mean over the GW-k opponents' opp_gc4,
  where opp_gc4 = trailing-4-calendar-GW mean of the opponent's TEAM-GW
  conceded over GWs WITH a fixture (true blanks shorten the divisor;
  n_gws4 recorded).
- Semantics for absence: n_blank4 = expected calendar GWs in the window
  (4, or k-1 before GW5) minus GWs where the team had a fixture; n_missing4 =
  team fixture GWs minus player records. True blanks and absent records are
  never merged.
- Eligibility (UNCHANGED outcome vs v1): nrows4 = 4 AND trailing minutes
  >= 180. The exclusion reason is now recorded (blanks vs missing vs minutes).

## Checks (tests/test_grain_v2.py, deterministic, all passing 31 Oct)

- A-series (synthetic league with a double GW, a true blank, missing records):
  double minutes/points summed into one GW row; blank counted as n_blank4 not a
  row; missing record counted as n_missing4; opp_strength_k in per-fixture
  goals (not row-scaled).
- B-series (real v2 DB): v1 vs v2 panel membership, f_pts4, f_xgi4,
  f_minshare4, target_pts IDENTICAL; only opp_strength_k changes
  (max delta 156, mean delta 52 - the removed row-scaling).

## First v2 fit (retrospective, inspected seasons - exploratory, NOT validation)

Fit on the same cached CSVs; rolling-origin, identical protocol to v1:
- 2024-25 (train 21-22..23-24): model MAE 2.201, corr 0.253, pair-acc 0.486;
  baseline (trailing form) MAE 2.380, pair-acc 0.477.
  (v1 same protocol: MAE 2.242, pair-acc 0.501.)
- 2025-26 (train 21-22..24-25): model MAE 2.295, corr 0.188, pair-acc 0.497;
  baseline MAE 2.578, pair-acc 0.484.
  (v1 same protocol: MAE 2.299, pair-acc 0.503.)
Read: MAE marginally better, pair-acc marginally worse than v1 on both
inspected holdouts. No promotion, no live change; these seasons are inspected,
so this is a sanity read on the corrected units, not evidence of improvement.

## Open source questions

1. Blank-round shape in live element-summary history (0-minute row vs absent)
   - decides whether the live gate needs a parallel blank rule. Testable with a
   source-shaped synthetic history against the refresh gate logic; first
   natural blank also works whenever one lands.
2. Reason for vaastav in-span gaps (371/841 players): mid-season registration
   vs scraper gaps - affects how n_missing4 should be interpreted.
3. Whether v2's opp_gc4 should include a defensive-home/away split - NOT in
   scope; would be a new spec and new version.
