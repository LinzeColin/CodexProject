# Memory Atlas 记忆时间河重做合同

- Version: v1.1.6 Stage 6 Phase 1
- Contract ID: `memory_river_rebuild_contract`
- Task ID: `MA-V116-S6P01`
- Status: `phase_6_1_contract_created_pending_stage_review`

## Goal

Stage 6 treats the old Timeline as a 0-score surface and rebuilds it as a
记忆时间河. The user must be able to see how memories evolve over time, how
themes strengthen or decay, where decisions happened, and which black-hole or
proto-star signals require action. A date list, flat activity table, or ordinary
timeline is not acceptable.

## Required Visual Layers

The Memory River must define these visible layers:

1. `time_river`: a continuous river surface anchored to real event time.
2. `theme_bands`: parallel or braided theme bands that show dominant, rising,
   declining and conflict topic flow.
3. `event_pulses`: visible pulses for important memory events.
4. `decision_nodes`: explicit decision markers with evidence and Inspector
   handoff.
5. `black_hole_band`: decay, stale, low-value-loop or risk compression region.
6. `proto_star_marker`: emerging opportunity markers and growth paths.
7. `evidence_density_lane`: compact evidence-count density without exposing raw
   private text.

## Required Interactions

The Memory River must support:

- `zoom`: zoom in/out without losing event labels or theme context.
- `brush`: select a time range and sync the selected range to shared state.
- `hover_card`: show a redacted summary, source scope, confidence and evidence
  count.
- `click_inspector`: open Inspector for an event, decision, theme band or
  lifecycle signal.
- `keyboard_navigation`: reach river markers without pointer-only interaction.
- `reduced_motion`: disable autoplay, excessive transitions and feedback motion
  when reduced motion is active.

## Required Data Fields

Every visible river item must be backed by redacted derived fields:

- `river_item_id`
- `item_type`
- `occurred_at`
- `theme_id`
- `theme_label`
- `topic_state`
- `importance`
- `confidence`
- `evidence_count`
- `evidence_refs`
- `source_scope`
- `linked_asset_ids`
- `linked_action_ids`
- `inspector_link`
- `proposal_hint`

## Anti-Regression Rules

Fail the future implementation if:

- The default view is a date list.
- The river is only dots and lines.
- Theme bands are absent.
- Event pulses are absent.
- Decision nodes are hidden in text only.
- `black_hole_band` and `proto_star_marker` are absent.
- Zoom or brush changes do not preserve Inspector handoff.
- Hover cards expose raw/private/cookie/session/secret text.
- Reduced motion still plays automatic animation or pseudo-haptic feedback.

## Safety Boundary

- `redacted_summary_only`
- No raw/private/cookie/session/secret payloads.
- No direct active-memory writeback.
- No direct writeback.
- No agent apply.
- No runtime UI implementation.
- No CSS change.
- No browser screenshot run in this phase.
- No Stage 7, Stage 8, Stage 9 or Stage 10 work.
- No GitHub main upload.

Machine-readable boundary summary: No runtime UI; No raw/private data read; No
direct writeback; No GitHub main upload.

本 phase 不修改运行时，不读取 raw/private，不直接写长期记忆，不进入 Stage 6
整体复审，不上传 GitHub main。

## Acceptance Hook

Future implementation phases must provide screenshots for:

- Desktop 1440x900
- Tablet 768x1024
- Mobile 390x844

This contract only defines the Memory River rebuild product and acceptance
boundary.
