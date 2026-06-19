# Provider Manual Team Total Workbench

- generated_at: `2026-06-14T06:02:38.724638+10:00`
- status: `waiting_for_first_batch`
- refresh_id: `20260613T194716Z-provider-2fec0bef`
- remaining_event_count: `64`
- remaining_high_priority_count: `51`
- batch_count: `8`
- next_batch: `TT-001`
- all_pair_template: `provider_manual_pair_template_latest.csv`
- next_batch_pair_template: `provider_manual_next_batch_pair_template_latest.csv`
- current_executable_new_stake_aud: `AUD 0`

Next action: 下一批执行 TT-001，校验 8 场；剩余高优先级 51 场，仍保持 stake AUD 0。

## Operator Cockpit

- title: `TT-001 Team Total 补齐操作台`
- primary_action: 下一批执行 TT-001，校验 8 场；剩余高优先级 51 场，仍保持 stake AUD 0。
- current_batch: `TT-001` / events `8` / pair rows `16`
- next_batch_pair_template: `provider_manual_next_batch_pair_template_latest.csv`
- import_target: `manual_verification/provider_team_total_manual_verification.csv`
- publish_status: `blocked_until_manual_import_and_signature`
- can_publish_now: `False`
- stake_policy: 通过 manual import、hash gate、overlay preview、签名预检和 explicit publish 前，current executable new stake 固定 AUD 0。

## Manual Intake Contract

- status: `waiting_for_first_batch`
- current_batch_id: `TT-001`
- template_csv: `provider_manual_next_batch_pair_template_latest.csv`
- import_target: `outputs/manual_verification/provider_team_total_manual_verification.csv`
- rebuild_command: `TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py`
- publish_command_after_signature: `python3 publish_provider_manual_overlay.py`
- next_safe_action: 当前未检测到人工行；从 TT-001 下一批成对模板开始填写。

### Acceptance Criteria

- next_batch_quality.status_counts 中不再出现 missing_rows 或 invalid_rows。
- import_quality.invalid_event_count=0。
- hash_gate_status 不再是 waiting_for_import。
- overlay_preview_status 不再是 waiting_for_import。
- formal_publish_allowed=false 直到人工签名和显式 publish 通过。
- current_executable_new_stake_aud=0。

### Operator Steps

1. 打开 provider_manual_next_batch_pair_template_latest.csv，只处理当前批次 TT-001。
2. 在 TAB 页面只读核验 Team Total Goals Over/Under；每个 event 至少填同一 team_scope + line 的 Over 与 Under 两行。
3. 保存完整 CSV 到 outputs/manual_verification/provider_team_total_manual_verification.csv。
4. 运行 rebuild_command 重建 workbench、hash gate、overlay preview 和 Downloads app。
5. 只有 hash/approval/preflight 全部通过后，才允许人工显式运行 publish_command_after_signature；仍不自动下注。

## Workflow Steps

| Step | Title | Status | Action |
|---:|---|---|---|
| 1 | 打开下一批模板 | `manual_required` | 使用 provider_manual_next_batch_pair_template_latest.csv。 |
| 2 | 只读 TAB 核验 | `manual_required` | 按 match、commence_time、team_scope 查 Team Total Goals Over/Under。 |
| 3 | 保存导入文件 | `import_missing` | 把填好的行保存到 manual_verification/provider_team_total_manual_verification.csv。 |
| 4 | 重建工作台与 Hash Gate | `waiting_for_import` | 运行 build/download app 或 provider manual verification bundle。 |
| 5 | 签名后显式发布 | `blocked_until_manual_import_and_signature` | 只有 overlay approval hash 匹配后，才运行 publish_provider_manual_overlay.py。 |

## Field Checklist

| Field | Required | Validation | Reason |
|---|---|---|---|
| `event_id` | `True` | 必须来自模板，不要手写改动。 | 用于把人工 Team Total 行合回 provider staged match。 |
| `team_scope` | `True` | home 或 away。 | 区分 Team Total 属于哪支球队。 |
| `tab_match_name` | `True` | 按 TAB 页面显示填写。 | 用于人工复核 provider match 与 TAB match 是否一致。 |
| `tab_market_name` | `True` | 必须包含 Team Total / Team Goals 等语义。 | 防止把 Total Score O/U 错填为 Team Total。 |
| `selection_name` | `True` | 同一 event、team_scope、line 必须有 Over 与 Under 两行。 | 成对记录才能进入 hash gate。 |
| `line` | `True` | 必须是数字，如 0.5、1.5、2.5。 | 用于验证 Over/Under 是否同线。 |
| `decimal_odds` | `True` | 必须大于 1.00。 | 进入概率/EV 研究前必须是可解析价格。 |
| `observed_at_aest` | `True` | 使用 AEST 时间戳。 | 后续 CLV、回测和旧报告对比需要时间点。 |
| `operator_initials` | `True` | 填写人工核验人缩写。 | 人工签名和后续复盘需要责任链。 |
| `evidence_note_or_screenshot_ref` | `True` | 写明 TAB 页面观察备注或截图引用。 | 正式发布前需要人工复核依据。 |
| `verification_status` | `True` | verified / manual_verified / pending_review。 | 只有明确人工校验状态的行才能进入质量诊断。 |

## Import Quality

- import_quality_status: `waiting_for_manual_rows`
- next_batch_status_counts: `{"missing_rows": 8}`
- missing_event_count: `64`
- partial_event_count: `0`
- invalid_event_count: `0`
- complete_event_count: `0`
- next_action: 当前未检测到人工行；从 TT-001 下一批成对模板开始填写。

