# STAGE-009 Phase 4 Closeout - 存储预算基线

- Stage: `STAGE-009`
- Phase: `Phase 4`
- Task ID: `IDS-V0_1-STAGE009-P4`
- Acceptance ID: `ACC-STAGE-009`
- Recorded UTC: `2026-07-02T09:24:25Z`
- Scope: local closeout, whole-stage review, rollback, and owner feedback only.

## Goal

Close out the STAGE-009 storage-budget baseline by recording final
environment-check, path-check, storage-budget, waterline, recoverability,
rollback, default configuration, and Chinese owner-facing evidence.

This run does not enter STAGE-010 and does not push to GitHub. The
STAGE-001..010 batch remains locked until all ten stages are completed,
reviewed, and repaired.

Marker: `STAGE009_PHASE4_CLOSEOUT_NO_STAGE10_NO_GITHUB_UPLOAD`.

## Whole-Stage Review

| Phase | Review result | Evidence |
|---|---|---|
| Phase 1 | Passed. The entry contract and boundary document bind the P0 taskpack hash already recorded in Phase 1, STAGE-006/007/008 source evidence, internal/external/GitHub storage split, budget states, thresholds, safe-mode rules, and no-upload rule. | `STAGE009_ENTRY_CONTRACT.md`, `STAGE009_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 2 | Passed. The storage-budget preflight is read-only, operations-only, customer-invisible, and maps internal storage, removable-drive readiness, and unbounded-output risk into the STAGE-009 budget states. | `STAGE009_PHASE2_STORAGE_BUDGET_BASELINE.md`, `KM_IDSystem/scripts/check_storage_budget.py`, `tests/test_stage009_storage_budget.py` |
| Phase 3 | Passed. Scenario evidence covers OK, WARN, low-free blocked, high-waterline blocked, UNKNOWN, external-root-not-ready, missing output cap, planned output exceeding budget, and safe-mode pauses. | `STAGE009_PHASE3_SCENARIO_VALIDATION.md`, `KM_IDSystem/scripts/check_storage_budget.py`, `tests/test_stage009_storage_budget.py` |
| Phase 4 | Passed locally in this closeout. ACC-STAGE-009 evidence, recoverability rules, default configuration, rollback, Chinese owner feedback, and the no-upload stop line are recorded. | `STAGE009_PHASE4_CLOSEOUT.md`, `BATCH001_010_UPLOAD_LOCK.yaml`, `roadmap.yaml`, `events.jsonl` |

No blocking review finding remains inside STAGE-009. The only carried
validation limitations are:

- the known sparse-worktree semantic governance diagnostic, which must not be
  resolved by expanding unrelated projects;
- the original P0 stage source file is not materialized in this sparse project
  evidence folder, so Phase 4 relies on the Phase 1 recorded P0 SHA and the
  current stage execution index row rather than re-hashing the external
  taskpack file.

## Review Findings

| Finding | Severity | Result |
|---|---|---|
| `STAGE009-F1` Phase 1 defines budget state names, default thresholds, safe-mode pause rules, storage split, and no-write/no-scan boundary. | none | Passed. No change needed. |
| `STAGE009-F2` Phase 2 preflight avoids service start, directory creation, recursive scan, external-drive content scan, runtime writes, and customer-visible diagnostics. | none | Passed. Script and CLI smoke cover `does_not_start_services=true`, `does_not_create_ids_data_root=true`, `does_not_scan_recursively=true`, `does_not_scan_external_drive_contents=true`, `does_not_generate_outputs=true`, `does_not_write_runtime_data=true`, and `customer_visible=false`. |
| `STAGE009-F3` Phase 3 scenarios cover OK, WARN, BLOCKED, UNKNOWN, high-waterline, external-root-not-ready, unbounded-output risk, and safe-mode pause edges. | none | Passed. Scenario smoke returns `overall_valid=true`. |
| `STAGE009-F4` Phase 4 closeout evidence did not exist before this run. | minor | Resolved by this closeout artifact. |
| `STAGE009-F5` P0 stage source file is not present in this sparse evidence directory for fresh re-hash. | carried | Documented. Phase 1 already recorded SHA `490671d6372dd185fa829ce4a7ea05d25b6ae311feb92a986571cbdb2a567099`, and the current execution index maps STAGE-009 to `D02-S004` and `ACC-STAGE-009`. Do not expand unrelated project/taskpack content in this worktree. |
| `STAGE009-F6` Full semantic governance validate is blocked by sparse root/project omissions. | carried | Diagnostic only. Do not expand unrelated projects. |
| `STAGE009-F7` GitHub upload is still blocked by the 10-stage batch rule. | carried | Correct. Batch upload remains locked until STAGE-001..010 complete, reviewed, and repaired. |

## Changed-File Summary

STAGE-009 local evidence and governance touched these product-scoped files:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE009_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE009_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE009_PHASE2_STORAGE_BUDGET_BASELINE.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE009_PHASE3_SCENARIO_VALIDATION.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE009_PHASE4_CLOSEOUT.md`
- `KM_IDSystem/scripts/check_storage_budget.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage009_storage_budget.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`
- `KM_IDSystem/功能清单.md`
- `KM_IDSystem/开发记录.md`
- `KM_IDSystem/模型参数文件.md`

