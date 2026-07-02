# STAGE-007 Phase 4 Closeout - IDS_DATA_ROOT 检测

- Stage: `STAGE-007`
- Phase: `Phase 4`
- Task ID: `IDS-V0_1-STAGE007-P4`
- Acceptance ID: `ACC-STAGE-007`
- Recorded UTC: `2026-07-02T08:14:17Z`
- Scope: local closeout, whole-stage review, rollback, and owner feedback only.

## Goal

Close out the STAGE-007 `IDS_DATA_ROOT` detector by recording final path-check,
`00-99` directory-structure validation, recoverability, rollback, default
configuration, and Chinese owner-facing evidence.

This run does not enter STAGE-008 and does not push to GitHub. The
STAGE-001..010 batch remains locked until all ten stages are completed,
reviewed, and repaired.

Marker: `STAGE007_PHASE4_CLOSEOUT_NO_STAGE8_NO_GITHUB_UPLOAD`.

## Whole-Stage Review

| Phase | Review result | Evidence |
|---|---|---|
| Phase 1 | Passed. The stage entry contract and boundary document bind the P0 taskpack hash, read-only local baseline, `IDS_DATA_ROOT` explicit-configuration rule, `00-99` top-level slot contract, and safe-mode rules. | `STAGE007_ENTRY_CONTRACT.md`, `STAGE007_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 2 | Passed. The detector is read-only, operations-only, customer-invisible, and validates configured path, expected path, readability, top-level numeric slots, missing slots, duplicate slots, malformed entries, and raw-material slot policy. | `STAGE007_PHASE2_IDS_DATA_ROOT_DETECTOR.md`, `KM_IDSystem/scripts/detect_ids_data_root.py`, `tests/test_stage007_ids_data_root_detector.py` |
| Phase 3 | Passed. Scenario evidence covers complete root, absent root, reconnected root, permission denial, path change, non-directory path, missing slot, duplicate slot, malformed entry, internal-storage blocking, and safe-mode pauses. | `STAGE007_PHASE3_SCENARIO_VALIDATION.md`, `KM_IDSystem/scripts/detect_ids_data_root.py`, `tests/test_stage007_ids_data_root_detector.py` |
| Phase 4 | Passed locally in this closeout. ACC-STAGE-007 evidence, recoverability rules, default configuration, rollback, Chinese owner feedback, and the no-upload stop line are recorded. | `STAGE007_PHASE4_CLOSEOUT.md`, `BATCH001_010_UPLOAD_LOCK.yaml`, `roadmap.yaml`, `events.jsonl` |

No blocking review finding remains inside STAGE-007. The only carried
validation limitation is the known sparse-worktree semantic governance
diagnostic, which is not resolved by expanding unrelated projects.

## Review Findings

| Finding | Severity | Result |
|---|---|---|
| `STAGE007-F1` P1 boundary binds P0 taskpack and no-write root policy | none | Passed. No change needed. |
| `STAGE007-F2` P2 detector avoids directory creation and recursive scan | none | Passed. Tests and CLI contract cover `does_not_create_ids_data_root=true` and `does_not_scan_recursively=true`. |
| `STAGE007-F3` P3 scenarios cover reconnect, path change, permission, structure, and storage edges | none | Passed. Scenario helper returns `overall_valid=True`. |
| `STAGE007-F4` Phase 4 closeout evidence did not exist before this run | minor | Resolved by this closeout artifact. |
| `STAGE007-F5` Full semantic governance validate is blocked by sparse root/project omissions | carried | Diagnostic only. Do not expand unrelated projects. |
| `STAGE007-F6` GitHub upload is still blocked by the 10-stage batch rule | carried | Correct. Batch upload remains locked until STAGE-001..010 complete, reviewed, and repaired. |

## Changed-File Summary

STAGE-007 local evidence and governance touched these product-scoped files:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE007_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE007_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE007_PHASE2_IDS_DATA_ROOT_DETECTOR.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE007_PHASE3_SCENARIO_VALIDATION.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE007_PHASE4_CLOSEOUT.md`
- `KM_IDSystem/scripts/detect_ids_data_root.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage007_ids_data_root_detector.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`
- `KM_IDSystem/功能清单.md`
- `KM_IDSystem/开发记录.md`
- `KM_IDSystem/模型参数文件.md`

