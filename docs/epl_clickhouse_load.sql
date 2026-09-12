-- ClickHouse EPL playground load script
-- Sources: vaastav/Fantasy-Premier-League (GitHub, CC0-style public repo), football-data.co.uk (public match CSVs)
-- Run top to bottom in the ClickHouse Cloud SQL console.

SET max_http_get_redirects = 10;

CREATE TABLE IF NOT EXISTS epl_fpl_gameweeks (
  season LowCardinality(String),
  gw UInt8,
  name String,
  position LowCardinality(String),
  team String,
  player_id UInt32,
  opponent_team_id UInt32,
  was_home Bool,
  kickoff_time Nullable(DateTime),
  round UInt8,
  minutes UInt32,
  goals_scored UInt32,
  assists UInt32,
  expected_goals Nullable(Float64),
  expected_assists Nullable(Float64),
  expected_goal_involvements Nullable(Float64),
  starts Nullable(UInt32),
  selected UInt32,
  value UInt32,
  total_points Int32,
  team_h_score Nullable(UInt32),
  team_a_score Nullable(UInt32)
) ENGINE = MergeTree ORDER BY (season, player_id, gw);

CREATE TABLE IF NOT EXISTS epl_fpl_players_raw (
  season LowCardinality(String),
  player_id UInt32,
  player_code UInt32,
  web_name String,
  first_name String,
  second_name String,
  position_id UInt8,
  team_id UInt8,
  now_cost UInt32,
  selected_by_percent Float64,
  total_points Int32,
  minutes UInt32,
  goals_scored UInt32,
  assists UInt32,
  expected_goals Nullable(Float64),
  expected_assists Nullable(Float64),
  starts Nullable(UInt32)
) ENGINE = MergeTree ORDER BY (season, player_id);


CREATE TABLE IF NOT EXISTS epl_teams (
  season LowCardinality(String),
  team_id UInt8,
  name String,
  short_name FixedString(3),
  strength UInt8,
  strength_defence_home UInt16,
  strength_defence_away UInt16,
  strength_attack_home UInt16,
  strength_attack_away UInt16
) ENGINE = MergeTree ORDER BY (season, team_id);

