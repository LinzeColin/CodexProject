# PFI v0.2.5 Stage 3 Phase 3.2 实施合同

## 唯一目标

- Contract：`PFI-V025-STAGE3-PHASE32-NORMALIZED-EVENT`
- Acceptance：`ACC-PFI-V025-S3-P32-NORMALIZED-EVENT`
- Tasks：`S3-P2-T1..T4`
- 风险层级：`T3_FINANCIAL_EVENT_POLICY_PRIVACY`

本 Phase 只建立标准化交易、Interconnection Group、Economic Event 影响策略和统一 Ledger Event 合同。完成状态只能是 `candidate_pass`；Stage 3 保持 `in_progress`，Phase 3.3 的真实重复导入、对账、差异定位与 Stage 3 整体验收均未开始。

## 合同决策

1. `NormalizedTransaction` 强制包含正数 canonical decimal `amount`、ISO 4217 三字母 `currency`、显式 `direction`，以及 `transaction_time`、`posted_at`、`effective_at`、`imported_at` 四类带时区时间。
2. `normalized_transaction_id` 由 source id、raw record id、source record hash 与 normalization version 内容寻址生成；同一输入稳定，不同 source record provenance 不复用 identity。
3. Interconnection 只允许两条可解释规则：显式 `link_reference` 精确相等，或没有显式链接时保持 singleton。禁止按金额相同、时间接近、来源名称或 provider label 猜测归组。
4. `EconomicEvent` 保存 raw → normalized → group 的完整 lineage；event time 固定取组内最早 `transaction_time`，event type 必须存在于显式 policy，未知类型 fail-closed 为 `review_required_no_publication`。
5. 影响 flags 区分净资产、现金、生活消费、用户定义活动总流出、投资配置、退款 offset 与 fee/tax 独立事件要求。投资入金、基金/黄金申购与投资买入进入活动总流出，但不进入生活消费。
6. `LedgerEvent` 不跨 posting 聚合金额；每个 normalized transaction 保留独立 amount/currency/direction/account_ref posting，支持多币种链路而不制造错误汇总值。
7. `idempotency_key` 对 Economic Event lineage、policy、影响 flags 与排序后的 postings 做 canonical JSON SHA-256；本 Phase 只证明键的确定性，不执行 Phase 3.3 的真实重复导入或持久化去重。

## 数据与隐私边界

- 不读取、复制、解析或修改真实财务记录、账户、持仓、金额、SQLite 或 source files。
- 单元测试使用最小 typed contract values，只验证 schema/rule behavior；这些值不是财务 fixture fallback、真实数据验证、E2E 或 production acceptance。
- Evidence 只记录 schema/policy/hash、flags、测试结果、脱敏 lineage 形状和零计数；不记录真实金额、账户、link reference、绝对私有路径或 credential。
- 不使用 Finder，不联网，不 push，不安装 App。

## 交付物

- `PFI/config/schemas/v025/normalized_transaction.schema.json`
- `PFI/config/schemas/v025/interconnection_group.schema.json`
- `PFI/config/schemas/v025/economic_event.schema.json`
- `PFI/config/schemas/v025/ledger_event.schema.json`
- `PFI/config/event_types/v025_phase_3_2_event_policy.json`
- `PFI/src/pfi_os/domain/economic_events.py`
- `PFI/src/pfi_os/application/economic_event_pipeline.py`
- `PFI/tests/test_v025_stage3_interconnection.py`
- `PFI/reports/pfi_v025/stage_3/phase_3_2/*`

## 验证

1. RED：缺少 Phase 3.2 application pipeline 时测试收集失败。
2. Focused：标准化字段、确定性 identity、可解释归组、事件 flags、完整 lineage、未知事件 fail-closed、逐笔 postings 与确定性 idempotency key。
3. Compatibility：Phase 3.1 与 Stage 2 不可变/功能合同保持通过，不修改它们的 evidence 或 current-state 断言。
4. 安全：Evidence 不含私有路径、真实金额、账户标识、link reference、credential、Finder、source mutation 或 fake fallback。
5. 治理：project governance、changed-scope semantic sync 与 renderer 必须为零错误/零漂移。

## Stop Conditions

- 标准化记录缺少金额、币种、方向或适用时间；
- 归组依赖金额/时间相似、来源名称或 provider hardcode；
- 未注册 event type 可自动发布；
- Ledger Event 丢失任一 raw/normalized/group/economic lineage；
- idempotency key 随输入顺序变化，或把多币种 posting 聚合为无 FX 依据的金额；
- 需要读取/修改真实财务数据、数据库或进入 Phase 3.3 才能通过。

## 回滚

只撤销本 Phase 的 schema、policy、domain/application、测试、Evidence 与治理提交。没有数据库 migration、真实数据或 App/remote 变更，因此不得对真实数据执行回滚、修复、迁移或清理。
