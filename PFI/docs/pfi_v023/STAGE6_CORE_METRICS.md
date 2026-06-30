# PFI v0.2.3 Stage 6 Core Metrics

## Stage 6 Phase 6.1 read model adapter

Phase 6.1 建立核心指标 read model adapter，只负责从当前 checkout 内的真实 `MetaDatabase/PFI` 派生机器可读指标状态。

当前真实输入：

- `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv`
- `MetaDatabase/PFI/alipay_daily/processed/alipay_import_manifest.json`
- `MetaDatabase/PFI/alipay_daily/raw/` 下 4 个原始 Alipay 文件

当前可展示指标：

- 生活消费：来自真实 Alipay 交易，口径为生活消费流出减退款，`as_of=2026-06-03`
- 消费总流出：来自真实 Alipay 交易，口径为生活消费、基金申购、资产买入流出减退款，`as_of=2026-06-03`
- 数据健康：来自导入清单的真实交易记录数，`as_of=2026-06-03`

当前阻塞指标：

- 净资产：未挂载账户余额与持仓 read model
- 现金余额：未挂载账户余额 read model
- 投资市值：未挂载持仓市值 read model

阻塞指标不显示 `CNY 0.00`，只返回 Stage 2 状态机中的中文阻塞状态。

## Stage 6 Phase 6.2 页面接入

Phase 6.2 将 Phase 6.1 read model 输出接入页面级 view model，覆盖：

- 首页核心指标：净资产、现金余额、投资市值、生活消费、消费总流出、数据健康
- 账户与资产：净资产、现金余额、数据健康
- 投资管理：投资市值、数据健康
- 消费管理：生活消费、消费总流出、数据健康

页面卡片规则：

- `ready` 或 `confirmed_zero` 指标必须带 `source`、`as_of`、`evidence_hash` 才显示数值。
- 阻塞指标显示中文原因和 Stage 2 状态，不显示 `CNY 0.00`。
- 当前净资产、现金余额、投资市值仍为 `not_mounted`，等待真实账户余额与持仓 read model。
- 当前生活消费、消费总流出、数据健康来自 Phase 6.1 的真实 `MetaDatabase/PFI` read model。

## Stage 6 Phase 6.3 指标一致性

Phase 6.3 建立首页、账户与资产、报告 projection 的同源一致性矩阵。

同源规则：

- 首页、账户与资产、报告 projection 均使用 Phase 6.1 `core_metrics.json` 的同一个 `read_model_hash`。
- 页面指标不得改写 `status`、`value`、`source`、`as_of`、`evidence_hash`。
- 报告 projection 直接承接核心 read model 的全部 6 个指标。
- 账户与资产页面只展示净资产、现金余额、数据健康，但这 3 个指标仍必须与核心 read model 完全一致。

口径说明：

- 现金余额：来自真实账户余额 read model；未挂载时只显示中文阻塞状态。
- 投资市值：来自真实持仓市值 read model；未挂载时只显示中文阻塞状态。
- 生活消费：真实 Alipay 交易中的生活消费流出减退款。
- 消费总流出：真实 Alipay 交易中的生活消费、基金申购、资产买入流出减退款。

错误状态截图位于 `PFI/reports/pfi_v023/stage_6/phase_6_3/screenshots/error_states.png`，用于证明未挂载数据源时所有页面显示中文阻塞状态且不显示 `CNY 0.00`。

Stage 6 whole-stage review 未执行。
GitHub main upload 未执行。
