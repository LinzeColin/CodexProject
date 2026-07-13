# STAGE-039 Phase 1 - Retry And Dead-Letter Scope Boundary

## Contract Identity

- Stage: `STAGE-039 · 重试与死信策略`
- Task: `IDS-V0_1-STAGE039-P1`
- Acceptance: `ACC-STAGE-039`
- Phase: `Phase 1 · 范围、输入输出与边界确认`
- `retry_policy_contract_id=ids.retry_dead_letter.v0_1.p1`
- `contract_state=PHASE1_ENGINEERING_CONTRACT_RUNTIME_DISABLED`
- Machine contract:
  `retry_dead_letter/stage039_retry_dead_letter_policy_contract.json`
- Read-only checker: `KM_IDSystem/scripts/check_retry_dead_letter_policy.py`

The exact taskpack member is
`IDS_v0_1_Final_Chinese_Revised/stages/STAGE-039_重试与死信策略.md`, with
`source_member_sha256=504caf72a6aeab67a650b4b096e728f03269f6ca8798f6e8a5c51210c8ddd7d9`.
Its Phase 1 requires job/worker, retry/dead-letter, resource-pause,
idempotency/lock, and partial-output safety boundaries. This document
specializes those requirements without executing Phase 2.

## Input Boundary

The decision input is bounded control metadata only:

- identity: `job_id`, `job_type`, `state_version`, `idempotency_key`,
  `attempt_id`, and `transition_request_id`;
- retry budget: `retry_count`, immutable `max_retries`, `retry_pending`, and
  `retry_disposition`;
- failure evidence: `failure_observation_ref`, allowlisted `safe_error_code`,
  and `error_ref`; classification is derived and cannot be trusted as input;
- restart evidence: `checkpoint_ref`, never raw checkpoint content;
- eligibility: `next_eligible_at`, `next_eligible_evidence_ref`, and a
  versioned `policy_version`;
- safety: `resource_gate_refs`, current claim/lock disposition, and
  append-only `audit_ref`.

Missing fields, raw source bodies, plaintext secrets, untracked refs, unknown
error classes, or unversioned policy fail closed to manual review. No source
content is copied into the retry or dead-letter control plane.

## Output Boundary

The Phase 2 decision surface may emit exactly one bounded action:

- `SCHEDULE_RETRY`: record `RETRY_WAIT`; reservation does not increment budget;
- `FAIL_TERMINAL`: record permanent `FAILED` without reopening it;
- `PAUSE_RESOURCE_GATE`: follow the legal state path to `PAUSED` without
  consuming retry budget;
- `DEAD_LETTER`: only `RETRY_WAIT -> DEAD_LETTERED` after exhaustion;
- `REQUIRE_MANUAL_REVIEW`: fail closed when policy, authorization, or safe
  classification evidence is missing.

Every decision carries the observed state version, policy version, safe reason,
owner-readable Chinese message, evidence refs, and audit ref. It is a decision
contract, not a claim that persistence or scheduling happened.

## Retry Budget Invariants

1. `max_retries` is retry attempts after the initial attempt.
2. `total_attempt_limit = 1 + max_retries`.
3. `max_retries` is immutable after job creation.
4. Entering `RETRY_WAIT` reserves no budget.
5. Only atomic `RETRY_WAIT -> QUEUED` admission increments `retry_count` and
   clears `retry_pending`.
6. Duplicate `transition_request_id` replay returns the original result and
   consumes no extra budget.
7. Resource pause preserves pending retry where applicable and consumes no
   budget.
8. `retry_count == max_retries` cannot requeue; it routes only from
   `RETRY_WAIT` to `DEAD_LETTERED`.

## Attempt And Rerun Identity

`job_id` represents the logical job and remains stable across its attempts.
Each actual execution uses a distinct `attempt_id`. The stable
`idempotency_key` prevents duplicate admission for that logical job.

`FAILED`, `DEAD_LETTERED`, `SUCCEEDED`, and `CANCELLED` are immutable. Manual
rerun after terminal review creates a new linked job and must include
`parent_job_id`, a unique owner-approved `rerun_request_id`, `new_job_id`, and
`new_idempotency_key`. The new identity is bound idempotently to
`parent_job_id + owner-approved rerun_request_id`; replaying either the old job
key or an already-used rerun request cannot create a duplicate linked job.

