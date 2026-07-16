# Known gaps · ADP-S1-P01-T010

- **build_id = 源自排除哈希，非 git commit sha**：build_id/source_sha256 由 worker 源码的自排除哈希得出（可复现、可验证），但不直接等于部署 commit 的 git sha；若需 build↔commit 强绑定，可后续在部署脚本注入 git sha。
- **bundle hash = source hash（单文件 worker）**：worker 为单文件 + 静态 assets（媒体），故 bundle 与 source 同源；若将来打包为多文件 bundle，需区分两者。
- **FACT-014 逐 host 更强验证**：本任务已实证「同一时刻两域名 /build.json 一致」，但「每次部署后恒一致」仍建议纳入 CI/部署纪律（下游 S1 任务）。部署传播存在数秒竞态（workers.dev 曾短暂晚于自定义域名），传播后一致。
- **回滚为已记录命令、未实际执行回滚**（部署成功且基线完好，无需回滚）：回滚目标 455afd98 已记录，命令 `wrangler versions deploy 455afd98...`；纯加法、无 schema/数据变更，回滚安全。
- 独立验证：本报告以 `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION` 结束，PASS/FAIL 由独立上下文判定，实现者不自签。
