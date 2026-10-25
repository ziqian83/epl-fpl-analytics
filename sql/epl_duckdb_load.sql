-- EPL playground load script - DuckDB port (from epl_clickhouse_load.sql)
-- Sources: vaastav/Fantasy-Premier-League (GitHub, CC0-style public repo), football-data.co.uk (public match CSVs)
-- Runs in DuckDB (local CLI, MotherDuck, or duckdb -ui). Loads straight from public URLs via httpfs.


CREATE TABLE IF NOT EXISTS epl_fpl_gameweeks (
  season VARCHAR,
  gw UTINYINT,
  name VARCHAR,
  position VARCHAR,
  team VARCHAR,
  player_id UINTEGER,
  opponent_team_id UINTEGER,
  was_home BOOLEAN,
  kickoff_time TIMESTAMP,
  round UTINYINT,
  minutes UINTEGER,
  goals_scored UINTEGER,
  assists UINTEGER,
  expected_goals DOUBLE,
  expected_assists DOUBLE,
  expected_goal_involvements DOUBLE,
  starts UINTEGER,
  selected UINTEGER,
  value UINTEGER,
  total_points INTEGER,
  team_h_score UINTEGER,
  team_a_score UINTEGER
) ;

CREATE TABLE IF NOT EXISTS epl_fpl_players_raw (
  season VARCHAR,
  player_id UINTEGER,
  player_code UINTEGER,
  web_name VARCHAR,
  first_name VARCHAR,
  second_name VARCHAR,
  position_id UTINYINT,
  team_id UTINYINT,
  now_cost UINTEGER,
  selected_by_percent DOUBLE,
  total_points INTEGER,
  minutes UINTEGER,
  goals_scored UINTEGER,
  assists UINTEGER,
  expected_goals DOUBLE,
  expected_assists DOUBLE,
  starts UINTEGER
) ;


CREATE TABLE IF NOT EXISTS epl_teams (
  season VARCHAR,
  team_id UTINYINT,
  name VARCHAR,
  short_name VARCHAR,
  strength UTINYINT,
  strength_defence_home USMALLINT,
  strength_defence_away USMALLINT,
  strength_attack_home USMALLINT,
  strength_attack_away USMALLINT
) ;

