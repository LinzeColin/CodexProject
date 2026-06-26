# Phase B Research + Policy Vertical Slice

Schema: `PFIOSPhaseBResearchPolicyContractV1`

Status: first Research + Policy vertical slice complete.

As of: 2026-06-19 Australia/Sydney

## Goal

Make the Research workspace produce reviewable policy and research-evidence
outputs from local reviewed inputs before Phase C worker scheduling and Phase
D local LLM/deployment work.

## Current Slice

- Adds `pfi_os.application.research_policy_workflow`.
- Declares workflow schema `PFIOSPhaseBResearchPolicyWorkflowV1`.
- Builds policy radar summaries using `pfi_os.policy.radar`.
- Builds report evidence-gap validation tasks using
  `pfi_os.research.report_gap_tasks`.
- Emits compact cards for policy authority, policy opportunities, and research
  evidence gaps.
- Exposes source authority, review status, evidence completeness, source ids,
  model version, and `human_review_required: true`.
- Emits decision-support output with thesis, catalysts, counter-evidence,
  invalidation conditions, risks, portfolio effect, model versions, and source
  ids.
- Writes Research + Policy source, evidence, job, and review-task records into
  the Operational Store.

## Contract Tests

- `tests/contract/test_phase_b_research_policy_workflow.py`

The tests verify:

1. Research + Policy contract fields and non-regression constraints.
2. Policy radar outputs authority and evidence completeness metadata.
3. Report evidence-gap tasks are visible without appending to runtime queues.
4. Decision-support output includes counter-evidence and invalidation
   conditions.
5. Workflow ids are stable for identical inputs.
6. Operational Store receives source, evidence, job, and human-review task
   records.
7. No government portal action, legal/tax advice, live trading, broker call, or
   order execution path is exposed.

## Out Of Scope

- Phase C policy/document worker, scheduler, retry/backoff, SSE/WebSocket, and
  60-second Fast Path acceptance.
- Direct live policy scraping inside this workflow.
- Legal, tax, compliance, subsidy, or investment conclusions.
- Portfolio impact calculations that require private holdings.
- Full Web Shell Research UI migration.
- Portfolio vertical slice is covered by `docs/phase/PHASE_B_PORTFOLIO.md`.

## Next Iterations

1. Promote the four Phase B workflow contracts into Web Shell read models.
2. Start Phase C worker/reliability only after the four Phase B workflows have
   evidence contracts.