CREATE TABLE IF NOT EXISTS epl_matches (
  season LowCardinality(String),
  match_date Date,
  date_string String,
  match_time String,
  home_team String,
  away_team String,
  fthg Int16, ftag Int16, ftr FixedString(1),
  hthg Int16, htag Int16, htr FixedString(1),
  referee String,
  hs Int16, as_ Int16, hst Int16, ast Int16,
  hc Int16, ac Int16, hy Int16, ay Int16, hr Int16, ar Int16
) ENGINE = MergeTree ORDER BY (season, match_date);
INSERT INTO epl_fpl_gameweeks
SELECT
  '2016-17' AS season, toUInt8OrZero(GW) AS gw, name, '' AS position, '' AS team, toUInt32OrZero(element) AS player_id, toUInt32OrZero(opponent_team) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, parseDateTimeBestEffortOrNull(kickoff_time) AS kickoff_time, toUInt8OrZero(round) AS round, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, CAST(NULL, 'Nullable(Float64)') AS expected_goals, CAST(NULL, 'Nullable(Float64)') AS expected_assists, CAST(NULL, 'Nullable(Float64)') AS expected_goal_involvements, CAST(NULL, 'Nullable(UInt32)') AS starts, toUInt32OrZero(selected) AS selected, toUInt32OrZero(value) AS value, toInt32OrZero(total_points) AS total_points, toUInt32OrNull(team_h_score) AS team_h_score, toUInt32OrNull(team_a_score) AS team_a_score
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2016-17/gws/merged_gw.csv', CSVWithNames, 'name String, element String, opponent_team String, was_home String, kickoff_time String, round String, minutes String, goals_scored String, assists String, selected String, value String, total_points String, team_h_score String, team_a_score String, GW String');
INSERT INTO epl_fpl_gameweeks
SELECT
  '2017-18' AS season, toUInt8OrZero(GW) AS gw, name, '' AS position, '' AS team, toUInt32OrZero(element) AS player_id, toUInt32OrZero(opponent_team) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, parseDateTimeBestEffortOrNull(kickoff_time) AS kickoff_time, toUInt8OrZero(round) AS round, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, CAST(NULL, 'Nullable(Float64)') AS expected_goals, CAST(NULL, 'Nullable(Float64)') AS expected_assists, CAST(NULL, 'Nullable(Float64)') AS expected_goal_involvements, CAST(NULL, 'Nullable(UInt32)') AS starts, toUInt32OrZero(selected) AS selected, toUInt32OrZero(value) AS value, toInt32OrZero(total_points) AS total_points, toUInt32OrNull(team_h_score) AS team_h_score, toUInt32OrNull(team_a_score) AS team_a_score
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2017-18/gws/merged_gw.csv', CSVWithNames, 'name String, element String, opponent_team String, was_home String, kickoff_time String, round String, minutes String, goals_scored String, assists String, selected String, value String, total_points String, team_h_score String, team_a_score String, GW String');
INSERT INTO epl_fpl_gameweeks
SELECT
  '2018-19' AS season, toUInt8OrZero(GW) AS gw, name, '' AS position, '' AS team, toUInt32OrZero(element) AS player_id, toUInt32OrZero(opponent_team) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, parseDateTimeBestEffortOrNull(kickoff_time) AS kickoff_time, toUInt8OrZero(round) AS round, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, CAST(NULL, 'Nullable(Float64)') AS expected_goals, CAST(NULL, 'Nullable(Float64)') AS expected_assists, CAST(NULL, 'Nullable(Float64)') AS expected_goal_involvements, CAST(NULL, 'Nullable(UInt32)') AS starts, toUInt32OrZero(selected) AS selected, toUInt32OrZero(value) AS value, toInt32OrZero(total_points) AS total_points, toUInt32OrNull(team_h_score) AS team_h_score, toUInt32OrNull(team_a_score) AS team_a_score
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2018-19/gws/merged_gw.csv', CSVWithNames, 'name String, element String, opponent_team String, was_home String, kickoff_time String, round String, minutes String, goals_scored String, assists String, selected String, value String, total_points String, team_h_score String, team_a_score String, GW String');
INSERT INTO epl_fpl_gameweeks
SELECT
  '2019-20' AS season, toUInt8OrZero(GW) AS gw, name, '' AS position, '' AS team, toUInt32OrZero(element) AS player_id, toUInt32OrZero(opponent_team) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, parseDateTimeBestEffortOrNull(kickoff_time) AS kickoff_time, toUInt8OrZero(round) AS round, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, CAST(NULL, 'Nullable(Float64)') AS expected_goals, CAST(NULL, 'Nullable(Float64)') AS expected_assists, CAST(NULL, 'Nullable(Float64)') AS expected_goal_involvements, CAST(NULL, 'Nullable(UInt32)') AS starts, toUInt32OrZero(selected) AS selected, toUInt32OrZero(value) AS value, toInt32OrZero(total_points) AS total_points, toUInt32OrNull(team_h_score) AS team_h_score, toUInt32OrNull(team_a_score) AS team_a_score
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2019-20/gws/merged_gw.csv', CSVWithNames, 'name String, element String, opponent_team String, was_home String, kickoff_time String, round String, minutes String, goals_scored String, assists String, selected String, value String, total_points String, team_h_score String, team_a_score String, GW String');
INSERT INTO epl_fpl_gameweeks
SELECT
  '2020-21' AS season, toUInt8OrZero(GW) AS gw, name, position, team, toUInt32OrZero(element) AS player_id, toUInt32OrZero(opponent_team) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, parseDateTimeBestEffortOrNull(kickoff_time) AS kickoff_time, toUInt8OrZero(round) AS round, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, CAST(NULL, 'Nullable(Float64)') AS expected_goals, CAST(NULL, 'Nullable(Float64)') AS expected_assists, CAST(NULL, 'Nullable(Float64)') AS expected_goal_involvements, CAST(NULL, 'Nullable(UInt32)') AS starts, toUInt32OrZero(selected) AS selected, toUInt32OrZero(value) AS value, toInt32OrZero(total_points) AS total_points, toUInt32OrNull(team_h_score) AS team_h_score, toUInt32OrNull(team_a_score) AS team_a_score
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2020-21/gws/merged_gw.csv', CSVWithNames, 'name String, position String, team String, element String, opponent_team String, was_home String, kickoff_time String, round String, minutes String, goals_scored String, assists String, selected String, value String, total_points String, team_h_score String, team_a_score String, GW String');
INSERT INTO epl_fpl_gameweeks
SELECT
  '2021-22' AS season, toUInt8OrZero(GW) AS gw, name, position, team, toUInt32OrZero(element) AS player_id, toUInt32OrZero(opponent_team) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, parseDateTimeBestEffortOrNull(kickoff_time) AS kickoff_time, toUInt8OrZero(round) AS round, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, CAST(NULL, 'Nullable(Float64)') AS expected_goals, CAST(NULL, 'Nullable(Float64)') AS expected_assists, CAST(NULL, 'Nullable(Float64)') AS expected_goal_involvements, CAST(NULL, 'Nullable(UInt32)') AS starts, toUInt32OrZero(selected) AS selected, toUInt32OrZero(value) AS value, toInt32OrZero(total_points) AS total_points, toUInt32OrNull(team_h_score) AS team_h_score, toUInt32OrNull(team_a_score) AS team_a_score
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2021-22/gws/merged_gw.csv', CSVWithNames, 'name String, position String, team String, element String, opponent_team String, was_home String, kickoff_time String, round String, minutes String, goals_scored String, assists String, selected String, value String, total_points String, team_h_score String, team_a_score String, GW String');
INSERT INTO epl_fpl_gameweeks
SELECT
  '2022-23' AS season, toUInt8OrZero(GW) AS gw, name, position, team, toUInt32OrZero(element) AS player_id, toUInt32OrZero(opponent_team) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, parseDateTimeBestEffortOrNull(kickoff_time) AS kickoff_time, toUInt8OrZero(round) AS round, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, toFloat64OrNull(expected_goals) AS expected_goals, toFloat64OrNull(expected_assists) AS expected_assists, toFloat64OrNull(expected_goal_involvements) AS expected_goal_involvements, toUInt32OrNull(starts) AS starts, toUInt32OrZero(selected) AS selected, toUInt32OrZero(value) AS value, toInt32OrZero(total_points) AS total_points, toUInt32OrNull(team_h_score) AS team_h_score, toUInt32OrNull(team_a_score) AS team_a_score
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2022-23/gws/merged_gw.csv', CSVWithNames, 'name String, position String, team String, element String, opponent_team String, was_home String, kickoff_time String, round String, minutes String, goals_scored String, assists String, expected_goals String, expected_assists String, expected_goal_involvements String, starts String, selected String, value String, total_points String, team_h_score String, team_a_score String, GW String');
INSERT INTO epl_fpl_gameweeks
SELECT
  '2023-24' AS season, toUInt8OrZero(GW) AS gw, name, position, team, toUInt32OrZero(element) AS player_id, toUInt32OrZero(opponent_team) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, parseDateTimeBestEffortOrNull(kickoff_time) AS kickoff_time, toUInt8OrZero(round) AS round, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, toFloat64OrNull(expected_goals) AS expected_goals, toFloat64OrNull(expected_assists) AS expected_assists, toFloat64OrNull(expected_goal_involvements) AS expected_goal_involvements, toUInt32OrNull(starts) AS starts, toUInt32OrZero(selected) AS selected, toUInt32OrZero(value) AS value, toInt32OrZero(total_points) AS total_points, toUInt32OrNull(team_h_score) AS team_h_score, toUInt32OrNull(team_a_score) AS team_a_score
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2023-24/gws/merged_gw.csv', CSVWithNames, 'name String, position String, team String, element String, opponent_team String, was_home String, kickoff_time String, round String, minutes String, goals_scored String, assists String, expected_goals String, expected_assists String, expected_goal_involvements String, starts String, selected String, value String, total_points String, team_h_score String, team_a_score String, GW String');
INSERT INTO epl_fpl_gameweeks
SELECT
  '2024-25' AS season, toUInt8OrZero(GW) AS gw, name, position, team, toUInt32OrZero(element) AS player_id, toUInt32OrZero(opponent_team) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, parseDateTimeBestEffortOrNull(kickoff_time) AS kickoff_time, toUInt8OrZero(round) AS round, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, toFloat64OrNull(expected_goals) AS expected_goals, toFloat64OrNull(expected_assists) AS expected_assists, toFloat64OrNull(expected_goal_involvements) AS expected_goal_involvements, toUInt32OrNull(starts) AS starts, toUInt32OrZero(selected) AS selected, toUInt32OrZero(value) AS value, toInt32OrZero(total_points) AS total_points, toUInt32OrNull(team_h_score) AS team_h_score, toUInt32OrNull(team_a_score) AS team_a_score
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2024-25/gws/merged_gw.csv', CSVWithNames, 'name String, position String, team String, element String, opponent_team String, was_home String, kickoff_time String, round String, minutes String, goals_scored String, assists String, expected_goals String, expected_assists String, expected_goal_involvements String, starts String, selected String, value String, total_points String, team_h_score String, team_a_score String, GW String');
INSERT INTO epl_fpl_gameweeks
SELECT
  '2025-26' AS season, toUInt8OrZero(GW) AS gw, name, position, team, toUInt32OrZero(element) AS player_id, toUInt32OrZero(opponent_team) AS opponent_team_id, was_home IN ('True','true','1') AS was_home, parseDateTimeBestEffortOrNull(kickoff_time) AS kickoff_time, toUInt8OrZero(round) AS round, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, toFloat64OrNull(expected_goals) AS expected_goals, toFloat64OrNull(expected_assists) AS expected_assists, toFloat64OrNull(expected_goal_involvements) AS expected_goal_involvements, toUInt32OrNull(starts) AS starts, toUInt32OrZero(selected) AS selected, toUInt32OrZero(value) AS value, toInt32OrZero(total_points) AS total_points, toUInt32OrNull(team_h_score) AS team_h_score, toUInt32OrNull(team_a_score) AS team_a_score
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2025-26/gws/merged_gw.csv', CSVWithNames, 'name String, position String, team String, element String, opponent_team String, was_home String, kickoff_time String, round String, minutes String, goals_scored String, assists String, expected_goals String, expected_assists String, expected_goal_involvements String, starts String, selected String, value String, total_points String, team_h_score String, team_a_score String, GW String');
INSERT INTO epl_fpl_players_raw
SELECT
  '2016-17' AS season, toUInt32OrZero(id) AS player_id, toUInt32OrZero(code) AS player_code, web_name, first_name, second_name, toUInt8OrZero(element_type) AS position_id, toUInt8OrZero(team) AS team_id, toUInt32OrZero(now_cost) AS now_cost, toFloat64OrZero(selected_by_percent) AS selected_by_percent, toInt32OrZero(total_points) AS total_points, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, CAST(NULL, 'Nullable(Float64)') AS expected_goals, CAST(NULL, 'Nullable(Float64)') AS expected_assists, CAST(NULL, 'Nullable(UInt32)') AS starts
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2016-17/players_raw.csv', CSVWithNames, 'id String, code String, web_name String, first_name String, second_name String, element_type String, team String, now_cost String, selected_by_percent String, total_points String, minutes String, goals_scored String, assists String');
INSERT INTO epl_fpl_players_raw
SELECT
  '2017-18' AS season, toUInt32OrZero(id) AS player_id, toUInt32OrZero(code) AS player_code, web_name, first_name, second_name, toUInt8OrZero(element_type) AS position_id, toUInt8OrZero(team) AS team_id, toUInt32OrZero(now_cost) AS now_cost, toFloat64OrZero(selected_by_percent) AS selected_by_percent, toInt32OrZero(total_points) AS total_points, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, CAST(NULL, 'Nullable(Float64)') AS expected_goals, CAST(NULL, 'Nullable(Float64)') AS expected_assists, CAST(NULL, 'Nullable(UInt32)') AS starts
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2017-18/players_raw.csv', CSVWithNames, 'id String, code String, web_name String, first_name String, second_name String, element_type String, team String, now_cost String, selected_by_percent String, total_points String, minutes String, goals_scored String, assists String');
INSERT INTO epl_fpl_players_raw
SELECT
  '2018-19' AS season, toUInt32OrZero(id) AS player_id, toUInt32OrZero(code) AS player_code, web_name, first_name, second_name, toUInt8OrZero(element_type) AS position_id, toUInt8OrZero(team) AS team_id, toUInt32OrZero(now_cost) AS now_cost, toFloat64OrZero(selected_by_percent) AS selected_by_percent, toInt32OrZero(total_points) AS total_points, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, CAST(NULL, 'Nullable(Float64)') AS expected_goals, CAST(NULL, 'Nullable(Float64)') AS expected_assists, CAST(NULL, 'Nullable(UInt32)') AS starts
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2018-19/players_raw.csv', CSVWithNames, 'id String, code String, web_name String, first_name String, second_name String, element_type String, team String, now_cost String, selected_by_percent String, total_points String, minutes String, goals_scored String, assists String');
INSERT INTO epl_fpl_players_raw
SELECT
  '2019-20' AS season, toUInt32OrZero(id) AS player_id, toUInt32OrZero(code) AS player_code, web_name, first_name, second_name, toUInt8OrZero(element_type) AS position_id, toUInt8OrZero(team) AS team_id, toUInt32OrZero(now_cost) AS now_cost, toFloat64OrZero(selected_by_percent) AS selected_by_percent, toInt32OrZero(total_points) AS total_points, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, CAST(NULL, 'Nullable(Float64)') AS expected_goals, CAST(NULL, 'Nullable(Float64)') AS expected_assists, CAST(NULL, 'Nullable(UInt32)') AS starts
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2019-20/players_raw.csv', CSVWithNames, 'id String, code String, web_name String, first_name String, second_name String, element_type String, team String, now_cost String, selected_by_percent String, total_points String, minutes String, goals_scored String, assists String');
INSERT INTO epl_fpl_players_raw
SELECT
  '2020-21' AS season, toUInt32OrZero(id) AS player_id, toUInt32OrZero(code) AS player_code, web_name, first_name, second_name, toUInt8OrZero(element_type) AS position_id, toUInt8OrZero(team) AS team_id, toUInt32OrZero(now_cost) AS now_cost, toFloat64OrZero(selected_by_percent) AS selected_by_percent, toInt32OrZero(total_points) AS total_points, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, CAST(NULL, 'Nullable(Float64)') AS expected_goals, CAST(NULL, 'Nullable(Float64)') AS expected_assists, CAST(NULL, 'Nullable(UInt32)') AS starts
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2020-21/players_raw.csv', CSVWithNames, 'id String, code String, web_name String, first_name String, second_name String, element_type String, team String, now_cost String, selected_by_percent String, total_points String, minutes String, goals_scored String, assists String');
INSERT INTO epl_fpl_players_raw
SELECT
  '2021-22' AS season, toUInt32OrZero(id) AS player_id, toUInt32OrZero(code) AS player_code, web_name, first_name, second_name, toUInt8OrZero(element_type) AS position_id, toUInt8OrZero(team) AS team_id, toUInt32OrZero(now_cost) AS now_cost, toFloat64OrZero(selected_by_percent) AS selected_by_percent, toInt32OrZero(total_points) AS total_points, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, CAST(NULL, 'Nullable(Float64)') AS expected_goals, CAST(NULL, 'Nullable(Float64)') AS expected_assists, CAST(NULL, 'Nullable(UInt32)') AS starts
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2021-22/players_raw.csv', CSVWithNames, 'id String, code String, web_name String, first_name String, second_name String, element_type String, team String, now_cost String, selected_by_percent String, total_points String, minutes String, goals_scored String, assists String');
INSERT INTO epl_fpl_players_raw
SELECT
  '2022-23' AS season, toUInt32OrZero(id) AS player_id, toUInt32OrZero(code) AS player_code, web_name, first_name, second_name, toUInt8OrZero(element_type) AS position_id, toUInt8OrZero(team) AS team_id, toUInt32OrZero(now_cost) AS now_cost, toFloat64OrZero(selected_by_percent) AS selected_by_percent, toInt32OrZero(total_points) AS total_points, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, toFloat64OrNull(expected_goals) AS expected_goals, toFloat64OrNull(expected_assists) AS expected_assists, toUInt32OrNull(starts) AS starts
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2022-23/players_raw.csv', CSVWithNames, 'id String, code String, web_name String, first_name String, second_name String, element_type String, team String, now_cost String, selected_by_percent String, total_points String, minutes String, goals_scored String, assists String, expected_goals String, expected_assists String, starts String');
INSERT INTO epl_fpl_players_raw
SELECT
  '2023-24' AS season, toUInt32OrZero(id) AS player_id, toUInt32OrZero(code) AS player_code, web_name, first_name, second_name, toUInt8OrZero(element_type) AS position_id, toUInt8OrZero(team) AS team_id, toUInt32OrZero(now_cost) AS now_cost, toFloat64OrZero(selected_by_percent) AS selected_by_percent, toInt32OrZero(total_points) AS total_points, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, toFloat64OrNull(expected_goals) AS expected_goals, toFloat64OrNull(expected_assists) AS expected_assists, toUInt32OrNull(starts) AS starts
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2023-24/players_raw.csv', CSVWithNames, 'id String, code String, web_name String, first_name String, second_name String, element_type String, team String, now_cost String, selected_by_percent String, total_points String, minutes String, goals_scored String, assists String, expected_goals String, expected_assists String, starts String');
INSERT INTO epl_fpl_players_raw
SELECT
  '2024-25' AS season, toUInt32OrZero(id) AS player_id, toUInt32OrZero(code) AS player_code, web_name, first_name, second_name, toUInt8OrZero(element_type) AS position_id, toUInt8OrZero(team) AS team_id, toUInt32OrZero(now_cost) AS now_cost, toFloat64OrZero(selected_by_percent) AS selected_by_percent, toInt32OrZero(total_points) AS total_points, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, toFloat64OrNull(expected_goals) AS expected_goals, toFloat64OrNull(expected_assists) AS expected_assists, toUInt32OrNull(starts) AS starts
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2024-25/players_raw.csv', CSVWithNames, 'id String, code String, web_name String, first_name String, second_name String, element_type String, team String, now_cost String, selected_by_percent String, total_points String, minutes String, goals_scored String, assists String, expected_goals String, expected_assists String, starts String');
INSERT INTO epl_fpl_players_raw
SELECT
  '2025-26' AS season, toUInt32OrZero(id) AS player_id, toUInt32OrZero(code) AS player_code, web_name, first_name, second_name, toUInt8OrZero(element_type) AS position_id, toUInt8OrZero(team) AS team_id, toUInt32OrZero(now_cost) AS now_cost, toFloat64OrZero(selected_by_percent) AS selected_by_percent, toInt32OrZero(total_points) AS total_points, toUInt32OrZero(minutes) AS minutes, toUInt32OrZero(goals_scored) AS goals_scored, toUInt32OrZero(assists) AS assists, toFloat64OrNull(expected_goals) AS expected_goals, toFloat64OrNull(expected_assists) AS expected_assists, toUInt32OrNull(starts) AS starts
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2025-26/players_raw.csv', CSVWithNames, 'id String, code String, web_name String, first_name String, second_name String, element_type String, team String, now_cost String, selected_by_percent String, total_points String, minutes String, goals_scored String, assists String, expected_goals String, expected_assists String, starts String');
INSERT INTO epl_teams
SELECT
  '2019-20' AS season, toUInt8OrZero(id) AS team_id, name, short_name, toUInt8OrZero(strength) AS strength,
  toUInt16OrZero(strength_defence_home) AS strength_defence_home, toUInt16OrZero(strength_defence_away) AS strength_defence_away,
  toUInt16OrZero(strength_attack_home) AS strength_attack_home, toUInt16OrZero(strength_attack_away) AS strength_attack_away
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2019-20/teams.csv', CSVWithNames, 'id String, name String, short_name String, strength String, strength_defence_home String, strength_defence_away String, strength_attack_home String, strength_attack_away String');
INSERT INTO epl_teams
SELECT
  '2020-21' AS season, toUInt8OrZero(id) AS team_id, name, short_name, toUInt8OrZero(strength) AS strength,
  toUInt16OrZero(strength_defence_home) AS strength_defence_home, toUInt16OrZero(strength_defence_away) AS strength_defence_away,
  toUInt16OrZero(strength_attack_home) AS strength_attack_home, toUInt16OrZero(strength_attack_away) AS strength_attack_away
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2020-21/teams.csv', CSVWithNames, 'id String, name String, short_name String, strength String, strength_defence_home String, strength_defence_away String, strength_attack_home String, strength_attack_away String');
INSERT INTO epl_teams
SELECT
  '2021-22' AS season, toUInt8OrZero(id) AS team_id, name, short_name, toUInt8OrZero(strength) AS strength,
  toUInt16OrZero(strength_defence_home) AS strength_defence_home, toUInt16OrZero(strength_defence_away) AS strength_defence_away,
  toUInt16OrZero(strength_attack_home) AS strength_attack_home, toUInt16OrZero(strength_attack_away) AS strength_attack_away
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2021-22/teams.csv', CSVWithNames, 'id String, name String, short_name String, strength String, strength_defence_home String, strength_defence_away String, strength_attack_home String, strength_attack_away String');
INSERT INTO epl_teams
SELECT
  '2022-23' AS season, toUInt8OrZero(id) AS team_id, name, short_name, toUInt8OrZero(strength) AS strength,
  toUInt16OrZero(strength_defence_home) AS strength_defence_home, toUInt16OrZero(strength_defence_away) AS strength_defence_away,
  toUInt16OrZero(strength_attack_home) AS strength_attack_home, toUInt16OrZero(strength_attack_away) AS strength_attack_away
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2022-23/teams.csv', CSVWithNames, 'id String, name String, short_name String, strength String, strength_defence_home String, strength_defence_away String, strength_attack_home String, strength_attack_away String');
INSERT INTO epl_teams
SELECT
  '2023-24' AS season, toUInt8OrZero(id) AS team_id, name, short_name, toUInt8OrZero(strength) AS strength,
  toUInt16OrZero(strength_defence_home) AS strength_defence_home, toUInt16OrZero(strength_defence_away) AS strength_defence_away,
  toUInt16OrZero(strength_attack_home) AS strength_attack_home, toUInt16OrZero(strength_attack_away) AS strength_attack_away
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2023-24/teams.csv', CSVWithNames, 'id String, name String, short_name String, strength String, strength_defence_home String, strength_defence_away String, strength_attack_home String, strength_attack_away String');
INSERT INTO epl_teams
SELECT
  '2024-25' AS season, toUInt8OrZero(id) AS team_id, name, short_name, toUInt8OrZero(strength) AS strength,
  toUInt16OrZero(strength_defence_home) AS strength_defence_home, toUInt16OrZero(strength_defence_away) AS strength_defence_away,
  toUInt16OrZero(strength_attack_home) AS strength_attack_home, toUInt16OrZero(strength_attack_away) AS strength_attack_away
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2024-25/teams.csv', CSVWithNames, 'id String, name String, short_name String, strength String, strength_defence_home String, strength_defence_away String, strength_attack_home String, strength_attack_away String');
INSERT INTO epl_teams
SELECT
  '2025-26' AS season, toUInt8OrZero(id) AS team_id, name, short_name, toUInt8OrZero(strength) AS strength,
  toUInt16OrZero(strength_defence_home) AS strength_defence_home, toUInt16OrZero(strength_defence_away) AS strength_defence_away,
  toUInt16OrZero(strength_attack_home) AS strength_attack_home, toUInt16OrZero(strength_attack_away) AS strength_attack_away
