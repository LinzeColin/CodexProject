# TAB FIFA KPI Status

Updated: 2026-06-14 06:04 AEST

## Provider KPI

- Source artifact: `artifacts/latest/provider_kpi_latest.json`
- Coverage artifact: `artifacts/latest/odds_provider_coverage_latest.json`
- Provider raw manifest: `artifacts/latest/odds_provider_raw_latest.json`
- PDF: `artifacts/latest/provider_kpi_latest.pdf`
- Alternate plan artifact: `artifacts/latest/provider_alternate_plan_latest.json`
- Alternate plan PDF: `artifacts/latest/provider_alternate_plan_latest.pdf`
- Alternate probe evidence: `artifacts/latest/provider_alternate_probe_evidence_latest.json`
- Provider config doctor: `artifacts/latest/provider_config_doctor_latest.json`
- Provider config doctor PDF: `artifacts/latest/provider_config_doctor_latest.pdf`
- Fallback verification artifact: `artifacts/latest/provider_fallback_verification_latest.json`
- Fallback verification PDF: `artifacts/latest/provider_fallback_verification_latest.pdf`
- Manual verification template: `artifacts/latest/provider_manual_verification_template_latest.csv`
- Manual pair template: `artifacts/latest/provider_manual_pair_template_latest.csv`
- Manual next-batch pair template: `artifacts/latest/provider_manual_next_batch_pair_template_latest.csv`
- Manual verification status: `artifacts/latest/provider_manual_verification_status_latest.json`
- Manual verification PDF: `artifacts/latest/provider_manual_verification_status_latest.pdf`
- Manual hash gate: `artifacts/latest/provider_manual_hash_gate_latest.json`
- Manual hash gate PDF: `artifacts/latest/provider_manual_hash_gate_latest.pdf`
- Manual overlay preview: `artifacts/latest/provider_manual_overlay_preview_latest.json`
- Manual overlay publish preflight: `artifacts/latest/provider_manual_overlay_publish_preflight_latest.json`
- Manual overlay publish: `artifacts/latest/provider_manual_overlay_publish_latest.json`
- Public snapshot import: `artifacts/latest/public_snapshot_import_status_latest.json`
- Public snapshot preview raw: `artifacts/latest/public_snapshot_import_preview_raw_latest.json`
- Public snapshot approval template: `artifacts/latest/public_snapshot_import_approval_template_latest.json`
- Public snapshot publish preflight: `artifacts/latest/public_snapshot_import_publish_preflight_latest.json`
- Public snapshot raw publish: `artifacts/latest/public_snapshot_raw_publish_latest.json`
- Refresh id: `20260613T194716Z-provider-2fec0bef`
- Overall score: `61.50%`
- Current executable new stake: `AUD 0`
- Formal publish allowed: `false`
- Full automation allowed: `false`

## Latest Coverage

| Market | Coverage |
|---|---:|
| Result | 64/64 |
| Handicap | 46/64 |
| Total Score O/U | 51/64 |
| Both Teams to Score | 14/64 |
| Double Chance | 11/64 |
| Draw No Bet | 12/64 |
| Team Total Score O/U | 0/64 |

## Credit

- Reported used: `299`
- Reported remaining: `201`
- Latest request cost: `7`
- Inferred monthly limit: `500`
- Remaining ratio: `40.20%`

Credit note: coverage improved, but remaining credits are now only `201`. The next recommended batch is estimated at `4-7` credits, which would take the account below the `200` credit reserve floor. The provider command center therefore sets `can_run_provider_batch=false` and routes the next action to Team Total manual verification or OpticOdds official access.

## Current Gap

Primary gap: `Team Total Score O/U 覆盖: 0/64`.

## Provider Config Doctor

- Status: `ready`
- Local env exists: `true`
- The Odds API key present: `true`，真实 key 不写入产物。
- OpticOdds key present: `false`，当前未在本机 local env 检测到可用 key。
- Sports discovery enabled: `true`
- Requested sports: `soccer_fifa_world_cup`
- Recommended sports: `soccer_fifa_world_cup`
- Known invalid / legacy sports: none
- Event-market probe limit: `0`
- Current executable new stake: `AUD 0`
- Next action: 配置可用；下一步执行 matches 主盘口刷新或 Team Total 人工下一批。

## Public Snapshot Raw Publish

