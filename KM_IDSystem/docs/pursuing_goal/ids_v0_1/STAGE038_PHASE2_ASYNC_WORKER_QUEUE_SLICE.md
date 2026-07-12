# STAGE-038 Phase 2 - Asynchronous Worker Queue Slice

## Identity

- Stage: `STAGE-038 · Worker 队列基线`
- Phase: `Phase 2 · 实现、接入与最小可运行切片`
- Task: `IDS-V0_1-STAGE038-P2`
- Acceptance: `ACC-STAGE-038`
- Pursuing goal: `建立异步 worker 队列，避免长任务阻塞前端和 API。`
- Execution mode:
  `ISOLATED_NON_PRODUCTION_ASYNC_CONTROL_METADATA_SLICE`
- Next gate: `IDS-STAGE038-P3-GATE`

## Implemented Slice

The Phase 2 checker implements a standard-library `asyncio` queue with one
background worker. A synchronous submission acknowledgement returns before
worker completion; the API-facing path does not execute the control operation
inline. The worker processes one real Git-tracked control-file reference and
applies the reviewed STAGE-037 transitions:

`QUEUED -> CLAIMED -> RUNNING -> SUCCEEDED`

The smoke input is the real tracked reference:

`repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md`

The operation reads that tracked project document, calculates its actual
SHA-256, and returns only bounded `output_refs` and `checkpoint_ref` values.
It does not read IDS business data, access the raw metadata root, call an
external API, connect to a database, or write a runtime artifact.

## Queue Contract

- Contract: `ids.worker_queue_baseline.v0_1.p2`
- Envelope: `ids.job_control_envelope.v1`
- State model: `ids.job_state.v1`
- Queue mode: `ASYNCIO_IN_MEMORY_ISOLATED_NON_PRODUCTION`
- Submission mode: `SYNCHRONOUS_ACK_ASYNC_WORKER`
- Ordering: `FIFO_ADMISSION_SEQUENCE_NO_PRIORITY_REORDERING`
- Duplicate admission returns the existing queue-entry reference.
- `job_id`, `idempotency_key`, and admission request ID are deterministically
  derived from `task_id + input_ref + job_type`; `lock_key` is derived only
  from `task_id + input_ref`. Distinct processing, extraction, indexing, and
  reporting jobs over the same tracked input therefore share one conflict key.
- An existing non-terminal record with that key returns
  `RESOURCE_CONFLICT_ACTIVE` before a second queue record is created.
- Non-empty dependency refs fail closed because dependency qualification is
  not implemented by this baseline.
- Queue-full admission returns `QUEUE_CAPACITY_REACHED` with the reviewed
  Chinese `已暂停` projection.
- The in-process resource lock and fencing counter are valid only inside this
  isolated single-process slice. They are not production Stage 041 evidence.

## Numeric Parameters And Rationale

| Parameter | Value | Rationale |
|---|---:|---|
| `worker_count` | 1 | Keeps Phase 2 deterministic and prevents this run from taking over Phase 3 concurrency validation or Stage 041 production lock ownership. |
| `default_isolated_capacity` | 1 | Smallest queue that proves asynchronous admission, one background operation, duplicate reuse, and queue-full backpressure without implying throughput. |
| `maximum_isolated_capacity` | 16 | With the inherited 1 MiB envelope cap, this bounds queued serialized input to at most 16 MiB; it is not a production queue-length, fairness, or scaling policy. |
| `payload_size_bytes_maximum` | 1048576 | Inherited STAGE-030 control-plane envelope bound. |
| `maximum_text_length` | 512 | Inherited STAGE-037 bounded-reference limit. |
| `maximum_refs_per_field` | 64 | Inherited STAGE-037 bounded-reference limit. |

STAGE-040 retains measured backpressure and fairness policy. No queue-length
threshold, throughput target, worker scaling rule, retry delay, lease duration,
or production capacity is asserted here.

## Task Record

Every accepted queue record carries:

- `input_refs`
- `output_refs`
- `error_ref`
- `checkpoint_ref`
- `state_history`
- `transition_audit`
- `owner_status`

The successful smoke produced:

- input:
  `repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md`
- output:
  `sha256:d8930c3c3c9551afb2801952bb42d135247847352838aeb37b988d6c283f6e76`
- checkpoint:
  `checkpoint:sha256:d8930c3c3c9551afb2801952bb42d135247847352838aeb37b988d6c283f6e76`
- error: `null`
- final machine state: `SUCCEEDED`
- final owner label: `已完成`

An actual injected worker exception is converted to bounded
`error:RuntimeError`, transitions `RUNNING -> FAILED`, and maps to
`处理失败`. No exception message, raw body, secret, or fabricated business log
is persisted.

## Runtime Evidence

- `submission acknowledgement returns before worker completion`
- `queue_runtime_performed=true`
- `worker_runtime_performed=true`
- `isolated_control_job_created=true`
- `production_runtime_activation_performed=false`
- `claim_persistence_performed=false`
- `persistent_queue_write_performed=false`
- `database_connection_performed=false`
- `schema_change_performed=false`
- `state_registry_write_performed=false`
- `runtime_output_written=false`
- `ids_business_source_read_performed=false`
- `external_api_call_performed=false`
- `raw_metadata_content_accessed=false`
- `fake_ids_business_data_used=false`
- `real_ids_business_job_created=false`
- `push_allowed=false`

The runtime evidence is limited to the one in-process control-metadata smoke.
It is not production queue readiness, production worker deployment, or proof
that IDS business work has run.

## Ownership Boundary

STAGE-039..044 retain runtime ownership for their dedicated mechanisms:

- STAGE-039: retry scheduling and dead-letter policy.
- STAGE-040: measured backpressure and fairness.
- STAGE-041: production lock, lease, renewal, and fencing.
- STAGE-042: production automatic run, pause, resume, and shutdown.
- STAGE-043: worker-crash recovery.
- STAGE-044: half-product cleanup and deletion safety.

Phase 2 implements no retry scheduler, dead-letter processor, measured
backpressure controller, production lock service, automatic lifecycle
controller, crash recovery, or cleanup.

## Rollback

Revert the Phase 2 checker, machine contract, focused test, this evidence,
Stage005 compatibility update, batch/roadmap/event projection, handoff,
changelog, and rendered owner views. Do not alter the Phase 1 evidence,
STAGE-037 contract, user-owned dirty files, raw metadata, databases, reports,
app entries, GitHub state, or later stages.
