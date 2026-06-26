# Phase C Workflow Runtime Read Model

Schema: `PFIOSPhaseCWorkflowRuntimeContractV1`

Status: first three Phase C workflow runtime slices complete.

As of: 2026-06-20 Australia/Sydney

## Goal

Promote the four Phase B workflow contracts into a cached runtime read model
that the Web Shell can consume before full worker scheduling, retry workers,
SSE/WebSocket progress, and deployment readiness are implemented.

## Current Slices

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
- Emits `supervisor_runtime` from PFI-003 durable `job_records`, including
  active, running, retrying, dead-letter, latest phase, latest event, and safety
  boundary fields.
- Adds the runtime summary to `PFIOSHomeSummaryV1` as `workflow_runtime`.
- Updates the static Web Shell to accept `workflow_runtime` and refresh the
  task center/background job label from cached JSON.
- Updates the static Web Shell to consume `workflow_runtime.supervisor_runtime`
  in the Data/System workspace, showing PFI-003 supervisor task health without
  direct provider, private-file, broker, or launchd calls.
- Keeps private portfolio holdings out of the read model; only aggregate card
  metadata and holding snapshot counts are exposed.
- Adds `pfi_os.application.workflow_runtime_scheduler`.
- Declares scheduler schema `PFIOSPhaseCWorkflowRuntimeSchedulerV1` and run
  schema `PFIOSPhaseCWorkflowRuntimeSchedulerRunV1`.
- Schedules idempotent local cache-refresh jobs in Operational Store using
  existing `source_records` and `job_records`; no new tables are introduced.
- Executes cached runtime refreshes into
  `PFIOSPhaseCWorkflowRuntimeReadModelV1`, records runtime evidence/tasks via
  the existing read-model recorder, and reports 60-second acceptance metadata.
- Implements bounded retry/backoff with max attempts 3 and `[1, 5, 15]`
  second policy metadata. Exhausted retries fail closed with human review
  required.
- Confirms the scheduler has no provider fetch, broker, LLM, network,
  live-trading, order-execution, or holdings-mutation dependency.
- Adds Web Shell workflow-card rendering for `workflow_runtime.workflow_cards`.
- Renders Fast Path target/status metadata, per-workflow status, evidence id,
  freshness, task counts, source type, and private-safe evidence drawer
  payloads.
- Keeps the default error banner hidden with an explicit `[hidden]` visual
  contract so loading/error states do not display before user action.
- Verifies the static Web Shell in real headless Google Chrome with injected
  Phase C runtime payload: four cards render, Fast Path badge updates,
  Portfolio evidence opens the drawer, and console errors remain empty.

## Contract Tests

- `tests/contract/test_phase_c_workflow_runtime_read_model.py`
- `tests/contract/test_phase_c_workflow_runtime_scheduler.py`
- `tests/contract/test_pfi_web_shell_contract.py`
- `tests/e2e/test_pfi_web_shell_static_flow.py`
- `tests/visual/test_pfi_web_shell_visual_baseline.py`

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
8. Scheduler contract fields, local-only dependency boundary, idempotent
   scheduling, 60-second cache-refresh acceptance, runtime evidence writes,
   retry scheduling, and fail-closed exhausted retries.
9. PFI-003 supervisor runtime jobs surface in `supervisor_runtime`,
   `background_jobs`, and `task_center_rows`.
10. Web Shell workflow-card DOM anchors, JS rendering path, responsive visual
   grid, hidden loading/error states, private-safe evidence drawer updates,
   and Fast Path badge updates.

## Out Of Scope

- SSE/WebSocket progress stream.
- Provider fetch, broker integration, order routing, account mutation, payment,
  betting, or real-money execution.
- Full deployment/backup/restore readiness.
- Final Phase 5 packaging and Phase 6 deployment package.

## Next Iterations

1. Add SSE/WebSocket-style progress only if it materially improves local
   workflow observability.
2. Continue toward Phase D deployment, backup/restore, local model readiness,
   and final Phase 5 acceptance package.