CREATE TABLE IF NOT EXISTS epl_matches (
  season VARCHAR,
  match_date Date,
  date_string VARCHAR,
  match_time VARCHAR,
  home_team VARCHAR,
  away_team VARCHAR,
  fthg SMALLINT, ftag SMALLINT, ftr VARCHAR,
  hthg SMALLINT, htag SMALLINT, htr VARCHAR,
  referee VARCHAR,
  hs SMALLINT, as_ SMALLINT, hst SMALLINT, ast SMALLINT,
  hc SMALLINT, ac SMALLINT, hy SMALLINT, ay SMALLINT, hr SMALLINT, ar SMALLINT
) ;
INSERT INTO epl_fpl_gameweeks
SELECT
  '2016-17' AS season, COALESCE(TRY_CAST(GW AS UTINYINT),0) AS gw, name, '' AS position, '' AS team, COALESCE(TRY_CAST(element AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(opponent_team AS UINTEGER),0) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, TRY_CAST(TRY_CAST(kickoff_time AS TIMESTAMPTZ) AS TIMESTAMP) AS kickoff_time, COALESCE(TRY_CAST("round" AS UTINYINT),0) AS round, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, CAST(NULL AS DOUBLE) AS expected_goals, CAST(NULL AS DOUBLE) AS expected_assists, CAST(NULL AS DOUBLE) AS expected_goal_involvements, CAST(NULL AS UINTEGER) AS starts, COALESCE(TRY_CAST(selected AS UINTEGER),0) AS selected, COALESCE(TRY_CAST(value AS UINTEGER),0) AS value, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, TRY_CAST(team_h_score AS UINTEGER) AS team_h_score, TRY_CAST(team_a_score AS UINTEGER) AS team_a_score
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2016-17/gws/merged_gw.csv', header=true, all_varchar=true, encoding='latin-1');
INSERT INTO epl_fpl_gameweeks
SELECT
  '2017-18' AS season, COALESCE(TRY_CAST(GW AS UTINYINT),0) AS gw, name, '' AS position, '' AS team, COALESCE(TRY_CAST(element AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(opponent_team AS UINTEGER),0) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, TRY_CAST(TRY_CAST(kickoff_time AS TIMESTAMPTZ) AS TIMESTAMP) AS kickoff_time, COALESCE(TRY_CAST("round" AS UTINYINT),0) AS round, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, CAST(NULL AS DOUBLE) AS expected_goals, CAST(NULL AS DOUBLE) AS expected_assists, CAST(NULL AS DOUBLE) AS expected_goal_involvements, CAST(NULL AS UINTEGER) AS starts, COALESCE(TRY_CAST(selected AS UINTEGER),0) AS selected, COALESCE(TRY_CAST(value AS UINTEGER),0) AS value, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, TRY_CAST(team_h_score AS UINTEGER) AS team_h_score, TRY_CAST(team_a_score AS UINTEGER) AS team_a_score
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2017-18/gws/merged_gw.csv', header=true, all_varchar=true, encoding='latin-1');
INSERT INTO epl_fpl_gameweeks
SELECT
  '2018-19' AS season, COALESCE(TRY_CAST(GW AS UTINYINT),0) AS gw, name, '' AS position, '' AS team, COALESCE(TRY_CAST(element AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(opponent_team AS UINTEGER),0) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, TRY_CAST(TRY_CAST(kickoff_time AS TIMESTAMPTZ) AS TIMESTAMP) AS kickoff_time, COALESCE(TRY_CAST("round" AS UTINYINT),0) AS round, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, CAST(NULL AS DOUBLE) AS expected_goals, CAST(NULL AS DOUBLE) AS expected_assists, CAST(NULL AS DOUBLE) AS expected_goal_involvements, CAST(NULL AS UINTEGER) AS starts, COALESCE(TRY_CAST(selected AS UINTEGER),0) AS selected, COALESCE(TRY_CAST(value AS UINTEGER),0) AS value, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, TRY_CAST(team_h_score AS UINTEGER) AS team_h_score, TRY_CAST(team_a_score AS UINTEGER) AS team_a_score
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2018-19/gws/merged_gw.csv', header=true, all_varchar=true, encoding='latin-1');
INSERT INTO epl_fpl_gameweeks
SELECT
  '2019-20' AS season, COALESCE(TRY_CAST(GW AS UTINYINT),0) AS gw, name, '' AS position, '' AS team, COALESCE(TRY_CAST(element AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(opponent_team AS UINTEGER),0) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, TRY_CAST(TRY_CAST(kickoff_time AS TIMESTAMPTZ) AS TIMESTAMP) AS kickoff_time, COALESCE(TRY_CAST("round" AS UTINYINT),0) AS round, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, CAST(NULL AS DOUBLE) AS expected_goals, CAST(NULL AS DOUBLE) AS expected_assists, CAST(NULL AS DOUBLE) AS expected_goal_involvements, CAST(NULL AS UINTEGER) AS starts, COALESCE(TRY_CAST(selected AS UINTEGER),0) AS selected, COALESCE(TRY_CAST(value AS UINTEGER),0) AS value, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, TRY_CAST(team_h_score AS UINTEGER) AS team_h_score, TRY_CAST(team_a_score AS UINTEGER) AS team_a_score
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2019-20/gws/merged_gw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_gameweeks
SELECT
  '2020-21' AS season, COALESCE(TRY_CAST(GW AS UTINYINT),0) AS gw, name, position, team, COALESCE(TRY_CAST(element AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(opponent_team AS UINTEGER),0) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, TRY_CAST(TRY_CAST(kickoff_time AS TIMESTAMPTZ) AS TIMESTAMP) AS kickoff_time, COALESCE(TRY_CAST("round" AS UTINYINT),0) AS round, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, CAST(NULL AS DOUBLE) AS expected_goals, CAST(NULL AS DOUBLE) AS expected_assists, CAST(NULL AS DOUBLE) AS expected_goal_involvements, CAST(NULL AS UINTEGER) AS starts, COALESCE(TRY_CAST(selected AS UINTEGER),0) AS selected, COALESCE(TRY_CAST(value AS UINTEGER),0) AS value, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, TRY_CAST(team_h_score AS UINTEGER) AS team_h_score, TRY_CAST(team_a_score AS UINTEGER) AS team_a_score
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2020-21/gws/merged_gw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_gameweeks
SELECT
  '2021-22' AS season, COALESCE(TRY_CAST(GW AS UTINYINT),0) AS gw, name, position, team, COALESCE(TRY_CAST(element AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(opponent_team AS UINTEGER),0) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, TRY_CAST(TRY_CAST(kickoff_time AS TIMESTAMPTZ) AS TIMESTAMP) AS kickoff_time, COALESCE(TRY_CAST("round" AS UTINYINT),0) AS round, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, CAST(NULL AS DOUBLE) AS expected_goals, CAST(NULL AS DOUBLE) AS expected_assists, CAST(NULL AS DOUBLE) AS expected_goal_involvements, CAST(NULL AS UINTEGER) AS starts, COALESCE(TRY_CAST(selected AS UINTEGER),0) AS selected, COALESCE(TRY_CAST(value AS UINTEGER),0) AS value, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, TRY_CAST(team_h_score AS UINTEGER) AS team_h_score, TRY_CAST(team_a_score AS UINTEGER) AS team_a_score
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2021-22/gws/merged_gw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_gameweeks
SELECT
  '2022-23' AS season, COALESCE(TRY_CAST(GW AS UTINYINT),0) AS gw, name, position, team, COALESCE(TRY_CAST(element AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(opponent_team AS UINTEGER),0) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, TRY_CAST(TRY_CAST(kickoff_time AS TIMESTAMPTZ) AS TIMESTAMP) AS kickoff_time, COALESCE(TRY_CAST("round" AS UTINYINT),0) AS round, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, TRY_CAST(expected_goals AS DOUBLE) AS expected_goals, TRY_CAST(expected_assists AS DOUBLE) AS expected_assists, TRY_CAST(expected_goal_involvements AS DOUBLE) AS expected_goal_involvements, TRY_CAST(starts AS UINTEGER) AS starts, COALESCE(TRY_CAST(selected AS UINTEGER),0) AS selected, COALESCE(TRY_CAST(value AS UINTEGER),0) AS value, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, TRY_CAST(team_h_score AS UINTEGER) AS team_h_score, TRY_CAST(team_a_score AS UINTEGER) AS team_a_score
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2022-23/gws/merged_gw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_gameweeks
SELECT
  '2023-24' AS season, COALESCE(TRY_CAST(GW AS UTINYINT),0) AS gw, name, position, team, COALESCE(TRY_CAST(element AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(opponent_team AS UINTEGER),0) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, TRY_CAST(TRY_CAST(kickoff_time AS TIMESTAMPTZ) AS TIMESTAMP) AS kickoff_time, COALESCE(TRY_CAST("round" AS UTINYINT),0) AS round, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, TRY_CAST(expected_goals AS DOUBLE) AS expected_goals, TRY_CAST(expected_assists AS DOUBLE) AS expected_assists, TRY_CAST(expected_goal_involvements AS DOUBLE) AS expected_goal_involvements, TRY_CAST(starts AS UINTEGER) AS starts, COALESCE(TRY_CAST(selected AS UINTEGER),0) AS selected, COALESCE(TRY_CAST(value AS UINTEGER),0) AS value, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, TRY_CAST(team_h_score AS UINTEGER) AS team_h_score, TRY_CAST(team_a_score AS UINTEGER) AS team_a_score
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2023-24/gws/merged_gw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_gameweeks
SELECT
  '2024-25' AS season, COALESCE(TRY_CAST(GW AS UTINYINT),0) AS gw, name, position, team, COALESCE(TRY_CAST(element AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(opponent_team AS UINTEGER),0) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, TRY_CAST(TRY_CAST(kickoff_time AS TIMESTAMPTZ) AS TIMESTAMP) AS kickoff_time, COALESCE(TRY_CAST("round" AS UTINYINT),0) AS round, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, TRY_CAST(expected_goals AS DOUBLE) AS expected_goals, TRY_CAST(expected_assists AS DOUBLE) AS expected_assists, TRY_CAST(expected_goal_involvements AS DOUBLE) AS expected_goal_involvements, TRY_CAST(starts AS UINTEGER) AS starts, COALESCE(TRY_CAST(selected AS UINTEGER),0) AS selected, COALESCE(TRY_CAST(value AS UINTEGER),0) AS value, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, TRY_CAST(team_h_score AS UINTEGER) AS team_h_score, TRY_CAST(team_a_score AS UINTEGER) AS team_a_score
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2024-25/gws/merged_gw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_gameweeks
SELECT
  '2025-26' AS season, COALESCE(TRY_CAST(GW AS UTINYINT),0) AS gw, name, position, team, COALESCE(TRY_CAST(element AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(opponent_team AS UINTEGER),0) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, TRY_CAST(TRY_CAST(kickoff_time AS TIMESTAMPTZ) AS TIMESTAMP) AS kickoff_time, COALESCE(TRY_CAST("round" AS UTINYINT),0) AS round, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, TRY_CAST(expected_goals AS DOUBLE) AS expected_goals, TRY_CAST(expected_assists AS DOUBLE) AS expected_assists, TRY_CAST(expected_goal_involvements AS DOUBLE) AS expected_goal_involvements, TRY_CAST(starts AS UINTEGER) AS starts, COALESCE(TRY_CAST(selected AS UINTEGER),0) AS selected, COALESCE(TRY_CAST(value AS UINTEGER),0) AS value, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, TRY_CAST(team_h_score AS UINTEGER) AS team_h_score, TRY_CAST(team_a_score AS UINTEGER) AS team_a_score
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2025-26/gws/merged_gw.csv', header=true, all_varchar=true);

-- 2026-27 (current season, refreshes weekly)
INSERT INTO epl_fpl_gameweeks
SELECT
  '2026-27' AS season, COALESCE(TRY_CAST(GW AS UTINYINT),0) AS gw, name, position, team, COALESCE(TRY_CAST(element AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(opponent_team AS UINTEGER),0) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, TRY_CAST(TRY_CAST(kickoff_time AS TIMESTAMPTZ) AS TIMESTAMP) AS kickoff_time, COALESCE(TRY_CAST("round" AS UTINYINT),0) AS round, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, TRY_CAST(expected_goals AS DOUBLE) AS expected_goals, TRY_CAST(expected_assists AS DOUBLE) AS expected_assists, TRY_CAST(expected_goal_involvements AS DOUBLE) AS expected_goal_involvements, TRY_CAST(starts AS UINTEGER) AS starts, COALESCE(TRY_CAST(selected AS UINTEGER),0) AS selected, COALESCE(TRY_CAST(value AS UINTEGER),0) AS value, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, TRY_CAST(team_h_score AS UINTEGER) AS team_h_score, TRY_CAST(team_a_score AS UINTEGER) AS team_a_score
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2026-27/gws/merged_gw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_players_raw
SELECT
  '2016-17' AS season, COALESCE(TRY_CAST(id AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(code AS UINTEGER),0) AS player_code, web_name, first_name, second_name, COALESCE(TRY_CAST(element_type AS UTINYINT),0) AS position_id, COALESCE(TRY_CAST(team AS UTINYINT),0) AS team_id, COALESCE(TRY_CAST(now_cost AS UINTEGER),0) AS now_cost, COALESCE(TRY_CAST(selected_by_percent AS DOUBLE),0) AS selected_by_percent, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, CAST(NULL AS DOUBLE) AS expected_goals, CAST(NULL AS DOUBLE) AS expected_assists, CAST(NULL AS UINTEGER) AS starts
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2016-17/players_raw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_players_raw
SELECT
  '2017-18' AS season, COALESCE(TRY_CAST(id AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(code AS UINTEGER),0) AS player_code, web_name, first_name, second_name, COALESCE(TRY_CAST(element_type AS UTINYINT),0) AS position_id, COALESCE(TRY_CAST(team AS UTINYINT),0) AS team_id, COALESCE(TRY_CAST(now_cost AS UINTEGER),0) AS now_cost, COALESCE(TRY_CAST(selected_by_percent AS DOUBLE),0) AS selected_by_percent, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, CAST(NULL AS DOUBLE) AS expected_goals, CAST(NULL AS DOUBLE) AS expected_assists, CAST(NULL AS UINTEGER) AS starts
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2017-18/players_raw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_players_raw
SELECT
  '2018-19' AS season, COALESCE(TRY_CAST(id AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(code AS UINTEGER),0) AS player_code, web_name, first_name, second_name, COALESCE(TRY_CAST(element_type AS UTINYINT),0) AS position_id, COALESCE(TRY_CAST(team AS UTINYINT),0) AS team_id, COALESCE(TRY_CAST(now_cost AS UINTEGER),0) AS now_cost, COALESCE(TRY_CAST(selected_by_percent AS DOUBLE),0) AS selected_by_percent, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, CAST(NULL AS DOUBLE) AS expected_goals, CAST(NULL AS DOUBLE) AS expected_assists, CAST(NULL AS UINTEGER) AS starts
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2018-19/players_raw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_players_raw
SELECT
  '2019-20' AS season, COALESCE(TRY_CAST(id AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(code AS UINTEGER),0) AS player_code, web_name, first_name, second_name, COALESCE(TRY_CAST(element_type AS UTINYINT),0) AS position_id, COALESCE(TRY_CAST(team AS UTINYINT),0) AS team_id, COALESCE(TRY_CAST(now_cost AS UINTEGER),0) AS now_cost, COALESCE(TRY_CAST(selected_by_percent AS DOUBLE),0) AS selected_by_percent, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, CAST(NULL AS DOUBLE) AS expected_goals, CAST(NULL AS DOUBLE) AS expected_assists, CAST(NULL AS UINTEGER) AS starts
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2019-20/players_raw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_players_raw
SELECT
  '2020-21' AS season, COALESCE(TRY_CAST(id AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(code AS UINTEGER),0) AS player_code, web_name, first_name, second_name, COALESCE(TRY_CAST(element_type AS UTINYINT),0) AS position_id, COALESCE(TRY_CAST(team AS UTINYINT),0) AS team_id, COALESCE(TRY_CAST(now_cost AS UINTEGER),0) AS now_cost, COALESCE(TRY_CAST(selected_by_percent AS DOUBLE),0) AS selected_by_percent, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, CAST(NULL AS DOUBLE) AS expected_goals, CAST(NULL AS DOUBLE) AS expected_assists, CAST(NULL AS UINTEGER) AS starts
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2020-21/players_raw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_players_raw
SELECT
  '2021-22' AS season, COALESCE(TRY_CAST(id AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(code AS UINTEGER),0) AS player_code, web_name, first_name, second_name, COALESCE(TRY_CAST(element_type AS UTINYINT),0) AS position_id, COALESCE(TRY_CAST(team AS UTINYINT),0) AS team_id, COALESCE(TRY_CAST(now_cost AS UINTEGER),0) AS now_cost, COALESCE(TRY_CAST(selected_by_percent AS DOUBLE),0) AS selected_by_percent, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, CAST(NULL AS DOUBLE) AS expected_goals, CAST(NULL AS DOUBLE) AS expected_assists, CAST(NULL AS UINTEGER) AS starts
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2021-22/players_raw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_players_raw
SELECT
  '2022-23' AS season, COALESCE(TRY_CAST(id AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(code AS UINTEGER),0) AS player_code, web_name, first_name, second_name, COALESCE(TRY_CAST(element_type AS UTINYINT),0) AS position_id, COALESCE(TRY_CAST(team AS UTINYINT),0) AS team_id, COALESCE(TRY_CAST(now_cost AS UINTEGER),0) AS now_cost, COALESCE(TRY_CAST(selected_by_percent AS DOUBLE),0) AS selected_by_percent, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, TRY_CAST(expected_goals AS DOUBLE) AS expected_goals, TRY_CAST(expected_assists AS DOUBLE) AS expected_assists, TRY_CAST(starts AS UINTEGER) AS starts
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2022-23/players_raw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_players_raw
SELECT
  '2023-24' AS season, COALESCE(TRY_CAST(id AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(code AS UINTEGER),0) AS player_code, web_name, first_name, second_name, COALESCE(TRY_CAST(element_type AS UTINYINT),0) AS position_id, COALESCE(TRY_CAST(team AS UTINYINT),0) AS team_id, COALESCE(TRY_CAST(now_cost AS UINTEGER),0) AS now_cost, COALESCE(TRY_CAST(selected_by_percent AS DOUBLE),0) AS selected_by_percent, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, TRY_CAST(expected_goals AS DOUBLE) AS expected_goals, TRY_CAST(expected_assists AS DOUBLE) AS expected_assists, TRY_CAST(starts AS UINTEGER) AS starts
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2023-24/players_raw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_players_raw
SELECT
  '2024-25' AS season, COALESCE(TRY_CAST(id AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(code AS UINTEGER),0) AS player_code, web_name, first_name, second_name, COALESCE(TRY_CAST(element_type AS UTINYINT),0) AS position_id, COALESCE(TRY_CAST(team AS UTINYINT),0) AS team_id, COALESCE(TRY_CAST(now_cost AS UINTEGER),0) AS now_cost, COALESCE(TRY_CAST(selected_by_percent AS DOUBLE),0) AS selected_by_percent, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, TRY_CAST(expected_goals AS DOUBLE) AS expected_goals, TRY_CAST(expected_assists AS DOUBLE) AS expected_assists, TRY_CAST(starts AS UINTEGER) AS starts
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2024-25/players_raw.csv', header=true, all_varchar=true);
INSERT INTO epl_fpl_players_raw
SELECT
  '2025-26' AS season, COALESCE(TRY_CAST(id AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(code AS UINTEGER),0) AS player_code, web_name, first_name, second_name, COALESCE(TRY_CAST(element_type AS UTINYINT),0) AS position_id, COALESCE(TRY_CAST(team AS UTINYINT),0) AS team_id, COALESCE(TRY_CAST(now_cost AS UINTEGER),0) AS now_cost, COALESCE(TRY_CAST(selected_by_percent AS DOUBLE),0) AS selected_by_percent, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, TRY_CAST(expected_goals AS DOUBLE) AS expected_goals, TRY_CAST(expected_assists AS DOUBLE) AS expected_assists, TRY_CAST(starts AS UINTEGER) AS starts
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2025-26/players_raw.csv', header=true, all_varchar=true);

-- 2026-27 (current season, refreshes weekly)
INSERT INTO epl_fpl_players_raw
SELECT
  '2026-27' AS season, COALESCE(TRY_CAST(id AS UINTEGER),0) AS player_id, COALESCE(TRY_CAST(code AS UINTEGER),0) AS player_code, web_name, first_name, second_name, COALESCE(TRY_CAST(element_type AS UTINYINT),0) AS position_id, COALESCE(TRY_CAST(team AS UTINYINT),0) AS team_id, COALESCE(TRY_CAST(now_cost AS UINTEGER),0) AS now_cost, COALESCE(TRY_CAST(selected_by_percent AS DOUBLE),0) AS selected_by_percent, COALESCE(TRY_CAST(total_points AS INTEGER),0) AS total_points, COALESCE(TRY_CAST(minutes AS UINTEGER),0) AS minutes, COALESCE(TRY_CAST(goals_scored AS UINTEGER),0) AS goals_scored, COALESCE(TRY_CAST(assists AS UINTEGER),0) AS assists, TRY_CAST(expected_goals AS DOUBLE) AS expected_goals, TRY_CAST(expected_assists AS DOUBLE) AS expected_assists, TRY_CAST(starts AS UINTEGER) AS starts
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2026-27/players_raw.csv', header=true, all_varchar=true);
INSERT INTO epl_teams
SELECT
  '2019-20' AS season, COALESCE(TRY_CAST(id AS UTINYINT),0) AS team_id, name, short_name, COALESCE(TRY_CAST(strength AS UTINYINT),0) AS strength,
  COALESCE(TRY_CAST(strength_defence_home AS USMALLINT),0) AS strength_defence_home, COALESCE(TRY_CAST(strength_defence_away AS USMALLINT),0) AS strength_defence_away,
  COALESCE(TRY_CAST(strength_attack_home AS USMALLINT),0) AS strength_attack_home, COALESCE(TRY_CAST(strength_attack_away AS USMALLINT),0) AS strength_attack_away
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2019-20/teams.csv', header=true, all_varchar=true);
INSERT INTO epl_teams
SELECT
  '2020-21' AS season, COALESCE(TRY_CAST(id AS UTINYINT),0) AS team_id, name, short_name, COALESCE(TRY_CAST(strength AS UTINYINT),0) AS strength,
  COALESCE(TRY_CAST(strength_defence_home AS USMALLINT),0) AS strength_defence_home, COALESCE(TRY_CAST(strength_defence_away AS USMALLINT),0) AS strength_defence_away,
  COALESCE(TRY_CAST(strength_attack_home AS USMALLINT),0) AS strength_attack_home, COALESCE(TRY_CAST(strength_attack_away AS USMALLINT),0) AS strength_attack_away
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2020-21/teams.csv', header=true, all_varchar=true);
INSERT INTO epl_teams
SELECT
  '2021-22' AS season, COALESCE(TRY_CAST(id AS UTINYINT),0) AS team_id, name, short_name, COALESCE(TRY_CAST(strength AS UTINYINT),0) AS strength,
  COALESCE(TRY_CAST(strength_defence_home AS USMALLINT),0) AS strength_defence_home, COALESCE(TRY_CAST(strength_defence_away AS USMALLINT),0) AS strength_defence_away,
  COALESCE(TRY_CAST(strength_attack_home AS USMALLINT),0) AS strength_attack_home, COALESCE(TRY_CAST(strength_attack_away AS USMALLINT),0) AS strength_attack_away
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2021-22/teams.csv', header=true, all_varchar=true);
INSERT INTO epl_teams
SELECT
  '2022-23' AS season, COALESCE(TRY_CAST(id AS UTINYINT),0) AS team_id, name, short_name, COALESCE(TRY_CAST(strength AS UTINYINT),0) AS strength,
  COALESCE(TRY_CAST(strength_defence_home AS USMALLINT),0) AS strength_defence_home, COALESCE(TRY_CAST(strength_defence_away AS USMALLINT),0) AS strength_defence_away,
  COALESCE(TRY_CAST(strength_attack_home AS USMALLINT),0) AS strength_attack_home, COALESCE(TRY_CAST(strength_attack_away AS USMALLINT),0) AS strength_attack_away
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2022-23/teams.csv', header=true, all_varchar=true);
INSERT INTO epl_teams
SELECT
  '2023-24' AS season, COALESCE(TRY_CAST(id AS UTINYINT),0) AS team_id, name, short_name, COALESCE(TRY_CAST(strength AS UTINYINT),0) AS strength,
  COALESCE(TRY_CAST(strength_defence_home AS USMALLINT),0) AS strength_defence_home, COALESCE(TRY_CAST(strength_defence_away AS USMALLINT),0) AS strength_defence_away,
  COALESCE(TRY_CAST(strength_attack_home AS USMALLINT),0) AS strength_attack_home, COALESCE(TRY_CAST(strength_attack_away AS USMALLINT),0) AS strength_attack_away
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2023-24/teams.csv', header=true, all_varchar=true);
INSERT INTO epl_teams
SELECT
  '2024-25' AS season, COALESCE(TRY_CAST(id AS UTINYINT),0) AS team_id, name, short_name, COALESCE(TRY_CAST(strength AS UTINYINT),0) AS strength,
  COALESCE(TRY_CAST(strength_defence_home AS USMALLINT),0) AS strength_defence_home, COALESCE(TRY_CAST(strength_defence_away AS USMALLINT),0) AS strength_defence_away,
  COALESCE(TRY_CAST(strength_attack_home AS USMALLINT),0) AS strength_attack_home, COALESCE(TRY_CAST(strength_attack_away AS USMALLINT),0) AS strength_attack_away
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2024-25/teams.csv', header=true, all_varchar=true);
INSERT INTO epl_teams
SELECT
  '2025-26' AS season, COALESCE(TRY_CAST(id AS UTINYINT),0) AS team_id, name, short_name, COALESCE(TRY_CAST(strength AS UTINYINT),0) AS strength,
  COALESCE(TRY_CAST(strength_defence_home AS USMALLINT),0) AS strength_defence_home, COALESCE(TRY_CAST(strength_defence_away AS USMALLINT),0) AS strength_defence_away,
  COALESCE(TRY_CAST(strength_attack_home AS USMALLINT),0) AS strength_attack_home, COALESCE(TRY_CAST(strength_attack_away AS USMALLINT),0) AS strength_attack_away
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2025-26/teams.csv', header=true, all_varchar=true);

-- 2026-27 (current season, refreshes weekly)
INSERT INTO epl_teams
SELECT
  '2026-27' AS season, COALESCE(TRY_CAST(id AS UTINYINT),0) AS team_id, name, short_name, COALESCE(TRY_CAST(strength AS UTINYINT),0) AS strength,
  COALESCE(TRY_CAST(strength_defence_home AS USMALLINT),0) AS strength_defence_home, COALESCE(TRY_CAST(strength_defence_away AS USMALLINT),0) AS strength_defence_away,
  COALESCE(TRY_CAST(strength_attack_home AS USMALLINT),0) AS strength_attack_home, COALESCE(TRY_CAST(strength_attack_away AS USMALLINT),0) AS strength_attack_away
FROM read_csv('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2026-27/teams.csv', header=true, all_varchar=true);
INSERT INTO epl_matches
SELECT
  '2016-17' AS season, COALESCE(TRY_CAST(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)) AS DATE), DATE '1970-01-01') AS match_date, Date AS date_string, '' AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, TRY_CAST(FTHG AS SMALLINT) AS fthg, TRY_CAST(FTAG AS SMALLINT) AS ftag, FTR AS ftr, TRY_CAST(HTHG AS SMALLINT) AS hthg, TRY_CAST(HTAG AS SMALLINT) AS htag, HTR AS htr, Referee AS referee, TRY_CAST("HS" AS SMALLINT) AS hs, TRY_CAST("AS" AS SMALLINT) AS as_, TRY_CAST("HST" AS SMALLINT) AS hst, TRY_CAST("AST" AS SMALLINT) AS ast, TRY_CAST("HC" AS SMALLINT) AS hc, TRY_CAST("AC" AS SMALLINT) AS ac, TRY_CAST("HY" AS SMALLINT) AS hy, TRY_CAST("AY" AS SMALLINT) AS ay, TRY_CAST("HR" AS SMALLINT) AS hr, TRY_CAST("AR" AS SMALLINT) AS ar
FROM read_csv('https://www.football-data.co.uk/mmz4281/1617/E0.csv', header=true, all_varchar=true);
INSERT INTO epl_matches
SELECT
  '2017-18' AS season, COALESCE(TRY_CAST(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)) AS DATE), DATE '1970-01-01') AS match_date, Date AS date_string, '' AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, TRY_CAST(FTHG AS SMALLINT) AS fthg, TRY_CAST(FTAG AS SMALLINT) AS ftag, FTR AS ftr, TRY_CAST(HTHG AS SMALLINT) AS hthg, TRY_CAST(HTAG AS SMALLINT) AS htag, HTR AS htr, Referee AS referee, TRY_CAST("HS" AS SMALLINT) AS hs, TRY_CAST("AS" AS SMALLINT) AS as_, TRY_CAST("HST" AS SMALLINT) AS hst, TRY_CAST("AST" AS SMALLINT) AS ast, TRY_CAST("HC" AS SMALLINT) AS hc, TRY_CAST("AC" AS SMALLINT) AS ac, TRY_CAST("HY" AS SMALLINT) AS hy, TRY_CAST("AY" AS SMALLINT) AS ay, TRY_CAST("HR" AS SMALLINT) AS hr, TRY_CAST("AR" AS SMALLINT) AS ar
FROM read_csv('https://www.football-data.co.uk/mmz4281/1718/E0.csv', header=true, all_varchar=true);
INSERT INTO epl_matches
SELECT
  '2018-19' AS season, COALESCE(TRY_CAST(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)) AS DATE), DATE '1970-01-01') AS match_date, Date AS date_string, '' AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, TRY_CAST(FTHG AS SMALLINT) AS fthg, TRY_CAST(FTAG AS SMALLINT) AS ftag, FTR AS ftr, TRY_CAST(HTHG AS SMALLINT) AS hthg, TRY_CAST(HTAG AS SMALLINT) AS htag, HTR AS htr, Referee AS referee, TRY_CAST("HS" AS SMALLINT) AS hs, TRY_CAST("AS" AS SMALLINT) AS as_, TRY_CAST("HST" AS SMALLINT) AS hst, TRY_CAST("AST" AS SMALLINT) AS ast, TRY_CAST("HC" AS SMALLINT) AS hc, TRY_CAST("AC" AS SMALLINT) AS ac, TRY_CAST("HY" AS SMALLINT) AS hy, TRY_CAST("AY" AS SMALLINT) AS ay, TRY_CAST("HR" AS SMALLINT) AS hr, TRY_CAST("AR" AS SMALLINT) AS ar
FROM read_csv('https://www.football-data.co.uk/mmz4281/1819/E0.csv', header=true, all_varchar=true);
INSERT INTO epl_matches
SELECT
  '2019-20' AS season, COALESCE(TRY_CAST(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)) AS DATE), DATE '1970-01-01') AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, TRY_CAST(FTHG AS SMALLINT) AS fthg, TRY_CAST(FTAG AS SMALLINT) AS ftag, FTR AS ftr, TRY_CAST(HTHG AS SMALLINT) AS hthg, TRY_CAST(HTAG AS SMALLINT) AS htag, HTR AS htr, Referee AS referee, TRY_CAST("HS" AS SMALLINT) AS hs, TRY_CAST("AS" AS SMALLINT) AS as_, TRY_CAST("HST" AS SMALLINT) AS hst, TRY_CAST("AST" AS SMALLINT) AS ast, TRY_CAST("HC" AS SMALLINT) AS hc, TRY_CAST("AC" AS SMALLINT) AS ac, TRY_CAST("HY" AS SMALLINT) AS hy, TRY_CAST("AY" AS SMALLINT) AS ay, TRY_CAST("HR" AS SMALLINT) AS hr, TRY_CAST("AR" AS SMALLINT) AS ar
FROM read_csv('https://www.football-data.co.uk/mmz4281/1920/E0.csv', header=true, all_varchar=true);
INSERT INTO epl_matches
SELECT
  '2020-21' AS season, COALESCE(TRY_CAST(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)) AS DATE), DATE '1970-01-01') AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, TRY_CAST(FTHG AS SMALLINT) AS fthg, TRY_CAST(FTAG AS SMALLINT) AS ftag, FTR AS ftr, TRY_CAST(HTHG AS SMALLINT) AS hthg, TRY_CAST(HTAG AS SMALLINT) AS htag, HTR AS htr, Referee AS referee, TRY_CAST("HS" AS SMALLINT) AS hs, TRY_CAST("AS" AS SMALLINT) AS as_, TRY_CAST("HST" AS SMALLINT) AS hst, TRY_CAST("AST" AS SMALLINT) AS ast, TRY_CAST("HC" AS SMALLINT) AS hc, TRY_CAST("AC" AS SMALLINT) AS ac, TRY_CAST("HY" AS SMALLINT) AS hy, TRY_CAST("AY" AS SMALLINT) AS ay, TRY_CAST("HR" AS SMALLINT) AS hr, TRY_CAST("AR" AS SMALLINT) AS ar
FROM read_csv('https://www.football-data.co.uk/mmz4281/2021/E0.csv', header=true, all_varchar=true);
INSERT INTO epl_matches
SELECT
  '2021-22' AS season, COALESCE(TRY_CAST(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)) AS DATE), DATE '1970-01-01') AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, TRY_CAST(FTHG AS SMALLINT) AS fthg, TRY_CAST(FTAG AS SMALLINT) AS ftag, FTR AS ftr, TRY_CAST(HTHG AS SMALLINT) AS hthg, TRY_CAST(HTAG AS SMALLINT) AS htag, HTR AS htr, Referee AS referee, TRY_CAST("HS" AS SMALLINT) AS hs, TRY_CAST("AS" AS SMALLINT) AS as_, TRY_CAST("HST" AS SMALLINT) AS hst, TRY_CAST("AST" AS SMALLINT) AS ast, TRY_CAST("HC" AS SMALLINT) AS hc, TRY_CAST("AC" AS SMALLINT) AS ac, TRY_CAST("HY" AS SMALLINT) AS hy, TRY_CAST("AY" AS SMALLINT) AS ay, TRY_CAST("HR" AS SMALLINT) AS hr, TRY_CAST("AR" AS SMALLINT) AS ar
FROM read_csv('https://www.football-data.co.uk/mmz4281/2122/E0.csv', header=true, all_varchar=true);
INSERT INTO epl_matches
SELECT
  '2022-23' AS season, COALESCE(TRY_CAST(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)) AS DATE), DATE '1970-01-01') AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, TRY_CAST(FTHG AS SMALLINT) AS fthg, TRY_CAST(FTAG AS SMALLINT) AS ftag, FTR AS ftr, TRY_CAST(HTHG AS SMALLINT) AS hthg, TRY_CAST(HTAG AS SMALLINT) AS htag, HTR AS htr, Referee AS referee, TRY_CAST("HS" AS SMALLINT) AS hs, TRY_CAST("AS" AS SMALLINT) AS as_, TRY_CAST("HST" AS SMALLINT) AS hst, TRY_CAST("AST" AS SMALLINT) AS ast, TRY_CAST("HC" AS SMALLINT) AS hc, TRY_CAST("AC" AS SMALLINT) AS ac, TRY_CAST("HY" AS SMALLINT) AS hy, TRY_CAST("AY" AS SMALLINT) AS ay, TRY_CAST("HR" AS SMALLINT) AS hr, TRY_CAST("AR" AS SMALLINT) AS ar
FROM read_csv('https://www.football-data.co.uk/mmz4281/2223/E0.csv', header=true, all_varchar=true);
INSERT INTO epl_matches
SELECT
  '2023-24' AS season, COALESCE(TRY_CAST(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)) AS DATE), DATE '1970-01-01') AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, TRY_CAST(FTHG AS SMALLINT) AS fthg, TRY_CAST(FTAG AS SMALLINT) AS ftag, FTR AS ftr, TRY_CAST(HTHG AS SMALLINT) AS hthg, TRY_CAST(HTAG AS SMALLINT) AS htag, HTR AS htr, Referee AS referee, TRY_CAST("HS" AS SMALLINT) AS hs, TRY_CAST("AS" AS SMALLINT) AS as_, TRY_CAST("HST" AS SMALLINT) AS hst, TRY_CAST("AST" AS SMALLINT) AS ast, TRY_CAST("HC" AS SMALLINT) AS hc, TRY_CAST("AC" AS SMALLINT) AS ac, TRY_CAST("HY" AS SMALLINT) AS hy, TRY_CAST("AY" AS SMALLINT) AS ay, TRY_CAST("HR" AS SMALLINT) AS hr, TRY_CAST("AR" AS SMALLINT) AS ar
FROM read_csv('https://www.football-data.co.uk/mmz4281/2324/E0.csv', header=true, all_varchar=true);
INSERT INTO epl_matches
SELECT
  '2024-25' AS season, COALESCE(TRY_CAST(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)) AS DATE), DATE '1970-01-01') AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, TRY_CAST(FTHG AS SMALLINT) AS fthg, TRY_CAST(FTAG AS SMALLINT) AS ftag, FTR AS ftr, TRY_CAST(HTHG AS SMALLINT) AS hthg, TRY_CAST(HTAG AS SMALLINT) AS htag, HTR AS htr, Referee AS referee, TRY_CAST("HS" AS SMALLINT) AS hs, TRY_CAST("AS" AS SMALLINT) AS as_, TRY_CAST("HST" AS SMALLINT) AS hst, TRY_CAST("AST" AS SMALLINT) AS ast, TRY_CAST("HC" AS SMALLINT) AS hc, TRY_CAST("AC" AS SMALLINT) AS ac, TRY_CAST("HY" AS SMALLINT) AS hy, TRY_CAST("AY" AS SMALLINT) AS ay, TRY_CAST("HR" AS SMALLINT) AS hr, TRY_CAST("AR" AS SMALLINT) AS ar
FROM read_csv('https://www.football-data.co.uk/mmz4281/2425/E0.csv', header=true, all_varchar=true);
INSERT INTO epl_matches
SELECT
  '2025-26' AS season, COALESCE(TRY_CAST(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)) AS DATE), DATE '1970-01-01') AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, TRY_CAST(FTHG AS SMALLINT) AS fthg, TRY_CAST(FTAG AS SMALLINT) AS ftag, FTR AS ftr, TRY_CAST(HTHG AS SMALLINT) AS hthg, TRY_CAST(HTAG AS SMALLINT) AS htag, HTR AS htr, Referee AS referee, TRY_CAST("HS" AS SMALLINT) AS hs, TRY_CAST("AS" AS SMALLINT) AS as_, TRY_CAST("HST" AS SMALLINT) AS hst, TRY_CAST("AST" AS SMALLINT) AS ast, TRY_CAST("HC" AS SMALLINT) AS hc, TRY_CAST("AC" AS SMALLINT) AS ac, TRY_CAST("HY" AS SMALLINT) AS hy, TRY_CAST("AY" AS SMALLINT) AS ay, TRY_CAST("HR" AS SMALLINT) AS hr, TRY_CAST("AR" AS SMALLINT) AS ar
FROM read_csv('https://www.football-data.co.uk/mmz4281/2526/E0.csv', header=true, all_varchar=true);

-- 2026-27 (current season, refreshes weekly)
INSERT INTO epl_matches
SELECT
  '2026-27' AS season, COALESCE(TRY_CAST(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)) AS DATE), DATE '1970-01-01') AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, TRY_CAST(FTHG AS SMALLINT) AS fthg, TRY_CAST(FTAG AS SMALLINT) AS ftag, FTR AS ftr, TRY_CAST(HTHG AS SMALLINT) AS hthg, TRY_CAST(HTAG AS SMALLINT) AS htag, HTR AS htr, Referee AS referee, TRY_CAST("HS" AS SMALLINT) AS hs, TRY_CAST("AS" AS SMALLINT) AS as_, TRY_CAST("HST" AS SMALLINT) AS hst, TRY_CAST("AST" AS SMALLINT) AS ast, TRY_CAST("HC" AS SMALLINT) AS hc, TRY_CAST("AC" AS SMALLINT) AS ac, TRY_CAST("HY" AS SMALLINT) AS hy, TRY_CAST("AY" AS SMALLINT) AS ay, TRY_CAST("HR" AS SMALLINT) AS hr, TRY_CAST("AR" AS SMALLINT) AS ar
