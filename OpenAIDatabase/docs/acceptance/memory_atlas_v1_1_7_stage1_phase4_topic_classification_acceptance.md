# Memory Atlas v1.1.7 Stage 1 Phase 1.4 Topic Classification Acceptance

- Task ID: `MA-V117-S1P04`
- Acceptance ID: `ACC-MA-V117-S1P04`
- Status: `phase_1_4_topic_classification_detail_completed_pending_stage1_review`
- Validator: `validate:v1.1.7-stage1-phase4`

## Acceptance Scope

This phase completes Topic Classification detail visibility for the Home
Overview. It adds a model contract, parameter section, runtime topic cards,
`ThemeDetailPanel`, records and validator.

## Required Topic States

The model and runtime must support `dominant`, `rising`, `declining`,
`emerging`, `conflict`, `black_hole` and `stale`.

## Required Fields

Each visible topic detail must include:

- `topic_id`
- `topic_label`
- `parent_topic`
- `category`
- `topic_state`
- `topic_strength`
- `trend`
- `roi_score`
- `conflict_score`
- `confidence`
- `record_count`
- `recent_count`
- `representative_record_ids`
- `evidence_refs`
- `matched_reason`
- `linked_asset_ids`
- `linked_action_ids`
- `starfield_handoff`
- `river_handoff`
- `proposal_hint`
- `rollback_hint`
- `proposal_only`

## Runtime Acceptance

- Home Overview renders Topic Classification cards for up to Top 10 topics.
- Cards expose `topic_label`, `topic_state`, `topic_strength`, `trend`,
  `category`, `record_count`, `matched_reason` and Starfield handoff.
- Clicking a topic opens `ThemeDetailPanel`.
- `ThemeDetailPanel` shows the full field set, including ROI, conflict,
  confidence, representative records, evidence refs, linked assets/actions,
  Starfield handoff, River handoff and proposal-only safety hints.
- Opening a topic target can synchronize the current focus node and move to
  Memory Starfield or Memory River context without direct writeback.

## Safety Acceptance

- `proposal_only` is always true.
- No raw/private/cookie/session/secret/plaintext transcript data is read.
- No direct writeback is allowed.
- No proposal write is allowed.
- No Stage 2 proposal editor, Search 2.0 runtime, Review workflow runtime,
  Data Map 2.0 runtime, screenshot, production build, app reinstall, deploy or
  GitHub main upload is included.

## Validation

Run:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage1-phase4
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage1-phase3
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage1-phase2
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage1-phase1
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage0
pnpm --dir OpenAIDatabase/apps/memory-atlas run lint
git diff --check -- OpenAIDatabase
```

## Stop Boundary

Stop after Stage 1 Phase 1.4. Do not enter Stage 1 review, Stage 2 proposal
editing, Search 2.0, Review workflow, Data Map 2.0, build, deploy, app install
or GitHub main upload in this run.
