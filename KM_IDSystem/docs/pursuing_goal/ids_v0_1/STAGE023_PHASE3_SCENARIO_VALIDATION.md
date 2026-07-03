# IDS v0.1 STAGE-023 Phase 3 Scenario Validation

## Scope
- Stage: `STAGE-023 · 预检场景测试`
- Task: `IDS-V0_1-STAGE023-P3`
- Acceptance: `ACC-STAGE-023`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Phase: `Phase 3 · 场景、异常、回归与数据验证`
- Recorded at UTC: `2026-07-03T01:47:39Z`

This phase validates the metadata-only preflight scenario-test slice with
process-owned temporary structural inputs. Those inputs are not IDS corpus data,
database rows, business evidence, committed examples, or user source documents.
They exist only during focused tests and are removed by the test harness.

## Implemented Validation Helpers
- `build_stage023_scenario_report`
- `build_preflight_scenario_owner_decision_plan`
- Scenario validation schema: `ids.stage023.preflight_scenario_tests.scenario_validation.v1`
- Owner decision schema: `ids.stage023.preflight_scenario_tests.owner_decision.v1`

The scenario report wraps the Phase 2 `ids.stage023.preflight_scenario_tests.v1`
payload for each required scenario and records a no-persistence owner decision
plan beside it.

## Required Scenarios
- `empty_directory`
- `small_directory`
- `large_directory`
- `offline_drive`
- `bad_file`
- `archive_present`
- `insufficient_space`

Each scenario is evaluated by metadata only: file count, format, size, archive
candidate, scanned candidate, bad-file metadata signal, OCR estimate, Embedding
token estimate, external API cost estimate, index size estimate, risk, cost, and
priority suggestion.

## Owner Decision Plan
Supported owner actions:
- `save_for_owner_review`
- `pause_without_side_effects`
- `cancel_without_side_effects`
- `split_into_batches`
- `skip_high_risk_files`

`save_for_owner_review` means the report is JSON-serializable and can be saved
only if owner selects a destination in a later gated flow. The helper itself
does not persist scenario results, manifests, runtime outputs, reports, audit
logs, evidence ledgers, database rows, indexes, documents, chunks, jobs, imports,
screenshots, PDFs, or JSON output files.

`cancel_without_side_effects` and `pause_without_side_effects` preserve zero
document, chunk, job, index, import, manifest, evidence, audit, report, database,
and scenario-result deltas.

`split_into_batches` creates an in-memory batch plan from candidate-file
metadata only. `skip_high_risk_files` identifies archive, scanned, unknown, bad,
or broken-file candidates for owner review without deleting, moving, copying, or
rewriting source files.

## Processing Boundary
- 只读取元信息.
- 不解析正文.
- 不修改原始文件.
- 不启动 OCR.
- 不启动 Embedding.
- 不建立索引.
- 不启动实际导入.
- 不启动 scenario runner.
- 不调用外部 API.
- 不写 manifest、database、evidence ledger、audit log、runtime data、reports、outputs、document/chunk/job/index/import/scenario result row.
- 不生成 screenshot、PDF、JSON 输出文件或 production preflight report.
- 不安装依赖、不启动服务、不执行 GitHub upload、PR、merge 或 app reinstall.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.
- `NO_PHASE4`: this run must not close out STAGE-023, perform whole-stage review, generate owner feedback closeout, enter STAGE-024, upload to GitHub, reinstall app entries, or resolve the ten-stage batch gate.

## Evidence
- `KM_IDSystem/scripts/check_preflight_scenario_tests.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE3_SCENARIO_VALIDATION.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage023_preflight_scenario_tests.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`

## Rollback
Revert `build_stage023_scenario_report`,
`build_preflight_scenario_owner_decision_plan`, this Phase 3 evidence file,
focused tests, `BATCH021_030_UPLOAD_LOCK.yaml`, Stage005 validator/test updates,
roadmap/event updates, and rendered owner-file changes only. Do not touch
`/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports, outputs,
persisted manifests, evidence ledgers, audit logs, indexes, app entries, GitHub
state, or Phase 4 artifacts.