FROM read_csv('https://www.football-data.co.uk/mmz4281/2627/E0.csv', header=true, all_varchar=true);
-- Season-aggregate player table (backtest-ready: one row per player per season)
CREATE TABLE IF NOT EXISTS epl_player_season AS
SELECT
  g.season,
  g.player_id,
  max(r.player_code) AS player_code,
  any_value(g.name) AS name,
  any_value(g.position) AS position,
  arg_max(g.team, g.round) AS team,
  sum(g.minutes) AS minutes,
  sum(g.starts) AS starts,
  sum(g.goals_scored) AS goals,
  sum(g.assists) AS assists,
  sum(g.expected_goals) AS xg,
  sum(g.expected_assists) AS xa,
  sum(g.total_points) AS fpl_points_from_gws,
  max(r.now_cost) AS fpl_price_x10,
  max(r.selected_by_percent) AS fpl_selected_by_percent,
  max(r.total_points) AS fpl_total_points
FROM epl_fpl_gameweeks g
LEFT JOIN epl_fpl_players_raw r ON r.season = g.season AND r.player_id = g.player_id
GROUP BY g.season, g.player_id
ORDER BY g.season, fpl_points_from_gws DESC;

-- Sanity checks
SELECT 'epl_fpl_gameweeks' AS t, count(*) FROM epl_fpl_gameweeks
UNION ALL SELECT 'epl_fpl_players_raw', count(*) FROM epl_fpl_players_raw
UNION ALL SELECT 'epl_matches', count(*) FROM epl_matches
UNION ALL SELECT 'epl_teams', count(*) FROM epl_teams
UNION ALL SELECT 'epl_player_season', count(*) FROM epl_player_season;
SELECT season, count(*) FROM epl_fpl_gameweeks GROUP BY season ORDER BY season;
SELECT season, count(*) FROM epl_matches GROUP BY season ORDER BY season;
