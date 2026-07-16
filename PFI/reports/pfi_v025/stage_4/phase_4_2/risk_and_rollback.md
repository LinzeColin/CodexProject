# Phase 4.2 风险与回滚

- 当前 `SRC-HOLDINGS`、`SRC-MARKET-PRICES`、`SRC-FX-SNAPSHOT` 均未加载，因此三个投资指标保持 `not_loaded/null`，不声明 production valuation 已完成。
- cost basis method 未从真实来源确认，production method 为 `null`；禁止猜测。
- 无 market-price staleness 阈值的权威参数，本阶段只强制 snapshot 不得晚于 valuation time，不虚构时效阈值。
- CNY 估值使用恒等汇率 1；其他币种必须具有方向明确且不晚于估值时间的 production FX snapshot。
- 回滚：撤销本地 Phase 4.2 提交并重建派生 read model；不修改 raw、ledger、数据库或用户输入。
- 停止边界：本轮停在 Phase 4.3 前，不执行五页面一致性、Stage 4 whole review、push 或 app reinstall。