STAGE-007 did not change backend services, frontend UI, app bundle launchers,
raw data, generated reports, outputs, dependency folders, or external projects.

## Final Decision

`ACC-STAGE-007` is locally satisfied for v0.1 as a read-only
`IDS_DATA_ROOT` detection and top-level directory-structure contract.

The accepted capability is intentionally narrow:

- It is an IDS operations entrance diagnostic, not a customer-facing workflow.
- It does not start Docker, backend, frontend, OCR, Embedding, indexing, or
  report jobs.
- It does not create, write, repair, or recursively scan `IDS_DATA_ROOT`.
- It verifies only explicit configuration and immediate top-level `00-99`
  structure.
- It keeps future v0.2+ architecture open by separating external cold raw
  material, internal hot metadata, and GitHub-tracked governance/code evidence.

## Path And Structure Evidence

Current shell path check:

- `IDS_DATA_ROOT` is not configured in this shell.
- CLI smoke returns `state=NOT_CONFIGURED`, `safe_mode=true`,
  `customer_visible=false`, `does_not_start_services=true`,
  `does_not_create_ids_data_root=true`, and `does_not_scan_recursively=true`.

Synthetic `00-99` structure validation evidence:

- Complete top-level slot structure returns `STRUCTURE_COMPLETE`.
- A structurally complete root after prior absence returns `RECONNECTED` and
  requires revalidation before resuming work.
- Missing slot returns `MISSING_NUMERIC_SLOTS`.
- Duplicate slot returns `DUPLICATE_NUMERIC_SLOT`.
- Malformed top-level entry returns `MALFORMED_TOP_LEVEL_ENTRY`.
- `00_ORIGINAL_RAW_DATA` remains represented as slot `00` with
  `read_only_required` policy metadata.

Internal storage evidence:

- Adequate free space returns `OK`.
- Low free space returns `BLOCKED`.
- High used waterline returns `BLOCKED`.

## Recoverable States

| State | Recovery path |
|---|---|
| `NOT_CONFIGURED` | Configure `IDS_DATA_ROOT` explicitly, then rerun the detector. No guessed directory is created. |
| `ROOT_ABSENT` | Reconnect or mount the external drive, then rerun validation before any import or indexing job resumes. |
| `RECONNECTED` | Keep safe mode enabled until the operator revalidates path identity and top-level structure. |
| `ROOT_PERMISSION_DENIED` | Correct filesystem permission or mount options, then rerun the detector. |
| `PATH_CHANGED` | Require operator confirmation before accepting the new path; never resume automatically. |
| `ROOT_NOT_DIRECTORY` | Correct the configuration to point at a directory, then rerun validation. |
| `MISSING_NUMERIC_SLOTS` | Operator must repair the external root structure or approve a migration plan outside this detector. |
| `DUPLICATE_NUMERIC_SLOT` | Operator must remove or migrate duplicate top-level slots outside this detector. |
| `MALFORMED_TOP_LEVEL_ENTRY` | Operator must review and move invalid top-level entries outside this detector. |
| `WARN` / `BLOCKED` storage states | Free local disk space, reduce planned workload, or move cold material to the external root; rerun storage guard evidence. |

## Non-Recoverable Stop States

The following states are not auto-recovered by STAGE-007 and must stop the run:

- Any real raw material deletion, move, overwrite, cleanup, or unapproved copy.
- Any recursive scan of `00_ORIGINAL_RAW_DATA` or nested external-drive
  contents by this detector.
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
- A complete STAGE-007 root contains exactly one immediate directory for every
  numeric slot `00` through `99`.
- Slot directory names may be exactly `NN` or start with `NN_`; later stages may
  refine labels, but the numeric completeness rule is fixed here.
- `00_ORIGINAL_RAW_DATA` is read-only by default.
- Internal storage defaults remain conservative: minimum free space `100GiB`,
  warning free space `200GiB`, and maximum used ratio `85%`.
- The detector is bound to `IDS 系统运营入口`; `customer_visible=false`.
- Safe mode pauses `bulk_import`, `recursive_directory_scanning`,
  `raw_material_cleanup`, `ocr`, `embedding`, `index_rebuild`, and
  `batch_report_generation`.

