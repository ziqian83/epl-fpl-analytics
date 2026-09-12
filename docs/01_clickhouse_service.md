# ClickHouse Cloud service & warehouse schema

## Service
- Account: ziqian83+clickhouse@gmail.com (email+password, vault: "clickhouse-cloud-playground")
- Org: "ZI's Organization", id f370731e-3bd2-4415-952f-debd2bafffe1 (fresh; dead org "HZ's Organization" e46ef355-cc1b-44f7-b5bd-42fb239b18c9 must NOT be used)
- Service: "epl-playground", id f09805e2-0374-4f68-9adb-9e79d4b5a3ea
- AWS Singapore (ap-southeast-1), 16-120 GiB RAM, 4-30 vCPU, 2 replicas, Read-write
- Plan: Scale - Trial, 300 credits Active Sep 11 - Oct 12 2026, $0 used at creation. No card on file; service stops at expiry unless user adds payment. Console banner: "Your trial ends in 30 days".
- Console URL: https://console.clickhouse.cloud/services/f09805e2-0374-4f68-9adb-9e79d4b5a3ea/console

## Tables (row counts verified live 2026-09-11)
- epl_fpl_gameweeks (253,900): player-gameweek, 2016-17..2025-26. Key cols: season, gw, round, player_id (SEASON-SCOPED - reissued yearly), name, team, was_home, minutes, total_points, goals_scored, assists, expected_goals (2022-23+), expected_assists (2022-23+), starts (2022-23+), kickoff_time. Era gaps: position/team cols only from 2020-21.
- epl_fpl_players_raw (7,358): FPL season aggregates. Has player_code (STABLE cross-season key), player_id, total_points, price (x10), selected_by_percent.
- epl_matches (3,800; 380/season): match_date, home_team, away_team, fthg, ftag, ftr, hthg/htag/htr, referee. Team names football-data style ("Man United", NOT "Man Utd"; "Tottenham" NOT "Spurs").
- epl_teams (140): 2019-20+ only; strength_defence_home/away etc for fixture weighting.
- epl_player_season (7,358): derived backtest table. season, player_id, player_code, name, position, team, minutes, starts, goals, assists, xg, xa, fpl_points_from_gws, fpl_price_x10, fpl_selected_by_percent, fpl_total_points.

## JOIN DISCIPLINE (hard-won)
- Cross-season player joins: player_code ONLY. player_id is reissued per season (Haaland: 318/355/351/430). A player_id cross-season join produced garbage -0.07 correlation vs 0.52 on player_code.
- Gameweeks table has NO player_code - join via epl_player_season on (season, player_id) to resolve codes.
- Gameweek->match result join: on match_date = toDate(kickoff_time) AND (home_team=team OR away_team=team), same season. Name-format mismatches (Man Utd/Man United, Spurs/Tottenham) mean team-name joins need a mapping.
- Name formats vary by era: "Harry_Kane" (2016-19), "Sadio_Mane_251" (id suffixes, encoding artifacts), "Harry Kane" (2020-21+). Never join on names.
- Cold-start/history checks must scan ALL 10 seasons by player_code, never one season (the Leif Davis miss).

## Data sources (all verified)
- vaastav/Fantasy-Premier-League raw github: data/<season>/gws/merged_gw.csv, players_raw.csv, teams.csv (2019-20+)
- football-data.co.uk/mmz4281/<yy1yy2>/E0.csv (needs SET max_http_get_redirects = 10; old seasons lack Time col; Date dd/mm/yy or dd/mm/yyyy)
- FPL API (unauthenticated): /api/bootstrap-static/ (codes, prices, ownership, form), /api/entry/<id>/, /api/entry/<id>/history/, /api/entry/<id>/event/<gw>/picks/ (completed GWs only), /api/element-summary/<id>/, /api/fixtures/?event=<gw>