FROM url('https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2025-26/teams.csv', CSVWithNames, 'id String, name String, short_name String, strength String, strength_defence_home String, strength_defence_away String, strength_attack_home String, strength_attack_away String');
INSERT INTO epl_matches
SELECT
  '2016-17' AS season, toDateOrDefault(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)), toDate('1970-01-01')) AS match_date, Date AS date_string, '' AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, toInt16OrNull(FTHG) AS fthg, toInt16OrNull(FTAG) AS ftag, FTR AS ftr, toInt16OrNull(HTHG) AS hthg, toInt16OrNull(HTAG) AS htag, HTR AS htr, Referee AS referee, toInt16OrNull(`HS`) AS hs, toInt16OrNull(`AS`) AS as_, toInt16OrNull(`HST`) AS hst, toInt16OrNull(`AST`) AS ast, toInt16OrNull(`HC`) AS hc, toInt16OrNull(`AC`) AS ac, toInt16OrNull(`HY`) AS hy, toInt16OrNull(`AY`) AS ay, toInt16OrNull(`HR`) AS hr, toInt16OrNull(`AR`) AS ar
FROM url('https://www.football-data.co.uk/mmz4281/1617/E0.csv', CSVWithNames, 'Date String, HomeTeam String, AwayTeam String, FTHG String, FTAG String, FTR String, HTHG String, HTAG String, HTR String, Referee String, HS String, AS String, HST String, AST String, HF String, AF String, HC String, AC String, HY String, AY String, HR String, AR String');
INSERT INTO epl_matches
SELECT
  '2017-18' AS season, toDateOrDefault(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)), toDate('1970-01-01')) AS match_date, Date AS date_string, '' AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, toInt16OrNull(FTHG) AS fthg, toInt16OrNull(FTAG) AS ftag, FTR AS ftr, toInt16OrNull(HTHG) AS hthg, toInt16OrNull(HTAG) AS htag, HTR AS htr, Referee AS referee, toInt16OrNull(`HS`) AS hs, toInt16OrNull(`AS`) AS as_, toInt16OrNull(`HST`) AS hst, toInt16OrNull(`AST`) AS ast, toInt16OrNull(`HC`) AS hc, toInt16OrNull(`AC`) AS ac, toInt16OrNull(`HY`) AS hy, toInt16OrNull(`AY`) AS ay, toInt16OrNull(`HR`) AS hr, toInt16OrNull(`AR`) AS ar
