# Public Raw Snapshot Import

- generated_at: `2026-06-14T01:52:01.453077+10:00`
- status: `waiting_for_snapshot_import`
- board_id: `world_cup_matches`
- import_dir: `manual_verification/public_raw_snapshots`
- selected_snapshot: ``
- selected_snapshot_sha256: ``
- preview_raw_snapshot: `public_snapshot_import_preview_raw_latest.json`
- preview_raw_sha256: `d980285c984bdcf4d4a5536f0dae9557f78ff4a29f695242b723f7de39794d46`
- match_count: `0`
- formal_publish_allowed: `False`
- full_automation_allowed: `False`
- current_executable_new_stake_aud: `AUD 0`

Next action: 把公开导出的 World Cup Matches raw JSON 放入 manual_verification/public_raw_snapshots/ 后重新生成 app；该入口只生成研究预览，不替代 TAB 最终人工校验。

## Market Coverage

| Market | Covered Matches |
|---|---:|
| - | 0 |

## Issues

| Field | Issue |
|---|---|
| `import_dir` | 请把 JSON 快照放到 manual_verification/public_raw_snapshots/，文件名保持 .json。 |

Truthfulness: 该入口只接收用户或第三方工具导出的公开 raw JSON 并生成研究预览；不能证明 TAB 页面真实性，不替代授权 API raw、TAB 人工最终校验、hash/signature gate。
