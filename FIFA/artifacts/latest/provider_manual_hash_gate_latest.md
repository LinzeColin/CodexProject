# Provider Manual Hash Gate

- generated_at: `2026-06-14T06:02:38.611004+10:00`
- status: `waiting_for_import`
- refresh_id: `20260613T194716Z-provider-2fec0bef`
- board_id: `world_cup_matches`
- market_family: `Team Total Goals Over/Under`
- complete_event_count: `0/64`
- high_priority_complete_count: `0/51`
- import_file_sha256: ``
- manual_import_sha256: ``
- ready_for_manual_signature: `False`
- approved_by_user: `False`
- current_executable_new_stake_aud: `AUD 0`

Next action: 先填写人工 Team Total CSV；当前没有可 hash 的完整候选。

## Draft Boundary

- publish_compatible_with_provider_raw: `False`
- note: 这是人工导入 hash gate 草案，不是 provider raw publish approvals；不能直接传给 --verification-file 发布 raw。

## Invalid Rows

| Row | Event | Issue |
|---:|---|---|
| - | - | No invalid rows. |

Truthfulness: 该 hash gate 只证明人工导入 CSV 的规范化内容可复核；不证明 TAB 盘口真实性，不替代 provider raw sha256 publish gate，不自动设置 approved_by_user。
