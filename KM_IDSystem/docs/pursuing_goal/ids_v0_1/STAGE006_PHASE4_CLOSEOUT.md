# STAGE-006 Phase 4 Closeout - macOS M2 Max Docker Baseline

- Stage: `STAGE-006`
- Phase: `Phase 4`
- Task ID: `IDS-V0_1-STAGE006-P4`
- Acceptance ID: `ACC-STAGE-006`
- Recorded UTC: `2026-07-02T07:35:39Z`
- Scope: local closeout, whole-stage review, rollback, and owner feedback only.

## Goal

Close out the STAGE-006 macOS M2 Max Docker baseline by recording final
environment-check, path-check, storage-budget, recoverability, rollback, and
Chinese owner-facing evidence.

This run does not enter STAGE-007 and does not push to GitHub. The
STAGE-001..010 batch remains locked until all ten stages are completed,
reviewed, and repaired.

## Whole-Stage Review

| Phase | Review result | Evidence |
|---|---|---|
| Phase 1 | Passed. The stage entry contract and boundary document bind the P0 taskpack hash, read-only macOS/Docker facts, internal/external storage split, removable-drive states, and safe-mode rules. | `STAGE006_ENTRY_CONTRACT.md`, `STAGE006_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 2 | Passed. The read-only operations diagnostic exposes environment, path, storage-budget, and safe-mode state without starting services, installing dependencies, creating `IDS_DATA_ROOT`, or scanning external-drive contents. | `STAGE006_PHASE2_ENVIRONMENT_BASELINE.md`, `KM_IDSystem/scripts/check_environment_baseline.py`, `tests/test_stage006_environment_baseline.py` |
| Phase 3 | Passed. Synthetic scenarios cover online, offline, reconnected, permission-denied, path-changed, low-free-space, high-waterline, and safe-mode pause behavior. | `STAGE006_PHASE3_SCENARIO_VALIDATION.md`, `KM_IDSystem/scripts/check_environment_baseline.py`, `tests/test_stage006_environment_baseline.py` |
| Phase 4 | Passed locally in this closeout. ACC-STAGE-006 evidence, recoverability rules, default configuration, rollback, and no-upload stop line are recorded. | `STAGE006_PHASE4_CLOSEOUT.md`, `BATCH001_010_UPLOAD_LOCK.yaml`, `roadmap.yaml`, `events.jsonl` |

No blocking review finding remains inside STAGE-006. The only carried
validation limitation is the known sparse-worktree semantic governance
diagnostic, which is not resolved by expanding unrelated projects.

## Changed-File Summary

STAGE-006 local evidence and governance touched these product-scoped files:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE006_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE006_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE006_PHASE2_ENVIRONMENT_BASELINE.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE006_PHASE3_SCENARIO_VALIDATION.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE006_PHASE4_CLOSEOUT.md`
- `KM_IDSystem/scripts/check_environment_baseline.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`
- `KM_IDSystem/功能清单.md`
- `KM_IDSystem/开发记录.md`
- `KM_IDSystem/模型参数文件.md`

STAGE-006 did not change backend services, frontend UI, app bundle launchers,
raw data, generated reports, outputs, dependency folders, or external projects.

## Final Decision

`ACC-STAGE-006` is locally satisfied for v0.1 as a read-only operations baseline.

The accepted baseline is intentionally narrow:

- It is an operations entrance diagnostic, not a customer-facing workflow.
- It does not prove Docker Desktop is running; it records CLI/Compose presence
  and safe failure behavior.
- It does not start backend, frontend, Docker, or worker services.
- It does not create, write, or scan `IDS_DATA_ROOT`.
- It does not create runtime `data/`, `reports/`, `outputs/`, `.venv`,
  `node_modules`, or build artifacts.
- It keeps future v0.2+ architecture open by separating raw material storage,
  internal hot metadata, and GitHub-tracked metadata contracts.

## Recoverable States

| State | Recovery path |
|---|---|
| `NOT_CONFIGURED` | Configure `IDS_DATA_ROOT`, then rerun the read-only baseline check. Safe mode stays enabled until configuration is explicit. |
| `OFFLINE` | Reconnect the external drive or mount path, then rerun validation before any import or indexing job resumes. |
| `RECONNECTED` | Treat as safe mode until revalidation confirms the path identity and accessibility. |
| `PERMISSION_DENIED` | Correct filesystem permission or mount options, then rerun the diagnostic. |
| `PATH_CHANGED` | Require operator confirmation before accepting the new path; never resume automatically. |
| `WARN` / `BLOCKED` storage states | Free local disk space, reduce planned workload, or move cold material to the external root; rerun the storage check. |
| Docker CLI or Compose unavailable | Repair Docker Desktop or CLI installation outside this stage, then rerun the diagnostic. |

## Non-Recoverable Stop States

