# Phase C Workflow Runtime Read Model

Schema: `PFIOSPhaseCWorkflowRuntimeContractV1`

Status: first Phase C workflow runtime slice complete.

As of: 2026-06-20 Australia/Sydney

## Goal

Promote the four Phase B workflow contracts into a cached runtime read model
that the Web Shell can consume before full worker scheduling, retry workers,
SSE/WebSocket progress, and deployment readiness are implemented.

## Current Slice

- Adds `pfi_os.application.workflow_runtime_read_model`.
- Declares read model schema `PFIOSPhaseCWorkflowRuntimeReadModelV1`.
- Reads Phase B Strategy Lab, Markets, Research + Policy, and Portfolio
  workflow records from Operational Store source, evidence, job, task, and
  holding snapshot tables.
- Emits workflow cards with workspace, source type, evidence class, data
  domain, source id, evidence id, job id, open task count, freshness, and
  review requirement.
- Emits 60-second Fast Path metadata with cached-read-model requirement,
  target seconds, estimated seconds, ready/blocked/running/failed counts, and
  no provider/broker/LLM requirements.
- Emits retry policy metadata: max attempts, backoff seconds, fail-closed
  behavior, idempotency key fields, and retryable statuses.
- Emits background job rows and task-center rows for the Web Shell.
- Adds the runtime summary to `PFIOSHomeSummaryV1` as `workflow_runtime`.
- Updates the static Web Shell to accept `workflow_runtime` and refresh the
  task center/background job label from cached JSON.
- Keeps private portfolio holdings out of the read model; only aggregate card
  metadata and holding snapshot counts are exposed.

## Contract Tests

- `tests/contract/test_phase_c_workflow_runtime_read_model.py`

The tests verify:

1. Phase C contract fields, required workflows, Fast Path, retry policy, and
   safety constraints.
2. Four Phase B workflow records produce four runtime cards.
3. Portfolio remains `PRIVATE_DERIVED` and does not leak `holdings_json` or
   private holding symbols into the runtime payload.
4. Missing Phase B workflow evidence fails closed to `Review` with explicit
   missing-data logs.
5. Homepage summary carries `workflow_runtime`.
6. Runtime read model snapshots can be recorded back into Operational Store as
   source, evidence, job, and human-review task records.
7. Static Web Shell assets accept the Phase C runtime summary without direct
   provider/private file reads.

## Out Of Scope

- Real scheduler loop.
- Retry/backoff executor implementation.
- SSE/WebSocket progress stream.
- Provider fetch, broker integration, order routing, account mutation, payment,
  betting, or real-money execution.
- Full deployment/backup/restore readiness.
- Final Phase 5 packaging and Phase 6 deployment package.

## Next Iterations

1. Implement the Phase C worker scheduler around this read model with bounded
   retry/backoff and idempotent job writes.
2. Add 60-second acceptance around a local cached refresh path.
3. Add Web Shell read-model rendering for workflow cards beyond the task
   center.
4. Continue toward Phase D deployment, backup/restore, local model readiness,
   and final Phase 5 acceptance package.
