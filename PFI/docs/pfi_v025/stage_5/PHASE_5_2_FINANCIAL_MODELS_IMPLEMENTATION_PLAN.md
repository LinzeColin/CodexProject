# PFI v0.2.5 Stage 5 / Phase 5.2 财务模型与用户口径实施记录

## Run Contract

- 唯一范围：`S5-P2-T1..T4`。
- 唯一验收：`ACC-PFI-V025-S5-P52-FINANCIAL-MODELS`；该 ID 由项目治理分配，源 Roadmap 没有 Phase 级 Acceptance ID。
- 风险路由：`T2`，因为本轮修改财务公式、模型、参数与 evidence contract。
- 当前 Phase 只证明 deterministic capability 与 fail-closed 行为；不读取真实财务行，不完成真实数据不变量、敏感性或模型有效性。
- 明确不做：Phase 5.3、Stage 5 whole-stage review、Web/UI 源码、SQLite、Finder、网络、push、PFI.app 安装。

## 任务映射

| Task | 实施 | 验收证据 |
|---|---|---|
| `S5-P2-T1` | source-record + economic-event/type 双层去重；消费总流出、生活消费、投资入金、投资域内配置和费用分别计算；退款只抵消唯一链接原事件。 | `dual_consumption_reconciliation.json`；同一 payload contract 覆盖 homepage / consumption_page / report。 |
| `S5-P2-T2` | 净资产组成、现金滚动、投资重配置三项精确 Decimal 不变量；任一差异非零即 fail closed 且不发布值。 | `core_invariant_capability.json`。 |
| `S5-P2-T3` | 已实现/未实现/总净收益、费用/税费/FX/闲置现金拖累；日期感知 XIRR 使用 365 日基准和 bisection，多次符号变化时阻断潜在多根。 | `investment_formula_capability.json`。 |
| `S5-P2-T4` | 7/21/30/60/90/180/360 日外部现金流；内部转账单列；无事件窗口为 `filtered_empty/null`；保留 v0.2.2 taxonomy/tag 限制。 | `cashflow_taxonomy_contract.json`。 |

## 关键业务口径

- `消费总流出金额（用户定义活动口径） = 生活消费 + 投资资金流出 + 投资域内配置 + 金融费用 - 对应退款`。
- 投资资金流出表示家庭可用现金进入投资域；投资域内配置表示基金、黄金或证券买入。两者是不同活动阶段，分别展示，不得解释为两次净资产损失。
- 同一 source record 不重复；同一 `economic_event_id + event_type` 不重复；冲突重复、无链接退款或超额退款均失败关闭。
- 净资产、现金与投资重配置只有精确守恒才输出 contract-test value；当前生产来源仍不因此变为 ready。
- XIRR 需要至少一个负流和一个正流、至少两个日期、且聚合日期序列只有一次符号变化；否则标记 blocked。
- 分类限制固定为 L1 ≤ 12、单 L1 的 L2 ≤ 5、总 L2 ≤ 50、每条记录一个主分类；多维分析使用默认/自定义标签并保留停用历史。

## 验证与停止条件

- RED：新增两份测试因 `pfi_os.application.metrics.financial_models` 不存在而 collection error。
- 聚焦：`test_v025_stage5_dual_consumption.py`、`test_v025_stage5_financial_invariants.py`、Phase 5.1 formula registry。
- 回归：Stage 4 全部测试及 v0.2.2 consumption/interconnection/taxonomy 规则。
- 治理：formula hash rebuild、参数五载体一致、JSON/schema、renderer、完整检出 changed-scope governance 与 `git diff --check`。
- 停止：口径冲突、投资入金/买入无法解释的双计、XIRR 非唯一却返回结果、空输入伪零、载体参数冲突，或需要真实数据才能证明的结论被误写为 valid。

## 风险与回滚

- 风险集中在事件去重键、退款 lineage、投资活动阶段解释、XIRR 多根与零分母。
- 回滚整个 Phase 5.2 local commit 即可；本轮不修改 raw、ledger、数据库、真实财务行、生产 FX、GitHub 或 PFI.app。
