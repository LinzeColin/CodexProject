# Provider Manual Team Total Overlay Preview

- generated_at: `2026-06-14T06:02:38.612381+10:00`
- status: `waiting_for_import`
- refresh_id: `20260613T194716Z-provider-2fec0bef`
- board_id: `world_cup_matches`
- market_family: `Team Total Goals Over/Under`
- overlay_event_count: `0/64`
- overlay_row_count: `0`
- high_priority_complete_count: `0/51`
- manual_import_sha256: ``
- overlay_raw_snapshot: `provider_manual_team_total_overlay_raw_latest.json`
- overlay_raw_sha256: `fef7bb4305f0c52eb17d56e148aa84e14b098b457bccdb25c3c375402c0dfda9`
- ready_for_publish_preflight: `False`
- approved_by_user: `False`
- formal_publish_allowed: `False`
- current_executable_new_stake_aud: `AUD 0`

Next action: 等待人工导入 Team Total CSV；当前 overlay raw 只生成空预览 envelope。

## Overlay Boundary

- overlay_preview_only: `True`
- publish_compatible_with_provider_raw: `False`
- note: 这是 Team Total overlay raw 预览草案，不是正式 provider raw publish approval；不能用于自动下注或自动发布。

## Invalid Rows

| Row | Event | Issue |
|---:|---|---|
| - | - | No invalid rows. |

## Overlaid Events Sample

- None.

Truthfulness: 该 overlay 只把已通过结构校验的人工 Team Total CSV 合入一个 preview-only raw；不覆盖正式 raw，不证明 TAB 盘口真实性，不设置 approved_by_user，不生成新增可执行下注金额。
