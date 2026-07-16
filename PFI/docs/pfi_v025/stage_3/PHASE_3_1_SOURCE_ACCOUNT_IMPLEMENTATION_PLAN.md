# PFI v0.2.5 Stage 3 Phase 3.1 实施合同

## 唯一目标

- Contract：`PFI-V025-STAGE3-PHASE31-SOURCE-ACCOUNT`
- Acceptance：`ACC-PFI-V025-S3-P31-SOURCE-ACCOUNT`
- Tasks：`S3-P1-T1..T4`
- 风险层级：`T3_FINANCIAL_SCHEMA_PRIVACY`

本 Phase 只建立可扩展 Source Profile、多角色账户生效期、parser provenance 与未知角色复核路由。完成状态只能是 `candidate_pass`；Stage 3 保持 `in_progress`，Phase 3.2 与 Stage 3 整阶段验收均未开始。

## 合同决策

1. `source_type` 与 `capabilities` 使用 lowercase namespaced token，不枚举数据源名称；新增来源类型或 capability 不需要修改核心分类代码。
2. Source Profile 必须绑定 `parser_id`、`parser_version`、`source_hash`、hash algorithm 与 hash scheme；`source_hash` 只接受 `sha256:<64 lowercase hex>`。
3. 一个 `account_ref` 可在同一时间区间拥有多个角色；每个 assignment 单独保存 `effective_from` 与可空 `effective_to`，结束日为包含边界。
4. 可发布角色只由显式 `role_registry` 判定，不从来源名称、label、provider 或文件名推断。
5. 未注册角色必须生成 `review_required` item，且 `publish_allowed=false`；本 Phase 不持久化 review queue，也不写数据库。

## 数据与隐私边界

- 不读取、复制、解析或修改真实财务记录、账户、持仓、金额或数据库。
- 测试仅使用非财务合同 metadata；不得把它解释为财务数据或生产验收样本。
- Evidence 只记录 schema/policy/hash、测试结果和零计数，不记录 account_ref、source instance、绝对私有路径或 credential。
- 不使用 Finder，不联网，不 push，不安装 App。

## 交付物

- `PFI/config/schemas/v025/parser_provenance.schema.json`
- `PFI/config/schemas/v025/source_profile.schema.json`
- `PFI/config/schemas/v025/account_role_assignment.schema.json`
- `PFI/config/schemas/v025/role_review_item.schema.json`
- `PFI/config/sources/v025_phase_3_1_source_account_policy.json`
- `PFI/src/pfi_os/domain/source_accounts.py`
- `PFI/src/pfi_os/application/source_account_roles.py`
- `PFI/tests/test_v025_stage3_source_profiles.py`
- `PFI/reports/pfi_v025/stage_3/phase_3_1/*`

## 验证

1. RED：缺少 v0.2.5 application service 时测试收集失败。
2. Focused：Source Profile、角色生效期、provenance、unknown-role queue 与 Evidence 合同全部通过。
3. Compatibility：不可变 Stage 2 review commit 的完整门禁保持 `72 passed`；当前 Stage 3 工作树执行 69 项功能兼容测试，3 项 Stage-2-current-state 断言按生命周期隔离。
4. 安全：schema/policy/evidence 不含来源名称映射、私有路径、账户标识、财务行值、credential、Finder 或 source mutation。
5. 治理：project governance、changed-scope semantic sync 与 renderer 全部为零错误/零漂移。

## Stop Conditions

- 代码需要按来源名称推断账户角色；
- 未知角色可自动发布或静默丢弃；
- parser/version/source hash 任一可缺失或 hash 不可验证；
- 需要读取或修改真实财务数据、数据库或进入 Phase 3.2 才能通过；
- Evidence 需要输出私有账户标识、绝对路径或财务值。

## 回滚

只撤销本 Phase 的 schema、policy、domain/application、测试、Evidence 与治理提交。没有数据库 migration，也没有真实数据变更，因此禁止对真实数据执行回滚、修复、迁移或清理。