FROM url('https://www.football-data.co.uk/mmz4281/1718/E0.csv', CSVWithNames, 'Date String, HomeTeam String, AwayTeam String, FTHG String, FTAG String, FTR String, HTHG String, HTAG String, HTR String, Referee String, HS String, AS String, HST String, AST String, HF String, AF String, HC String, AC String, HY String, AY String, HR String, AR String');
INSERT INTO epl_matches
SELECT
  '2018-19' AS season, toDateOrDefault(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)), toDate('1970-01-01')) AS match_date, Date AS date_string, '' AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, toInt16OrNull(FTHG) AS fthg, toInt16OrNull(FTAG) AS ftag, FTR AS ftr, toInt16OrNull(HTHG) AS hthg, toInt16OrNull(HTAG) AS htag, HTR AS htr, Referee AS referee, toInt16OrNull(`HS`) AS hs, toInt16OrNull(`AS`) AS as_, toInt16OrNull(`HST`) AS hst, toInt16OrNull(`AST`) AS ast, toInt16OrNull(`HC`) AS hc, toInt16OrNull(`AC`) AS ac, toInt16OrNull(`HY`) AS hy, toInt16OrNull(`AY`) AS ay, toInt16OrNull(`HR`) AS hr, toInt16OrNull(`AR`) AS ar
