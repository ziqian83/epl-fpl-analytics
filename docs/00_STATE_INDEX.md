# EPL/FPL Analytics Project - Sprint State (as of 2026-09-12, Sat)

Owner: Ziqian Hoe. Sprint: V1 requirements Sat Sep 12, iteration Sun Sep 13, possible demo Mon Sep 14 (AMG call).

## Files
- 01_clickhouse_service.md - service details, console URL, trial terms, table schemas, join keys, load sources
- 02_picker_signals.md - the 11 picker signals with definitions and status
- 03_model_notes.md - consistency baseline, cold-start variants, exhibit names, wildcard backtest, FPL 2026-27 rule changes
- my_team_gw4.json - his GW4 squad record (parsed from WhatsApp screenshot, verified vs FPL API + warehouse)

## ClickHouse quick facts
- Org "ZI's Organization" f370731e-3bd2-4415-952f-debd2bafffe1 (NOT the dead "HZ's Organization")
- Service "epl-playground" f09805e2-0374-4f68-9adb-9e79d4b5a3ea, AWS ap-southeast-1, Scale-Trial, 300 credits, expires Oct 12 2026
- Console: https://console.clickhouse.cloud/services/f09805e2-0374-4f68-9adb-9e79d4b5a3ea/console
- Login: vault entry "clickhouse-cloud-playground" (ziqian83+clickhouse@gmail.com), saved in cloud-browser profile
- 5 tables, 10 seasons 2016-17..2025-26, 253,900 gameweek rows. Load script: epl_clickhouse_load.sql (37 statements)
