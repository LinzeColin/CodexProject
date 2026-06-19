# Provider Manual Verification Import Status

- generated_at: `2026-06-14T06:02:38.604133+10:00`
- status: `import_missing`
- refresh_id: `20260613T194716Z-provider-2fec0bef`
- import_file: `manual_verification/provider_team_total_manual_verification.csv`
- complete_event_count: `0/64`
- high_priority_complete_count: `0/51`
- current_executable_new_stake_aud: `AUD 0`

Next action: 下载 CSV 模板，人工只读 TAB 后保存到 manual_verification/provider_team_total_manual_verification.csv。

## Required Columns

`event_id`, `rank`, `match`, `commence_time`, `priority_tier`, `missing_market`, `tab_match_name`, `team_scope`, `tab_market_name`, `selection_name`, `line`, `decimal_odds`, `observed_at_aest`, `operator_initials`, `evidence_note_or_screenshot_ref`, `verification_status`

## Invalid Rows

| Row | Event | Issue |
|---:|---|---|
| - | - | No invalid rows. |

Truthfulness: 该状态只验证人工填写文件是否结构完整；不证明 TAB 盘口真实性，不自动登录 TAB、不点击赔率、不下注。