- Status: `blocked_publish_preflight`
- OK: `false`
- Formal raw publish performed: `false`
- Raw batch manifest written: `false`
- Current executable new stake: `AUD 0`
- Command: `python3 publish_public_snapshot_raw.py`
- Next action: 导入有效 Matches JSON 并保存匹配的 `manual_verification/public_snapshot_import_approval.json` 后再运行显式 publish 命令。

## Fallback Verification Queue

- Status: `provider_blocked_manual_verification_required`
- Queue: `64` Team Total candidates
- High priority: `51`
- Provider blocker: `opticodds_access_denied_1010`
- Current executable new stake: `AUD 0`
- Next action: 对 high priority 候选做 TAB 人工 Team Total 校验，或向 OpticOdds 申请官方允许访问/白名单。

## Manual Verification Import

- Status: `import_missing`
- Template: `provider_manual_verification_template_latest.csv`
- Template rows: `64`
- Pair template: `provider_manual_pair_template_latest.csv`
- Pair template rows: `128`
- Next-batch pair template: `provider_manual_next_batch_pair_template_latest.csv`
- Next-batch pair rows: `16`
- Import target: `manual_verification/provider_team_total_manual_verification.csv`
- Complete events: `0/64`
- High priority complete: `0/51`
- Invalid rows: `0`
- Current executable new stake: `AUD 0`
- Next action: 下载 CSV 模板，人工只读 TAB 后保存到 `manual_verification/provider_team_total_manual_verification.csv`，再重建状态；完成后也只进入 hash gate。

## Manual Verification Workbench

- Status: `waiting_for_first_batch`
- Operator cockpit: `TT-001`
- Batch count: `9`
- Next batch: `TT-001`
- Next batch event count: `8`
- Next-batch pair rows required: `16`
- Remaining events: `64`
- Remaining high priority: `51`
- Pair template rows: `128`
- Next-batch pair template: `provider_manual_next_batch_pair_template_latest.csv`
- Next-batch pair rows: `16`
- Field checklist: `11`
- Workflow steps: `5`
- Import quality status: `waiting_for_manual_rows`
- Missing events: `64`
- Next-batch quality: `missing_rows=8`
- Missing directions: `over=8` / `under=8`
- Publish status: `blocked_until_manual_import_and_signature`
- Can publish now: `false`
- Current executable new stake: `AUD 0`
- Next action: 下载 `provider_manual_next_batch_pair_template_latest.csv`，对 `TT-001` 的 8 场逐行填写 Over/Under；保存到 `manual_verification/provider_team_total_manual_verification.csv` 后重建状态，仍保持 stake AUD 0。

### Manual Intake Contract

- Current batch: `TT-001`
- Template CSV: `provider_manual_next_batch_pair_template_latest.csv`
- Import target: `outputs/manual_verification/provider_team_total_manual_verification.csv`
- Rebuild command: `TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py`
- Current state: missing `64` / partial `0` / invalid `0` / complete `0` / next-batch pair rows `16`
- API exposure: `/api/status.provider_manual_workbench.manual_intake_contract` and `/api/status.provider_command_center.team_total_manual.manual_intake_contract`
- Homepage exposure: `人工校验导入状态 -> TT-001 Intake Contract` with copy buttons for import target and rebuild command.
- Acceptance: next batch has no `missing_rows` or `invalid_rows`; import invalid count `0`; hash gate and overlay status move out of `waiting_for_import`; formal publish remains `false` until signature and explicit publish; stake remains `AUD 0`.
- Forbidden: automatic betting, clicking odds, adding to Bet Slip, modifying wagering ticket, bypassing TAB access control.

## Manual Hash Gate

- Status: `waiting_for_import`
- Complete events: `0/64`
- Manual import sha256: pending
- Ready for manual signature: `false`
- Approved by user: `false`
- Publish-compatible with provider raw: `false`
- Current executable new stake: `AUD 0`
- Boundary: 该 gate 只证明人工导入 CSV 规范化内容可复核，不证明 TAB 盘口真实性，不替代 provider raw publish approvals。

## Manual Overlay Publish

- Status: `blocked_overlay_publish_preflight`
- OK: `false`
- Overlay events: `0/64`
- Formal raw publish performed: `false`
- Raw batch manifest written: `false`
- Current executable new stake: `AUD 0`
- Command: `python3 publish_provider_manual_overlay.py`
- Next action: 填写 Team Total 人工 CSV 并保存匹配的 `manual_verification/provider_team_total_overlay_approval.json` 后再运行显式 publish 命令。

