# Known gaps · ADP-S0-P02-T005

- **漂移只登记不修复**：DRIFT-FACT-006（board3 config ↔ worker 硬编码源）与 DRIFT-FACT-007（STATUS.yaml J5 vs R6）本任务只固定为漂移候选；修复属后续 S1/S2 来源真相任务与治理一致性任务（本任务禁止顺带重构）。
- **schema 为文件定义**：`schema_cloud.sql` 8 张 `cn_*` 表是仓库定义；线上 D1 实际 schema/行数/大小/延迟 = `UNVERIFIED_PRIVATE`（FACT-011），属 T006。
- **build↔线上一致性**：worker_cloud.js blob 是仓库真身；「线上部署的确为此 blob」需 T006 的 Cloudflare 只读导出证实（FACT-014）。
- **D1 database_id**：记录于 wrangler_cloud.jsonc（已在公开仓库），非本任务新增暴露；账户级密钥/令牌未采集、未记录。
- 独立验证：本报告以 `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION` 结束，PASS/FAIL 由独立上下文判定，实现者不自签。
