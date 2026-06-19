# Public Snapshot Publish Preflight

- generated_at: `2026-06-14T01:52:01.454319+10:00`
- status: `waiting_for_snapshot_import`
- board_id: `world_cup_matches`
- approval_relative_path: `manual_verification/public_snapshot_import_approval.json`
- approval_file_sha256: ``
- selected_snapshot_file: ``
- selected_snapshot_sha256: ``
- preview_raw_snapshot: `public_snapshot_import_preview_raw_latest.json`
- preview_raw_sha256: `d980285c984bdcf4d4a5536f0dae9557f78ff4a29f695242b723f7de39794d46`
- match_count: `0`
- approved_by_user: `False`
- snapshot_publish_preflight_passed: `False`
- publish_compatible_with_snapshot_preview: `False`
- formal_publish_allowed: `False`
- current_executable_new_stake_aud: `AUD 0`

Next action: 先导入有效 public snapshot JSON，生成 preview raw 后再签名。

## Issues

| Field | Issue |
|---|---|
| `snapshot_import_preview_ready` | public snapshot preview is not ready |
| `approval_file` | missing manual_verification/public_snapshot_import_approval.json |

Truthfulness: 该预检只确认 public snapshot preview 与人工签名文件匹配；不证明 TAB 页面真实性，不写正式 raw，不生成下注金额。
