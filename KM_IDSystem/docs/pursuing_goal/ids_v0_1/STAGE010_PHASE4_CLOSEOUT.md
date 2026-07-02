# STAGE-010 Phase 4 Closeout - 本地路径合同

- Stage: `STAGE-010`
- Phase: `Phase 4`
- Task ID: `IDS-V0_1-STAGE010-P4`
- Acceptance ID: `ACC-STAGE-010`
- Recorded UTC: `2026-07-02T10:07:42Z`
- Scope: local closeout, delivery evidence, rollback, and owner feedback only.

## Goal

Close out the STAGE-010 local path contract by recording final environment
check, path check, storage-budget evidence, path-contract state evidence,
recoverability, rollback, default configuration, and Chinese owner-facing
feedback.

This run does not perform the separate whole-stage review/fix pass and does not
push to GitHub. The STAGE-001..010 batch remains locked until all ten stages
are completed, reviewed, repaired, and explicitly uploaded together.

Marker: `STAGE010_PHASE4_CLOSEOUT_NO_STAGE_REVIEW_NO_GITHUB_UPLOAD`.

## Phase Evidence Summary

| Phase | Local result | Evidence |
|---|---|---|
| Phase 1 | Completed. Defined `file:// source_uri`, processed, backup, manifest, report export, storage/root dependencies, safe-mode rules, and no-upload boundary. | `STAGE010_ENTRY_CONTRACT.md`, `STAGE010_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 2 | Completed. Implemented read-only local path contract preflight and JSON CLI. | `STAGE010_PHASE2_LOCAL_PATH_CONTRACT.md`, `KM_IDSystem/scripts/check_local_path_contract.py`, `tests/test_stage010_local_path_contract.py` |
| Phase 3 | Completed. Validated online, offline, reconnected, permission-denied, path-changed, missing-source, invalid-source, storage-budget, output-risk, and safe-mode scenarios. | `STAGE010_PHASE3_SCENARIO_VALIDATION.md`, `KM_IDSystem/scripts/check_local_path_contract.py`, `tests/test_stage010_local_path_contract.py` |
| Phase 4 | Completed locally in this closeout. ACC-STAGE-010 evidence, recoverability, rollback, Chinese owner feedback, and no-upload stop line are recorded. | `STAGE010_PHASE4_CLOSEOUT.md`, `BATCH001_010_UPLOAD_LOCK.yaml`, `roadmap.yaml`, `events.jsonl` |

## Review Handoff

STAGE-010 implementation phases are locally complete, but the separate
whole-stage review/fix pass has not been executed in this run.

The next run must review STAGE-010 end to end before any batch upload:

1. Verify Phase 1 boundary still matches the P0 taskpack.
2. Verify Phase 2 implementation is read-only and operations-only.
3. Verify Phase 3 scenarios cover the required exception matrix.
4. Verify Phase 4 closeout evidence is complete and truthful.
5. Fix or explicitly gate any review finding.
6. Only after review/fix, evaluate the STAGE-001..010 batch upload gate.

## Changed-File Summary

STAGE-010 local evidence and governance touched these product-scoped files:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE010_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE010_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE010_PHASE2_LOCAL_PATH_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE010_PHASE3_SCENARIO_VALIDATION.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE010_PHASE4_CLOSEOUT.md`
- `KM_IDSystem/scripts/check_local_path_contract.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage010_local_path_contract.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`
- `KM_IDSystem/功能清单.md`
- `KM_IDSystem/开发记录.md`
- `KM_IDSystem/模型参数文件.md`

STAGE-010 did not change backend services, frontend UI, app bundle launchers,
real raw data, generated reports, outputs, dependency folders, or external
projects.

## Final Decision

`ACC-STAGE-010` is locally satisfied at phase-closeout level as a read-only
local path contract and scenario-validation contract, pending the separate
whole-stage review/fix pass.

The accepted capability is intentionally narrow:

- It is an IDS operations entrance diagnostic, not a customer-facing workflow.
- It does not start Docker, backend, frontend, OCR, Embedding, indexing,
  cleanup, backup, manifest, or report jobs.
- It does not create, write, repair, or recursively scan `IDS_DATA_ROOT`.
- It does not open, hash, copy, move, delete, or mutate source material.
- It blocks unsafe source URI, source path, processed path, backup path,
  manifest path, report export path, and unbounded derived-output work before
  local output is created.
- It keeps future v0.2+ architecture open by making local path handling a
  deterministic preflight contract rather than a runtime side effect.

## Environment, Path, Storage, And Contract Evidence

Current shell environment check:

