# Memory Atlas v1.1.7 Stage 2 Phase 2.2 Proposal UI Acceptance

- Task ID: `MA-V117-S2P02`
- Acceptance ID: `ACC-MA-V117-S2P02`
- Status: `phase_2_2_proposal_ui_completed_pending_stage2_review`
- Validator: `validate:v1.1.7-stage2-phase2`
- UI model: `proposal_ui_v1_1_7_stage2_phase2`
- Draft schema: `memory_atlas_proposal_draft.v1`
- Export schema: `memory_atlas_proposal_export.v1`
- Store key: `memory-atlas.proposal-drafts.v1`

## Acceptance Criteria

| Area | Required result | Evidence |
|---|---|---|
| Proposal UI | Existing writeback panel embeds `ProposalEditor`. | `App.tsx` |
| Importance / Priority Editor | User can adjust `importance` and `priority` with labeled controls. | `ProposalEditor.tsx` |
| Value comparison | UI 显示原值、新值、影响说明。 | `ProposalDiffPreview.tsx` |
| Proposal Diff Preview | Diff preview renders `original_value`, `proposed_value`, `impact_summary` and `rollback_metadata`. | `ProposalDiffPreview.tsx` |
| Export / Rollback Contract | User can export `memory_atlas_proposal_export.v1` JSON and undo local changes. | `ProposalEditor.tsx` |
| Safety | UI stays `proposal_only`, requires conflict check and requires agent or human apply. | component data attributes + export payload |
| Boundary | No direct writeback, no raw/private read, no agent apply and no GitHub main upload. | validator |

## Required Components

1. `ProposalEditor.tsx`
2. `ProposalDiffPreview.tsx`

## Required UI Fields

1. `importance`
2. `priority`

The wider editable whitelist remains `importance`, `priority`, `status`,
`theme_override`, `action_state` and `note`, but Phase 2.2 only exposes the
first two as primary UI controls. Later phases may expose the rest.

## Runtime Anchors

The implementation must preserve these anchors:

1. `ProposalEditor`
2. `ProposalDiffPreview`
3. `data-proposal-editor`
4. `data-proposal-diff-preview`
5. `data-proposal-only="true"`
6. `data-active-memory-mutation="false"`
7. `proposalDraftRefreshWarning`
8. `upsertProposalDraftChange`
9. `removeProposalDraftChange`
10. `saveProposalDraftStore`
11. `loadProposalDraftStore`
12. `serializeProposalDraftStore`
13. `导出 proposal JSON`
14. `撤销本地调整`

## Required Export Fields

1. `schema_version = memory_atlas_proposal_export.v1`
2. `draft_id`
3. `parent_snapshot_id`
4. `source_surface`
5. `target_ref`
6. `original_value`
7. `proposed_value`
8. `changes`
9. `rollback_metadata`
10. `proposal_only`
11. `requires_conflict_check`
12. `requires_agent_or_human_apply`

## Failure Conditions

1. UI implies the change has already been written to active memory.
2. UI sends a network write, performs agent apply or directly mutates active
   memory.
3. Diff preview omits original value, proposed value, impact summary or
   rollback metadata.
4. Export payload omits `memory_atlas_proposal_export.v1`, conflict check or
   human/agent apply requirement.
5. The phase enters Search 2.0, Review workflow, Data Map 2.0, browser
   screenshot, production build, deployment or GitHub main upload.

## Validation

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage2-phase2
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage2-phase1
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage1
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage0
pnpm --dir OpenAIDatabase/apps/memory-atlas run lint
git diff --check -- OpenAIDatabase
```

## Stop Boundary

Stop after Stage 2 Phase 2.2. Do not enter Search 2.0, Review workflow, Data
Map 2.0, Stage 2 review, browser screenshot, build, deploy or GitHub main
upload.

Machine-readable boundary summary: Proposal UI; ProposalEditor;
ProposalDiffPreview; Importance / Priority Editor; Export / Rollback Contract;
memory_atlas_proposal_export.v1; original_value; proposed_value;
impact_summary; rollback_metadata; data-proposal-editor;
data-proposal-diff-preview; data-proposal-only="true";
data-active-memory-mutation="false"; proposalDraftRefreshWarning;
upsertProposalDraftChange; removeProposalDraftChange; saveProposalDraftStore;
loadProposalDraftStore; serializeProposalDraftStore; 导出 proposal JSON;
撤销本地调整; 可导出 JSON; No raw/private; No direct writeback; No agent apply;
No GitHub main upload.
