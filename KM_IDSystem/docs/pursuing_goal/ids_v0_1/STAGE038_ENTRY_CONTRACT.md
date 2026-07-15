# IDS v0.1 STAGE-038 Entry Contract

## Task Identity

- Stage: `STAGE-038 · Worker 队列基线`
- Phase task: `IDS-V0_1-STAGE038-P1`
- Source-reverification task: `IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY`
- Acceptance: `ACC-STAGE-038`
- Version: `v0.1`
- Local code: `D07-S002`
- Domain: `D07 · 任务编排与机器控制`
- Entrance: `IDS 系统运营入口`
- Phase scope: `Phase 1 · 范围、输入输出与边界确认`
- Pursuing goal:
  `建立异步 worker 队列，避免长任务阻塞前端和 API。`

## Verified Source Binding

- External archive:
  `/Users/linzezhang/Downloads/IDS_Taskpack_v0_1_only_中文修订版.zip`
- Exact member:
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

The exact Stage038 member was read directly from the named archive without
extracting the taskpack. Its integrity check returned `OK`, and the standalone
v0.1-only roadmap confirms the same title, goal, non-parallel direction, and
8-16 hour Stage estimate. The v0.1-only instructions confirm one Stage per run.
The durable verification and reconciliation record is
`STAGE038_PHASE1_SOURCE_REVERIFICATION.md`; the independent gate is recorded in
`STAGE038_PHASE1_SOURCE_REVERIFICATION_REVIEW.md`. Phase 2 is authorized only
as the next separate run and was not executed by this task.

## Preconditions

- STAGE-037 is `completed_reviewed_local`; its canonical envelope is
  `job_control_envelope_schema=ids.job_control_envelope.v1` and its lifecycle
  authority is `job_state_model_version=ids.job_state.v1`.
- STAGE-022 defines the four owner-governed priority classes. No numeric weight
  is introduced here.
- STAGE-030 bounds control-plane payload metadata with
  `payload_size_bytes <= 1048576` and forbids raw bodies in the control plane.
- `BATCH031_040_UPLOAD_LOCK.yaml` remains active with `push_allowed=false`.
- `/Users/linzezhang/Downloads/IDS_MetaData` remains path-only governance
  context. 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描该目录
  或其任何子内容。

## Source-Reconciled Phase 1 Contract

- `worker_queue_contract_id=ids.worker_queue_baseline.v0_1.p1`
- `worker_queue_contract_status=SOURCE_RECONCILED_PHASE1_CONTRACT`
- API and frontend request lifecycles may submit or request control actions,
  but long-running import, archive, parse, OCR, chunk, embed, index, and report
  work belongs outside the synchronous request lifecycle.
- Only `QUEUED` jobs are queue-eligible. Queue status is not a second job
  lifecycle state and cannot bypass STAGE-037 transitions.
- A queue entry may contain bounded metadata refs only, including `job_id`,
  `state_version`, `idempotency_key`, `priority_ref`, `resource_gate_refs`,
  `dependency_refs`, `input_refs`, `output_refs`, `checkpoint_ref`,
  `error_ref`, `cleanup_manifest_ref`, and `audit_ref`. This is a field floor,
  not the final Phase 2 schema.
- `ordering_policy=DEFERRED_TO_PHASE2_NO_NUMERIC_POLICY_IN_P1`; numeric
  priority weights are not invented.
- `enqueue_idempotency_contract=REQUIRE_ENVELOPE_IDEMPOTENCY_KEY_NO_DUPLICATE_ENTRY`:
  `idempotency_key is required`; the queue must not derive it from raw source
  bodies, and duplicate admission must return the existing queue-entry
  reference rather than create a second entry.
- `dependency_admission_contract=PHASE2_DEFINITION_REQUIRED_FAIL_CLOSED`;
  missing dependency evidence fails closed. P1 does not invent a universal
  dependency-success rule.
- `claim_transport_contract=PHASE2_DEFINITION_REQUIRED_STAGE041_RUNTIME` and
  `claim_atomic_sequence=PHASE2_DEFINITION_REQUIRED_STAGE041_RUNTIME`.
- `lock_granularity=RESOURCE_CONFLICT_DOMAIN_NOT_GLOBAL_QUEUE`: `lock_key`
  identifies the smallest canonical input/output resource conflict domain;
  STAGE-041 defines and runs the lease/lock/fencing mechanism.

## Stage038 Baseline Versus Downstream Runtime

- STAGE-038 defines retry/dead-letter interface; STAGE-039 owns retry
  scheduling and dead-letter runtime.
- STAGE-038 defines resource-gate backpressure interface; STAGE-040 owns
  measured backpressure and fairness runtime.
- STAGE-038 defines lock granularity and claim-proof requirements; STAGE-041
  owns lock/lease/fencing runtime.
- STAGE-038 defines automatic lifecycle interface; STAGE-042 owns automatic
  run, pause, resume, and shutdown runtime.
- STAGE-038 defines crash-recovery checkpoint boundary; STAGE-043 owns
  worker-crash recovery runtime.
- STAGE-038 defines cleanup allowlist boundary; STAGE-044 owns half-product
  cleanup runtime.

The baseline requires relevant work to pause on `external_drive_offline`,
`disk_space_insufficient`, or `external_api_budget_insufficient`. It requires
retry/error/checkpoint/audit refs and allows cleanup only through an explicit
`cleanup_manifest_ref`. Facts, manifests, evidence ledgers, audit logs, and
report snapshots are protected. Exact thresholds, retry timing, capacity,
fairness, lease duration, renewal, crash takeover, and deletion mechanics stay
with STAGE-039..044.

## Explicit Non-Goals For This Run

- `NO_PHASE2`: no Phase 2 implementation in this run.
- `NO_QUEUE_RUNTIME`: no enqueue, dequeue, reserve, prioritize, or dispatch.
- `NO_WORKER_RUNTIME`: no worker process or job execution.
- `NO_CLAIM_PERSISTENCE`: no lease, claim, lock, or fencing record is written.
- `NO_SCHEMA_CHANGE`: no SQL, migration, registry, or table change.
- `NO_POSTGRES_CONNECTION`: no connection, pool, transaction, query, or row.
- `NO_RUNTIME_OUTPUT`: no queue file, job row, log, report, index, or artifact.
- `NO_STAGE039`: no retry/dead-letter or later-stage runtime implementation.
- `NO_GITHUB_UPLOAD`: no push, PR, merge, issue mutation, or batch gate.
- `NO_APP_REINSTALL`: no launcher or app entry installation.
- 不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据。

## Verified No-Action Record

- `taskpack_source_read_performed=true`
- `ids_business_source_read_performed=false`
- `raw_metadata_content_accessed=false`
- `database_connection_performed=false`
- `real_job_created=false`
- `fake_ids_business_data_used=false`

## Acceptance Evidence

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_SOURCE_REVERIFICATION.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_SOURCE_REVERIFICATION_REVIEW.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH031_040_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage038_worker_queue_baseline.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md`

## Stop And Rollback

Stop if source hashes or the single-member identity cannot be reproduced, an
independent review finds an unresolved contract conflict, Phase 2 begins in
this run, raw/business data access is requested, or a shared test fails without
explanation.

Rollback only the Stage038 source-reverification evidence, corrected entry and
Phase 1 boundary, focused tests, Stage005 validator/test support, batch/roadmap/
event changes, handoff/changelog, and rendered owner views. Preserve prior
stages, user-owned dirty files, raw metadata, databases, source/runtime data,
reports, app entries, and GitHub state.
