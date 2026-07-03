# IDS v0.1 STAGE-023 Phase 2 Preflight Scenario Tests Slice

## Scope
- Stage: `STAGE-023 · 预检场景测试`
- Task: `IDS-V0_1-STAGE023-P2`
- Acceptance: `ACC-STAGE-023`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Phase: `Phase 2 · 实现、接入与最小可运行切片`
- Recorded at UTC: `2026-07-03T01:18:21Z`

This phase adds a metadata-only preflight scenario-test payload helper:

`KM_IDSystem/scripts/check_preflight_scenario_tests.py`

The helper builds `ids.stage023.preflight_scenario_tests.v1` by composing the existing Stage 020 metadata-only cost estimator. It does not read body text, does not recursively scan a corpus, and does not persist scenario results.

## Implemented Payload
- `schema_version`: `ids.stage023.preflight_scenario_tests.v1`
- `task_id`: `IDS-V0_1-STAGE023-P2`
- `source_preflight_schema`: `ids.stage018.import_preflight.v1`
- `source_cost_schema`: `ids.stage020.import_cost_estimator.v1`
- `file_count_estimate`
- `format_counts`
- `total_size_bytes_estimate`
- `archive_candidate_count`
- `scanned_document_candidate_count`
- `unknown_format_count`
- `bad_file_candidate_count`
- `embedding_token_estimate`
- `ocr_page_estimate`
- `external_api_cost_estimate`
- `index_size_estimate`
- `local_space_pressure`
- `risk_items`
- `cost_items`
- `priority_suggestion`
- `required_scenarios`
- `scenario_validation_summary`
- `human_product_entrance_payload`
- `ids_operations_entrance_payload`
- `ui_component_contract`: `PreflightScenarioTestsPanel`

## Human Product Entrance
The helper emits a restrained Chinese `human_product_entrance_payload` for `人类产品入口 + IDS 系统运营入口` with:
- summary cards for file count, format count, size, archive candidates, scanned candidates, bad-file candidates, OCR estimate, Embedding estimate, index estimate, and confirmation state;
- owner actions: `review_preflight_scenario_tests`, `approve_preflight_scenarios`, `pause_without_side_effects`, `split_batch`, `skip_high_risk_files`, and `cancel_without_side_effects`;
- message: `确认前不会启动解析、OCR、Embedding、索引或实际导入`.

## Risk, Cost, And Priority
The helper maps Stage 020 cost risks into Stage 023 scenario risk items:
- archive risk -> `SCENARIO_ARCHIVE_REVIEW_REQUIRED`
- unknown format risk -> `SCENARIO_UNKNOWN_FORMAT_PRESENT`
- bad-file metadata signal -> `SCENARIO_BAD_FILE_PRESENT`
- insufficient space -> `SCENARIO_INSUFFICIENT_SPACE`
- offline drive -> `SCENARIO_OFFLINE_DRIVE`
- local-space block -> `SCENARIO_LOCAL_SPACE_BLOCKED`

`priority_suggestion` is advisory only:
- `blocked`
- `split_or_skip_risk_items`
- `owner_review_required`
- `low_risk_first`

Owner confirmation remains mandatory: owner 确认后才进入批量处理.

## Processing Boundary
- 只读取元信息.
- 不解析正文.
- 不修改原始文件.
- 不启动 OCR.
- 不启动 Embedding.
- 不建立索引.
- 不启动实际导入.
- 不调用外部 API.
- 不写 manifest、database、evidence ledger、audit log、runtime data、reports、outputs、document/chunk/job/index/import row.
- 不写 scenario result runtime output.
- 不生成 screenshot、PDF、JSON 输出文件或 production preflight report.
- 不安装依赖、不启动服务、不执行 GitHub upload、PR、merge 或 app reinstall.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.
- `NO_PHASE3`: this run must not implement Phase 3 scenario validation, save/cancel/split/skip-high-risk owner decision persistence, screenshots, or closeout evidence.

## Evidence
- `KM_IDSystem/scripts/check_preflight_scenario_tests.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE2_PREFLIGHT_SCENARIO_TESTS_SLICE.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage023_preflight_scenario_tests.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`

## Rollback
Revert `check_preflight_scenario_tests.py`, this Phase 2 evidence file, focused tests, `BATCH021_030_UPLOAD_LOCK.yaml`, Stage005 validator/test updates, roadmap/event updates, and rendered owner-file changes only. Do not touch `/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports, outputs, persisted manifests, evidence ledgers, audit logs, indexes, app entries, GitHub state, or Phase 3 artifacts.
