# M3 Picker v1 - the signal engine applied live

Run date: 12 Sep 2026, ahead of the GW4 deadline (20:30 SGT). Live season data from the official FPL API (bootstrap-static, element-summary, fixtures event=4); model parameters from the M2 backtest on the ClickHouse warehouse. Worked example: MatchDay Blues (team ID 4120529), GW4 squad.

## How the picker reads a player

Per player, per gameweek, five dials - each one backtested in M2:

1. **Consistency** - % of 60+ minute GWs with 4+ points (backtest: 73.5% top-quintile precision). The squad screen.
2. **Value (ppm)** - season points per million of price (59.2% top-quintile precision). The affordability screen.
3. **Team-proof** - W/D/L in matches played; low L/W is the good side (negative correlation confirmed, -0.19 Spearman). "Carries the team" is a warning label, not a virtue.
4. **Fixture weight** - opponent quality this GW; the warehouse gradient says the weakest defensive quartile is worth +36% points vs the strongest.
5. **Home/away split** - descriptive only; the backtest showed splits do not persist season to season (0.001), so this dial informs captaincy, never transfers.

The -4 rule gates every swap: expected gain over the hold horizon must beat 4 points, or the transfer does not happen.

## The squad readout - MatchDay Blues, GW4

| Player | Pos | Team | Price | Own% | Pts | Min | ppm | Consistency | H/A ppg | Team W-D-L | GW4 fixture |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Steele | GKP | BHA | 4.0 | 4.3 | 0 | 0 | - | - | - | - | COV (A, 2) |
| Gabriel | DEF | ARS | 8.0 | 24.1 | 15 | 270 | 1.88 | 0.667 | 3.5 / 8.0 | 3-0-0 | SUN (A, 3) |
| De Cuyper | DEF | BHA | 4.8 | 21.9 | 21 | 243 | 4.38 | 0.667 | 10.5 / 0.0 | 1-1-1 | COV (A, 2) |
| Mitchell | DEF | CRY | 4.5 | 6.6 | 16 | 253 | 3.56 | 0.333 | 0.0 / 8.0 | 1-0-2 | IPS (H, 2) |
| Yalcouye | MID | BHA | 4.5 | 3.3 | 11 | 167 | 2.44 | 0.500 | 1.5 / 8.0 | 1-1-1 | COV (A, 2) |
| Odegaard | MID | ARS | 6.7 | 17.4 | 24 | 221 | 3.58 | 0.667 | 10.5 / 3.0 | 3-0-0 | SUN (A, 3) |
| Szoboszlai | MID | LIV | 7.0 | 38.5 | 15 | 270 | 2.14 | 0.667 | 4.0 / 5.5 | 1-2-0 | FUL (H, 2) |
| B.Fernandes | MID | MUN | 12.0 | 43.4 | 27 | 270 | 2.25 | 0.333 | 23.0 / 2.0 | 1-1-1 | MCI (H, 4) |
| Tzolis | MID | ARS | 6.4 | 16.2 | 11 | 210 | 1.72 | 1.000 | 5.5 / 0.0 | 3-0-0 | SUN (A, 3) |
| Joao Pedro | FWD | CHE | 7.7 | 73.4 | 21 | 270 | 2.73 | 0.667 | 9.0 / 6.0 | 2-0-1 | HUL (H, 2) |
| Isak (C) | FWD | LIV | 9.1 | 23.1 | 23 | 243 | 2.53 | 0.667 | 8.0 / 7.5 | 1-2-0 | FUL (H, 2) |
| Kinsky | GKP | TOT | 4.5 | 18.2 | 9 | 270 | 2.00 | 0.333 | 1.0 / 4.0 | 0-1-2 | EVE (H, 3) |
| Guehi | DEF | MCI | 6.0 | 18.4 | 20 | 270 | 3.33 | 0.667 | 9.0 / 2.0 | 3-0-0 | MUN (A, 4) |
| Davis | DEF | IPS | 4.0 | 5.1 | 9 | 270 | 2.25 | 0.333 | 1.5 / 6.0 | 1-0-2 | CRY (A, 3) |

