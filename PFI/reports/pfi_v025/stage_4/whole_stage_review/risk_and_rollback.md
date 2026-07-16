# Stage 4 Whole-stage Review — Risk and Rollback

- 余额、负债、持仓、市场价格和生产 FX 均为 `not_loaded`；七个核心 metric 为 `value=null`，不是财务零。
- 生产成本基础未选择，真实持仓估值未运行；Stage 5 公式/模型有效性尚未开始。
- 本轮浏览器证据仅使用本地 Chrome headless；未使用 Finder、网络、真实财务行或 App 安装。
- 回滚：仅 revert 本次 Stage 4 whole-review 本地提交并恢复 `in_progress`；保留三个 Phase 的不可变 evidence，不修改 raw、ledger、数据库、App 或远端。
