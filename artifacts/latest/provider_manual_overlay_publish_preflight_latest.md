# Provider Manual Team Total Overlay Publish Preflight

- generated_at: `2026-06-14T06:02:38.700723+10:00`
- status: `waiting_for_import`
- refresh_id: `20260613T194716Z-provider-2fec0bef`
- board_id: `world_cup_matches`
- market_family: `Team Total Goals Over/Under`
- approval_relative_path: `manual_verification/provider_team_total_overlay_approval.json`
- approval_file_sha256: ``
- manual_import_sha256: ``
- overlay_raw_snapshot: `provider_manual_team_total_overlay_raw_latest.json`
- overlay_raw_sha256: `fef7bb4305f0c52eb17d56e148aa84e14b098b457bccdb25c3c375402c0dfda9`
- overlay_event_count: `0`
- approved_by_user: `False`
- overlay_publish_preflight_passed: `False`
- publish_compatible_with_provider_raw: `False`
- formal_publish_allowed: `False`
- current_executable_new_stake_aud: `AUD 0`

Next action: 先完成 Team Total 人工 CSV 导入并生成非空 overlay raw 预览。

## Issues

| Field | Issue |
|---|---|
| `overlay` | overlay raw preview is not ready |

Truthfulness: 该预检只验证人工签名文件与 overlay preview hash 是否匹配；即使通过，也只是进入后续显式 publish 流程的前置条件。它不会自动覆盖正式 raw，不会解锁自动下注。
