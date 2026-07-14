# Memory Atlas v1.1.7 Stage 2 Phase 2.1 Editable Draft Acceptance

- Task ID: `MA-V117-S2P01`
- Acceptance ID: `ACC-MA-V117-S2P01`
- Status: `phase_2_1_editable_draft_model_completed_pending_stage2_review`
- Validator: `validate:v1.1.7-stage2-phase1`
- Model: `proposal_edit_model_v1_1_7_stage2_phase1`
- Store key: `memory-atlas.proposal-drafts.v1`
- Draft schema: `memory_atlas_proposal_draft.v1`

## Acceptance Criteria

| Area | Required result | Evidence |
|---|---|---|
| Editable Draft Model | `proposal_edit_model.md` defines the whitelist and blocked fields. | `docs/architecture/proposal_edit_model.md` |
| 可编辑字段白名单 | Only `importance`, `priority`, `status`, `theme_override`, `action_state` and `note` are allowed. | model + validator |
| Draft State Store | `proposalDraftStore.ts` creates, updates, removes, serializes, parses, loads, saves and clears local drafts. | `apps/memory-atlas/src/state/proposalDraftStore.ts` |
| Refresh warning | Store exposes `proposalDraftRefreshWarning` for unsaved changes before refresh/close. | store helper |
| Undo | Store exposes `removeProposalDraftChange` for field-level undo draft change. | store helper |
| Safety | Drafts are `proposal_only`, require conflict check and require agent or human apply. | store schema |
| Boundary | No Proposal UI, no direct writeback, no agent apply, no raw/private read and no GitHub main upload. | validator |

## Required Editable Fields

1. `importance`
2. `priority`
3. `status`
4. `theme_override`
5. `action_state`
6. `note`

## Required Target Types

1. `memory_node`
2. `suggested_action`
3. `tier_asset`
4. `topic_classification`

## Required Draft Statuses

1. `draft_local`
2. `needs_review`
3. `ready_for_agent_apply`
4. `reverted`

## Required Draft Fields

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

## Failure Conditions

1. The whitelist includes raw transcript, source hash, secret, cookie, session,
   local absolute path, memory database primary key or any direct active-memory
   mutation field.
2. `proposalDraftStore.ts` writes network requests, writes active memory,
   performs agent apply, or bypasses `proposal_only`.
3. The model omits refresh warning or undo draft change behavior.
4. The phase adds `ProposalEditor.tsx`, Proposal UI, diff preview, export UI,
   browser screenshot, production build, deployment or GitHub main upload.
5. Records do not include `MA-V117-S2P01`, `ACC-MA-V117-S2P01`,
   `phase_2_1_editable_draft_model_completed_pending_stage2_review` and
   `validate:v1.1.7-stage2-phase1`.

## Validation

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage2-phase1
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage1
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage0
pnpm --dir OpenAIDatabase/apps/memory-atlas run lint
git diff --check -- OpenAIDatabase
```

## Stop Boundary

Stop after Stage 2 Phase 2.1. Do not enter Phase 2.2 Proposal UI, Proposal
Diff Preview, proposal export, Search 2.0, Review workflow, Data Map 2.0,
browser screenshot, build, deploy or GitHub main upload.

Machine-readable boundary summary: Editable Draft Model; Draft State Store;
importance; priority; status; theme_override; action_state; note; refresh
warning; undo draft change; No raw/private; No direct writeback; No agent apply;
No Proposal UI; No GitHub main upload.
