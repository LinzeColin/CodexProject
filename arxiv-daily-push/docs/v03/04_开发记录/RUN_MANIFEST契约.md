# Run Manifest 契约 —— 这一次实际上做了什么

每次 `adp run`（含手动、定时、云端 Worker）必须追加一行 JSON 到 `data/run_manifests.jsonl`，用户中心与系统页由它自动生成——**系统里没有一句手写状态**。

```json
{
  "run_id": "2026-07-14T0630+10:00",
  "trigger": "launchd|manual|cloud_worker",
  "result": "正常|降级|弃权|失败|未运行",
  "side_effects_authorized": false,
  "counts": {"扫描": 214, "过门": 37, "选中": 1, "讲义": 1, "到期复习": 4, "已交付": 0},
  "降级项": ["openalex_enrich_timeout"],
  "弃权原因": null,
  "config_versions": {"阈值": "v0.3", "数据": "sqlite-2026-07", "合同": "V7.2", "模板": "lesson-v1"},
  "artifacts": ["lessons/2026-07-14.json"],
  "duration_seconds": 221
}
```

规则：
- 五态必填；「降级」必须列出降级项；「弃权」必须给原因与最高分。
- `side_effects_authorized=false` 时 counts.已交付 必须为 0（不变量 5 的落地检查）。
- 云端 Worker 的轻任务同样落行（trigger=cloud_worker），本机每日汇拢。
- 徽章/首页状态点只允许读取最近一行的 result 渲染。
