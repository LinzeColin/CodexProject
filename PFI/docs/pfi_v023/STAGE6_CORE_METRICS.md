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

Phase 6.2 UI wiring 未执行。
Phase 6.3 cross-page consistency 未执行。
Stage 6 whole-stage review 未执行。
GitHub main upload 未执行。