| Rank | Match | Quality | Missing Fields | Missing Directions | Next Action |
|---:|---|---|---|---|---|
| 1 | Qatar v Switzerland | `missing_rows` | tab_match_name, team_scope, tab_market_name, selection_name, line, decimal_odds, observed_at_aest, operator_initials, evidence_note_or_screenshot_ref, verification_status | over/under | 补字段 tab_match_name, team_scope, tab_market_name, selection_name；补方向 over/under |
| 2 | Brazil v Morocco | `missing_rows` | tab_match_name, team_scope, tab_market_name, selection_name, line, decimal_odds, observed_at_aest, operator_initials, evidence_note_or_screenshot_ref, verification_status | over/under | 补字段 tab_match_name, team_scope, tab_market_name, selection_name；补方向 over/under |
| 3 | Haiti v Scotland | `missing_rows` | tab_match_name, team_scope, tab_market_name, selection_name, line, decimal_odds, observed_at_aest, operator_initials, evidence_note_or_screenshot_ref, verification_status | over/under | 补字段 tab_match_name, team_scope, tab_market_name, selection_name；补方向 over/under |
| 4 | Australia v Turkey | `missing_rows` | tab_match_name, team_scope, tab_market_name, selection_name, line, decimal_odds, observed_at_aest, operator_initials, evidence_note_or_screenshot_ref, verification_status | over/under | 补字段 tab_match_name, team_scope, tab_market_name, selection_name；补方向 over/under |
| 5 | Germany v Curaçao | `missing_rows` | tab_match_name, team_scope, tab_market_name, selection_name, line, decimal_odds, observed_at_aest, operator_initials, evidence_note_or_screenshot_ref, verification_status | over/under | 补字段 tab_match_name, team_scope, tab_market_name, selection_name；补方向 over/under |
| 6 | Netherlands v Japan | `missing_rows` | tab_match_name, team_scope, tab_market_name, selection_name, line, decimal_odds, observed_at_aest, operator_initials, evidence_note_or_screenshot_ref, verification_status | over/under | 补字段 tab_match_name, team_scope, tab_market_name, selection_name；补方向 over/under |
| 7 | Ivory Coast v Ecuador | `missing_rows` | tab_match_name, team_scope, tab_market_name, selection_name, line, decimal_odds, observed_at_aest, operator_initials, evidence_note_or_screenshot_ref, verification_status | over/under | 补字段 tab_match_name, team_scope, tab_market_name, selection_name；补方向 over/under |
| 8 | Sweden v Tunisia | `missing_rows` | tab_match_name, team_scope, tab_market_name, selection_name, line, decimal_odds, observed_at_aest, operator_initials, evidence_note_or_screenshot_ref, verification_status | over/under | 补字段 tab_match_name, team_scope, tab_market_name, selection_name；补方向 over/under |

## Operator Checklist

- 打开 TAB 的 2026 World Cup Matches，对照 batch 中 match 和 commence_time。
- 只读 Team Total Goals Over/Under；每个 event 至少记录同一 line 的 Over 与 Under 成对赔率。
- 保存 event_id、team_scope、selection_name、line、decimal_odds、observed_at_aest、operator_initials 和证据备注。
- 写入 manual_verification/provider_team_total_manual_verification.csv 后重建 app；通过 hash gate 前 stake 保持 AUD 0。

## Next Batch

| Rank | Match | Time | Tier | Reason |
|---:|---|---|---|---|
| 1 | Qatar v Switzerland | `2026-06-13T19:04:00Z` | `high` | Result 已由 provider 覆盖；Total O/U 已由 provider 覆盖；Handicap 已由 provider 覆盖；Team Total 是当前主要缺口。 |
| 2 | Brazil v Morocco | `2026-06-13T22:00:00Z` | `high` | Result 已由 provider 覆盖；Total O/U 已由 provider 覆盖；Handicap 已由 provider 覆盖；Team Total 是当前主要缺口。 |
| 3 | Haiti v Scotland | `2026-06-14T01:00:00Z` | `high` | Result 已由 provider 覆盖；Total O/U 已由 provider 覆盖；Handicap 已由 provider 覆盖；Team Total 是当前主要缺口。 |
| 4 | Australia v Turkey | `2026-06-14T04:00:00Z` | `high` | Result 已由 provider 覆盖；Total O/U 已由 provider 覆盖；Team Total 是当前主要缺口。 |
| 5 | Germany v Curaçao | `2026-06-14T17:00:00Z` | `high` | Result 已由 provider 覆盖；Total O/U 已由 provider 覆盖；Handicap 已由 provider 覆盖；Team Total 是当前主要缺口。 |
| 6 | Netherlands v Japan | `2026-06-14T20:00:00Z` | `high` | Result 已由 provider 覆盖；Total O/U 已由 provider 覆盖；Team Total 是当前主要缺口。 |
| 7 | Ivory Coast v Ecuador | `2026-06-14T23:00:00Z` | `high` | Result 已由 provider 覆盖；Total O/U 已由 provider 覆盖；Team Total 是当前主要缺口。 |
| 8 | Sweden v Tunisia | `2026-06-15T02:00:00Z` | `high` | Result 已由 provider 覆盖；Total O/U 已由 provider 覆盖；Team Total 是当前主要缺口。 |

## Gate Snapshot

- import_status: `import_missing`
- hash_gate_status: `waiting_for_import`
- overlay_preview_status: `waiting_for_import`
- overlay_publish_preflight_status: `waiting_for_import`
- ready_for_manual_signature: `False`
- ready_for_publish_preflight: `False`
- overlay_publish_preflight_passed: `False`

Truthfulness: 该 workbench 只组织人工只读校验任务；不自动登录 TAB、不点击赔率、不修改 下注单、不发布正式 raw，也不生成新增下注金额。
