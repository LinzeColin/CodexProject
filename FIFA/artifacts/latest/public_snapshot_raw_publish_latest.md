# Public Snapshot Raw Publish

- generated_at: `2026-06-14T01:51:52.077469+10:00`
- status: `blocked_publish_preflight`
- ok: `False`
- board_id: `world_cup_matches`
- refresh_id: `20260614T015152+1000-public-snapshot`
- selected_snapshot_file: ``
- selected_snapshot_sha256: ``
- preview_raw_snapshot: `public_snapshot_import_preview_raw_latest.json`
- preview_raw_sha256: `5d36524a2e6184635f5cf6923728958e67a957d9949236336eb82e711b4a4438`
- approval_relative_path: `manual_verification/public_snapshot_import_approval.json`
- approval_file_sha256: ``
- published_raw_snapshot: ``
- published_raw_sha256: ``
- formal_raw_publish_performed: `False`
- full_automation_allowed: `False`
- raw_batch_manifest_written: `False`
- raw_gate_ready: `False`
- current_executable_new_stake_aud: `AUD 0`

Next action: 先导入有效 public snapshot，并让 approval 文件通过签名预检；发布失败时不要手工复制 preview raw 到正式 raw。

## Issues

| Field | Issue |
|---|---|
| `preflight` | public snapshot publish preflight has not passed |
| `raw_validation` | detail coverage 0/26 below 95% |
| `raw_validation` | full core coverage 0/26 below 90% for Result, Double Chance, Handicap, Total Goals Over/Under, Both Teams to Score, Draw No Bet |

## Raw Gate

- staged_raw_ready: `False`

No raw-gate blocking reasons recorded.

Truthfulness: Public snapshot publish is an explicit manual-signature path for Matches raw only. It does not prove live TAB page access, does not write a 5-board batch manifest, and does not allow betting execution.