STAGE-009 did not change backend services, frontend UI, app bundle launchers,
raw data, generated reports, outputs, dependency folders, or external projects.

## Final Decision

`ACC-STAGE-009` is locally satisfied for v0.1 as a read-only storage-budget
baseline and scenario-validation contract.

The accepted capability is intentionally narrow:

- It is an IDS operations entrance diagnostic, not a customer-facing workflow.
- It does not start Docker, backend, frontend, OCR, Embedding, indexing,
  cleanup, or report jobs.
- It does not create, write, repair, or recursively scan `IDS_DATA_ROOT`.
- It distinguishes internal hot data, external cold raw material, and
  GitHub-tracked code/governance evidence.
- It blocks unbounded derived output before local output is created.
- It keeps future v0.2+ architecture open by making storage budget a
  deterministic preflight contract rather than a runtime side effect.

## Environment, Path, And Storage Evidence

Current shell environment check:

- macOS `15.1`, build `24B83`.
- Machine architecture `arm64`; CPU `Apple M2 Max`.
- Root filesystem `/` shows `926Gi` size, `15Gi` used, and `577Gi` available
  at the time of this closeout check.
- Docker CLI and Docker Compose are visible through the STAGE-006 baseline
  script, but no Docker service is started by STAGE-009.

Current shell path check:

- `IDS_DATA_ROOT` is not configured in this shell.
- STAGE-007 detector smoke returns `state=NOT_CONFIGURED`, `safe_mode=true`,
  `customer_visible=false`, `does_not_start_services=true`,
  `does_not_create_ids_data_root=true`, and `does_not_scan_recursively=true`.
- STAGE-008 removable-drive smoke returns `state=NOT_CONFIGURED`,
  `safe_mode=true`, `resume_allowed=false`, `auto_resume=false`,
  `customer_visible=false`, `does_not_create_ids_data_root=true`,
  `does_not_scan_recursively=true`, and
  `does_not_scan_external_drive_contents=true`.

Storage-budget evidence:

- STAGE-006 baseline smoke with synthetic `1000Gi` total and `300Gi` free
  returns internal storage `state=OK`, `safe_mode=false`, `min_free_gib=100`,
  `warn_free_gib=200`, and `max_used_percent=85`.
- STAGE-009 CLI smoke with synthetic `1000Gi` total, `300Gi` free, and
  `20Gi` planned output returns `state=BUDGET_OK`, `safe_mode=false`,
  `bounded_preflight_only=true`, `customer_visible=false`,
  `does_not_generate_outputs=true`, and `does_not_write_runtime_data=true`.
- STAGE-009 scenario smoke returns `BUDGET_BLOCKED_LOW_FREE` for low free
  space, `BUDGET_BLOCKED_HIGH_WATERLINE` for high used waterline,
  `BUDGET_UNKNOWN` when storage cannot be classified, and
  `UNBOUNDED_OUTPUT_RISK` for missing or excessive derived-output budgets.

## Recoverable States