FROM url('https://www.football-data.co.uk/mmz4281/1819/E0.csv', CSVWithNames, 'Date String, HomeTeam String, AwayTeam String, FTHG String, FTAG String, FTR String, HTHG String, HTAG String, HTR String, Referee String, HS String, AS String, HST String, AST String, HF String, AF String, HC String, AC String, HY String, AY String, HR String, AR String');
INSERT INTO epl_matches
SELECT
  '2019-20' AS season, toDateOrDefault(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)), toDate('1970-01-01')) AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, toInt16OrNull(FTHG) AS fthg, toInt16OrNull(FTAG) AS ftag, FTR AS ftr, toInt16OrNull(HTHG) AS hthg, toInt16OrNull(HTAG) AS htag, HTR AS htr, Referee AS referee, toInt16OrNull(`HS`) AS hs, toInt16OrNull(`AS`) AS as_, toInt16OrNull(`HST`) AS hst, toInt16OrNull(`AST`) AS ast, toInt16OrNull(`HC`) AS hc, toInt16OrNull(`AC`) AS ac, toInt16OrNull(`HY`) AS hy, toInt16OrNull(`AY`) AS ay, toInt16OrNull(`HR`) AS hr, toInt16OrNull(`AR`) AS ar
FROM url('https://www.football-data.co.uk/mmz4281/1920/E0.csv', CSVWithNames, 'Date String, Time String, HomeTeam String, AwayTeam String, FTHG String, FTAG String, FTR String, HTHG String, HTAG String, HTR String, Referee String, HS String, AS String, HST String, AST String, HF String, AF String, HC String, AC String, HY String, AY String, HR String, AR String');
INSERT INTO epl_matches
SELECT
  '2020-21' AS season, toDateOrDefault(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)), toDate('1970-01-01')) AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, toInt16OrNull(FTHG) AS fthg, toInt16OrNull(FTAG) AS ftag, FTR AS ftr, toInt16OrNull(HTHG) AS hthg, toInt16OrNull(HTAG) AS htag, HTR AS htr, Referee AS referee, toInt16OrNull(`HS`) AS hs, toInt16OrNull(`AS`) AS as_, toInt16OrNull(`HST`) AS hst, toInt16OrNull(`AST`) AS ast, toInt16OrNull(`HC`) AS hc, toInt16OrNull(`AC`) AS ac, toInt16OrNull(`HY`) AS hy, toInt16OrNull(`AY`) AS ay, toInt16OrNull(`HR`) AS hr, toInt16OrNull(`AR`) AS ar
