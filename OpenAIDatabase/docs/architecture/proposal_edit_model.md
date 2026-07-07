# Memory Atlas v1.1.7 Stage 2 Phase 2.1 Proposal Edit Model

- Model ID: `proposal_edit_model_v1_1_7_stage2_phase1`
- Task ID: `MA-V117-S2P01`
- Acceptance ID: `ACC-MA-V117-S2P01`
- Status: `phase_2_1_editable_draft_model_completed_pending_stage2_review`
- Required validator: `validate:v1.1.7-stage2-phase1`
- Draft schema version: `memory_atlas_proposal_draft.v1`
- Draft store key: `memory-atlas.proposal-drafts.v1`

## Purpose

Editable Draft Model defines which derived Memory Atlas fields may be adjusted
from the frontend and how those adjustments are held as local proposal drafts.
It is a model/store phase only. It does not implement Proposal UI, diff preview,
proposal export, agent apply, direct writeback, runtime route changes, browser
screenshot validation, deployment or GitHub main upload.

## 可编辑字段白名单

Only these fields may enter a local proposal draft:

| Field | Meaning | Allowed scope |
|---|---|---|
| `importance` | Human importance level for a memory or asset | derived metadata only |
| `priority` | Review or action priority | derived metadata only |
| `status` | Review/status override for a visible item | derived metadata only |
| `theme_override` | Proposed theme/category override | derived topic label only |
| `action_state` | Suggested action state, such as todo/reviewed/deferred | derived action metadata only |
| `note` | Human note explaining the proposed change | short redacted note only |

Blocked fields include raw transcript text, plaintext secrets, local absolute
paths, source hashes, cookies, sessions, memory database primary keys and any
field that would directly mutate active memory.

## Draft State Store

The draft store is local-browser state for unsaved proposal adjustments:

- Store key: `memory-atlas.proposal-drafts.v1`.
- Draft schema: `memory_atlas_proposal_draft.v1`.
- Store implementation: `apps/memory-atlas/src/state/proposalDraftStore.ts`.
- A draft is proposal-only and must include conflict/apply safety metadata.
- A refresh warning is required when any draft has unsaved changes.
- The store supports undo draft change by removing a field-level draft change.
- The store can be serialized and parsed deterministically for later Proposal UI
  or export phases.

Required target types:

1. `memory_node`
2. `suggested_action`
3. `tier_asset`
4. `topic_classification`

Required draft statuses:

1. `draft_local`
2. `needs_review`
3. `ready_for_agent_apply`
4. `reverted`

Required draft fields:

1. `draft_id`
2. `schema_version`
3. `parent_snapshot_id`
4. `source_surface`
5. `target_type`
6. `target_id`
7. `field`
8. `old_value`
9. `proposed_value`
10. `reason`
11. `evidence_refs`
12. `confidence`
13. `status`
14. `created_at`
15. `updated_at`
16. `proposal_only`
17. `requires_conflict_check`
18. `requires_agent_or_human_apply`
19. `rollback_hint`

## Store Behavior

1. `createProposalDraft` creates an empty draft for one target and records the
   parent snapshot.
2. `upsertProposalDraftChange` adds or replaces one whitelisted field change.
3. `removeProposalDraftChange` removes one field-level change and marks an
   empty draft as `reverted`.
4. `hasUnsavedProposalDrafts` checks whether refresh warning is required.
5. `proposalDraftRefreshWarning` returns the warning copy when local changes
   exist.
6. `serializeProposalDraftStore` and `parseProposalDraftStore` preserve a
   deterministic local draft snapshot.
7. `loadProposalDraftStore`, `saveProposalDraftStore` and
   `clearProposalDraftStore` are guarded localStorage helpers.

## Safety Boundary

- No raw/private/cookie/session/secret data access.
- No direct writeback.
- No direct frontend mutation of active memory.
- No agent apply.
- No Proposal UI in this phase.
- No proposal JSON export in this phase.
- No network write.
- No GitHub main upload before the whole Stage 0-10 project is complete.

Machine-readable boundary summary: Editable Draft Model; Draft State Store;
importance; priority; status; theme_override; action_state; note; refresh
warning; undo draft change; No raw/private; No direct writeback; No agent apply;
No Proposal UI; No GitHub main upload.
