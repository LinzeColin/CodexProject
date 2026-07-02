# STAGE-008 Phase 4 Closeout - 可拔插移动硬盘状态机

- Stage: `STAGE-008`
- Phase: `Phase 4`
- Task ID: `IDS-V0_1-STAGE008-P4`
- Acceptance ID: `ACC-STAGE-008`
- Recorded UTC: `2026-07-02T08:51:29Z`
- Scope: local closeout, whole-stage review, rollback, and owner feedback only.

## Goal

Close out the STAGE-008 removable-drive state machine by recording final
environment-check, path-check, storage-budget, state-transition, recoverability,
rollback, default configuration, and Chinese owner-facing evidence.

This run does not enter STAGE-009 and does not push to GitHub. The
STAGE-001..010 batch remains locked until all ten stages are completed,
reviewed, and repaired.

Marker: `STAGE008_PHASE4_CLOSEOUT_NO_STAGE9_NO_GITHUB_UPLOAD`.

## Whole-Stage Review

| Phase | Review result | Evidence |
|---|---|---|
| Phase 1 | Passed. The entry contract and boundary document bind the P0 taskpack hash, read-only macOS/Docker/internal-disk/IDS_DATA_ROOT facts, removable-drive lifecycle states, safe-mode rules, and no-upload rule. | `STAGE008_ENTRY_CONTRACT.md`, `STAGE008_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 2 | Passed. The state machine is read-only, operations-only, customer-invisible, and maps STAGE-007 root/storage evidence into STAGE-008 lifecycle states without automatic resume. | `STAGE008_PHASE2_REMOVABLE_DRIVE_STATE.md`, `KM_IDSystem/scripts/check_removable_drive_state.py`, `tests/test_stage008_removable_drive_state.py` |
| Phase 3 | Passed. Scenario evidence covers online, offline, reconnected, permission-denied, path-changed, structure-invalid, low-free-space, high-waterline, and safe-mode pause scenarios. | `STAGE008_PHASE3_SCENARIO_VALIDATION.md`, `KM_IDSystem/scripts/check_removable_drive_state.py`, `tests/test_stage008_removable_drive_state.py` |
| Phase 4 | Passed locally in this closeout. ACC-STAGE-008 evidence, recoverability rules, default configuration, rollback, Chinese owner feedback, and the no-upload stop line are recorded. | `STAGE008_PHASE4_CLOSEOUT.md`, `BATCH001_010_UPLOAD_LOCK.yaml`, `roadmap.yaml`, `events.jsonl` |

No blocking review finding remains inside STAGE-008. The only carried
validation limitation is the known sparse-worktree semantic governance
diagnostic, which is not resolved by expanding unrelated projects.

## Review Findings

| Finding | Severity | Result |
|---|---|---|
| `STAGE008-F1` Phase 1 binds the removable-drive lifecycle state names and no-write/no-scan boundary | none | Passed. No change needed. |
| `STAGE008-F2` Phase 2 state machine avoids service start, directory creation, recursive scan, external-drive content scan, and customer-visible diagnostics | none | Passed. Script contract and CLI smoke cover `does_not_start_services=true`, `does_not_create_ids_data_root=true`, `does_not_scan_recursively=true`, `does_not_scan_external_drive_contents=true`, and `customer_visible=false`. |
| `STAGE008-F3` Phase 3 scenarios cover drive transition, storage pressure, and safe-mode pause edges | none | Passed. Scenario smoke returns `overall_valid=true`. |
| `STAGE008-F4` Phase 4 closeout evidence did not exist before this run | minor | Resolved by this closeout artifact. |
| `STAGE008-F5` Full semantic governance validate is blocked by sparse root/project omissions | carried | Diagnostic only. Do not expand unrelated projects. |
| `STAGE008-F6` GitHub upload is still blocked by the 10-stage batch rule | carried | Correct. Batch upload remains locked until STAGE-001..010 complete, reviewed, and repaired. |

## Changed-File Summary

STAGE-008 local evidence and governance touched these product-scoped files:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE008_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE008_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE008_PHASE2_REMOVABLE_DRIVE_STATE.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE008_PHASE3_SCENARIO_VALIDATION.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE008_PHASE4_CLOSEOUT.md`
- `KM_IDSystem/scripts/check_removable_drive_state.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage008_removable_drive_state.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`
- `KM_IDSystem/功能清单.md`
- `KM_IDSystem/开发记录.md`
- `KM_IDSystem/模型参数文件.md`