FROM url('https://www.football-data.co.uk/mmz4281/2021/E0.csv', CSVWithNames, 'Date String, Time String, HomeTeam String, AwayTeam String, FTHG String, FTAG String, FTR String, HTHG String, HTAG String, HTR String, Referee String, HS String, AS String, HST String, AST String, HF String, AF String, HC String, AC String, HY String, AY String, HR String, AR String');
INSERT INTO epl_matches
SELECT
  '2021-22' AS season, toDateOrDefault(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)), toDate('1970-01-01')) AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, toInt16OrNull(FTHG) AS fthg, toInt16OrNull(FTAG) AS ftag, FTR AS ftr, toInt16OrNull(HTHG) AS hthg, toInt16OrNull(HTAG) AS htag, HTR AS htr, Referee AS referee, toInt16OrNull(`HS`) AS hs, toInt16OrNull(`AS`) AS as_, toInt16OrNull(`HST`) AS hst, toInt16OrNull(`AST`) AS ast, toInt16OrNull(`HC`) AS hc, toInt16OrNull(`AC`) AS ac, toInt16OrNull(`HY`) AS hy, toInt16OrNull(`AY`) AS ay, toInt16OrNull(`HR`) AS hr, toInt16OrNull(`AR`) AS ar
FROM url('https://www.football-data.co.uk/mmz4281/2122/E0.csv', CSVWithNames, 'Date String, Time String, HomeTeam String, AwayTeam String, FTHG String, FTAG String, FTR String, HTHG String, HTAG String, HTR String, Referee String, HS String, AS String, HST String, AST String, HF String, AF String, HC String, AC String, HY String, AY String, HR String, AR String');
INSERT INTO epl_matches
SELECT
  '2022-23' AS season, toDateOrDefault(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)), toDate('1970-01-01')) AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, toInt16OrNull(FTHG) AS fthg, toInt16OrNull(FTAG) AS ftag, FTR AS ftr, toInt16OrNull(HTHG) AS hthg, toInt16OrNull(HTAG) AS htag, HTR AS htr, Referee AS referee, toInt16OrNull(`HS`) AS hs, toInt16OrNull(`AS`) AS as_, toInt16OrNull(`HST`) AS hst, toInt16OrNull(`AST`) AS ast, toInt16OrNull(`HC`) AS hc, toInt16OrNull(`AC`) AS ac, toInt16OrNull(`HY`) AS hy, toInt16OrNull(`AY`) AS ay, toInt16OrNull(`HR`) AS hr, toInt16OrNull(`AR`) AS ar
