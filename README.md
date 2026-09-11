# EPL x FPL Analytics Playground

Ten seasons of Premier League data sitting in ClickHouse Cloud, queried in plain English through the ChatGPT data connector. The same tables power a backtested player model and a Fantasy Premier League picker that hunts undervalued players.

**Status: build in progress.** ClickHouse Cloud trial reactivation is in flight with their team. The load script is written and tested end-to-end; the tables go in the moment the trial flips.

## The idea

One dataset, two payoffs.

1. **A showcase.** 10 seasons of EPL data (2016-17 to 2025-26) in a real warehouse, with ChatGPT as the natural-language front door through its ClickHouse data connector. Ask a question in English, get an answer straight off the warehouse. That is the "ChatGPT as front door to the data warehouse" story, running live on data I actually care about.
2. **An edge.** The same tables drive a backtested player-performance model and an FPL picker that surfaces differentials (high predicted points, low ownership) before the crowd notices.

## Architecture (zero code)

- **ClickHouse Cloud SQL console** - the engine. Every load and every model run is plain SQL pasted into the browser console.
- **Public CSV sources** loaded straight from their URLs with ClickHouse's `url()` table function. No downloads, no scripts, no servers:
  - [vaastav/Fantasy-Premier-League](https://github.com/vaastav/Fantasy-Premier-League) - official FPL data per player per gameweek, 2016-17 through 2025-26.
  - [football-data.co.uk](https://www.football-data.co.uk/) - match-level results and stats for the same 10 seasons.
- **ChatGPT data connector** - the natural-language layer on top. Questions in, answers out, nothing exported.

## Data model

Three raw tables, one derived:

- `epl_fpl_gameweeks` - one row per player per gameweek (~254k rows): minutes, goals, assists, xG/xA, starts, FPL points, price, opponent, venue.
- `epl_fpl_players_raw` - FPL's own season aggregates per player (~7.4k rows), including `player_code`, the stable cross-season join key.
- `epl_matches` - every match, 380 per season, 3,800 total: scores, shots, corners, cards.
- `epl_player_season` (derived) - one row per player per season, the backtest workhorse.

One early catch worth documenting: FPL reissues player IDs every season (Haaland has had four), so cross-season joins run on `player_code`. The first backtest attempt joined on the wrong key and produced garbage.

## Backtest

- Train on 2021-22 to 2024-25, test on 2025-26.
- Cohort: players with 900+ minutes in both windows (203 qualified in the dry run).
- Baseline to beat: "next season = last season". Measured on real data, that correlation is **0.52**. A model ships only if it beats the naive baseline; if nothing does, that is itself a publishable finding.
- Candidates: weighted 3-season form, minutes trend, age curve (needs an extra data source).

## FPL picker

Per gameweek: predicted points = recent per-90 form x expected minutes x fixture difficulty. Differential score = predicted points vs ownership %. High prediction plus low ownership is the pick that wins mini-leagues.

## Demo queries (all verified against the loaded data)

- Top scorer every season for 10 years, one query.
- Which players beat their expected goals two years running?
- Best FPL value this season: points per million, 900+ minutes.
- Differentials: top scorers owned by under 5% of managers.
- Home advantage by season: 49% home wins in 2016-17, 38% in the behind-closed-doors 2020-21 season.
- Is last year's form a good predictor? The 0.52 baseline, computed live.

## Milestones

- [ ] M1 - Data loaded + sanity queries (script tested, blocked only on the trial)
- [ ] M2 - Backtest v1: cohort, baseline, weighted-form model, verdict vs 0.52
- [ ] M3 - Picker v1: form + fixture model, differential leaderboard
- [ ] M4 - Showcase writeup: the demo queries packaged as the ChatGPT-connector story

The full working blueprint lives in [docs/blueprint.txt](docs/blueprint.txt).