| State | Recovery path |
|---|---|
| `BUDGET_OK` | Later stages may run bounded preflight only. Do not auto-start data-moving work. |
| `BUDGET_WARN` | Keep operations visible, require operator review before large derived-output jobs, then rerun budget preflight. |
| `BUDGET_BLOCKED_LOW_FREE` | Free internal disk space, reduce planned workload, or move cold material to the external root; rerun storage-budget preflight. |
| `BUDGET_BLOCKED_HIGH_WATERLINE` | Reduce internal disk usage below the waterline before running derived-output or batch work. |
| `BUDGET_UNKNOWN` | Treat as fail-closed; require manual operator review and rerun preflight with classifiable storage evidence. |
| `EXTERNAL_ROOT_NOT_READY` | Configure, reconnect, or revalidate `IDS_DATA_ROOT` through STAGE-007/008 checks before cold-data workflows resume. |
| `UNBOUNDED_OUTPUT_RISK` | Declare an output budget/cap or reduce planned output before any OCR, Embedding, indexing, cleanup, or batch report work starts. |

## Non-Recoverable Stop States

The following states are not auto-recovered by STAGE-009 and must stop the run:

- Any real raw material deletion, move, overwrite, cleanup, or unapproved copy.
- Any guessed `IDS_DATA_ROOT` creation or unapproved `00-99` directory repair.
- Any recursive scan of `00_ORIGINAL_RAW_DATA` or nested external-drive
  contents by this storage-budget preflight.
- Any OCR, Embedding, indexing, cleanup, or batch report output created without
  a bounded output budget.
- Any storage block that tries to resume data-moving work automatically.
- Unknown validation failure that cannot be classified as a known safe-mode
  state.
- Irreversible schema, runtime-data, or service-state mutation.
- Secrets or credentials appearing in tracked evidence.
- Any push, PR, or merge before the STAGE-001..010 batch is complete,
  reviewed, and repaired.

These are stop conditions, not automatic repair tasks.

## Default Configuration Notes

- Internal storage defaults remain conservative: minimum free space `100GiB`,
  warning free space `200GiB`, and maximum used ratio `85%`.
- The owner-facing internal planning label remains `800GB`; the current APFS
  root measurement may differ.
- External cold root nominal size remains `5TB`, but STAGE-009 does not verify
  a real external disk in this shell.
- `IDS_DATA_ROOT` must come from explicit environment/config in later stages.
  Missing configuration maps to `EXTERNAL_ROOT_NOT_READY` for cold-data jobs.
- `00_ORIGINAL_RAW_DATA` remains read-only by default.
- The storage-budget preflight is bound to `IDS 系统运营入口`;
  `customer_visible=false`.
- `auto_resume=false` even when a bounded preflight is allowed.
- Safe mode pauses `bulk_import`, `recursive_directory_scanning`,
  `raw_material_cleanup`, `ocr`, `embedding`, `index_rebuild`, and
  `batch_report_generation`.

## Acceptance Evidence

- P0 STAGE-009 taskpack SHA recorded in Phase 1:
  `490671d6372dd185fa829ce4a7ea05d25b6ae311feb92a986571cbdb2a567099`
- Stage execution index:
  `STAGE-009,D02-S004,存储预算基线,...,ACC-STAGE-009,...,stages/STAGE-009_存储预算基线.md`
- Phase 1 boundary evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE009_PHASE1_SCOPE_BOUNDARY.md`
- Phase 2 implementation evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE009_PHASE2_STORAGE_BUDGET_BASELINE.md`
- Phase 3 scenario evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE009_PHASE3_SCENARIO_VALIDATION.md`
- Phase 4 closeout evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE009_PHASE4_CLOSEOUT.md`
- Executable storage-budget preflight:
  `KM_IDSystem/scripts/check_storage_budget.py`