STAGE-008 did not change backend services, frontend UI, app bundle launchers,
raw data, generated reports, outputs, dependency folders, or external projects.

## Final Decision

`ACC-STAGE-008` is locally satisfied for v0.1 as a read-only removable-drive
lifecycle state machine and scenario-validation contract.

The accepted capability is intentionally narrow:

- It is an IDS operations entrance diagnostic, not a customer-facing workflow.
- It does not start Docker, backend, frontend, OCR, Embedding, indexing, or
  report jobs.
- It does not create, write, repair, or recursively scan `IDS_DATA_ROOT`.
- It composes STAGE-007 root and storage evidence into STAGE-008 lifecycle
  states.
- It keeps reconnect in safe mode until explicit revalidation passes.
- It keeps future v0.2+ architecture open by separating external cold raw
  material, internal hot metadata, and GitHub-tracked governance/code evidence.

## Environment, Path, And Storage Evidence

Current shell environment check:

- macOS `15.1`, build `24B83`.
- Machine architecture `arm64`; CPU `Apple M2 Max`.
- Root filesystem `/` shows `926Gi` size, `15Gi` used, and `637Gi` available
  at the time of this closeout check.
- Docker CLI and Docker Compose are visible through the STAGE-006 baseline
  script, but no Docker service is started by STAGE-008.

Current shell path check:

- `IDS_DATA_ROOT` is not configured in this shell.
- STAGE-007 detector smoke returns `state=NOT_CONFIGURED`, `safe_mode=true`,
  `customer_visible=false`, `does_not_start_services=true`,
  `does_not_create_ids_data_root=true`, and `does_not_scan_recursively=true`.
- STAGE-008 CLI smoke returns `state=NOT_CONFIGURED`, `safe_mode=true`,
  `resume_allowed=false`, `auto_resume=false`, `customer_visible=false`,
  `does_not_create_ids_data_root=true`, and `does_not_scan_recursively=true`.

Storage-budget evidence:

- STAGE-006 baseline smoke with synthetic `1000Gi` total and `300Gi` free
  returns internal storage `state=OK`, `safe_mode=false`, `min_free_gib=100`,
  `warn_free_gib=200`, and `max_used_percent=85`.
- STAGE-008 scenario smoke returns `STORAGE_BLOCKED` for synthetic low free
  space and high waterline cases.

State-transition evidence:

- `ONLINE_VALIDATED`: complete `00-99` structure with OK storage.
- `OFFLINE`: configured root absent.
- `RECONNECTED_NEEDS_REVALIDATION`: complete root after prior offline state.
- `PERMISSION_DENIED`: permission probe fails.
- `PATH_CHANGED`: configured path differs from expected path.
- `STRUCTURE_INVALID`: missing numeric slot.
- `STORAGE_BLOCKED`: low free space or high used waterline.

## Recoverable States

| State | Recovery path |
|---|---|
| `NOT_CONFIGURED` | Configure `IDS_DATA_ROOT` explicitly, then rerun STAGE-007 and STAGE-008 checks. No guessed directory is created. |
| `OFFLINE` | Reconnect or mount the external drive, then rerun validation before any import or indexing job resumes. |
| `RECONNECTED_NEEDS_REVALIDATION` | Keep safe mode enabled until the operator revalidates path identity, permissions, top-level structure, and storage budget. |
| `PATH_CHANGED` | Require operator confirmation before accepting the new path; never resume automatically. |
| `PERMISSION_DENIED` | Correct filesystem permission or mount options, then rerun validation. |
| `STRUCTURE_INVALID` | Operator must repair the external root structure or approve a migration plan outside this state machine. |
| `STORAGE_BLOCKED` | Free local disk space, reduce planned workload, or move cold material to the external root; rerun storage guard evidence. |

