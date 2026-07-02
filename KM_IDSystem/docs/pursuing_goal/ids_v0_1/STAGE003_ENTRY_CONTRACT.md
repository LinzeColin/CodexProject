# IDS v0.1 STAGE-003 Entry Contract

## Identity

- Stage: `STAGE-003`
- Local code: `D01-S003`
- Title: `MetaDatabase 更名为 FinanceMetaDatabase`
- Version: `v0.1`
- Domain: `D01 · 一次性仓库治理与产品命名`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-003`
- Parallel: `否`
- Estimated time: `6-14 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-003_MetaDatabase更名为FinanceMetaDatabase.md`
- P0 stage file SHA-256:
  `e1ef61af5b2f728df3d246049036dd49cee35285e2e9eebcce726193d4c43b5d`

## Pursuing Goal

将 `MetaDatabase` 一次性更名为 `FinanceMetaDatabase`，并更新引用、迁移说明和
回滚说明。

## Required Reads For STAGE-003

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
4. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
6. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-003_MetaDatabase更名为FinanceMetaDatabase.md`

## Naming Boundary

The target rename is the standalone historical subsystem name
`MetaDatabase` to `FinanceMetaDatabase`.

Do not treat `ProductMetaDatabase` as a target. `ProductMetaDatabase` was
created and accepted in STAGE-002 as the IDS product metadata control plane.
It contains the substring `MetaDatabase`, but it is a distinct active subsystem
and must not be renamed by STAGE-003.

## Phase Boundary

STAGE-003 must be split into phase-limited runs. Do not implement all of
STAGE-003 in one run.

### Phase 1：范围、输入输出与边界确认

1. 确认独立 `MetaDatabase` 改名的仓库治理边界、允许路径和禁止路径。
2. 列出受影响的 README、governance、roadmap、脚本、测试或文档路径。
3. 明确 `ProductMetaDatabase` 不属于本 Stage 改名目标。

### Phase 2：实现、接入与最小可运行切片

1. 按最小变更原则完成 `MetaDatabase` 到 `FinanceMetaDatabase` 的引用迁移。
2. 同步更新相关引用，不引入运行时代码耦合。
3. 保留迁移说明和回滚说明。

### Phase 3：MetaDatabase 更名为 FinanceMetaDatabase 专项验证与异常场景

1. 扫描客户可见文案和治理文件，验证独立旧名称不再作为新正式显示名出现。
2. 验证 README、治理文件、测试路径和脚本引用没有断裂。
3. 检查本 Stage 没有触碰真实资料、secrets 或本地数据目录。

### Phase 4：MetaDatabase 更名为 FinanceMetaDatabase 交付证据、回滚与中文反馈

1. 提交变更文件清单、引用扫描结果和回滚步骤。
2. 写明仍保留的 legacy alias 位置及原因。
3. 生成 `ACC-STAGE-003` 证据，未完成扫描不得验收。

## Acceptance Summary

- 追求目标对应能力已经可运行，或已形成可执行、可测试、可回滚的工程合同。
- 本 Stage 的失败状态、停止条件、审计记录、回滚路径明确。
- 本 Stage 不破坏原始资料、manifest、证据账本、审计日志和已交付报告。
- 相关测试、场景验证或文档证据真实存在。
- 中文交互反馈清楚、克制、面向企业用户，不使用夸大或 AI 化承诺。

## Stop Conditions

- 需要真实资料但没有 fixture 或 owner 授权样本。
- 可能删除、移动、覆盖原始文件。
- schema migration 无法回滚。
- 测试失败且原因不明。
- 修改范围超出本 Stage。
- 并行开发导致共享文件冲突。
- Phase 2 试图把 `ProductMetaDatabase` 重命名为 `FinanceMetaDatabase`。

## Rollback

回滚本 Stage 的代码、schema、配置、UI 或文档变更；不得影响原始资料、
manifest、evidence ledger、audit log、已交付报告或 STAGE-002 的
`ProductMetaDatabase` 合同。
