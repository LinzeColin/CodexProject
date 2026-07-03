# IDS v0.1 STAGE-021 Phase 2 Preflight Confirmation UI Slice

## Identity
- Stage: `STAGE-021 · 预检确认 UI`
- Task: `IDS-V0_1-STAGE021-P2`
- Acceptance: `ACC-STAGE-021`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Phase: `Phase 2 · 实现、接入与最小可运行切片`
- Recorded at UTC: `2026-07-02T23:01:12Z`

## Goal

Implement the smallest runnable preflight confirmation UI payload. The slice
does not start the runtime frontend or backend. It creates a tested UI data
contract that can display preflight, risk, cost, and owner decision data in the
human product entrance.

Marker: `STAGE021_PHASE2_PREFLIGHT_CONFIRMATION_UI_NO_PHASE3_NO_RAW_DATA`.

## Implementation

- Added `KM_IDSystem/scripts/check_preflight_confirmation_ui.py`.
- Reuses the metadata-only Stage 020 cost estimator chain:
  - Stage 018 import preflight metadata.
  - Stage 019 import risk estimator metadata.
  - Stage 020 import cost estimator metadata.
- Outputs `schema_version: ids.stage021.preflight_confirmation_ui.v1`.
- Outputs `human_product_entrance_payload` for `人类产品入口 + IDS 系统运营入口`.
- Defines `ui_component_contract.component_name: PreflightConfirmationPanel`.
- Supports owner decision buttons:
  - `continue_after_owner_confirmation`
  - `pause_without_side_effects`
  - `split_batch`
  - `exclude_selected_items`
  - `cancel_without_side_effects`
  - `review_later`

## UI Payload Fields

The minimal UI payload includes:

- `file_count_estimate`
- `format_counts`
- `total_size_bytes_estimate`
- `archive_candidate_count`
- `scanned_document_candidate_count`
- `unknown_format_count`
- `oversized_file_count`
- `high_risk_file_count`
- `embedding_token_estimate`
- `ocr_page_estimate`
- `external_api_cost_estimate`
- `index_size_estimate`
- `local_space_pressure`
- `risk_items`
- `cost_items`
- `priority_hint`
- `confirmation_status`
- `human_product_entrance_payload`
- `ids_operations_entrance_payload`

The human product entrance message is intentionally restrained:

`这是导入前的元信息预检确认；确认前不会启动解析、OCR、Embedding、索引或实际导入。`

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
- 不生成 screenshot、PDF、JSON 输出文件或 production preflight report.
- 不安装依赖、不启动服务、不执行 GitHub upload、PR、merge 或 app reinstall.
- 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData` 内容.
- 不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档或伪造证据.
- `NO_PHASE3`: this run must not execute scenario validation, save/cancel/split/skip persistence behavior, screenshot capture, runtime frontend launch, backend route integration, GitHub upload, or app reinstall.

## Validation Evidence

- RED:
  - `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage021_preflight_confirmation_ui -q`
  - Failed with 4 failures because `check_preflight_confirmation_ui.py` and this Phase 2 evidence file did not exist.
  - `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage021_phase2_preflight_confirmation_ui_slice -q`
  - Failed because `IDS-STAGE021-P2` was not yet accepted by the governance state machine.
- GREEN:
  - `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage021_preflight_confirmation_ui -q`
    passed with `Ran 8 tests ... OK`.
  - `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage021_phase2_preflight_confirmation_ui_slice -q`
    passed with `Ran 1 test ... OK`.
  - `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression -q`
    passed with `Ran 54 tests ... OK`.
  - `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py`
    returned `valid=true`.
  - `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q`
    passed with `Ran 179 tests ... OK`.
  - `python3 -B -m py_compile` passed for `check_preflight_confirmation_ui.py`, the Stage021 focused test, the Stage005 governance regression test, and the Stage005 validator.

## Rollback

Revert `check_preflight_confirmation_ui.py`, this evidence file, focused tests,
`BATCH021_030_UPLOAD_LOCK.yaml` Phase 2 status changes, roadmap/event changes,
Stage005 validator/test changes, and rendered owner files. Do not touch
`/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports, outputs,
persisted manifests, evidence ledgers, audit logs, indexes, app entries,
GitHub state, or Phase 3 artifacts.
