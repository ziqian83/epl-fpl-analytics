# Picker signals (11 as of 2026-09-12)

1. Consistency: % of 60+ min GWs with 4+ FPL points (tunable; the 2+ bar is meaningless - appearance points auto-satisfy it).
2. Form-sustain: streak analysis beyond raw form number.
3. Fixture weighting: epl_teams strength_defence_home/away (2019-20+).
4. Minutes security: rotation/injury risk; presser quotes are earliest warning (see #11).
5. Home/away splits.
6. Points-per-million: value discipline.
7. Team-proof: team W/D/L record in matches the player appeared in; metric = L/W ratio (Bruno 0.33 vs Haaland 0.38 dry run - hypothesis did not hold; Odegaard 0.25 vs Isak 0.57 in 2025-26).
8. Transfer economics: -4 hit cost; only swap when expected gain over hold horizon exceeds it.
9. Transfer banking / option value: FTs bank to cap of FIVE (2026-27 rule, corrected from 2). Model BOTH sides: real-options value vs "cash drag" (his phrase) = foregone points from moves not made. Engine output = crossover point. At the 5-cap the weekly FT is forfeited - expiring allowance, same family as GW19 chip expiry. Demo exhibit name: "option value vs cash drag in one model".
10. Cold-start handling for no/thin-history players: priors from transfer fee, FPL starting price, position priors (DEF settle faster than FWD), early ownership movement as sharp-money signal; weekly Bayesian updating. Three variants: no history (promoted sides), thin+stale (Tzolis: 326 min 2021-22), full-but-dated (Davis: full 2024-25 season). "Data staleness vs development curve" note: young players' old cameos barely predict them; live evidence overrules fast (his "changed player" instinct = recency-decay parameter).
11. External news overlay (future milestone): scrape social/public media, categorize, key to player_code. Prioritize high-precision (injury, suspension, presser quotes) over transfer-rumour sentiment (noisy, priced in via ownership/price proxies). FPL API status+news is the free baseline to beat.

## Backtest framing
- Train 2021-22..2024-25, test 2025-26; cohort 900+ minutes both windows; beat-the-baseline bar = 0.52 Pearson (verified 2023-24 -> 2024-25, 203 players); use rank correlation for final metric.
