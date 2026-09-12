# M2 Backtest results - the 11 picker signals vs 10 seasons of history

Run date: 12 Sep 2026, live against ClickHouse Cloud service `epl-playground` (253,900 player-gameweek rows, 2016-17 to 2025-26). Every number below is the output of one SQL query on the warehouse; no numbers are carried from memory. Queries reproduced in the appendix.

## Method

- **Train window:** 2021-22 to 2024-25 (four completed seasons). **Test season:** 2025-26.
- **Cohort:** players with 900+ minutes in the window(s) being compared (a season is ~3,420; 900 drops cameos). Join key is `player_code` throughout - FPL reissues `player_id` every season, and a cross-season `player_id` join is known to produce garbage (-0.07 vs 0.52 correlation).
- **Metrics:** Pearson correlation, Spearman rank correlation (the final metric, fairer to outliers), and top-quintile precision: of the players the signal ranks top-20%, what share go on to beat the cohort's average points-per-90 in the test season.
- **Outcome:** 2025-26 FPL points per 90 minutes.

## The baseline to beat

"Next season = last season", season total points, 2023-24 -> 2024-25, 900+ minutes both seasons:

| cohort | Pearson | Spearman |
|---|---|---|
| n = 203 | **0.517** | 0.454 |

This revalidates the 0.52 logged in the dry run. Any model that cannot beat it does not ship; if nothing beats it, that is the finding.

## Signal-by-signal verdicts

| # | Signal | n | Pearson | Spearman | Top-quintile precision | Verdict |
|---|---|---|---|---|---|---|
| 1 | Consistency (4-season, % of 60+min GWs with 4+ pts) | 242 | 0.304 | 0.263 | **73.5%** (base rate 46.7%) | **HOLDS** as a screen |
| 1b | Consistency (single-season lag 24-25 -> 25-26) | 203 | 0.345 | 0.316 | 68.3% | holds, slightly sharper short-window |
| 2 | Form-sustain (longest 4+pt streak, train window) | 242 | 0.214 | 0.176 | 67.3% | weak standalone; tiebreaker |
| 3 | Fixture weighting (opponent defensive strength) | ~13.8k GWs/tier | see gradient below | - | - | **HOLDS strongly** at GW level |
| 4 | Minutes security (train availability share) | 242 | 0.105 | 0.083 | - | **BUSTED** as historical predictor |
| 5 | Home/away split persistence | 173 | 0.001 | - | - | **BUSTED** as a stable trait |
| 6 | Points per million | 242 | 0.206 | 0.249 | 59.2% | holds as a value screen |
| 7 | Team-proof (L/W ratio in matches played) | 242 | -0.133 | -0.192 | 65.3% | **HOLDS directionally** |
| 8 | Transfer economics (-4 hit) | analytic | - | - | - | rule, applied in picker |
| 9 | Banking / option value | wildcard backtest 11 Sep | - | - | - | see below |
| 10 | Cold-start price prior (newcomers 2025-26) | 43 | 0.534 | 0.497 | - | **HOLDS** - matches veteran baseline |
| 11 | News overlay | - | - | - | - | future milestone, out of scope |

### What the numbers say

**1. Consistency is the flagship.** Of the 242 qualifying players, the top consistency quintile went on to beat the cohort's average p90 73.5% of the time, against a 46.7% base rate. Top quintile averaged 4.71 p90 in the test season vs 3.87 for the bottom quintile. It is a screen, not a ranker (Spearman 0.263): it reliably separates dependable from streaky, but does not order the dependable among themselves. Corporate read: revenue quality - recurring beats lumpy.

**2. Form-sustain is real but thin.** Longest qualifying streak predicts at Spearman 0.176 with 67.3% top-quintile precision. Keep it as the tiebreaker inside the consistency screen, not as a standalone signal.

**3. Fixture weighting is the cleanest gradient in the warehouse.** Average FPL points in 60+ minute GWs, 2019-20 onward, by opponent defensive-strength quartile (higher rating = stronger defence): 4.04 / 3.75 / 3.37 / 2.98, ~13,800 player-GWs per tier, perfectly monotonic. Facing the weakest-quartile defence is worth +36% points vs the strongest. This is the fixture multiplier in the picker.

**4. Minutes security does not persist.** Training-window availability predicts test-season p90 at 0.083 (Spearman), and availability itself only persists at 0.174. Rotation and injury risk are live information (pressers, news), not history. Dropped as a historical signal; kept as the live overlay.

