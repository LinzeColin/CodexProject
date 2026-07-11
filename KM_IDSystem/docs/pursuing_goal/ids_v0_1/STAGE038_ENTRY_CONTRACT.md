# IDS v0.1 STAGE-038 Entry Contract

## Task Identity
- Stage: `STAGE-038 · Worker 队列基线`
- Task: `IDS-V0_1-STAGE038-P1`
- Acceptance: `ACC-STAGE-038`
- Version: `v0.1`
- Local code: `D07-S002`
- Domain: `D07 · 任务编排与机器控制`
- Entrance: `IDS 系统运营入口`
- Phase scope: `Phase 1 · 范围、输入输出与边界确认`
- Tracked taskpack reference:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-038_Worker队列基线.md`
- `P0 source verification: EXTERNAL_TASKPACK_ABSENT`
- `P0 SHA-256: UNKNOWN_UNDER_IDS-V0_1-STAGE038-P1`
- `source_reverification_required_before_phase2=true`

The exact external taskpack body was not available at its approved path when
this run started. This Phase 1 contract therefore uses only the tracked
execution-index identity and the intersection of reviewed STAGE-037, STAGE-022,
and STAGE-030 contracts. It does not invent a taskpack hash, acceptance wording,
runtime behavior, or numeric queue policy. The source must be reverified before
Phase 2 begins; any conflict stops implementation and requires a P1 correction.

## Preconditions
- STAGE-037 is `completed_reviewed_local`; its canonical envelope is
  `job_control_envelope_schema=ids.job_control_envelope.v1` and its lifecycle
  authority is `job_state_model_version=ids.job_state.v1`.
- STAGE-022 defines the four owner-governed priority classes. Phase 1 preserves
  those names and invents no numeric weights.
- STAGE-030 bounds control-plane payload metadata with
  `payload_size_bytes <= 1048576`.
- `BATCH031_040_UPLOAD_LOCK.yaml` remains active with `push_allowed=false`.
- `/Users/linzezhang/Downloads/IDS_MetaData` remains path-only governance
  context. 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描
  that directory or any child content.

## Phase 1 Contract
The source-limited identity is
`worker_queue_contract_id=UNASSIGNED_UNTIL_SOURCE_REVERIFICATION` with
`worker_queue_contract_status=PROVISIONAL_SOURCE_LIMITED_BOUNDARY`.
Phase 1 records only inherited constraints and decision dimensions that the
approved taskpack must resolve. It does not choose an exact ordering tuple,
idempotency key, dependency policy, queue-entry schema, claim-request schema,
or atomic claim sequence. It performs no enqueue, dequeue, claim, worker
execution, state transition, persistence, database action, or source read.

Only the reviewed STAGE-037 lifecycle remains authoritative: only `QUEUED` jobs
are queue-eligible, and queue status is not a second job lifecycle state. A
queue entry may contain bounded metadata refs only: `job_id`, `state_version`,
`priority_ref`, `resource_gate_refs`, `dependency_refs`, and `audit_ref`.
The exact approved field set remains source-gated. Any future persistence may
store refs, not source content; raw source bodies and plaintext secrets are
forbidden.

## Ownership Boundary
- `STAGE-039 owns retry scheduling and dead-letter policy`.
- `STAGE-040 owns measured backpressure and fairness policy`.
- `STAGE-041 owns lock/lease/fencing runtime`.
- `STAGE-042 owns automatic run, pause, resume, and shutdown`.
- `STAGE-043 owns worker-crash recovery`.
- `STAGE-044 owns half-product cleanup`.

STAGE-038 does not absorb those policies. In particular, exact concurrency,
queue capacity, fairness weights, lease duration, renewal cadence, fencing
storage, retry delay, and cleanup behavior remain deferred to their owners.

## Explicit Non-Goals
- `NO_PHASE2`: no machine-readable contract, checker, evaluator, or queue
  candidate implementation in this run.
- `NO_QUEUE_RUNTIME`: no enqueue, dequeue, reserve, prioritize, or dispatch.
- `NO_WORKER_RUNTIME`: no worker process, job execution, checkpoint, or output.
- `NO_CLAIM_PERSISTENCE`: no lease, claim, lock, or fencing record is written.
- `NO_SCHEMA_CHANGE`: no SQL, migration, registry, or table change.
- `NO_POSTGRES_CONNECTION`: no connection, pool, transaction, query, or row.
- `NO_RUNTIME_OUTPUT`: no queue file, job row, log, report, index, or artifact.
- `NO_STAGE039`: no retry/dead-letter or later-stage implementation.
- `NO_GITHUB_UPLOAD`: no push, PR, merge, issue mutation, or batch gate.
- `NO_APP_REINSTALL`: no launcher or app entry installation.
- 不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据.

## Verified No-Action Record
- `phase2_entry_authorized=false`
- `source_read_performed=false`
- `database_connection_performed=false`
- `real_job_created=false`
- `fake_ids_business_data_used=false`

## Acceptance Evidence
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_baseline.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`

## Stop And Rollback
Stop if the exact external taskpack cannot be reverified before Phase 2, if it
conflicts with this conservative boundary, if any runtime or data access is
required, or if a shared contract/test fails without explanation.

Rollback only the `IDS-V0_1-STAGE038-P1` entry/scope evidence, focused test,
Stage005 validator/test support, batch/roadmap/event changes, handoff/changelog,
and rendered owner views. Preserve prior stages, raw metadata, databases,
source/runtime data, reports, app entries, and GitHub state.
