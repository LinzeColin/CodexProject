# STAGE-038 Phase 1 - Worker Queue Scope Boundary

## Identity And Source Status
- Stage: `STAGE-038 · Worker 队列基线`
- Task: `IDS-V0_1-STAGE038-P1`
- Acceptance: `ACC-STAGE-038`
- Local code: `D07-S002`
- Domain: `D07 · 任务编排与机器控制`
- Entrance: `IDS 系统运营入口`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- Tracked source reference:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-038_Worker队列基线.md`
- `P0 source verification: EXTERNAL_TASKPACK_ABSENT`
- `P0 SHA-256: UNKNOWN_UNDER_IDS-V0_1-STAGE038-P1`
- `source_reverification_required_before_phase2=true`

This is a provisional boundary derived from the tracked execution index and
reviewed upstream contracts. It is not an approved queue contract and is not
evidence that a queue or worker exists. Phase 2 is unauthorized until exact
taskpack source reverification and P1 reconciliation complete.

## Authoritative Upstream Contracts
- `worker_queue_contract_id=UNASSIGNED_UNTIL_SOURCE_REVERIFICATION`
- `worker_queue_contract_status=PROVISIONAL_SOURCE_LIMITED_BOUNDARY`
- `job_control_envelope_schema=ids.job_control_envelope.v1`
- `job_state_model_version=ids.job_state.v1`
- STAGE-037 lifecycle rule: only `QUEUED` jobs are queue-eligible.
- STAGE-037 separation rule: queue status is not a second job lifecycle state.
- STAGE-022 priority vocabulary is owner-governed.
- STAGE-030 control-plane limit: `payload_size_bytes <= 1048576`.

The queue contract may reference a job but cannot redefine its lifecycle,
change state, or claim admission without current state/version evidence.

## Queue Input And Output Decision Boundary
The only approved input floor is a bounded reference to the reviewed
`job_control_envelope`. A future queue entry may contain bounded metadata refs
only, including inherited dimensions such as `job_id`, `state_version`,
`priority_ref`, `resource_gate_refs`, `dependency_refs`, and `audit_ref`.
This is not an approved exact schema. Queue-specific identifiers, versions,
timestamps, sequence fields, and persistence shape remain unassigned.

Future queue persistence may store refs, not source content. Raw source bodies
are forbidden. Plaintext secrets are forbidden. Referenced control-plane
metadata remains bounded by `payload_size_bytes <= 1048576`; no payload rule is
executed in Phase 1.

## Source-Gated Admission Dimensions
Only inherited constraints are fixed:

1. Only `QUEUED` jobs are queue-eligible; queue metadata cannot redefine or
   mutate the STAGE-037 lifecycle.
2. Any priority dimension must use an owner-approved priority_ref from the
   existing vocabulary: `P0_CRITICAL_ENGINEERING_DATA`,
   `P1_HIGH_VALUE_ENGINEERING_DATA`, `P2_SUPPORTING_ENGINEERING_DATA`, or
   `P3_LOW_VALUE_OR_DEFERRED_DATA`. The rule is
   `numeric priority weights are not invented`.
3. `ordering_policy=UNASSIGNED_UNTIL_SOURCE_REVERIFICATION`; Phase 1 does not
   choose a tuple, sequence source, tie-breaker, fairness rule, or capacity.
4. `enqueue_idempotency_contract=UNASSIGNED_UNTIL_SOURCE_REVERIFICATION`;
   Phase 1 does not choose a key, duplicate return shape, or persistence rule.
5. `dependency_admission_contract=UNASSIGNED_UNTIL_SOURCE_REVERIFICATION`;
   missing dependency evidence fails closed pending source approval, but P1
   does not invent which outcomes or versions qualify.
6. Resource-gate admission semantics, exact concurrency, waits, thresholds,
   and owner overrides remain source- and owner-gated.

## Claim Transport Decision Boundary
- `claim_transport_contract=UNASSIGNED_UNTIL_SOURCE_REVERIFICATION`
- `claim_atomic_sequence=UNASSIGNED_UNTIL_SOURCE_REVERIFICATION`
- inherited STAGE-037 dimensions include `job_id`, `expected_state=QUEUED`,
  `expected_state_version`, `lease_owner_ref`, `lease_expires_at`,
  `fencing_token`, and `lock_key`.

STAGE-041 owns lock, lease, renewal, and fencing runtime. Phase 1 does not
choose a claim request shape, queue version tuple, acquisition sequence, lease
duration, renewal cadence, timeout, or storage schema. The inherited safety
floor remains: `missing or stale claim proof fails closed`. The inherited rule
is `a stale worker cannot commit`. No proof is acquired or evaluated here.

## Downstream Ownership And Non-Goals
- STAGE-039 owns retry scheduling and dead-letter policy.
- STAGE-040 owns measured backpressure and fairness policy.
- STAGE-041 owns lock/lease/fencing runtime.
- STAGE-042 owns automatic run, pause, resume, and shutdown.
- STAGE-043 owns worker-crash recovery.
- STAGE-044 owns half-product cleanup.

Mandatory stop markers:
`NO_PHASE2`, `NO_QUEUE_RUNTIME`, `NO_WORKER_RUNTIME`,
`NO_CLAIM_PERSISTENCE`, `NO_SCHEMA_CHANGE`, `NO_POSTGRES_CONNECTION`,
`NO_RUNTIME_OUTPUT`, `NO_STAGE039`, `NO_GITHUB_UPLOAD`, `NO_APP_REINSTALL`.

This run does not create a machine contract/checker, queue adapter, worker,
scheduler, service, API, UI, migration, database record, source read, runtime
output, app entry, PR, issue, or upload.

## Raw And Real-Data Boundary
- `/Users/linzezhang/Downloads/IDS_MetaData` is path-only. 不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描 any content below it.
- 不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据.
- `raw source bodies are forbidden` from queue entries and claim transport.
- `plaintext secrets are forbidden` from queue entries and audit text.
- `future queue persistence may store refs, not source content`.
- `source_read_performed=false`
- `database_connection_performed=false`
- `real_job_created=false`
- `fake_ids_business_data_used=false`

## Phase 2 Entry Gate
`phase2_entry_authorized=false`. The next allowed task is only
`IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY`; Phase 2 remains planned and blocked.
Before any Phase 2 implementation, the source-reverification task must:

1. Reattach and verify the exact approved Stage038 taskpack source and record a
   truthful hash.
2. Reconcile every P1 rule against that source; any conflict returns to P1.
3. Keep evaluation metadata-only and side-effect-free, with no queue/worker
   runtime, PostgreSQL action, real job, raw source read, or fake IDS data.

## Rollback
Revert only Stage038 P1 entry/scope documents, focused tests, Stage005
validator/test support, batch/roadmap/event changes, handoff/changelog, and
rendered owner views. Preserve STAGE-037 and earlier evidence, raw metadata,
databases, source/runtime content, reports, indexes, app entries, and GitHub.
