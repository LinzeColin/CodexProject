# IDS v0.1 STAGE-037 Entry Contract

## Taskpack Identity
- Stage: `STAGE-037 · 任务状态模型`
- Task: `IDS-V0_1-STAGE037-P1`
- Acceptance: `ACC-STAGE-037`
- Version: `v0.1`
- Local code: `D07-S001`
- Domain: `D07 · 任务编排与机器控制`
- Entrance: `IDS 系统运营入口`
- Pursuing goal:
  `定义 import、archive、parse、ocr、chunk、embed、index、report 的统一 job 状态机。`
- Phase scope: `Phase 1 · 范围、输入输出与边界确认`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-037_任务状态模型.md`
- P0 stage file SHA-256:
  `ab1296ab690e445f2ae915ff508d68e9fac40c888cd9ce851bfcc0cf5ce77dc2`

## Preconditions
- `STAGE-036` is `completed_reviewed_local`; its state-registry structure is
  tracked but no STAGE-037 values were inserted or applied to PostgreSQL.
- `BATCH031_040_UPLOAD_LOCK.yaml` remains active with `push_allowed=false`.
- STAGE-008 removable-drive state, STAGE-009 storage budget, STAGE-011 safe
  mode, STAGE-016 import idempotency, STAGE-022 data priority, STAGE-030
  `ids_jobs`, and STAGE-031..036 database safety contracts remain authoritative.
- The raw metadata root `/Users/linzezhang/Downloads/IDS_MetaData` is path-only.
  This phase must not read, list, hash, open, copy, move, delete, modify, dump,
  scan, normalize, restore, or commit any content under that path.

## Phase 1 Contract
This phase defines one versioned job-state engineering contract. It separates
the durable lifecycle state from pause/retry/error/cleanup reasons, binds every
transition to compare-and-set and append-only audit requirements, and defines
the interfaces later stages must implement. It does not create a queue, worker,
lock, database migration, state-registry row, runtime job, or output artifact.

Canonical job types:
`IMPORT, ARCHIVE, PARSE, OCR, CHUNK, EMBED, INDEX, REPORT`

Canonical job states:
`CREATED, QUEUED, CLAIMED, RUNNING, PAUSE_REQUESTED, PAUSED, RETRY_WAIT, SUCCEEDED, FAILED, DEAD_LETTERED, CANCELLED`

The canonical registry identity is `state_namespace=job_state`; the compatible
state membership is versioned as `state_model_version=ids.job_state.v1`.
Phase 1 records this contract only and writes no state-registry row.

The state set is deliberately small. Resource conditions such as drive offline,
low disk, API budget exhaustion, backpressure, dependency unavailability, or
owner hold are `pause_reason_code` values and evidence refs; pause reason is not
a job state. Retry classification, exact backoff values, queue limits, resource
thresholds, lease durations, and lock timeouts remain
`POLICY_VALUE_DEFERRED_TO_STAGE039_040_041`.

## Downstream Ownership
- `STAGE-038` implements the worker queue and claim transport.
- `STAGE-039` implements retry scheduling, failure classification, and
  dead-letter handling.
- `STAGE-040` implements measured backpressure and pause admission.
- `STAGE-041` implements lock registration, lease renewal, and fencing.
- `STAGE-042` implements automatic run/pause/resume/shutdown policy.
- `STAGE-043` implements worker-crash recovery.
- `STAGE-044` implements half-product cleanup from an explicit cleanup allowlist.

Phase 1 defines compatibility interfaces for those stages but performs none of
their runtime behavior.

## Explicit Non-Goals
- `NO_PHASE2`: no machine index, checker, registry payload, schema, service,
  API, UI, queue, worker, scheduler, or runtime state transition.
- `NO_QUEUE_IMPLEMENTATION`: do not enqueue, dequeue, prioritize, reserve, or
  dispatch a task.
- `NO_WORKER_EXECUTION`: do not claim work, renew a lease, execute a job,
  retry, dead-letter, pause, resume, cancel, shut down, or clean an artifact.
- `NO_STATE_REGISTRY_WRITE`: do not populate `ids_state_value_registry` or
  claim that the Stage036 migration was applied.
- `NO_SCHEMA_CHANGE`: do not edit STAGE-030/036 SQL or create a migration.
- `NO_POSTGRES_CONNECTION`: do not connect to PostgreSQL, instantiate a pool,
  open a transaction, query rows, or write job/control-plane records.
- `NO_RUNTIME_OUTPUT`: do not create a database, queue file, job record,
  checkpoint, error log, lock record, cleanup manifest, report, PDF, index,
  evidence event, fixture row, screenshot, or generated output.
- `NO_FAKE_DATA`: no fake IDS business data, fake database rows, fake source
  documents, placeholder corpus, fabricated jobs, profiles, logs, or evidence.
- `NO_STAGE038`: do not enter STAGE-038 or any later stage in this run.
- Do not install dependencies, start services, call external APIs, upload to
  GitHub, create/merge a PR, mutate issues, reinstall app entries, run stage or
  batch review, or run an upload gate.

## Source And Cleanup Protection
- `00_ORIGINAL_RAW_DATA`, source files, source databases, manifest, evidence
  ledger, audit log, report snapshot, and active index are never cleanup targets.
- A future cleanup action may remove only attempt-owned temporary artifacts
  listed by an exact `cleanup_manifest_ref` under an approved staging/cache
  boundary. The cleanup allowlist must fail closed on unknown ownership.
- A state transition never authorizes deletion. Cleanup is a separately
  audited action owned by STAGE-044.

## Acceptance Evidence
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage037_job_state_model.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`

## Stop And Rollback
Stop on an unexplained test failure, a shared-contract conflict, any request for
raw/real task execution without an owner-authorized bounded source, any
non-reversible schema proposal, or any attempt to exceed Phase 1.

Rollback only the `IDS-V0_1-STAGE037-P1` entry/scope evidence, focused tests,
batch/roadmap/event updates, Stage005 compatibility updates, and rendered owner
views. Do not touch raw data, PostgreSQL, manifests, evidence, audit logs,
reports, indexes, app entries, GitHub state, or prior Stage evidence.