## Alternate Markets Plan

- Status: `in_progress`
- Operational decision: `alternate_probe_plus_team_total_manual`
- Persistent evidence: `provider_alternate_probe_evidence_latest.json`
- Event-market sample: `14`
- Team Total available sample: `0`
- Available sample counts: `spreads=14`、`totals=14`、`btts=14`、`double_chance=11`、`draw_no_bet=12`、`h2h=14`
- Probe queue: `50`
- Fallback queue: `64` Team Total candidates.
- Recommended next batch: `1`
- Estimated next batch credit range: `4-7` including the required primary refresh.
- Credit runway status: `next_batch_would_cross_reserve`; reserve floor `200`, current remaining `201`, next-batch worst case `194`, safe next batch count `0`.
- Recommended command:

```bash
python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 1 --event-odds-limit 1 --event-odds-markets double_chance,draw_no_bet,btts
```

Do not execute this command while `credit_runway.status=next_batch_would_cross_reserve`; it remains in the plan for traceability, not as the current action.

Latest Total O/U coverage is preserved at `51/64`. The no-increment batch (`20260613T190633Z-provider-b35cbe30`, cost `5`, queue stayed `60`) exposed that prior credit estimates excluded the primary refresh and that event selection could repeat low-yield events. The system now prefers `provider_alternate_plan_latest.json.next_probe_queue`, skips prior `event_odds` and prior event-market probes, orders value-support markets by scarcity (`double_chance,draw_no_bet,btts`), and estimates next-batch total cost as `4-7` credits including the primary refresh. The latest refresh (`20260613T194716Z-provider-2fec0bef`, cost `7`) moved event-market evidence to sample `14`, BTTS `14/64`, Double Chance `11/64`, Draw No Bet `12/64`, and queue `53 -> 50`. Fourteen TAB event-market samples still exposed `0` Team Total market keys, so Team Total remains OpticOdds official-access/whitelist or TAB manual final verification from `TT-001`. Because remaining credits are now `201`, the command center blocks further API batch execution before the next batch would cross the `200` reserve floor.

Latest local verification in this run:

- `python3 -m py_compile tab-research-pipeline/scripts/build_downloads_app_entry.py tab-research-pipeline/scripts/tab_fifa_app_server.py tab-research-pipeline/tests/test_pipeline.py` -> OK.
- Focused app/manual contract tests -> `Ran 3 tests OK`.
- Full suite `python3 -m unittest tab-research-pipeline.tests.test_pipeline` -> `Ran 205 tests in 13.329s OK`.
- API smoke `/api/status.provider_command_center` -> provider alternate `in_progress`, refresh `20260613T194716Z-provider-2fec0bef`, probe queue `50`, batch `1`, estimated credit `4-7`, remaining credits `201`, credit runway `next_batch_would_cross_reserve`, `can_run_provider_batch=false`, TT batch `TT-001`, stake `AUD 0`, formal/full automation `false`.
- API smoke `/api/status.provider_manual_workbench` -> `manual_intake_contract` returns `TT-001`, import target, rebuild command, missing `64`, next-batch pair rows `16`, stake `0`.
- Browser smoke desktop `1280px` and mobile `390px` -> Provider 采集控制台 visible, `Credit Runway` visible, `下一批会破保底` visible, `TT-001 Intake Contract` visible, import target and rebuild command visible, Team Total `0/64`, stake `AUD 0`, page overflow `0`, console error `0`.
- Copy-command smoke -> Clipboard-blocked browser path falls back to a clear manual-copy message without console errors.
- LaunchAgent smoke -> `/Users/linzezhang/Library/LaunchAgents/com.linzezhang.tab-fifa-research.plist` has `KeepAlive=true`; `/api/health` returns OK.
- `git diff --check` -> OK.
- Tracked secret scan for the known The Odds API key and key-like env assignments -> no hits in tracked files.

Current raw/API gates still report formal publish `false`, full automation `false`, and stake `AUD 0`.

Safety boundary: this KPI is research/report only. It does not allow automatic betting, TAB odds clicking, Bet Slip mutation, or formal raw publication without manual TAB verification.
