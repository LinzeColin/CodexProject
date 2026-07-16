# PFI v0.2.5 Stage 9 Phase 9.3 建议、复盘与导出

## Run Contract

- Phase：`V025-S9-P9.3`
- Tasks：`S9-P3-T1..T4`
- Acceptance：`ACC-PFI-V025-STAGE9-WHOLE-REVIEW`；本轮只形成 Phase candidate，不执行整阶段验收。
- Risk：`T3_FINANCIAL_DECISION_REVIEW_EXPORT`
- 产品实现提交：`0b2aa6677a61a600eb2596bd8b5d39ca32522084`
- 产品身份提交：`168666305c874d91ab8fd45e9f925e49928e7e63`
- 输入：immutable Phase 9.2 analysis snapshot、Phase 9.1 data-quality report、standing interim authorization。
- 明确不做：确定性财务建议、自动交易/直接下单、raw/DB 读写、公式/参数/模型值修改、Stage 9 whole-stage review、Stage 10、push、PFI.app install、production/final acceptance。

## 决策对象与人工复核

- 两个建议对象仅处理“待复核交易分类”和“补齐关键财务来源”，不生成买卖、订单或组合金额动作。
- 每个对象都包含 action、horizon、status、confidence dimensions、thesis、catalysts、evidence、counter evidence、invalidation conditions、risks、portfolio effect、model versions、source IDs 和 human-review-required。
- 人工 outcome 固定为接受、拒绝、延后、失效；每次转换追加 SHA-256 链式事件。接受只表示接受复核任务，不执行该动作本身，更不触发交易。
- 当前净资产、现金、投资继续 blocked；消费、现金流继续 partial。建议对象不能提升报告完整度，也不能跨 analysis snapshot 延用。

## 四格式同源导出

- HTML、PDF、CSV、Markdown 全部来自 `export_snapshot_hash=sha256:59c05ea7de7cd86265b4d470dec8899ce0c20a6ea9e3097d74025923bbcd42a1`。
- `export_manifest` 为每个文件记录 format、filename、content type、byte size、SHA-256 与 source snapshot hash。
- 正式 UI 下载前再次核对内嵌字节与 manifest；正式 loopback 浏览器已真实下载四个文件并逐一核对 hash。
- PDF 使用 ReportLab 确定性生成并内嵌 CJK 字体；`pypdf/pdfinfo` 绑定 snapshot metadata，`pdftoppm` 实际渲染 A4 PNG 后完成目视检查。

## 正式 UI 与安全边界

- 报告页保留 Phase 9.2 的 5 份报告、6 条公式、4 组敏感性、1 张模型卡与 7 个来源入口，再增加 2 个建议对象和 4 个导出入口。
- 人工复核状态只保存在本机 browser storage；reload 后事件链仍可验证。来源或 snapshot 漂移会使当前建议失效。
- 公开 snapshot、UI、四格式导出、截图和 sanitized trace 均不含财务金额、账户标识、本机绝对路径或 runtime token。
- 本轮 Finder、LaunchServices、GUI 文件操作、外部网络、push、App install 均为 0。

## Stop 与回滚

- Phase tasks 完成后 Stage 9 为 `12/12 candidate_complete`，但 `whole_stage_review=not_started`；下一工作单元只能是 `STAGE9-WHOLE-REVIEW`。
- standing authorization 不豁免独立整阶段审查、整改、复审、隐私或证据门禁。
- 回滚：依次 revert Phase 9.3 Evidence/治理提交、产品身份提交和实现提交；Phase 9.1/9.2 immutable snapshots 保持不变。
