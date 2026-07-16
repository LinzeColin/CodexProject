# PFI v0.2.5 Stage 9 / Phase 9.1 实施记录

## 唯一执行合同

- Phase：`V025-S9-P9.1` — 报告合同与完整度。
- Tasks：`S9-P1-T1`、`S9-P1-T2`、`S9-P1-T3`、`S9-P1-T4`。
- Acceptance：`ACC-PFI-V025-STAGE9-WHOLE-REVIEW`；本轮只形成 Phase 9.1 candidate evidence，Stage 9 Gate 尚未验收。
- 风险层：`T2`，因为本轮建立 schema、完整度规则与 Evidence Contract；没有修改公式、参数或模型值。
- 实施基线：`be592b1ccecdd68c15eb3b225c0fa2184be67488`（Stage 8 accepted_for_transition）。
- 来源锁：Roadmap SHA-256=`fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b`；Task Pack SHA-256=`591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2`。

## S9-P1-T1 — report schema 与 immutable manifest

- `PFI/config/reports/v025_report.schema.json` 是 Task Pack `report.schema.json` 的严格实现：保留全部 required 字段，并增加 coverage、dependencies、completeness、gaps、review links、privacy/value flags 与可重建 snapshot hash。
- `report_manifest.json` 固定六类报告：data quality、net worth、cash、investment、consumption、cashflow。每个 entry 都是 immutable snapshot，并有独立 `snapshot_hash`；manifest 自身有 `manifest_hash`。
- 报告合同不读取 Downloads 作为运行依赖；外部 Roadmap/Task Pack 只在本实施记录与 evidence 中做来源 hash 绑定。

## S9-P1-T2 — complete / partial / blocked

- `complete`：所有 critical dependencies ready 且 hash 一致，才允许完整财务结论。
- `partial`：至少一个可独立解释的 scope 的全部依赖 ready；当前只允许 transaction source coverage 结论，不允许消费、现金流金额或确定性财务结论。
- `blocked`：关键依赖未 ready 且没有可独立计算 scope；结论数组必须为空，必须给出缺口和复核路由。
- data quality report 在任何依赖状态都为 `complete`，但结论 scope 永远是 `data_quality_only`。
- `financial_analysis_implementation` 在 Phase 9.2 前是显式 blocked dependency，防止 Phase 9.1 把“依赖数据已存在”冒充“完整财务分析已实现”。

## S9-P1-T3 — 当前数据质量与缺口报告

- 输入只使用已验收、无私密值的 aggregate artifacts：Stage 2 source manifest、Stage 4 unified read-model status、Stage 7 whole-review workflow validation。
- 当前 source truth：7 个注册源中 1 ready、1 partial、5 not_loaded；唯一 ready transaction source 有 8815 条 aggregate record count，范围 `2022-06-06..2026-06-03`。
- 当前 operational truth：1571 个 confirmed ledger events；economic-event lineage complete=0、missing=1571；11 个 metric 保持 blocked/null；non-ready false-zero count=0。
- 当前报告状态：data quality=`complete`；consumption/cashflow=`partial`（只确认 source coverage）；net worth/cash/investment=`blocked`。
- Evidence Pack 不包含账户标识、raw rows、原始来源文件名或财务数值；数据库未读取、未修改，输入 artifact hash 前后相同。

## S9-P1-T4 — 同源 hash 绑定

六类报告精确共享：

- `data_manifest_hash`：Stage 2 accepted source manifest 文件 hash。
- `read_model_hash`：Stage 7 accepted whole-review metric-lineage read model hash。
- `formula_registry_hash`：当前 `v025_formula_registry.json` 文件 hash，且必须与 Stage 7 accepted evidence 一致。
- `parameter_hash`：当前 `pfi_parameters.yaml` 文件 hash，且必须与 Stage 7 accepted evidence 一致。

另外绑定 schema/rules contract、builder、Stage 4 read-model artifact、Stage 7 workflow artifact 和整个 input bundle hash。任一报告 hash 漂移、snapshot/manifest hash 不可重建或 blocked 报告出现结论，validator 都 fail closed。

## 验证、风险与回滚

- 目标测试：`PFI/tests/test_v025_stage9_report_schema.py`。
- 回归：Stage 4 read model、Stage 5 formula/parameter、Stage 7 metric lineage 和 Stage 8 release identity 的相关测试。
- 治理：JSON Schema、Python AST、privacy、input immutability、`git diff --check`、renderer 与完整 checkout PFI governance。
- 回滚整个本地 Phase commit 即可；Stage 2/4/7 artifact、raw、DB、公式/参数值、GitHub 与 PFI.app 均不改。
- 任一缺依赖报告被标为 complete、blocked 报告出现财务结论、跨报告 hash 不一致、证据含私密值，或实现需要进入 Phase 9.2，本 Phase 必须停止并整改。

## 停止边界

Phase 9.2、Phase 9.3 和 Stage 9 whole-stage review 均保持 `not_started`。本轮不 push、不安装、不执行 production/final acceptance，也不使用 Finder、LaunchServices 或 GUI 文件操作。
