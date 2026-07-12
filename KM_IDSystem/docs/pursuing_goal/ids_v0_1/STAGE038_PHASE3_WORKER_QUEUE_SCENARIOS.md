# STAGE-038 Phase 3 - Worker Queue Scenarios

## Identity

- Stage: `STAGE-038 · Worker 队列基线`
- Task: `IDS-V0_1-STAGE038-P3`
- Acceptance: `ACC-STAGE-038`
- Report schema: `ids.stage038.worker_queue_baseline.phase3.report.v1`
- Execution mode: `ISOLATED_NON_PRODUCTION_WORKER_QUEUE_SCENARIOS`
- Next gate: `IDS-STAGE038-P4-GATE`

## Scope And Source

Phase 3 implements and validates the six required scenarios from the uniquely
verified Stage038 taskpack member. The machine contract binds the repaired
Phase 2 checker, index, and evidence by SHA-256 before any scenario runs.

The scenarios use the real Git-tracked Phase 1 control document as their only
operation input. They do not use an IDS business corpus, fake database rows,
placeholder records, fabricated reports, or fabricated execution evidence.

## TDD Evidence

The initial focused run failed all 8 tests as expected:

- four operation types produced four different resource lock keys;
- all four same-source operations were accepted instead of conflict-paused;
- the Phase 3 checker, machine contract, evidence, and governance state did
  not yet exist.

After repair, `job_id` and `idempotency_key` remain job-type-specific, while
`lock_key` is derived from `task_id + input_ref`. A distinct active operation
over the same source returns `RESOURCE_CONFLICT_ACTIVE` before creating a
second queue record. Terminal records release that admission conflict.

## Scenario Matrix

The checker executes six required scenarios and returns `PASS` only when every
assertion is true:

| Scenario | Real action | Required result |
|---|---|---|
| `duplicate_click_one_execution` | Two actual in-memory submissions and one worker operation | The second click returns the existing entry; one operation runs. |
| `worker_crash_exception_and_lock_release` | One actual worker operation raises `RuntimeError`; a same-source follow-up then runs | First record is `FAILED`, output/checkpoint stay empty, lock is released, follow-up succeeds. |
| `external_drive_offline_pause_before_queue` | Control-gate input only; no hardware event is claimed | `PAUSED_EXTERNAL_DRIVE_OFFLINE`, Chinese `已暂停`, zero queue records. |
| `actual_low_disk_boundary_pause_without_allocation` | Reads actual project-volume free bytes and requests exactly free bytes plus one | `PAUSED_LOW_DISK`, zero queue records, zero allocation. |
| `same_source_cross_operation_lock` | Submits `ARCHIVE`, `PARSE`, `INDEX`, and `REPORT` against one real tracked ref | One shared key, one accepted record, three `RESOURCE_CONFLICT_ACTIVE` results, one operation. |
| `protected_cleanup_denied` | Evaluates four real Git-tracked refs without calling delete | Fact source, evidence ledger, report snapshot, and audit log all return `PROTECTED_ARTIFACT`. |

The worker-crash case is an actual exception path inside the isolated worker;
it is not a process-kill or STAGE-043 crash-recovery implementation.
`physical_drive_removal_performed=false`: the removable-drive case validates
the required fail-closed admission gate and does not claim that hardware was
physically removed. `disk_allocation_performed=false` and
`cleanup_runtime_performed=false`.

## Protected Artifacts

The cleanup evaluator has no deletion API. It verifies that these Git-tracked
artifact classes are protected before any cleanup action:

- `FACT_SOURCE`
- `EVIDENCE_LEDGER`
- `REPORT_SNAPSHOT`
- `AUDIT_LOG`

No delete attempt is made. The checker reports
`protected_ref_delete_performed=false`. STAGE-044 retains cleanup runtime
ownership; STAGE-041 retains production lock, lease, and fencing ownership.

## Truth Boundary

- `production_runtime_activation_performed=false`
- `persistent_queue_write_performed=false`
- `database_connection_performed=false`
- `schema_change_performed=false`
- `state_registry_write_performed=false`
- `runtime_output_written=false`
- `ids_business_source_read_performed=false`
- `raw_metadata_content_accessed=false`
- `fake_ids_business_data_used=false`
- `real_ids_business_job_created=false`
- `physical_drive_removal_performed=false`
- `disk_allocation_performed=false`
- `cleanup_runtime_performed=false`
- `protected_ref_delete_performed=false`
- `push_allowed=false`

`/Users/linzezhang/Downloads/IDS_MetaData` remains path-only governance
context. This phase did not read, list, hash, open, copy, move, delete, modify,
dump, or scan content under that path.

## Validation

Run from the repository root:

```bash
python3 -B -m unittest -q KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage038_worker_queue_scenarios
python3 -B -m unittest -q KM_IDSystem.docs.pursuing_goal.ids_v0_1.tests.test_stage038_worker_queue_runtime
python3 -B KM_IDSystem/scripts/check_worker_queue_scenarios.py
python3 -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage005_governance_regression.py
```

The Phase 3 checker prints one JSON report to stdout. It writes no scenario
report, queue record, database row, evidence ledger, audit log, report
snapshot, or runtime output file.

## Stop Conditions

- `NO_PHASE4`: do not enter Phase 4 or whole-stage review in this run.
- Do not activate production queue, worker, persistence, lock service,
  lifecycle automation, crash recovery, or cleanup.
- Do not access raw metadata content or use fake IDS business data.
- Do not upload GitHub, create or merge a PR, mutate issues, reinstall app
  entries, run batch review, or run an upload gate.

## Rollback

Revert the Phase 3 checker, machine contract, focused test, Phase 2 lock-domain
compatibility repair, this evidence file, Stage005 compatibility changes,
batch/roadmap/event updates, handoff/changelog, and rendered owner views only.
Preserve prior stages, user-owned dirty files, raw metadata, databases,
runtime data, reports, app entries, and GitHub state.

## 中文 Owner 反馈

Stage 38 Phase 3 已完成六类隔离场景验证。同源处理、解压、索引和报告任务共享
一个资源冲突键；重复点击只执行一次；worker 异常进入失败终态并释放锁；移动介质
离线和磁盘不足在入队前暂停；事实源、证据账本、报告快照和审计日志均禁止后台
清理。生产队列、原始资料访问和 GitHub 上传继续禁用，下一步只能进入独立
`IDS-STAGE038-P4-GATE`。
