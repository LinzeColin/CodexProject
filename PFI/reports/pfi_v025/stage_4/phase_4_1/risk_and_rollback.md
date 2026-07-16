# Phase 4.1 风险与回滚

- 当前账户余额与负债 source-level snapshot 均 `not_loaded`；本 Phase 只证明 fail-closed 合同，不证明任何真实财务值。
- 交易流水不可作为 opening/closing balance、liability 或 net-worth 证据，代码和 evidence 均禁止这种推断。
- 合同测试使用小型 Decimal 数值验证公式；这些值不是 financial fixture fallback，也不进入 tracked financial evidence。
- 本 Phase 只覆盖 homepage/accounts；投资、消费、报告五页面整体一致性属于 Phase 4.3。
- 回滚：revert Phase 4.1 本地提交并重建派生 read model；不触碰 Stage 2/3 immutable evidence、真实数据、数据库、App 或远端。
