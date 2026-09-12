# Model & demo notes (2026-09-12)

## Consistency baseline
% of 60+ min GWs with 4+ FPL points. Parameter agreed with user. Reference values (2025-26): Alex Scott 0.52 (33 starts), Janelt 0.53 (15 starts), Mitchell 0.49, Tavernier/Bogle 0.39, Barnes 0.22.

## FPL 2026-27 rule changes (verified from official sources)
- FT banking cap FIVE (game_settings max_extra_free_transfers=4).
- TWO chip sets: WC/FH/BB/TC for GW1-19 (expire at GW19 deadline Jan 2 2027), fresh set GW20-38. Use-it-or-lose-it.
- Defensive Contribution scoring: DEF 2pts for 10+ tackles/blocks/clearances/interceptions; MID/FWD 12+ actions+recoveries. Backtestable in warehouse (vaastav has these cols). Strongest new demo item.
- BPS rebalance toward GKP/full-backs/attackers. Official price-change prediction page (midnight UK daily). Real-time ranks. GW points lock 9am UK next day.
- Club limit 3 (his triple-Brighton is at the cap). 50% sell-on fee = churn tax.

## Wildcard backtest (run 2026-09-11, 10 seasons)
- Template settling (avg overlap of final top-20 by GW): GW1 4.0, GW2 5.5, GW3 6.5, GW4 6.8, GW6 8.4, GW8 9.1, GW12 10.6. NO information cliff at GW4 (+0.3 over GW3).
- Starter certainty: ~68% of eventual 2500+ min regulars identifiable by GW3.
- Verdict given: don't WC at GW4; stockpile to 5 FTs, reassess GW6-8 (~45% certainty + 5 FTs + WC in hand); latest window GW18-19 (chip expiry).

## Captaincy analysis (GW4, delivered)
Isak (FUL H) over Odegaard (SUN A): live form 23pts/7.7 vs 24/8.0, but Odegaard's double hauls both at home, away dip 3.0 vs 3.2 pts/app, Sunderland defense elite-value. Verdict: keep Isak (C).

## Derby hypothesis (delivered): does NOT survive
United home vs City 10y: W3 D2 L5, 8-12 goals. Home PPG vs City 1.10 vs ~1.98 vs others. City concede FEWER at Old Trafford (0.8/game, 50% CS) than general away (0.9, 42.8%). Relevant to Guehi CS odds.

## Differential scan GW4 (delivered)
Top 5: Alex Scott BOU 5.1%, Bogle LEE 1.7%, Tavernier BOU 3.4%, Janelt BRE 1.9%, Barnes NEW 2.2%. Flags: his own Mitchell (CRY, 6.1%) is a differential on his bench; Hull stack on watchlist (3 CS/3 but no history + hard fixtures).

## Demo layer
- Web deck on ziqian-hoe.netlify.app: local-first pre-computed snapshots, ONE live-mode slide querying ClickHouse Cloud. Visual rules: near-black base, black/white + matt-champagne-gold accents (never opulent), quiet confidence, serif OK no thin weights small, pure white over grey, mobile-size check.
- Corporate analogs: consistency=revenue quality; team-proof=alpha vs beta; form-sustain=initiative decay; fixture weighting=territory-adjusted measurement; ppm=ROI; minutes security=key-person risk; transfer economics=switching cost; banking=real options + cash drag; Defensive Contribution=scorecard redesign revealing glue work; chip expiry=expiring budgets; club limit=concentration cap; auto-subs=failover design; price changes=mark-to-market + transaction tax.
- Data-quality chapter exhibits (all from real weekend bugs): joins (player_id vs player_code), cold starts (3 variants), entity resolution (era name formats + stable keys), query scoping (Davis 2025-26-only miss).
