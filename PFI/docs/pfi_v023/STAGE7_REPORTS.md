# PFI v0.2.3 Stage 7 Reports

## Stage 7 Phase 7.1 报告合同

Phase 7.1 只建立报告中心的合同层，不生成净资产、现金余额、投资市值或消费结构正式报告。

本 phase 覆盖：

- `T7.1.1` 定义报告 schema。
- `T7.1.2` 定义公式 registry。
- `T7.1.3` 定义参数展示。
- `T7.1.4` 定义 blocked/partial 状态。

报告合同要求每个报告至少包含：

- 结论。
- 数据范围。
- 样本量。
- 核心指标。
- 公式。
- 参数。
- 数据来源。
- evidence hash。
- 缺失数据。
- 异常项。
- 下一步动作。

状态合同：

- `complete`：输入完整且可生成正式结论。
- `partial`：有真实输入，但缺少结构化明细或一部分输入。
- `blocked`：关键 read model 未挂载，禁止生成完整财务结论。
- `outdated`：输入快照过期。
- `review_required`：需要人工复核。

当前 Stage 7 Phase 7.1 基于 Stage 6 核心 read model：

- 真实输入：`MetaDatabase/PFI`，4 个原始 Alipay 文件，8815 条规范化交易。
- `read_model_hash=sha256:b5616d2c2ba17a73fb101d0c184d65c6ebbea904287074f1a9b1965dcd49b675`。
- `as_of=2026-06-03`。

当前报告状态：

- 净资产报告：`blocked`，未挂载账户余额与持仓 read model。
- 现金余额报告：`blocked`，未挂载账户余额 read model。
- 投资市值报告：`blocked`，未挂载持仓市值 read model。
- 消费结构报告：`partial`，已有真实生活消费和消费总流出输入，但缺少分类结构明细。
- 数据质量报告：`partial`，可解释当前阻断项。

公式 registry 当前覆盖：

- 净资产。
- 现金余额。
- 投资市值。
- 生活消费。
- 消费总流出。
- 数据健康。

## Stage 7 Phase 7.2 核心报告

Phase 7.2 只生成四个核心报告：

- 净资产报告。
- 现金余额报告。
- 投资市值报告。
- 消费结构报告。

报告输入仍只来自 Stage 6 核心 read model，不新增数据源，不补造账户余额、现金余额、持仓市值或消费分类结构。

当前报告结论：

- 净资产报告：`blocked`，未挂载账户余额与持仓 read model，禁止生成完整结论。
- 现金余额报告：`blocked`，未挂载账户余额 read model，禁止显示 `CNY 0.00`。
- 投资市值报告：`blocked`，未挂载持仓市值 read model，禁止显示 `CNY 0.00`。
- 消费结构报告：`partial`，真实输入为生活消费 `CNY 1,545,600.44`、消费总流出 `CNY 1,727,278.37`，数据范围 `2022-06-06` 至 `2026-06-03`，样本量 8815 条交易和 4 个原始文件；因缺少分类结构、商户、预算和异常消费明细，不能生成完整消费结构结论。

Phase 7.2 证据：

- `PFI/reports/pfi_v023/stage_7/phase_7_2/core_reports.json`
- `PFI/reports/pfi_v023/stage_7/phase_7_2/core_reports_page_model.json`
- `PFI/reports/pfi_v023/stage_7/phase_7_2/screenshots/core_reports.png`

Phase 7.3 数据质量与调参未执行。
Stage 7 whole-stage review 未执行。
GitHub main upload 未执行。