## Policy Parameter Principles

This Phase does not assign source-less numbers. Phase 2 must explicitly record:

- `max_retries`: non-negative integer, immutable per job;
- `backoff_schedule_seconds`: bounded, non-negative, sufficient for each
  allowed retry admission;
- `jitter_policy`: bounded and unable to create a negative effective delay;
- `retryable_safe_error_codes`: versioned allowlist with default deny.

The parameter source, rationale, version, validation evidence, and rollback
must accompany the Phase 2 implementation. No implicit library default, magic
number, infinite retry, immediate busy loop, or error-message substring may
decide production retry behavior.

## Failure And Human Status Matrix

| Machine result | Chinese status | Owner action |
|---|---|---|
| `RETRY_WAIT` | `等待重试` | 查看安全错误与下次资格时间 |
| `PAUSED` | `已暂停` | 恢复资源并完成复核 |
| `FAILED` | `处理失败` | 人工复核后可创建新的关联任务 |
| `DEAD_LETTERED` | `需要人工处理` | 人工复核，不自动继续 |
| `CANCELLED` | `已取消` | 查看停止原因与已保留证据 |

Feedback must identify what stopped, which safe evidence exists, and whether
the next action is automatic, scheduled, paused, or owner-controlled. It must
not promise recovery or hide a dead-letter/manual-review condition.

## Resource And Worker Boundary

- `external_drive_offline`, `disk_space_insufficient`, and
  `external_api_budget_insufficient` pause affected jobs without retry cost.
- STAGE-039 classifies and decides retry/dead-letter metadata; STAGE-038 owns
  queue/worker mechanics.
- STAGE-040 owns measured backpressure/fairness; STAGE-041 owns locks/leases/
  fencing; STAGE-042 owns automatic resume; STAGE-043 owns crash recovery;
  STAGE-044 owns cleanup execution.
- A worker crash is not automatically labelled retryable here. STAGE-043 must
  prove checkpoint/claim/fencing safety before any automated recovery.
- Partial outputs do not become dead-letter payloads. Cleanup may only occur
  under STAGE-044 and cannot delete facts, manifests, evidence ledgers, audit
  logs, or report snapshots.

## Phase 2 Entry Gate

`Phase 2 must run separately`. It may implement an isolated non-production
decision/scheduler/dead-letter metadata slice only after it selects and records
versioned policy parameters, revalidates all upstream hashes, and preserves
the state/identity/evidence invariants above. It may not connect PostgreSQL,
activate a production worker, read raw metadata, use fake IDS business data,
or absorb STAGE-040..044 runtime ownership.

Mandatory stop markers:
`NO_PHASE2`, `NO_RETRY_RUNTIME`, `NO_DEAD_LETTER_RUNTIME`,
`NO_QUEUE_RUNTIME`, `NO_WORKER_RUNTIME`, `NO_POSTGRES_CONNECTION`,
`NO_SCHEMA_CHANGE`, `NO_RUNTIME_OUTPUT`, `NO_RAW_METADATA_ACCESS`,
`NO_FAKE_IDS_BUSINESS_DATA`, `NO_GITHUB_UPLOAD`, `NO_APP_REINSTALL`.

The next gate is `IDS-STAGE039-P2-GATE`. `push_allowed=false` remains fixed.

## No-Action Evidence

- `taskpack_source_read_performed=true`
- `ids_business_source_read_performed=false`
- `raw_metadata_content_accessed=false`
- `retry_scheduler_performed=false`
- `dead_letter_runtime_performed=false`
- `queue_runtime_performed=false`
- `worker_runtime_performed=false`
- `database_connection_performed=false`
- `schema_change_performed=false`
- `runtime_output_written=false`
- `real_ids_business_job_created=false`
- `fake_ids_business_data_used=false`
- `external_api_call_performed=false`
- `github_upload_allowed=false`
- `app_reinstall_allowed=false`

## Rollback

Revert only the Stage039 Phase 1 artifacts and governance transition. Do not
touch earlier stages, raw metadata, databases, runtime artifacts, reports,
indexes, the four owner-authored dirty files, GitHub state, or app entries.