## Non-Recoverable Stop States

The following states are not auto-recovered by STAGE-008 and must stop the run:

- Any real raw material deletion, move, overwrite, cleanup, or unapproved copy.
- Any recursive scan of `00_ORIGINAL_RAW_DATA` or nested external-drive
  contents by this state machine.
- Any reconnect event that tries to resume import, OCR, Embedding, indexing,
  cleanup, or report generation without explicit revalidation.
- Unknown validation failure that cannot be classified as a known safe-mode
  state.
- Irreversible schema, runtime-data, or service-state mutation.
- Unexpected external-drive write or directory creation.
- Secrets or credentials appearing in tracked evidence.
- Any push, PR, or merge before the STAGE-001..010 batch is complete, reviewed,
  and repaired.

These are stop conditions, not automatic repair tasks.

## Default Configuration Notes

- `IDS_DATA_ROOT` must come from explicit environment/config in later stages.
  Missing configuration maps to `NOT_CONFIGURED` and safe mode.
- A complete root still depends on the STAGE-007 `00-99` top-level contract.
- `00_ORIGINAL_RAW_DATA` is read-only by default.
- Internal storage defaults remain conservative: minimum free space `100GiB`,
  warning free space `200GiB`, and maximum used ratio `85%`.
- The state machine is bound to `IDS 系统运营入口`; `customer_visible=false`.
- `auto_resume=false` even when `resume_allowed=true`; later stages must still
  start any bounded preflight explicitly.
- Safe mode pauses `bulk_import`, `recursive_directory_scanning`,
  `raw_material_cleanup`, `ocr`, `embedding`, `index_rebuild`, and
  `batch_report_generation`.

## Acceptance Evidence

- P0 STAGE-008 taskpack SHA:
  `5cd56ca188c4e13215d08b0281a412c877e3e02209b2c00e4f3ff1c943f2d357`
- Phase 1 boundary evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE008_PHASE1_SCOPE_BOUNDARY.md`
- Phase 2 implementation evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE008_PHASE2_REMOVABLE_DRIVE_STATE.md`
- Phase 3 scenario evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE008_PHASE3_SCENARIO_VALIDATION.md`
- Phase 4 closeout evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE008_PHASE4_CLOSEOUT.md`
- Executable state machine:
  `KM_IDSystem/scripts/check_removable_drive_state.py`