FROM url('https://www.football-data.co.uk/mmz4281/2223/E0.csv', CSVWithNames, 'Date String, Time String, HomeTeam String, AwayTeam String, FTHG String, FTAG String, FTR String, HTHG String, HTAG String, HTR String, Referee String, HS String, AS String, HST String, AST String, HF String, AF String, HC String, AC String, HY String, AY String, HR String, AR String');
INSERT INTO epl_matches
SELECT
  '2023-24' AS season, toDateOrDefault(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)), toDate('1970-01-01')) AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, toInt16OrNull(FTHG) AS fthg, toInt16OrNull(FTAG) AS ftag, FTR AS ftr, toInt16OrNull(HTHG) AS hthg, toInt16OrNull(HTAG) AS htag, HTR AS htr, Referee AS referee, toInt16OrNull(`HS`) AS hs, toInt16OrNull(`AS`) AS as_, toInt16OrNull(`HST`) AS hst, toInt16OrNull(`AST`) AS ast, toInt16OrNull(`HC`) AS hc, toInt16OrNull(`AC`) AS ac, toInt16OrNull(`HY`) AS hy, toInt16OrNull(`AY`) AS ay, toInt16OrNull(`HR`) AS hr, toInt16OrNull(`AR`) AS ar
FROM url('https://www.football-data.co.uk/mmz4281/2324/E0.csv', CSVWithNames, 'Date String, Time String, HomeTeam String, AwayTeam String, FTHG String, FTAG String, FTR String, HTHG String, HTAG String, HTR String, Referee String, HS String, AS String, HST String, AST String, HF String, AF String, HC String, AC String, HY String, AY String, HR String, AR String');
INSERT INTO epl_matches
SELECT
  '2024-25' AS season, toDateOrDefault(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)), toDate('1970-01-01')) AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, toInt16OrNull(FTHG) AS fthg, toInt16OrNull(FTAG) AS ftag, FTR AS ftr, toInt16OrNull(HTHG) AS hthg, toInt16OrNull(HTAG) AS htag, HTR AS htr, Referee AS referee, toInt16OrNull(`HS`) AS hs, toInt16OrNull(`AS`) AS as_, toInt16OrNull(`HST`) AS hst, toInt16OrNull(`AST`) AS ast, toInt16OrNull(`HC`) AS hc, toInt16OrNull(`AC`) AS ac, toInt16OrNull(`HY`) AS hy, toInt16OrNull(`AY`) AS ay, toInt16OrNull(`HR`) AS hr, toInt16OrNull(`AR`) AS ar
