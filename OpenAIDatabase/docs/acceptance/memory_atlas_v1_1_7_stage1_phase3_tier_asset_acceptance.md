# Memory Atlas v1.1.7 Stage 1 Phase 1.3 Tier Asset Acceptance

- Task ID: `MA-V117-S1P03`
- Acceptance ID: `ACC-MA-V117-S1P03`
- Status: `phase_1_3_tier_asset_detail_completed_pending_stage1_review`
- Required validator: `validate:v1.1.7-stage1-phase3`

## Scope

This phase implements the tier asset detail surface promised by Roadmap v2:
core profile, project, decision, workflow, knowledge, opportunity and stale
assets must become concrete, explainable and clickable. The user must see what
the asset is, why it matters, which theme it belongs to, when it was last seen,
how confident the system is and what safe next action is recommended.

## Required Evidence

- `docs/architecture/level_asset_model.md`
- `config/visualization/model_parameters.universe_state.yaml`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/components/AssetDetailPanel.tsx`
- `apps/memory-atlas/src/styles.css`
- governance records and this acceptance file

## Required Asset Fields

Every rendered tier asset detail must expose:

- `asset_id`
- `asset_tier`
- `title`
- `summary`
- `theme`
- `value_score`
- `updated_at`
- `importance`
- `priority`
- `confidence`
- `staleness_status`
- `last_seen_range`
- `evidence_count`
- `evidence_refs`
- `source_scope`
- `linked_action_ids`
- `linked_topic_ids`
- `recommended_asset_action`
- `proposal_hint`
- `rollback_hint`
- `proposal_only`

## Runtime Acceptance

- Home Overview shows a Level Assets section with grouped asset cards.
- Asset groups include `core_profile`, `project`, `decision`, `workflow`,
  `knowledge`, `opportunity` and `stale` when matching derived assets exist.
- Each card shows tier, title, theme, value score, importance, priority,
  staleness status, confidence, evidence count and recommended asset action.
- Clicking a card opens `AssetDetailPanel`.
- `AssetDetailPanel` shows summary, source scope, linked actions, linked
  topics, last seen range, updated at, evidence refs, proposal hint and rollback
  hint.
- The panel must be explicitly `proposal_only` and must expose
  `data-active-memory-mutation="false"`.
- Missing data renders an empty explanation, not mock data.

## Safety

- No raw/private/cookie/session/secret/plaintext transcript data may be read or
  rendered.
- No direct writeback is allowed.
- No proposal JSON write is allowed in Phase 1.3.
- No agent apply is allowed.
- No browser screenshot, production build, local app reinstall, deploy or
  GitHub main upload is allowed in this phase.

Machine-readable boundary summary: No raw/private; No direct writeback; No proposal write; No agent apply; No GitHub main upload.

## Failure Conditions

- Asset detail is only a count or bar chart.
- Any required field is absent from the model, component or records.
- Any UI path mutates active memory directly.
- The implementation enters Phase 1.4 topic classification detail.
- The implementation reads raw/private data or writes proposal JSON.
- The implementation uploads to GitHub main.

## Validation

Required commands:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage1-phase3
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage1-phase2
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage1-phase1
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage0
pnpm --dir OpenAIDatabase/apps/memory-atlas run lint
git diff --check -- OpenAIDatabase
```

## Stop Boundary

Stop after Stage 1 Phase 1.3. Do not implement topic classification detail,
proposal editor, Search 2.0, Review workflow, Data Map 2.0, screenshots,
build, app reinstall, deploy or GitHub main upload.
