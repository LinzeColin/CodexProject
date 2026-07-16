# Phase 4.3 风险与回滚

- 真实余额、负债、持仓、价格和生产 FX 仍未加载；当前七个核心指标为可解释 `not_loaded/null`，不是财务零。
- Stage 3 已证明事件集合和页面 snapshot hash，但未公开消费金额；双消费与投资流出公式属于 `S5-P2-T1`，本 Phase 不补造消费财务值。
- 净资产组成公式只定义 Stage 4 依赖关系；模型不变量与真实有效性验证仍属于 `S5-P2-T2` / Stage 5.3。
- `web/app/data_state.js` 与 runtime API 属于 release hash 闭包；已同步 source/embedded manifest 的派生 hash，但没有重装 canonical PFI.app，磁盘 App parity 仍留待 Stage 12。
- v0.2.4 `home/insights` 与旧状态数组保留为版本化兼容接口；v0.2.5 正式 surface/state 通过独立导出读取，避免破坏历史回归。
- Stage 4 仅完成 12/12 Phase tasks；whole-stage review、问题整改、复审和 Stage 5 transition acceptance 均未开始。

回滚：撤销本 Phase 单一提交，恢复 Phase 4.2 的 read-model/runtime/manifest 状态；统一 read model 和全部 Evidence 均可从既有 aggregate inputs 重建，不修改 raw、ledger、SQLite 或用户输入。