## Acceptance Evidence

- P0 STAGE-007 taskpack SHA:
  `1bdbb53699df9dffd53c88d74ac6ec1385852a4bebccdb0e780cc47f537bd458`
- Phase 1 boundary evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE007_PHASE1_SCOPE_BOUNDARY.md`
- Phase 2 implementation evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE007_PHASE2_IDS_DATA_ROOT_DETECTOR.md`
- Phase 3 scenario evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE007_PHASE3_SCENARIO_VALIDATION.md`
- Phase 4 closeout evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE007_PHASE4_CLOSEOUT.md`
- Executable detector:
  `KM_IDSystem/scripts/detect_ids_data_root.py`
- Focused tests:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage007_ids_data_root_detector.py`

## Final Validation Evidence

Fresh Phase 4 validation in this run:

- `python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage007_ids_data_root_detector.py -q`
  returned `Ran 7 tests`, `OK`.
- `python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py -q`
  returned `Ran 7 tests`, `OK`.
- `python -B KM_IDSystem/scripts/detect_ids_data_root.py --ids-data-root ''`
  returned `customer_visible=false`, `state=NOT_CONFIGURED`,
  `safe_mode=true`, `does_not_start_services=true`,
  `does_not_create_ids_data_root=true`, and `does_not_scan_recursively=true`.
- Phase 3 scenario smoke through `build_stage007_scenario_report(...)`
  returned `overall_valid=True`, all expected root states, both blocked storage
  states, and the safe-mode pause list.
- `python -B -m py_compile KM_IDSystem/scripts/detect_ids_data_root.py`
  passed; the generated `detect_ids_data_root` pyc was removed after
  verification.
- `python -B scripts/lean_governance.py check-render --project KM_IDSystem`
  returned `drift_count=0`.
- STAGE-007 Phase 4 marker, scope, and JSONL checks returned
  `stage007_phase4_marker_jsonl_scope_ok=True`.
- `git diff --check` passed.
- `python -B scripts/lean_governance.py validate --project KM_IDSystem --semantic`
  returned the known 28 sparse-worktree/root-governance/unrelated-project
  errors and no STAGE-007 product blocker.

Do not expand unrelated projects to satisfy the sparse-worktree diagnostic.

## Rollback

Rollback Phase 4 by reverting the local `IDS-V0_1-STAGE007-P4` commit. This
removes only the closeout document, batch-lock/roadmap/event updates, and
rendered owner views.

Rollback the whole stage, if required, in reverse order:

1. Revert `IDS-V0_1-STAGE007-P4`.
2. Revert `IDS-V0_1-STAGE007-P3`.
3. Revert `IDS-V0_1-STAGE007-P2`.
4. Revert `IDS-V0_1-STAGE007-P1`.

No Docker cleanup, runtime-data cleanup, external-drive cleanup, dependency
cleanup, report cleanup, output cleanup, or GitHub PR cleanup is needed because
STAGE-007 did not create those artifacts.

## Chinese Owner Feedback

STAGE-007 已在本地完成 v0.1 `IDS_DATA_ROOT` 检测：系统现在有一个只读的运营
诊断切片，可以判断根目录是否未配置、缺失、重连、权限异常、路径变化、不是目录，
以及 `00-99` 顶层目录是否缺失、重复或出现异常入口。

当前结论不是“已经可以导入真实资料”，而是“未来导入、OCR、Embedding、索引重建
和批量报告前，已有可验证、可回滚、不会自动修盘的根目录预检边界”。这能防止
v0.1 为了快速开发而误扫移动硬盘、创建猜测目录、修改 `00_ORIGINAL_RAW_DATA` 或
在路径变化后自动恢复批处理。

下一轮只能进入 `STAGE-008 Phase 1`。GitHub main 上传仍锁定到
`STAGE-001..010` 全部完成、复审和修复之后。

## Stop Line

Stop after `STAGE-007 Phase 4`. Do not start `STAGE-008` in this run. Do not
push, open PR, merge, or upload to GitHub main until the STAGE-001..010 batch is
complete, reviewed, and repaired.