- Focused tests:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage008_removable_drive_state.py`

## Final Validation Evidence

Fresh Phase 4 validation in this run:

- `python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage008_removable_drive_state.py -q`
  returned `Ran 6 tests in 0.203s`, `OK`.
- `python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage007_ids_data_root_detector.py -q`
  returned `Ran 7 tests in 0.258s`, `OK`.
- `python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py -q`
  returned `Ran 7 tests in 0.176s`, `OK`.
- `python -B KM_IDSystem/scripts/check_removable_drive_state.py --ids-data-root '' --storage-total-gib 1000 --storage-free-gib 300`
  returned `state=NOT_CONFIGURED`, `safe_mode=true`,
  `resume_allowed=false`, `auto_resume=false`,
  `customer_visible=false`, `does_not_start_services=true`,
  `does_not_create_ids_data_root=true`, and
  `does_not_scan_recursively=true`.
- `python -B KM_IDSystem/scripts/detect_ids_data_root.py --ids-data-root ''`
  returned `state=NOT_CONFIGURED`, `safe_mode=true`,
  `customer_visible=false`, `does_not_start_services=true`,
  `does_not_create_ids_data_root=true`, and
  `does_not_scan_recursively=true`.
- `python -B KM_IDSystem/scripts/check_environment_baseline.py --ids-data-root '' --internal-total-gib 1000 --internal-free-gib 300`
  returned `IDS_DATA_ROOT` state `NOT_CONFIGURED`, internal storage
  `state=OK`, `free_gib=300.0`, `min_free_gib=100`,
  `warn_free_gib=200`, `max_used_percent=85`, Docker CLI available, Docker
  Compose available, `does_not_start_services=true`, and
  `does_not_create_ids_data_root=true`.
- Scenario smoke through `build_stage008_scenario_report(...)` returned
  `overall_valid=true`, drive states `ONLINE_VALIDATED`, `OFFLINE`,
  `RECONNECTED_NEEDS_REVALIDATION`, `PERMISSION_DENIED`, `PATH_CHANGED`, and
  `STRUCTURE_INVALID`, storage states `ONLINE_VALIDATED` and
  `STORAGE_BLOCKED`, and the full safe-mode pause list.
- Static boundary search found directory creation only inside the temporary
  test helper; the production state-machine script has no `mkdir`, `open`,
  `os.walk`, `rglob`, `glob`, `iterdir`, `rmtree`, `unlink`, `subprocess`,
  Docker command, or `auto_resume=True` match.
- `python -B -m py_compile KM_IDSystem/scripts/check_removable_drive_state.py`
  passed; the generated `check_removable_drive_state` pyc was removed after
  verification.
- `python -B scripts/lean_governance.py check-render --project KM_IDSystem`
  returned `drift_count=0`, `reference_issue_count=0`.
- STAGE-008 Phase 4 marker, scope, and JSONL checks found
  `STAGE008_PHASE4_CLOSEOUT_NO_STAGE9_NO_GITHUB_UPLOAD`,
  `EVT-IDS-V0_1-STAGE008-P4-20260702-001`, `local_passed`,
  `IDS-STAGE009-P1-GATE`, and `completed_estimated_hours: 65`.
- `git diff --check` passed.
- `python -B scripts/lean_governance.py validate --project KM_IDSystem --semantic`
  returned sync validation `errors: 0`, `warnings: 0`, followed by the known
  28 sparse-worktree/root-governance/unrelated-project errors and no
  STAGE-008 product blocker.

Do not expand unrelated projects to satisfy the sparse-worktree diagnostic.

## Rollback

Rollback Phase 4 by reverting the local `IDS-V0_1-STAGE008-P4` commit. This
removes only the closeout document, batch-lock/roadmap/event updates, and
rendered owner views.

Rollback the whole stage, if required, in reverse order:

1. Revert `IDS-V0_1-STAGE008-P4`.
2. Revert `IDS-V0_1-STAGE008-P3`.
3. Revert `IDS-V0_1-STAGE008-P2`.
4. Revert `IDS-V0_1-STAGE008-P1`.

No Docker cleanup, runtime-data cleanup, external-drive cleanup, dependency
cleanup, report cleanup, output cleanup, or GitHub PR cleanup is needed because
STAGE-008 did not create those artifacts.

## Chinese Owner Feedback

STAGE-008 已在本地完成 v0.1 可拔插移动硬盘状态机：系统现在有一个只读的运营
诊断切片，可以把移动硬盘根目录状态归入未配置、离线、重连待复验、路径变化、
权限异常、结构异常、空间阻断和已验证在线。

当前结论不是“已经可以自动导入真实资料”，而是“未来导入、OCR、Embedding、索引
重建、清理和批量报告前，已有可验证、可回滚、不会自动恢复作业的移动硬盘状态
边界”。这能防止 v0.1 在移动硬盘重新插入、路径变化或空间不足时误扫原始资料、
创建猜测目录、修改 `00_ORIGINAL_RAW_DATA`，或在缺少复验的情况下继续批处理。

下一轮只能进入 `STAGE-009 Phase 1`。GitHub main 上传仍锁定到
`STAGE-001..010` 全部完成、复审和修复之后。

## Stop Line

Stop after `STAGE-008 Phase 4`. Do not start `STAGE-009` in this run. Do not
push, open PR, merge, or upload to GitHub main until the STAGE-001..010 batch is
complete, reviewed, and repaired.
