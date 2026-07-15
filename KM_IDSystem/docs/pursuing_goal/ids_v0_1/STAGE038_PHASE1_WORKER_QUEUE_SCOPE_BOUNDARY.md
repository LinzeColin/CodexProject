# STAGE-038 Phase 1 - Worker Queue Scope Boundary

## Identity And Source Status

- Stage: `STAGE-038 · Worker 队列基线`
- Task: `IDS-V0_1-STAGE038-P1`
- Source-reverification task: `IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY`
- Acceptance: `ACC-STAGE-038`
- Local code: `D07-S002`
- Domain: `D07 · 任务编排与机器控制`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Pursuing goal:
  `建立异步 worker 队列，避免长任务阻塞前端和 API。`
- Source member:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-038_Worker队列基线.md`
- `P0 source verification: SOURCE_VERIFIED`
- `P0 SHA-256: 613acde3cc8f9b8fdc267eb1b0f3076fbce6e858a0d00c3840a2bd730faa7634`
- `source_archive_path=/Users/linzezhang/Downloads/IDS_Taskpack_v0_1_only_中文修订版.zip`
- `source_archive_sha256=55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3`
- `source_member=IDS_v0_1_Final_Chinese_Revised/stages/STAGE-038_Worker队列基线.md`
- `source_member_match_count=1`
- `source_member_integrity=OK`
- `source_member_sha256=613acde3cc8f9b8fdc267eb1b0f3076fbce6e858a0d00c3840a2bd730faa7634`
- `roadmap_sha256=a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6`
- `instructions_sha256=ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8`
- `source_verification_status=SOURCE_VERIFIED`
- `reconciliation_status=passed`
- `source_reverification_required_before_phase2=false`
- `independent_review_status=passed`
- `phase2_entry_authorized=true`

This document is the corrected Phase 1 engineering boundary. It replaces the
earlier source-limited assumption that all retry, dead-letter, backpressure,
lock, automatic-lifecycle, crash-recovery, and cleanup definitions belonged
entirely to later stages. The verified taskpack requires STAGE-038 Phase 1 to
define those interfaces and safety boundaries; STAGE-039..044 still own their
runtime policy and implementation details.

## Authoritative Upstream Contracts

- `worker_queue_contract_id=ids.worker_queue_baseline.v0_1.p1`
- `worker_queue_contract_status=SOURCE_RECONCILED_PHASE1_CONTRACT`
- `job_control_envelope_schema=ids.job_control_envelope.v1`
- `job_state_model_version=ids.job_state.v1`
- Only `QUEUED` jobs are queue-eligible.
- Queue status is not a second job lifecycle state.
- The STAGE-022 priority vocabulary remains owner-governed.
- STAGE-030 control-plane limit: `payload_size_bytes <= 1048576`.

The queue may transport state-model refs but cannot redefine lifecycle or
persist a transition without current `job_id`, state, version, and claim proof.

## API, Queue, And Worker Boundary

1. Frontend and API request handlers may submit a bounded job-control request
   and return an owner-readable acknowledgement; they must not execute long
   import/archive/parse/OCR/chunk/embed/index/report work inline.
2. Queue admission accepts only a reviewed `ids.job_control_envelope.v1`
   reference floor. A queue entry may contain bounded metadata refs only:
   `job_id`, `state_version`, `idempotency_key`, `priority_ref`,
   `resource_gate_refs`, `dependency_refs`, `input_refs`, `output_refs`,
   `checkpoint_ref`, `error_ref`, `cleanup_manifest_ref`, and `audit_ref`.
3. Worker execution, queue persistence, queue-entry timestamps, sequence
   allocation, claim persistence, and output production are Phase 2 or later
   concerns and are not performed by this Phase 1 correction.
4. Raw source bodies and plaintext secrets are forbidden. Future queue
   persistence may store refs, not source content.

## Admission And Idempotency Floor

- Priority is an owner-approved priority_ref from:
  `P0_CRITICAL_ENGINEERING_DATA`, `P1_HIGH_VALUE_ENGINEERING_DATA`,
  `P2_SUPPORTING_ENGINEERING_DATA`, or `P3_LOW_VALUE_OR_DEFERRED_DATA`.
- `ordering_policy=DEFERRED_TO_PHASE2_NO_NUMERIC_POLICY_IN_P1`; numeric
  priority weights are not invented.
- `enqueue_idempotency_contract=REQUIRE_ENVELOPE_IDEMPOTENCY_KEY_NO_DUPLICATE_ENTRY`.
  `idempotency_key is required`, is an opaque bounded control value supplied
  by the upstream job contract, and must not be derived from raw source bodies.
  Duplicate admission must return the existing queue-entry reference instead
  of creating a second queue entry.
- `dependency_admission_contract=PHASE2_DEFINITION_REQUIRED_FAIL_CLOSED`;
  missing dependency evidence fails closed. P1 does not invent that all
  dependency refs must have one universal terminal state.
- Exact queue ordering, tie-breaking, capacity, sequence allocation, and
  duplicate response shape are required Phase 2 decisions.

## Claim And Lock Floor

- `claim_transport_contract=PHASE2_DEFINITION_REQUIRED_STAGE041_RUNTIME`
- `claim_atomic_sequence=PHASE2_DEFINITION_REQUIRED_STAGE041_RUNTIME`
- Inherited claim dimensions include `job_id`, `expected_state=QUEUED`,
  `expected_state_version`, `lease_owner_ref`, `lease_expires_at`,
  `fencing_token`, and `lock_key`.
- `lock_granularity=RESOURCE_CONFLICT_DOMAIN_NOT_GLOBAL_QUEUE`: the lock key
  identifies the smallest canonical source/output namespace whose concurrent
  mutation could duplicate work or corrupt output. A global queue lock is not
  the default.
- STAGE-041 owns lock, lease, renewal, and fencing runtime. Missing or stale
  claim proof fails closed, and a stale worker cannot commit.

No claim request, queue version, acquisition order, lease duration, renewal
cadence, timeout, fencing store, or persistence schema is implemented here.

## Retry, Dead Letter, Backpressure, Lifecycle, Recovery, And Cleanup

- STAGE-038 defines retry/dead-letter interface: failures retain bounded
  `safe_error_code`, `error_ref`, `attempt_id`, retry state, and `audit_ref`;
  exhausted or non-retryable work is owner-visible. STAGE-039 owns retry
  scheduling and dead-letter runtime, including numeric limits and timing.
- STAGE-038 defines resource-gate backpressure interface: relevant jobs pause
  on `external_drive_offline`, `disk_space_insufficient`, or
  `external_api_budget_insufficient`. STAGE-040 owns measured backpressure and
  fairness runtime, thresholds, capacity, and resume measurements.
- STAGE-038 defines lock granularity and claim-proof requirements; STAGE-041
  owns lock/lease/fencing runtime.
- STAGE-038 defines automatic lifecycle interface: only STAGE-037 transitions
  may represent run, pause, resume, cancel, success, or failure. STAGE-042 owns
  automatic run, pause, resume, and shutdown runtime.
- STAGE-038 defines crash-recovery checkpoint boundary: active work carries a
  bounded `checkpoint_ref` or safe failure/quarantine evidence where required.
  STAGE-043 owns worker-crash recovery runtime.
- STAGE-038 defines cleanup allowlist boundary: deletion requires an explicit
  `cleanup_manifest_ref` and may target only temporary or rebuildable outputs.
  Facts, manifests, evidence ledgers, audit logs, and report snapshots are
  protected. STAGE-044 owns half-product cleanup runtime and deletion safety.

## Current Run Non-Goals

Mandatory stop markers:
`NO_PHASE2`, `NO_QUEUE_RUNTIME`, `NO_WORKER_RUNTIME`,
`NO_CLAIM_PERSISTENCE`, `NO_SCHEMA_CHANGE`, `NO_POSTGRES_CONNECTION`,
`NO_RUNTIME_OUTPUT`, `NO_STAGE039`, `NO_GITHUB_UPLOAD`, `NO_APP_REINSTALL`.

This run does not create a queue adapter, worker, scheduler, service, API, UI,
migration, database record, runtime log, job, report, app entry, PR, issue, or
upload. It does not execute any retry, dead-letter, backpressure, lock,
automatic lifecycle, crash recovery, or cleanup behavior.

## Raw And Real-Data Boundary

- `/Users/linzezhang/Downloads/IDS_MetaData` is path-only. 不得读取、列出、hash、
  打开、复制、移动、删除、修改、dump 或扫描其任何内容。
- 不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据。
- `raw source bodies are forbidden` from queue entries and claim transport.
- `plaintext secrets are forbidden` from queue entries and audit text.
- `future queue persistence may store refs, not source content`.
- `taskpack_source_read_performed=true`
- `ids_business_source_read_performed=false`
- `raw_metadata_content_accessed=false`
- `database_connection_performed=false`
- `real_job_created=false`
- `fake_ids_business_data_used=false`

## Phase 2 Entry Gate

The exact source requirement and independent review gate are satisfied, so the
next separate run is authorized to enter Phase 2. This source-reverification
run did not execute Phase 2.

Phase 2 must implement the approved isolated non-production asynchronous
worker queue slice: keep long work outside frontend/API request lifecycles,
exercise STAGE-037 state transitions and at least one retry, backpressure, or
automatic-run slice, map machine state to restrained Chinese owner status, and
record bounded input/output/error/checkpoint refs. It must not access raw
metadata, use fake IDS business data, activate production, or take over the
dedicated STAGE-039..044 runtime policies.

## Rollback

Revert only Stage038 source-reverification evidence, this corrected Phase 1
boundary, entry contract, focused tests, Stage005 validator/test support,
batch/roadmap/event changes, handoff/changelog, and rendered owner views.
Preserve STAGE-037 and earlier evidence, user-owned dirty files, raw metadata,
databases, source/runtime content, reports, indexes, app entries, and GitHub.
