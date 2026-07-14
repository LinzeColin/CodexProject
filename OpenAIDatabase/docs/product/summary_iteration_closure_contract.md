# Memory Atlas v1.1.7 Stage 8 Phase 8.1 Summary Iteration Closure Contract

Task ID: `MA-V117-S8P01`

Acceptance ID: `ACC-MA-V117-S8P01`

Status: `phase_8_1_summary_iteration_closure_runtime_completed_pending_stage8_review`

Runtime version: `summary_iteration_closure_runtime.v1_1_7_stage8_phase1`

Closure schema version: `memory_atlas_summary_closure.v1_1_7_stage8_phase1`

Source review schema version: `memory_atlas_review_summary.v1_1_7_stage7_phase2`

## Purpose

Stage 8 Phase 8.1 closes the Stage 7 Review / Summary / Iteration output into
a visible summary-iteration closure layer. The runtime uses only the redacted
Stage 7.2 review output and shows:

- `change_comparison`
- `stale_conflict_signals`
- `proposal_candidates`

This phase turns review conclusions into proposal-only candidates and safety
signals. It does not write active memory, write the proposal queue, execute
agent apply, deploy, or upload GitHub main.

## Runtime Contract

The production `summary` view must include a section with
`data-summary-iteration-closure-runtime="summary_iteration_closure_runtime.v1_1_7_stage8_phase1"`.

The closure output must include:

| Field | Required behavior |
|---|---|
| `change_comparison` | Compare strengthening, declining and dominant topics with current count, previous count, delta and `evidence_refs`. |
| `stale_conflict_signals` | Show stale and conflict signals with severity, proposal hint, rollback hint and `evidence_refs`. |
| `proposal_candidates` | Show proposal-only candidates with `requires_conflict_check`, `requires_agent_or_human_apply`, rollback hint and `evidence_refs`. |

The runtime debug signal must expose `window.__memoryAtlasStage8Phase1()` with
runtime version, closure schema version, source review schema version, panel ids,
counts and safety flags.

## Safety Boundary

- Proposal-only.
- No raw/private/cookie/session/secret data access.
- No direct active-memory writeback.
- No proposal queue write.
- No agent apply.
- No Cloudflare deploy.
- No Stage 8 review.
- No Stage 9 or Stage 10 work.
- No GitHub main upload before the whole Stage 0-10 project is complete.

Machine-readable boundary summary: Summary and iteration closure; MA-V117-S8P01; ACC-MA-V117-S8P01; phase_8_1_summary_iteration_closure_runtime_completed_pending_stage8_review; validate:v1.1.7-stage8-phase1; validate:summary-iteration-closure-browser; summary_iteration_closure_runtime.v1_1_7_stage8_phase1; memory_atlas_summary_closure.v1_1_7_stage8_phase1; memory_atlas_review_summary.v1_1_7_stage7_phase2; change_comparison; stale_conflict_signals; proposal_candidates; proposal-only; No Stage 8 review; No direct active-memory writeback; No proposal queue write; No GitHub main upload.

## Rollback

Revert the Stage 8 Phase 8.1 commit. This removes the runtime section, scoped
CSS, validators, contract, acceptance and record entries. No data migration,
proposal queue cleanup or active-memory rollback is required.
