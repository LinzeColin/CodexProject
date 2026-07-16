# Known gaps · ADP-S0-P01-T002

- 历史输入 zip（`historical_inputs/*.zip`，共约 10MB）**不整包提交进本仓库**：遵守低 token/无冗余二进制契约。归档以 sha256 指纹 + `ARCHIVE_INDEX.csv` 状态在 `ARCHIVED_NOT_CANONICAL.md` 登记，物理留存于 Owner 侧最终包与 `LinzeColin/AgentDatabase`（私有 Release）。需要细节时按需解压查阅，按 `CONFLICT_LEDGER.csv` 裁决。
- 本任务只**降级并裁决**旧方向，不删除、不改写任何历史材料。
- 冲突账本覆盖已知 14 条方向；若后续从历史材料读到新的冲突主张，应新增 CL-0NN 行并按 `PRECEDENCE.md` 裁决，而非在历史材料与本轮之间反复摇摆。
- 私有 Cloudflare 事实 FACT-011..015（D1 schema/行数/大小/延迟、R2 状态、套餐/账单、build↔双域名一致、私有分支）仍为 `UNVERIFIED_PRIVATE`，由 **S0-P02（T004–T007）** 补齐；本任务未涉及。
- 独立验证：本报告以 `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION` 结束，PASS/FAIL 由独立上下文判定，实现者不自签。
