# IDS v0.1 STAGE-022 Phase 3 Scenario Validation

## Scope
- Stage: `STAGE-022 · 数据优先级队列`
- Task: `IDS-V0_1-STAGE022-P3`
- Acceptance: `ACC-STAGE-022`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Phase: `Phase 3 · 数据优先级队列 专项验证与异常场景`
- Recorded at UTC: `2026-07-03T00:18:42Z`

This phase validates the metadata-only P0/P1/P2/P3 data priority queue under
expected and abnormal source conditions. It does not start production queueing
or processing.

## Scenario Coverage
`build_stage022_scenario_report(...)` covers:
- `empty_directory`
- `small_directory`
- `large_directory`
- `offline_drive`
- `archive_present`
- `insufficient_space`

Each scenario reuses `evaluate_data_priority_queue(...)` and returns
`ids.stage022.data_priority_queue.scenario_validation.v1` with
`SCENARIO_VALIDATION_PASSED` when all required scenario IDs are present.

## Owner Decision Plan
`build_priority_queue_owner_decision_plan(...)` supports plan-only owner actions:
- `save_for_owner_review`
- `pause_without_side_effects`
- `cancel_without_side_effects`
- `split_into_batches`
- `skip_high_risk_files`

The helper proves that priority queue results are serializable and can be saved
by an owner-selected downstream workflow, but this helper does not persist the
result itself. Split and skip behavior is represented as a metadata-only plan.

## UI And Queue Contract
- UI component remains `DataPriorityQueuePanel`.
- Priority order remains `P0/P1/P2/P3`.
- P3 and risk-tagged files are eligible for `skip_high_risk_files`.
- Owner 确认后才进入批量处理.

## Raw Data And Processing Boundary
- 只读取元信息.
- 不解析正文.
- 不修改原始文件.
- 不启动 OCR.
- 不启动 Embedding.
- 不建立索引.
- 不启动实际导入.
- 不调用外部 API.
- 不写 manifest、database、evidence ledger、audit log、runtime data、reports、outputs、document/chunk/job/index/import row.
- 不生成 runtime 输出、screenshot、PDF、JSON 输出文件或 production preflight report.
- 不安装依赖、不启动服务、不执行 GitHub upload、PR、merge 或 app reinstall.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.
- `NO_PHASE4`: this run must not execute closeout, screenshots, delivery samples, app reinstall, GitHub upload, PR, or merge.

## Validation Evidence
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage022_data_priority_queue -q`
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage022_phase3_data_priority_queue_scenarios -q`
- `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
- `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
- `check-render --project KM_IDSystem`

## Rollback
Revert STAGE022 Phase3 helper additions, scenario tests, this evidence document,
BATCH021_030 phase3 status, Stage005 validator/test updates, roadmap/event
changes, and rendered owner-file changes only. Do not touch
`/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports, outputs,
persisted manifests, evidence ledgers, audit logs, indexes, app entries,
GitHub state, or Phase 4 artifacts.