(Read: 14 of 15 squad slots captured from the screenshot; one midfielder record was not legible. Difficulty 1-5, FPL rating.)

### What the engine flags

- **Best value on the squad: De Cuyper** (4.38 ppm, 0.667 consistency) - the backtested archetype: cheap defender clearing the consistency bar.
- **Watch item: B.Fernandes.** 27 pts at 12.0 is 2.25 ppm with 0.333 consistency; his 23-point home haul against Burnley inflates the line (home/away 23.0 vs 2.0 - descriptive only, but it is the entire season so far). Consistency says lumpy; ppm says expensive. Keep for the MCI home fixture, but he fails the squad screen on two dials - exactly the profile the model says to sell before the crowd does, not after.
- **Watch item: Mitchell and Davis** (0.333 consistency, teams losing when they play - the team-proof warning shape). Davis was the flagged cold-start case: full-but-dated history. Both stay because the -4 rule says a sideways move does not clear the bar; Mitchell (H vs IPS, difficulty 2) holds the better fixture.
- **Triple Brighton is at the 3-per-club concentration cap** - the model treats this as a portfolio concentration limit, and GW4 is away to Coventry (difficulty 2), so the cap is a feature this week.

## Value picks per position (ppm, min 180 mins, live)

| Pos | Top reads |
|---|---|
| GKP | Tzolakis HUL 4.6m (5.65 ppm, 9.8%), Trafford LEE 5.0m (3.0), Raya ARS 6.0m (2.5) |
| DEF | Ajayi HUL 4.2m (5.95), Mendy HUL 4.1m (5.85), Egan HUL 4.1m (5.61), Giles HUL 4.0m (5.0), Bogle LEE 4.5m (4.89), **De Cuyper BHA 4.8m (4.38)** |
| MID | Janelt BRE 5.0m (4.2, 2.2% owned), **Scott BOU 6.1m (3.93, 5.6%)**, Gakpo LIV 7.2m (3.89), Odegaard ARS 6.7m (3.58), Tavernier BOU 6.0m (3.5, 3.6%) |
| FWD | Joao Pedro CHE 7.7m (2.73), Isak LIV 9.1m (2.53), Barry EVE 5.6m (2.14), Havertz ARS 7.5m (2.13) |

## Differential scan (under 10% owned, min 180 mins)

| Player | Pos | Team | Price | Own% | Pts | ppm |
|---|---|---|---|---|---|---|
| Tzolakis | GKP | HUL | 4.6 | 9.8 | 26 | 5.65 |
| Scott | MID | BOU | 6.1 | 5.6 | 24 | 3.93 |
| Mendy | DEF | HUL | 4.1 | 8.1 | 24 | 5.85 |
| Egan | DEF | HUL | 4.1 | 6.3 | 23 | 5.61 |
| Bogle | DEF | LEE | 4.5 | 1.9 | 22 | 4.89 |
| Tavernier | MID | BOU | 6.0 | 3.6 | 21 | 3.50 |
| Janelt | MID | BRE | 5.0 | 2.2 | 21 | 4.20 |
| White | DEF | ARS | 5.5 | 7.6 | 20 | 3.64 |
| Giles | DEF | HUL | 4.0 | 1.6 | 20 | 5.00 |
| King | MID | FUL | 5.5 | 1.2 | 19 | 3.45 |

Notes: Hull City owns the top of the value board (3 clean sheets in 3) but carries no history and a hard fixture run - the cold-start rule says discount defenders without history, so Hull is a watchlist, not a buy. Scott, Tavernier, Janelt, Bogle repeat from the GW4 scan delivered 11 Sep - the model is stable week to week.

## Decision framework for GW5 (2 free transfers banked)

Per the banking model: no information cliff at GW4, ~68% of regulars identifiable by GW3, stockpile to the 5-FT cap, reassess GW6-8. Any GW5 move must clear the -4 bar; the names above are the candidates when it does.
