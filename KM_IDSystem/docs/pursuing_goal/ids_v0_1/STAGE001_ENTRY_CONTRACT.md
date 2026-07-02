# IDS v0.1 STAGE-001 Entry Contract

## Identity

- Stage: `STAGE-001`
- Local code: `D01-S001`
- Title: `IDS 产品命名合同`
- Version: `v0.1`
- Domain: `D01 · 一次性仓库治理与产品命名`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-001`
- Parallel: `否`
- Estimated time: `4-8 小时`
- P0 taskpack file: `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-001_IDS产品命名合同.md`
- P0 stage file SHA-256: `db3f6828b413d9f537a006058603ac8d1f306470ca8a51395c5815c20d36ebf4`

## Pursuing Goal

统一 IDS / Industrial Data System 产品命名，禁止新 UI、报告和正式文档继续使用旧产品名。

## Required Reads For STAGE-001

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
4. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
5. P0 taskpack stage file: `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-001_IDS产品命名合同.md`

## Phase Boundary

STAGE-001 itself still must be split into phase-limited runs. Do not implement all of STAGE-001 in one run unless the user explicitly widens the one-phase rule.

### Phase 1：范围、输入输出与边界确认
1. 确认本 Stage 的仓库治理边界、允许修改文件和禁止修改文件。
2. 列出受影响的 README、governance、roadmap、脚本、测试或文档路径。
3. 确认旧名称只允许出现在迁移说明和历史别名中。

### Phase 2：实现、接入与最小可运行切片
1. 按最小变更原则完成仓库治理或命名变更。
2. 同步更新相关引用，不引入运行时代码耦合。
3. 保留迁移说明和回滚说明。

### Phase 3：IDS 产品命名合同 专项验证与异常场景
1. 全仓扫描客户可见文案，验证不再出现旧产品名。
2. 验证 README、治理文件、测试路径和脚本引用没有断裂。
3. 检查本 Stage 没有触碰真实资料、secrets 或本地数据目录。

### Phase 4：IDS 产品命名合同 交付证据、回滚与中文反馈
1. 提交变更文件清单、引用扫描结果和回滚步骤。
2. 写明仍保留的 legacy alias 位置及原因。
3. 生成 ACC 证据，未完成扫描不得验收。

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

## Rollback

回滚本 Stage 的代码、schema、配置或 UI 变更；不得影响原始资料、manifest、evidence ledger、audit log 和已交付报告。若本 Stage 产生派生产物，应只清理明确允许清理的临时文件或可重建缓存。

## Stage 0 Bridge Decision

Stage 0 does not execute STAGE-001. It only proves that the next run can enter STAGE-001 with a stable source path, Acceptance ID, stage file hash, and one-phase execution boundary.
