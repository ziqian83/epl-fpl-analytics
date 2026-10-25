# 08 - Warehouse migration: ClickHouse Cloud to MotherDuck + local DuckDB

Date: 25 Oct 2026

## Why

The ClickHouse Cloud trial ended 12 Oct 2026. The warehouse there is documented as fully
rebuildable from public sources, so instead of adding a payment method, the project moved to
a free-tier setup with the same data and a friendlier AI-connection story.

## What changed

- `sql/epl_duckdb_load.sql` is the DuckDB port of the original ClickHouse load script. It
  builds the full warehouse (10 historical seasons + the current 2026-27 season) from the
  same public sources (vaastav/Fantasy-Premier-League, football-data.co.uk) in ~30 seconds.
- The same script runs unchanged against a local DuckDB file and against MotherDuck's free
  tier (cloud DuckDB), which is where the live warehouse now sits.
- Local fallback: run the script into a local `.duckdb` file and everything works offline.

## Data notes

- 2026-27 is the current season and refreshes weekly. To refresh: delete the 2026-27 rows
  and re-run that season's INSERT statements (the script is a full rebuild, not incremental).
- Coverage is as-of the public sources: player gameweek data typically lags the live FPL API
  by a few days; match results land within a day or two. Use the live FPL API for anything
  deadline-current.

## Access model

- AI assistants connect through MotherDuck's MCP server with a server-side read-only
  credential. Reads work; INSERT/UPDATE/DELETE/CREATE/DROP are rejected by the database,
  not by instructions.
- Recovery: this script + a parquet snapshot of the five tables (kept off-repo) rebuild or
  restore everything.
