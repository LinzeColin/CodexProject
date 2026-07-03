# IDS v0.1 STAGE-021 Phase 3 Scenario Validation

## Task

- Task ID: `IDS-V0_1-STAGE021-P3`
- Stage: `STAGE-021`
- Acceptance: `ACC-STAGE-021`
- Phase: `Phase 3`
- Entrance: `人类产品入口 + IDS 系统运营入口`
- Component contract: `PreflightConfirmationPanel`

## Scope

Phase 3 validates the preflight confirmation UI behavior around known owner-facing scenarios:

- `empty_directory`
- `small_directory`
- `large_directory`
- `offline_drive`
- `archive_present`
- `insufficient_space`

It also validates owner decisions without persistence:

- `save_for_owner_review`
- `cancel_without_side_effects`
- `split_into_batches`
- `skip_high_risk_files`

## Implementation

`KM_IDSystem/scripts/check_preflight_confirmation_ui.py` now exposes:

- `build_stage021_scenario_report(...)`
- `build_preflight_owner_decision_plan(...)`

The scenario report wraps the existing metadata-only preflight confirmation UI payload and returns:

- `ids.stage021.preflight_confirmation_ui.scenario_validation.v1`
- `SCENARIO_VALIDATION_PASSED` only when all six required scenarios are present
- per-scenario `preflight_confirmation`
- per-scenario `owner_decision_plan`
- zero processing guard counters
- zero persistence deltas

The owner decision plan treats save as JSON serialization readiness only. The helper does not write the saved result, does not create a report file, and does not persist owner choices.

## Data Boundary

This phase did not read, list, hash, open, copy, move, delete, modify, dump, scan, normalize, or commit `/Users/linzezhang/Downloads/IDS_MetaData`.

中文硬边界：不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 `/Users/linzezhang/Downloads/IDS_MetaData`。

All Phase 3 tests use tracked governance documents and process-owned temporary structural files only for metadata classification. Those fixtures are not IDS corpus, database rows, business evidence, or committed user data. No virtual IDS business data is introduced.

## No Processing

The scenario helper confirms:

- 不解析正文
- 不启动 OCR
- 不启动 Embedding
- 不建立索引
- 不启动实际导入
- 不调用外部 API
- 不写 manifest
- 不写 database
- 不写 evidence ledger
- 不写 runtime output
- 不创建 document/chunk/job rows

## Validation

Initial RED evidence:

- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage021_preflight_confirmation_ui -q` failed because `build_stage021_scenario_report`, `build_preflight_owner_decision_plan`, and this Phase 3 evidence file were missing.
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage021_phase3_preflight_confirmation_ui_scenarios -q` failed because the governance state machine did not yet accept `IDS-V0_1-STAGE021-P3`.

Final GREEN evidence:

- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage021_preflight_confirmation_ui -q` ran 11 tests OK.
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression.Stage005GovernanceRegressionTests.test_phase_state_allows_stage021_phase3_preflight_confirmation_ui_scenarios -q` ran 1 test OK.
- `python3 -B -m unittest KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage005_governance_regression -q` ran 55 tests OK.
- `python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py` returned `valid=true`.
- `python3 -B -m unittest discover -s KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests -q` ran 183 tests OK.
- `python3 -B scripts/lean_governance.py check-render --project KM_IDSystem` returned `drift_count=0`.
- `KM_IDSystem/docs/governance/events.jsonl` parsed as 99 JSONL events.
- `git diff --check` passed.

## Stop Boundary

NO_PHASE4

This run must not enter Phase 4, close out STAGE-021, push to GitHub, create or merge a PR, reinstall app entries, or process raw IDS metadata.