- macOS `15.1`, build `24B83` was recorded in Phase 1.
- Machine architecture `arm64`; CPU `Apple M2 Max` was recorded in Phase 1.
- Root filesystem `/` showed `926Gi` size and `577Gi` available in Phase 1.
- Docker CLI and Docker Compose are visible through the STAGE-006 baseline
  script, but no Docker service is started by STAGE-010.

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

Storage and path-contract evidence:

- STAGE-009 storage-budget smoke with synthetic `1000Gi` total, `300Gi` free,
  and `20Gi` planned output returns `state=BUDGET_OK`,
  `safe_mode=false`, `bounded_preflight_only=true`,
  `customer_visible=false`, `does_not_generate_outputs=true`, and
  `does_not_write_runtime_data=true`.
- STAGE-010 CLI smoke with a temporary source file and synthetic storage
  returns `state=PATH_CONTRACT_OK`, `safe_mode=false`,
  `customer_visible=false`, and no-write/no-scan/no-output/no-manifest/
  no-backup guard fields.
- STAGE-010 scenario smoke returns `overall_valid=true`, including
  `PATH_CONTRACT_OK`, `SOURCE_PATH_NOT_READY`, `SOURCE_URI_INVALID`,
  `PROCESSED_PATH_UNBOUNDED`, `BACKUP_PATH_UNSAFE`,
  `MANIFEST_PATH_UNSAFE`, and `REPORT_EXPORT_PATH_UNSAFE` states.

## Recoverable States

| State | Recovery path |
|---|---|
| `PATH_CONTRACT_OK` | Later stages may run bounded preflight only. Do not auto-start data-moving work. |
| `SOURCE_URI_INVALID` | Correct the source URI to an absolute local `file://` URI and rerun path preflight. |
| `SOURCE_PATH_NOT_READY` | Provide an existing readable source path, reconnect/revalidate external root when required, and rerun path preflight. |
| `PROCESSED_PATH_UNBOUNDED` | Declare an absolute bounded processed path and output budget before derived work starts. |
| `BACKUP_PATH_UNSAFE` | Choose a backup path outside source material and `IDS_DATA_ROOT`; rerun preflight before copying. |
| `MANIFEST_PATH_UNSAFE` | Choose a safe small `.json` or `.jsonl` metadata path outside unsafe roots. |
| `REPORT_EXPORT_PATH_UNSAFE` | Declare a safe bounded report export path before report generation. |
| `PATH_CONTRACT_UNKNOWN` | Treat as fail-closed; require manual operator review and rerun preflight with classifiable evidence. |

## Non-Recoverable Stop States

The following states are not auto-recovered by STAGE-010 and must stop the run:

- Any real raw material deletion, move, overwrite, cleanup, or unapproved copy.
- Any guessed `IDS_DATA_ROOT` creation or unapproved `00-99` directory repair.
- Any recursive scan of `00_ORIGINAL_RAW_DATA` or nested external-drive
  contents by this path-contract preflight.
- Any source file open/hash/copy/move/delete attempt by the path contract.
- Any manifest write, backup copy, processed output, report export, OCR,
  Embedding, or index output created by STAGE-010.
- Any path/storage block that tries to resume data-moving work automatically.
- Unknown validation failure that cannot be classified as a known safe-mode
  state.
- Irreversible schema, runtime-data, or service-state mutation.
- Secrets or credentials appearing in tracked evidence.
- Any push, PR, or merge before the STAGE-001..010 batch is complete,
  reviewed, and repaired.

These are stop conditions, not automatic repair tasks.

## Default Configuration Notes

- `source_uri` must use local `file://` syntax and normalize to an absolute
  local path.
- `processed_path`, `backup_path`, `manifest_path`, and `report_export_path`
  must be explicit absolute paths before any later workflow may write output.
- `manifest_path` must be a small `.json` or `.jsonl` metadata path.
- `backup_path` must not be the source path, inside the source path, or inside
  `IDS_DATA_ROOT`.
- Output paths must not be guessed, auto-created, or written by the path
  contract.
- Internal storage defaults remain inherited from STAGE-009: minimum free space
  `100GiB`, warning free space `200GiB`, and maximum used ratio `85%`.
- `IDS_DATA_ROOT` must come from explicit environment/config in later stages.
- `00_ORIGINAL_RAW_DATA` remains read-only by default.
- The local path contract is bound to `IDS 系统运营入口`;
  `customer_visible=false`.
- `auto_resume=false` even when a bounded preflight is allowed.
- Safe mode pauses `bulk_import`, `recursive_directory_scanning`,
  `raw_material_cleanup`, `ocr`, `embedding`, `index_rebuild`, `backup_copy`,
  `manifest_generation`, `report_export`, and `batch_report_generation`.

