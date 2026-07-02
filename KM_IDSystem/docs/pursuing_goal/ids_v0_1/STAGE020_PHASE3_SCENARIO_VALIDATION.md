# IDS v0.1 STAGE-020 Phase 3 Scenario Validation

## Task Identity
- Stage: `STAGE-020 · 导入成本估算器`
- Task: `IDS-V0_1-STAGE020-P3`
- Acceptance: `ACC-STAGE-020`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Implementation: `KM_IDSystem/scripts/check_import_cost_estimator.py build_stage020_scenario_report`

## Implemented Scenario Layer
Phase 3 adds in-memory scenario validation and owner decision planning on top of the Phase 2 metadata-only cost estimator. It does not create persistent output files and does not start any processing job.

Covered required scenarios:

- `empty_directory`
- `small_directory`
- `large_directory`
- `offline_drive`
- `archive_present`
- `insufficient_space`

The scenario report returns:

- `schema_version: ids.stage020.import_cost_estimator.scenario_validation.v1`
- `validation_state`
- `required_scenarios`
- `required_scenarios_covered`
- `scenario_results`
- `processing_guard`
- `no_persistence_deltas`

## Owner Decision Plan
`build_cost_owner_decision_plan` validates that the preflight result can support owner decisions without side effects:

- `save_for_owner_review`: the helper confirms the cost report is serializable, but `persisted_by_helper` remains `False` and an owner-selected path is required.
- `cancel_without_side_effects`: document, chunk, job, index, import, manifest, evidence, audit, report, and database deltas remain 0.
- `split_into_batches`: the helper builds an in-memory batch plan from metadata only.
- `skip_high_risk_files`: high-risk files can be separated from kept files in memory.

## Processing Guard
The Phase 3 scenario report records all processing counters as 0:

- `actual_parse_jobs_started`
- `actual_ocr_jobs_started`
- `actual_embedding_jobs_started`
- `actual_index_jobs_started`
- `actual_import_jobs_started`
- `actual_external_api_calls_started`

## Raw Data Boundary
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- Scenario tests use tracked governance documents plus process-owned temporary structural files for extension, size, archive, scanned-file, and large-batch classification only.
- These fixtures are not IDS corpus, database rows, business evidence, or committed user data.

## No Processing Or Persistence
- 不解析正文.
- 不启动 OCR.
- 不启动 Embedding.
- 不建立索引.
- 不启动实际导入.
- 不调用外部 API.
- 不写 manifest、database、evidence ledger、audit log、runtime data、reports、outputs、document/chunk/job/index/import row.
- 不生成 screenshot、PDF、JSON 输出文件或 production cost report.
- 不安装依赖、不启动服务、不执行 GitHub upload、PR、merge 或 app reinstall.
- `NO_PHASE4`: this run must not create Phase 4 delivery evidence, screenshots, report samples, final Chinese feedback, whole-stage closeout, or batch upload gate.

## Validation Plan
Final validation must include:

- RED/GREEN focused test for `KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage020_import_cost_estimator`.
- RED/GREEN Stage005 governance-regression state test for `IDS-V0_1-STAGE020-P3`.
- Stage005 validator report.
- Full IDS v0.1 pursuing-goal unittest discover.
- `py_compile` for `check_import_cost_estimator.py`, Stage020 focused test, Stage005 validator, and Stage005 regression test.
- events JSONL parse.
- owner render/check-render.
- `git diff --check`.
- exact old task-id spelling scan and legacy pre-rename path diff scan.
- semantic validate as sparse-worktree diagnostic only.

## Validation Results
Completed local validation:

- RED Stage020 focused test failed as expected before implementation: 10 tests ran with 1 failure and 2 errors because `build_stage020_scenario_report`, `build_cost_owner_decision_plan`, and this evidence file were absent.
- RED Stage005 targeted governance test failed as expected before implementation because `IDS-V0_1-STAGE020-P3` was not yet accepted by the governance state machine.
- GREEN Stage020 focused test: `Ran 10 tests in 0.100s`, `OK`.
- Stage005 governance regression: `Ran 46 tests in 0.136s`, `OK`.
- Stage005 validator: `valid: true`, `missing_required_files: []`, `missing_event_ids: []`, `unexpected_changed_paths: []`, `forbidden_changed_paths: []`.
- events JSONL parse: `events_jsonl_ok count=92`.
- Full IDS v0.1 pursuing-goal unittest discover: `Ran 161 tests in 2.357s`, `OK`.
- `py_compile` completed for the Phase 3 helper, Stage020 focused test, Stage005 validator, and Stage005 regression test.
- Owner render wrote `功能清单.md`, `开发记录.md`, and `模型参数文件.md`; check-render returned `drift_count: 0`.
- `git diff --check` passed.
- Exact legacy underscore task-id spelling scan returned no matches.
- Legacy pre-rename path diff scan returned `legacy_path_hits_in_diff=0`.
- Semantic validate was run as a sparse-worktree diagnostic only. It exited 1 with 29 expected missing root/registered-project paths from the sparse checkout, and did not report a KM_IDSystem semantic error.

## Rollback
Revert Phase 3 helper additions in `check_import_cost_estimator.py`, this evidence file, Stage020 focused tests, Stage005 validator/test updates, batch-lock, roadmap/event, and rendered owner-file changes only. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports, outputs, persisted manifests, evidence ledgers, audit logs, indexes, delivered reports, app entries, GitHub state, or Phase 4.