**5. Home/away splits are noise.** The train-window home-minus-away p90 split correlates with the test-season split at 0.001 (n=173). A player's home/away shape does not carry season to season. Splits stay in the toolkit only as descriptive, same-season context (e.g. captaincy calls) - never as a projected edge. This kills a popular pub stat with data.

**6. Points-per-million works where it is used.** Overall ranking is modest (Spearman 0.249), but 59.2% of the top ppm quintile went on to beat the cohort average - value discipline pays at the cheap end. Raw train p90 persists better (Spearman 0.445), so ppm is the screen for affordability, not the predictor of ceiling.

**7. Team-proof holds - in the direction that busts the pub narrative.** The correlation of L/W ratio with next-season p90 is negative (-0.13 Pearson, -0.19 Spearman): players whose teams LOSE more when they play score LESS next season, not more. The "he carries the team" reputation is priced wrong - being the good player on a bad side is a warning, not a virtue. Lowest-L/W quintile: 65.3% beat the average (4.53 vs 3.86 p90). Corporate read: alpha vs beta - separate the unit that outperforms its market from the one riding it.

**8. Transfer economics (the 4-point rule).** A swap only counts if expected gain over the hold horizon beats the -4 hit. With fixture weighting worth up to ~1.06 pts/GW between extremes (signal 3), a transfer held fewer than ~4 gameweeks against a similar-strength schedule rarely clears the bar. Applied as the gate in the picker.

**9. Banking / option value vs cash drag.** From the wildcard backtest run 11 Sep (10 seasons): overlap of the GW-by-GW points leaderboards with the final season's top-20 settles slowly - GW1 4.0, GW2 5.5, GW3 6.5, GW4 6.8, GW6 8.4, GW8 9.1, GW12 10.6. No information cliff at GW4. ~68% of eventual 2,500+ minute regulars are identifiable by GW3. Verdict stands: stockpile to the 5-FT cap (2026-27 rule), reassess GW6-8, latest window GW18-19 before the GW19 chip expiry. The engine output is the crossover point where the option value of a banked transfer beats the cash drag of the move not made.

**10. Cold starts: the price prior works.** 43 newcomers (no prior PL season) played 900+ minutes in 2025-26. Their GW1 price predicts their season p90 at Pearson 0.534 / Spearman 0.497 - as good as the veteran baseline. By position, newcomer attackers are NOT disadvantaged (FWD 4.86 vs returning 4.73 p90; MID 4.38 vs 4.30), but newcomer defenders lag (DEF 3.59 vs 3.83; GK sample tiny). Thin-history handling: trust the market's price for attackers fast, discount new defenders until ~900 live minutes.

## Showcase: the 2025-26 consistency leaderboard (min. 15 full GWs)

| Player | Pos | 60+min GWs | Consistency | Season pts |
|---|---|---|---|---|
| Rayan Cherki | MID | 16 | 0.812 | 135 |
| Gabriel (Arsenal) | DEF | 30 | 0.767 | 209 |
| Reece James | DEF | 19 | 0.737 | 115 |
| Bruno Fernandes | MID | 34 | 0.735 | 235 |
| Casemiro | MID | 29 | 0.690 | 165 |
| Riccardo Calafiori | DEF | 19 | 0.684 | 109 |
| Elliot Anderson | MID | 37 | 0.676 | 180 |
| Nico O'Reilly | DEF | 28 | 0.643 | 160 |
| Erling Haaland | FWD | 33 | 0.636 | 239 |
| Daniel Ballard | DEF | 22 | 0.636 | 116 |
| Lucas Digne | DEF | 19 | 0.632 | 97 |
| Jaka Bijol | DEF | 21 | 0.619 | 99 |

## Headline

No single signal beats the 0.517 naive baseline on its own - that is the honest result, and it is the point. The edge is composite: consistency screens the squad (73.5% precision), fixture strength adjusts the week (+36% swing), the price prior handles players with no history (0.534), and the 4-point rule stops value-destroying churn. Three signals hold strongly, three hold with caveats, two are busted and retired - and the busts are as publishable as the wins.

## Appendix - queries

All queries run 12 Sep 2026 in the ClickHouse Cloud SQL console against the five project tables (`epl_fpl_gameweeks`, `epl_fpl_players_raw`, `epl_matches`, `epl_teams`, `epl_player_season`). Key patterns: cohort join on `player_code`; gameweek rows resolved to codes via `epl_player_season` on `(season, player_id)`; ranks via `rank() OVER`, quintiles via `ntile(5) OVER`; streaks via the row-number island method; opponent strength via `epl_teams.team_id = gameweeks.opponent_team_id` (same season), using `strength_defence_away` when the player is home and `strength_defence_home` when away.