## Acceptance Evidence

- P0 STAGE-010 taskpack SHA recorded in Phase 1:
  `b459c6cac1b79be5a2904308236be2e41356adadfce9bf6a6f5febd27e3fa0a6`
- Stage execution index:
  `STAGE-010,D02-S005,本地路径合同,...,ACC-STAGE-010,...,stages/STAGE-010_本地路径合同.md`
- Phase 1 boundary evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE010_PHASE1_SCOPE_BOUNDARY.md`
- Phase 2 implementation evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE010_PHASE2_LOCAL_PATH_CONTRACT.md`
- Phase 3 scenario evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE010_PHASE3_SCENARIO_VALIDATION.md`
- Phase 4 closeout evidence:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE010_PHASE4_CLOSEOUT.md`
- Executable local path contract:
  `KM_IDSystem/scripts/check_local_path_contract.py`
- Focused tests:
  `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage010_local_path_contract.py`

## Final Validation Evidence

Fresh Phase 4 validation in this run:

- `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage010_local_path_contract.py -q`
  returned `Ran 7 tests`, `OK`.
- `python3 -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage006_environment_baseline.py KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage007_ids_data_root_detector.py KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage008_removable_drive_state.py KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage009_storage_budget.py -q`
  returned `Ran 25 tests`, `OK`.
- `python3 -B -m py_compile KM_IDSystem/scripts/check_local_path_contract.py`
  passed without tracked output.
- STAGE-010 CLI smoke through `check_local_path_contract.py` returned
  `state=PATH_CONTRACT_OK` and confirmed no output, manifest, or backup writes.
- Scenario smoke through `build_stage010_scenario_report(...)` returned
  `overall_valid=true`, scenario states `PATH_CONTRACT_OK`,
  `SOURCE_PATH_NOT_READY`, `SOURCE_URI_INVALID`, and
  `PROCESSED_PATH_UNBOUNDED`, plus role-risk states `BACKUP_PATH_UNSAFE`,
  `MANIFEST_PATH_UNSAFE`, and `REPORT_EXPORT_PATH_UNSAFE`.
- Static boundary search found no production-script `mkdir`, `open`, `os.walk`,
  `rglob`, `glob`, `rmtree`, `unlink`, `subprocess`, `write_text`,
  `write_bytes`, or `auto_resume=True` match in
  `KM_IDSystem/scripts/check_local_path_contract.py`.
- `python3 -B scripts/lean_governance.py check-render --project KM_IDSystem`
  returned `drift_count=0`, `reference_issue_count=0`.
- `git diff --check` passed.
- `python3 -B scripts/lean_governance.py validate --project KM_IDSystem --semantic`
  returned sync validation `errors: 0`, `warnings: 0`, followed by the known
  28 sparse-worktree/root-governance/unrelated-project errors and no STAGE-010
  product blocker.

Do not expand unrelated projects to satisfy the sparse-worktree diagnostic.

## Rollback

Rollback Phase 4 by reverting the local `IDS-V0_1-STAGE010-P4` commit. This
removes only the closeout document, batch-lock/roadmap/event updates, and
rendered owner views.

Rollback the whole stage, if required, in reverse order:

1. Revert `IDS-V0_1-STAGE010-P4`.
2. Revert `IDS-V0_1-STAGE010-P3`.
3. Revert `IDS-V0_1-STAGE010-P2`.
4. Revert `IDS-V0_1-STAGE010-P1`.

No Docker cleanup, runtime-data cleanup, external-drive cleanup, dependency
cleanup, report cleanup, output cleanup, manifest cleanup, backup cleanup, or
GitHub PR cleanup is needed because STAGE-010 did not create those artifacts.

## Chinese Owner Feedback

STAGE-010 已把本地路径合同收束成可验证的只读前置检查：系统能区分
`file://` 来源、源文件可用性、processed、backup、manifest、报告导出路径、
移动硬盘状态和存储预算风险。

这一步不会导入资料、不会扫描外接盘内容、不会复制备份、不会写 manifest、
不会生成报告，也不会自动恢复被暂停的大批量任务。后续阶段如果要真正导入、
OCR、Embedding、索引、备份或导出报告，必须先通过这个路径合同和存储预算
检查。

下一步不是上传 GitHub，而是对 STAGE-010 做整阶段复审并修复复审发现。只有
STAGE-001..010 全部完成、复审并修复后，才允许把 10 个 Stage 作为一个批次
上传到 GitHub main tree。
