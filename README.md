# EPL x FPL Analytics Playground

Eleven seasons of Premier League data in a DuckDB warehouse - local file for offline work, MotherDuck's free tier for the live cloud copy - queried in plain English through an AI assistant over a read-only connection. The same tables power a backtested player model and a Fantasy Premier League picker that hunts undervalued players.

**Status: live.** The warehouse runs on MotherDuck (cloud DuckDB) with a local DuckDB fallback built from the same script. It started life on ClickHouse Cloud; when the trial ended, the project moved to a free-tier setup with the same data and a simpler AI-connection story. The full migration note is [docs/08_motherduck_migration.md](docs/08_motherduck_migration.md); the original ClickHouse load script and tutorial chapters stay in the repo as the build record.

## The idea

One dataset, two payoffs.

1. **A showcase.** 11 seasons of EPL data (2016-17 through the current 2026-27 season) in a real warehouse, with an AI assistant as the natural-language front door. Ask a question in English, get an answer straight off the warehouse - over a connection that is read-only enforced by the database itself, not by instructions.
2. **An edge.** The same tables drive a backtested player-performance model and an FPL picker that surfaces differentials (high predicted points, low ownership) before the crowd notices.

## Architecture (zero code)

- **DuckDB SQL** - the engine. Every load and every model run is plain SQL, in [sql/epl_duckdb_load.sql](sql/epl_duckdb_load.sql).
- **MotherDuck free tier** - the live cloud warehouse. The same load script runs unchanged against a local `.duckdb` file, so everything also works offline.
- **Public CSV sources** loaded straight from their URLs. No downloads, no scripts, no servers:
  - [vaastav/Fantasy-Premier-League](https://github.com/vaastav/Fantasy-Premier-League) - official FPL data per player per gameweek, 2016-17 onward.
  - [football-data.co.uk](https://www.football-data.co.uk/) - match-level results and stats for the same seasons.
- **AI assistants via MCP** - the natural-language layer. Assistants connect to MotherDuck's MCP server with a server-side read-only credential: reads work, INSERT/UPDATE/DELETE/CREATE/DROP are rejected by the database.

## Data model

Three raw tables, one derived:

- `epl_fpl_gameweeks` - one row per player per gameweek (~258k rows): minutes, goals, assists, xG/xA, starts, FPL points, price, opponent, venue.
- `epl_fpl_players_raw` - FPL's own season aggregates per player (~8k rows), including `player_code`, the stable cross-season join key.
- `epl_matches` - every match, 380 per season: scores, shots, corners, cards.
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

- [x] M1 - Data loaded + sanity queries (first on ClickHouse Cloud, now rebuilt on MotherDuck + local DuckDB)
- [ ] M2 - Backtest v1: cohort, baseline, weighted-form model, verdict vs 0.52
- [ ] M3 - Picker v1: form + fixture model, differential leaderboard
- [ ] M4 - Showcase writeup: the demo queries packaged as the natural-language-to-warehouse story

The full working blueprint lives in [docs/blueprint.txt](docs/blueprint.txt).
