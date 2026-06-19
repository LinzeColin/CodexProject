# Provider Manual Team Total Overlay Publish

- generated_at: `2026-06-14T02:04:59.689199+10:00`
- status: `blocked_overlay_publish_preflight`
- ok: `False`
- board_id: `world_cup_matches`
- market_family: `Team Total Goals Over/Under`
- refresh_id: `20260614T020459+1000-manual-overlay`
- provider_refresh_id: `20260613T135338Z-provider-50380e82`
- manual_import_sha256: ``
- overlay_raw_snapshot: `provider_manual_team_total_overlay_raw_latest.json`
- overlay_raw_sha256: `bf706383775545e7f8888b801a29fa0d0dc6904e38d43834732bdb1782baab40`
- overlay_event_count: `0`
- overlay_row_count: `0`
- approval_relative_path: `manual_verification/provider_team_total_overlay_approval.json`
- approval_file_sha256: ``
- published_raw_snapshot: ``
- published_raw_sha256: ``
- formal_raw_publish_performed: `False`
- full_automation_allowed: `False`
- raw_batch_manifest_written: `False`
- raw_gate_ready: `False`
- current_executable_new_stake_aud: `AUD 0`

Next action: 先完成 Team Total CSV 导入、overlay raw 预览和人工签名预检；发布失败时不要手工复制 overlay raw 到正式 raw。

## Issues

| Field | Issue |
|---|---|
| `preflight` | manual Team Total overlay publish preflight has not passed |
| `raw_validation` | detail coverage 0/26 below 95% |
| `raw_validation` | full core coverage 0/26 below 90% for Result, Double Chance, Handicap, Total Goals Over/Under, Both Teams to Score, Draw No Bet |

## Raw Gate

- staged_raw_ready: `False`

No raw-gate blocking reasons recorded.

Truthfulness: Manual Team Total overlay publish is an explicit signature-gated path for Matches raw only. It does not prove live TAB page access, does not write a 5-board batch manifest, and does not allow betting execution.
