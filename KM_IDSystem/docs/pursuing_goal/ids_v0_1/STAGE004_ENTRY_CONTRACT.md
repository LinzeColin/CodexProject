# IDS v0.1 STAGE-004 Entry Contract

## Identity

- Stage: `STAGE-004`
- Local code: `D01-S004`
- Title: `旧名称引用扫描`
- Version: `v0.1`
- Domain: `D01 · 一次性仓库治理与产品命名`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-004`
- Parallel: `否`
- Estimated time: `4-8 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-004_旧名称引用扫描.md`
- P0 stage file SHA-256:
  `0e265f600726b8922eebf22151908bf69a4672240faa38fddb45278b290f2f8c`

## Pursuing Goal

扫描旧名称引用并限制其只出现在 legacy migration note 或历史说明中。

## Required Reads For STAGE-004

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
4. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
6. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-004_旧名称引用扫描.md`

## Old Name Boundary

STAGE-004 is a repository-bound legacy-name scan and classification stage. It
does not replace names in Phase 1.

The scan target includes:

- legacy product names and slugs:
  `Wuhan Kaiming OpMe`, `武汉开明智能工业运维助手`,
  `wuhan-kaiming-assistant`, `OpMe_System`, `opme-system`, word-boundary
  `OpMe`/`OPME`/`opme`, `wuhan_kaiming`, `Wuhan Kaiming`, and `武汉开明`;
- legacy asset/report identifiers:
  `OpMeIcon` and `OpMe_structure_report`;
- standalone finance metadata old name:
  standalone `MetaDatabase`.

The scan target explicitly excludes:

- `ProductMetaDatabase`, which is an accepted STAGE-002 subsystem;
- `FinanceMetaDatabase`, which is the accepted STAGE-003 canonical finance
  metadata name;
- incidental substrings that are not standalone legacy product names.

## Phase Boundary

STAGE-004 must be split into phase-limited runs. Do not implement all of
STAGE-004 in one run.

### Phase 1：范围、输入输出与边界确认

1. 确认本 Stage 的仓库治理边界、允许修改文件和禁止修改文件。
2. 列出受影响的 README、governance、roadmap、脚本、测试或文档路径。
3. 确认旧名称只允许出现在迁移说明和历史别名中。

### Phase 2：实现、接入与最小可运行切片

1. 按最小变更原则完成旧名称扫描工具或治理合同切片。
2. 同步更新相关引用，不引入运行时代码耦合。
3. 保留迁移说明和回滚说明。

### Phase 3：旧名称引用扫描专项验证与异常场景

1. 扫描客户可见文案，验证旧产品名不再作为新正式显示名出现。
2. 验证 README、治理文件、测试路径和脚本引用没有断裂。
3. 检查本 Stage 没有触碰真实资料、secrets 或本地数据目录。

### Phase 4：旧名称引用扫描交付证据、回滚与中文反馈

1. 提交变更文件清单、引用扫描结果和回滚步骤。
2. 写明仍保留的 legacy alias 位置及原因。
3. 生成 `ACC-STAGE-004` 证据，未完成扫描不得验收。

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
- 旧名称扫描试图改写 `ProductMetaDatabase` 或 `FinanceMetaDatabase`。

## Rollback

回滚本 Stage 的代码、schema、配置、UI 或文档变更；不得影响原始资料、
manifest、evidence ledger、audit log、已交付报告、STAGE-002
`ProductMetaDatabase` 合同或 STAGE-003 `FinanceMetaDatabase` 合同。
