# Memory Atlas 记忆时间河重做验收

- Version: v1.1.6 Stage 6 Phase 1
- Contract ID: `memory_river_rebuild_contract`
- Task ID: `MA-V116-S6P01`
- Status: `phase_6_1_contract_created_pending_stage_review`

## Required Checks

Stage 6 Phase 1 passes only when the product contract and records prove all of
the following:

1. `time_river`, `theme_bands`, `event_pulses`, `decision_nodes`,
   `black_hole_band`, `proto_star_marker` and `evidence_density_lane` are all
   required.
2. Required interactions include `zoom`, `brush`, `hover_card`,
   `click_inspector`, `keyboard_navigation` and `reduced_motion`.
3. River items include `river_item_id`, `item_type`, `occurred_at`, `theme_id`,
   `topic_state`, `importance`, `confidence`, `evidence_count`,
   `evidence_refs`, `source_scope`, `inspector_link` and `proposal_hint`.
4. The contract explicitly fails a default date list, plain dots-and-lines
   timeline, missing lifecycle bands, missing Inspector handoff and unsafe
   private text exposure.
5. The phase remains contract-only: no runtime UI, no CSS, no screenshot run, no
   direct writeback and no GitHub main upload.

## Required Responsive Evidence

Future runtime implementation must capture:

- Desktop 1440x900
- Tablet 768x1024
- Mobile 390x844

This phase only creates the contract and acceptance file, so screenshots are a
future implementation requirement, not evidence for this phase.

## Failure Conditions

Fail the future implementation if:

- The view is a date list.
- The view is a static table.
- The river lacks theme bands.
- Event pulses, decision nodes, `black_hole_band` or `proto_star_marker` are
  missing.
- Brush selection does not sync a time range.
- Clicking a marker does not open Inspector.
- Reduced motion is ignored.
- Raw/private/cookie/session/secret text appears in hover cards or Inspector
  handoff.

## Safety

- No runtime UI.
- No CSS change.
- No raw/private data read.
- No raw/private/cookie/session/secret payload.
- No direct writeback.
- No agent apply.
- No Stage 7, Stage 8, Stage 9 or Stage 10 work.
- No GitHub main upload.

Machine-readable boundary summary: No runtime UI; No raw/private data read; No
direct writeback; No GitHub main upload.

## Validation

Required local validator:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.6-stage6-phase1
```

The validator must verify this file, the product contract, package script,
delivery record, model parameters, feature list, development record, model
parameter file, changelog, changed-path scope and runtime/writeback boundary.
