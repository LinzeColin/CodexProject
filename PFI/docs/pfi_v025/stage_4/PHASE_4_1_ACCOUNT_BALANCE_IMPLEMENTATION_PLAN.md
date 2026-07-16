# PFI v0.2.5 Stage 4 Phase 4.1 账户与余额实现合同

## 唯一目标

- Tasks：`S4-P1-T1..T4`
- Acceptance：`ACC-PFI-V025-S4-P41-ACCOUNT-SNAPSHOT`（project governance assigned）
- 结果范围：账户/负债快照 schema、现金对账、coverage/status、homepage/accounts 同源 API。
- 停止边界：不进入 Phase 4.2 持仓/成本/价格/FX/估值，不进入 Phase 4.3 五页面整合，不执行 Stage 4 whole review。

## 真实输入状态

Phase 4.1 只读取已跟踪的 Stage 2 aggregate source manifest，不读取私有财务行或 operational database。当前：

- `SRC-ACCOUNT-BALANCES = not_loaded`
- `SRC-LIABILITIES = not_loaded`
- `SRC-TRANSACTIONS-ALIPAY = ready`，但其角色明确为 transaction history，不构成 opening/closing balance 或 liability proof。

因此当前 `account_assets_cny`、`cash_balance_cny`、`liabilities_cny` 全部必须 `value=null`；不得从交易流水倒推余额，不得使用 financial fixture fallback。

## Schema 与公式

`account_snapshot.schema.json` 要求 snapshot kind、opaque account ref、source id、currency、Decimal string opening/closing、coverage、data_as_of、record count 与 sha256 source hash。公开 evidence 只保留 aggregate 状态，不输出 account ref 或财务值。

`FORM-PFI-008`：

```text
expected_closing_balance = opening_balance + confirmed_net_flows + adjustments
discrepancy = observed_closing_balance - expected_closing_balance
```

金额使用有限 `Decimal`；tolerance=`0`。只有 lineage 完整且 discrepancy 精确为 0 时状态可为 `ready`；差异为 `reconciliation_failed`，缺证据为对应 non-ready 状态，两者均不得输出财务值。`confirmed_zero` 只允许完整 evidence 支持。

## 验收与证据

- 快照 schema 为 Draft 2020-12，金额不是 binary float。
- 当前 2/2 required sources 的 `not_loaded` 状态与 Stage 2 manifest 一致。
- 当前 3/3 metrics 为 non-ready/null，no-false-zero audit 通过。
- homepage/accounts 的 metrics 与 `read_model_hash` 完全一致。
- contract unit values 只验证 Decimal 公式和 fail-closed 分支，不构成真实财务或 production acceptance。
- Evidence Pack、privacy scan、回归和 governance validation 通过后，本 Phase 才可标记 `candidate_pass`。

## 风险与回滚

当前缺真实余额与负债快照，不能计算真实现金、资产、负债或净资产。Phase 4.2/4.3 和 Stage 4 pass 仍依赖后续真实持仓/价格/FX 与整体同源验证。回滚只需 revert 本 Phase 本地提交；read model 为可重建派生层，无真实数据、数据库、App 或远端回滚动作。