The following states are not auto-recovered by STAGE-006 and must stop the run:

- Any real raw material deletion, move, overwrite, or unapproved copy.
- Unknown validation failure that cannot be classified as a known safe-mode
  state.
- Irreversible schema, runtime-data, or service-state mutation.
- Unexpected external-drive write or directory creation.
- Secrets or credentials appearing in tracked evidence.

These are stop conditions, not automatic repair tasks.

## Default Configuration Notes

- `IDS_DATA_ROOT` is read from explicit environment/config in later stages.
  Missing configuration maps to `NOT_CONFIGURED` and safe mode.
- Internal storage defaults remain conservative: minimum free space `100GiB`,
  warning free space `200GiB`, and maximum used ratio `85%`.
- The diagnostic is bound to `IDS 系统运营入口`; `customer_visible=false`.
- Safe mode pauses `bulk_import`, `ocr`, `embedding`, `index_rebuild`,
  `batch_report_generation`, and `raw_material_cleanup`.

## Acceptance Evidence

- P0 STAGE-006 taskpack SHA:
  `00486235919499e8b0d9a17cc6241167779738bc5fb832d1fad9e547e32acafb`
- Phase 1 boundary evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE006_PHASE1_SCOPE_BOUNDARY.md`
- Phase 2 implementation evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE006_PHASE2_ENVIRONMENT_BASELINE.md`
- Phase 3 scenario evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE006_PHASE3_SCENARIO_VALIDATION.md`
- Phase 4 closeout evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE006_PHASE4_CLOSEOUT.md`
- Executable diagnostic:
  `KM_IDSystem/scripts/check_environment_baseline.py`
- Focused tests:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py`

## Final Validation Evidence

Fresh Phase 4 validation in this run:

- `python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py -q`
  returned `Ran 7 tests`, `OK`.
- `python -B KM_IDSystem/scripts/check_environment_baseline.py --ids-data-root '' --internal-total-gib 1000 --internal-free-gib 300`
  returned `customer_visible=false`, `ids_data_root.state=NOT_CONFIGURED`,
  `ids_data_root.safe_mode=true`, `internal_storage.state=OK`,
  `does_not_start_services=true`, and `does_not_create_ids_data_root=true`.
- Phase 3 scenario smoke through `build_phase3_scenario_report(...)` returned
  `overall_valid=True`, `customer_visible=False`, all five external-drive
  states, both blocked storage states, and the safe-mode pause list.
- `python -B -m py_compile KM_IDSystem/scripts/check_environment_baseline.py`
  passed; the generated `check_environment_baseline` pyc was removed after
  verification.
- `python -B scripts/lean_governance.py check-render --project KM_IDSystem`
  returned `drift_count=0`.
- STAGE-006 Phase 4 marker, scope, and JSONL checks returned
  `stage006_phase4_marker_jsonl_scope_ok=True`.
- `git diff --check` passed.
- `python -B scripts/lean_governance.py validate --project KM_IDSystem --semantic`
  returned the known 28 sparse-worktree/root-governance/unrelated-project
  errors and no STAGE-006 product blocker.

Do not expand unrelated projects to satisfy the sparse-worktree diagnostic.

## Rollback

Rollback Phase 4 by reverting the local `IDS-V0_1-STAGE006-P4` commit. This
removes only the closeout document, batch-lock/roadmap/event updates, and
rendered owner views.

Rollback the whole stage, if required, in reverse order:

1. Revert `IDS-V0_1-STAGE006-P4`.
2. Revert `IDS-V0_1-STAGE006-P3`.
3. Revert `IDS-V0_1-STAGE006-P2`.
4. Revert `IDS-V0_1-STAGE006-P1`.

No Docker cleanup, runtime-data cleanup, external-drive cleanup, or dependency
cleanup is needed because STAGE-006 did not create those artifacts.

## Chinese Owner Feedback

STAGE-006 已在本地完成 v0.1 运行环境基线：系统现在有一个只读的运营诊断切片，
可以判断 `IDS_DATA_ROOT` 是否未配置、离线、重连、权限异常或路径变化，并能在
内置盘空间不足时进入安全模式。

当前结论不是“生产环境已启动”，而是“未来导入、OCR、Embedding、索引重建和批量
报告前已有可验证的本机/存储保护边界”。这能防止 v0.1 为了快速开发而把原始资料
直接写进仓库、误扫移动硬盘或在未确认路径时自动恢复批处理。

下一轮只能进入 `STAGE-007 Phase 1`。GitHub main 上传仍锁定到
`STAGE-001..010` 全部完成、复审和修复之后。

## Stop Line

Stop after `STAGE-006 Phase 4`. Do not start `STAGE-007` in this run. Do not
push, open PR, merge, or upload to GitHub main until the STAGE-001..010 batch is
complete, reviewed, and repaired.
