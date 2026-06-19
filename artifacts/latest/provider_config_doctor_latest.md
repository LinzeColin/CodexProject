# Provider Config Doctor

- status: `ready`
- generated_at: `2026-06-14T05:52:49.690981+10:00`
- local_env_exists: `True`
- example_env_fallback: `False`
- effective_env_exists: `True`
- the_odds_api_key_present: `True`
- opticodds_key_present: `False`
- requested_sports: `soccer_fifa_world_cup`
- recommended_sports: `soccer_fifa_world_cup`
- known_invalid_or_legacy_sports: `none`
- sports_discovery_enabled: `True`
- event_market_probe_limit: `0`
- current_executable_new_stake_aud: `AUD 0`

Next safe action: 配置可用；下一步执行 matches 主盘口刷新或 Team Total 人工下一批。

## Issues
- none

## Recommended Commands
- 安全配置检查: `python3 scripts/build_provider_config_doctor.py`
- Matches 主盘口刷新: `python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 0`
- Team Total 人工下一批: `open '/Users/linzezhang/Downloads/FIFA Report/app_assets/provider_manual_next_batch_pair_template_latest.csv'`

Safety boundary: 该诊断只检查 provider 配置和 credit-safe 参数；不请求 odds、不登录 TAB、不点击赔率、不下注。