- Focused tests:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage009_storage_budget.py`

## Final Validation Evidence

Fresh Phase 4 validation in this run:

- `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage009_storage_budget.py -q`
  returned `Ran 5 tests`, `OK`.
- `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage008_removable_drive_state.py -q`
  returned `Ran 6 tests`, `OK`.
- `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage007_ids_data_root_detector.py -q`
  returned `Ran 7 tests`, `OK`.
- `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py -q`
  returned `Ran 7 tests`, `OK`.
- `python3 -B KM_IDSystem/scripts/check_storage_budget.py --internal-total-gib 1000 --internal-free-gib 300 --planned-output-gib 20 --job-kind bounded_preflight --no-require-external-root`
  returned `state=BUDGET_OK`, `safe_mode=false`,
  `customer_visible=false`, `bounded_preflight_only=true`,
  `does_not_create_ids_data_root=true`,
  `does_not_scan_external_drive_contents=true`,
  `does_not_generate_outputs=true`, and
  `does_not_write_runtime_data=true`.
- Scenario smoke through `build_stage009_scenario_report(...)` returned
  `overall_valid=true`, states `BUDGET_OK`, `BUDGET_WARN`,
  `BUDGET_BLOCKED_LOW_FREE`, `BUDGET_BLOCKED_HIGH_WATERLINE`,
  `BUDGET_UNKNOWN`, `EXTERNAL_ROOT_NOT_READY`, and
  `UNBOUNDED_OUTPUT_RISK`, plus the full safe-mode pause list.
- Static boundary search found directory creation and subprocess usage only
  inside temporary test helpers and CLI smoke; the production storage-budget
  script has no `mkdir`, `open`, `os.walk`, `rglob`, `glob`, `rmtree`,
  `unlink`, `subprocess`, Docker command, `write_text`, `write_bytes`, or
  `auto_resume=True` match.
- `python3 -B -m py_compile KM_IDSystem/scripts/check_storage_budget.py`
  passed without tracked output.
- `python3 -B scripts/lean_governance.py check-render --project KM_IDSystem`
  returned `drift_count=0`, `reference_issue_count=0`.
- STAGE-009 Phase 4 marker, scope, and JSONL checks found
  `STAGE009_PHASE4_CLOSEOUT_NO_STAGE10_NO_GITHUB_UPLOAD`,
  `EVT-IDS-V0_1-STAGE009-P4-20260702-001`, `local_passed`,
  `next_stage: STAGE-010`, and `completed_estimated_hours: 71`.
- `git diff --check` passed.
- `python3 -B scripts/lean_governance.py validate --project KM_IDSystem --semantic`
  returned sync validation `errors: 0`, `warnings: 0`, followed by the known
  28 sparse-worktree/root-governance/unrelated-project errors and no STAGE-009
  product blocker.

Do not expand unrelated projects to satisfy the sparse-worktree diagnostic.

## Rollback

Rollback Phase 4 by reverting the local `IDS-V0_1-STAGE009-P4` commit. This
removes only the closeout document, batch-lock/roadmap/event updates, and
rendered owner views.

Rollback the whole stage, if required, in reverse order:

1. Revert `IDS-V0_1-STAGE009-P4`.
2. Revert `IDS-V0_1-STAGE009-P3`.
3. Revert `IDS-V0_1-STAGE009-P2`.
4. Revert `IDS-V0_1-STAGE009-P1`.

No Docker cleanup, runtime-data cleanup, external-drive cleanup, dependency
cleanup, report cleanup, output cleanup, or GitHub PR cleanup is needed because
STAGE-009 did not create those artifacts.

## Chinese Owner Feedback

STAGE-009 已在本地完成 v0.1 存储预算基线：系统现在有一个只读的运营诊断切片，
可以把内置盘空间、水位线、移动硬盘可用性和派生产物预算归入清晰状态。

实际含义：

- 空间足够时，只允许后续阶段做有边界的预检，不会自动启动导入或生成任务。
- 空间接近警戒线时，大任务需要人工确认。
- 空间不足、水位线过高、状态未知、移动硬盘未就绪或派生产物预算缺失时，进入安全模式。
- 安全模式会暂停批量导入、递归扫描、清理、OCR、Embedding、索引重建和批量报告。
- 这轮没有写入真实原始资料、没有创建外接盘目录、没有生成报告或索引、没有上传 GitHub。

下一步是 STAGE-010 本地路径合同。GitHub 上传仍需等 STAGE-001..010 全部完成、
复审并修复后再按批次执行。
