# Memory Atlas v1.1.7 Stage 1 Phase 1.2 Next Action Acceptance

- Task ID: `MA-V117-S1P02`
- Acceptance ID: `ACC-MA-V117-S1P02`
- Status: `phase_1_2_next_action_detail_completed_pending_stage1_review`
- Validator: `validate:v1.1.7-stage1-phase2`

## Scope

This phase makes suggested actions visible, sortable, explainable and clickable.
It adds a Next Action model and an Action Detail Drawer, while preserving the
proposal-only and no-direct-writeback safety boundary.

## Required Evidence

| Evidence | Required proof |
|---|---|
| Product model | `docs/architecture/next_action_model.md` defines `next_action_model_v1_1_7_stage1_phase2`, required fields, sort score, Top 5 cap and fallback policy. |
| Parameter template | `config/visualization/model_parameters.universe_state.yaml` registers `MA-V117-S1P02`, required fields, sort weights and no-writeback boundary. |
| Runtime model | `apps/memory-atlas/src/App.tsx` exposes `HomeActionDetail`, `buildNextActionDetails`, `nextActionSortScore`, `selectedActionDetail`, and `ActionDetailDrawer`. |
| Runtime component | `apps/memory-atlas/src/components/ActionDetailDrawer.tsx` renders reason, ROI, effort cost, urgency, source, evidence, status, next step, linked topics/assets, proposal hint and rollback hint. |
| Runtime display | Home action cards expose ROI, effort cost, urgency, evidence count and next step, and open the detail drawer on click. |
| Styling | `apps/memory-atlas/src/styles.css` contains stable card/detail drawer layout, responsive constraints and no text overflow. |
| Safety | The UI marks all action changes as proposal-only; it does not write proposal JSON or mutate active memory in this phase. |
| Records | Changelog, feature list, development record, model parameter records and delivery record register this phase. |

## Required Action Fields

Each action detail must contain:

1. `action_id`
2. `title`
3. `action_type`
4. `reason`
5. `roi_score`
6. `effort_cost`
7. `urgency`
8. `confidence`
9. `source`
10. `status`
11. `evidence_count`
12. `evidence_refs`
13. `matched_reason`
14. `linked_topic_ids`
15. `linked_asset_ids`
16. `next_step`
17. `recommended_time_window`
18. `proposal_hint`
19. `rollback_hint`
20. `proposal_only`

## Failure Conditions

This phase fails if any of the following is true:

1. Fewer than five actions can be rendered when at least five candidate signals
   exist.
2. Actions cannot be sorted by ROI, urgency, confidence and effort.
3. Clicking an action does not open a detail drawer.
4. The detail drawer lacks reason, ROI, effort, urgency, source, evidence,
   status, next step, linked topics/assets, proposal hint or rollback hint.
5. The UI directly writes active memory, proposal JSON, raw/private data,
   cookies, sessions, secrets, deployment state or GitHub main.
6. Phase 1.3 tier asset detail, Phase 1.4 topic detail, Stage 2 proposal editor,
   browser screenshot, production build, app install or deploy work is included.

Machine-readable safety phrase: No raw/private data read. No direct writeback.
No proposal write. No GitHub main upload before whole Stage 0-8 completion.

## Validation

Required command:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage1-phase2
```

Recommended regression checks:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage1-phase1
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage0
pnpm --dir OpenAIDatabase/apps/memory-atlas run lint
git diff --check -- OpenAIDatabase
```

## Stop Boundary

Stop after this phase is validated and committed locally. Do not enter Stage 1
Phase 1.3, do not implement tier asset detail, do not implement topic detail,
do not run final app reinstall/upload gates, and do not upload to GitHub main
before the full Stage 0-8 project is complete.