FROM url('https://www.football-data.co.uk/mmz4281/2425/E0.csv', CSVWithNames, 'Date String, Time String, HomeTeam String, AwayTeam String, FTHG String, FTAG String, FTR String, HTHG String, HTAG String, HTR String, Referee String, HS String, AS String, HST String, AST String, HF String, AF String, HC String, AC String, HY String, AY String, HR String, AR String');
INSERT INTO epl_matches
SELECT
  '2025-26' AS season, toDateOrDefault(concat(if(length(Date) = 10, substring(Date, 7, 4), concat('20', substring(Date, 7, 2))), '-', substring(Date, 4, 2), '-', substring(Date, 1, 2)), toDate('1970-01-01')) AS match_date, Date AS date_string, Time AS match_time, HomeTeam AS home_team, AwayTeam AS away_team, toInt16OrNull(FTHG) AS fthg, toInt16OrNull(FTAG) AS ftag, FTR AS ftr, toInt16OrNull(HTHG) AS hthg, toInt16OrNull(HTAG) AS htag, HTR AS htr, Referee AS referee, toInt16OrNull(`HS`) AS hs, toInt16OrNull(`AS`) AS as_, toInt16OrNull(`HST`) AS hst, toInt16OrNull(`AST`) AS ast, toInt16OrNull(`HC`) AS hc, toInt16OrNull(`AC`) AS ac, toInt16OrNull(`HY`) AS hy, toInt16OrNull(`AY`) AS ay, toInt16OrNull(`HR`) AS hr, toInt16OrNull(`AR`) AS ar
FROM url('https://www.football-data.co.uk/mmz4281/2526/E0.csv', CSVWithNames, 'Date String, Time String, HomeTeam String, AwayTeam String, FTHG String, FTAG String, FTR String, HTHG String, HTAG String, HTR String, Referee String, HS String, AS String, HST String, AST String, HF String, AF String, HC String, AC String, HY String, AY String, HR String, AR String');
-- Season-aggregate player table (backtest-ready: one row per player per season)
CREATE TABLE IF NOT EXISTS epl_player_season
ENGINE = MergeTree ORDER BY (season, player_id) AS
SELECT
  g.season,
  g.player_id,
  max(r.player_code) AS player_code,
  any(g.name) AS name,
  any(g.position) AS position,
  argMax(g.team, g.round) AS team,
  sum(g.minutes) AS minutes,
  sumOrNull(g.starts) AS starts,
  sum(g.goals_scored) AS goals,
  sum(g.assists) AS assists,
  sumOrNull(g.expected_goals) AS xg,
  sumOrNull(g.expected_assists) AS xa,
  sum(g.total_points) AS fpl_points_from_gws,
  max(r.now_cost) AS fpl_price_x10,
  max(r.selected_by_percent) AS fpl_selected_by_percent,
  max(r.total_points) AS fpl_total_points
FROM epl_fpl_gameweeks g
LEFT JOIN epl_fpl_players_raw r ON r.season = g.season AND r.player_id = g.player_id
GROUP BY g.season, g.player_id
ORDER BY g.season, fpl_points_from_gws DESC;

-- Sanity checks
SELECT 'epl_fpl_gameweeks' AS t, count() FROM epl_fpl_gameweeks
UNION ALL SELECT 'epl_fpl_players_raw', count() FROM epl_fpl_players_raw
UNION ALL SELECT 'epl_matches', count() FROM epl_matches
UNION ALL SELECT 'epl_teams', count() FROM epl_teams
UNION ALL SELECT 'epl_player_season', count() FROM epl_player_season;
SELECT season, count() FROM epl_fpl_gameweeks GROUP BY season ORDER BY season;
SELECT season, count() FROM epl_matches GROUP BY season ORDER BY season;
