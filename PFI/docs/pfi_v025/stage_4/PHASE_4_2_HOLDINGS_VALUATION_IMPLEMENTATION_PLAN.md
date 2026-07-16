# Phase 4.2 持仓、成本与估值实施记录

- 唯一范围：`V025-S4-P4.2` / `S4-P2-T1..T4`。
- 唯一验收：`ACC-PFI-V025-S4-P42-HOLDINGS-VALUATION`。
- 当前真实状态：`SRC-HOLDINGS`、`SRC-MARKET-PRICES`、`SRC-FX-SNAPSHOT` 均为 `not_loaded`；投资市值、成本基础和未实现损益均保持 `value=null`。
- 持仓数量：只接受 `SRC-HOLDINGS` 的显式 snapshot lineage；交易存在不构成持仓数量证明，不按交易推断持仓。
- 成本基础：`acquisition_cost_ex_fees + capitalized_fee_total`；method 必须显式选择 `source_reported`、`specific_identification`、`fifo` 或 `weighted_average`，缺失时禁止计算。
- 估值：价格与 FX snapshot 均不得晚于 `valuation_as_of`；非 CNY 必须绑定 `BASE_TO_CNY`，CNY 仅使用恒等汇率 1；全部使用精确 `Decimal` 且本阶段不做舍入。
- 数据边界：不读取或修改私有持仓行、账户、数据库；不启用网络；不提升 legacy FX reference；不使用 financial fixture；tracked evidence 仅含 aggregate status。
- 当前交付：可验证的 schema、纯函数能力合同、fail-closed investment read model 与只读证据。
- 明确未完成：Phase 4.3 五页面同 hash、Stage 4 整阶段审查、production acceptance、GitHub push、canonical app reinstall。
- 回滚：撤销本地 Phase 4.2 提交并重建派生 read model；raw/ledger/用户输入不受影响。
