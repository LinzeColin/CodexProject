# Memory Atlas 记忆星系重做验收

- Version: v1.1.6 Stage 7 Phase 1
- Contract ID: `memory_starfield_rebuild_contract`
- Task ID: `MA-V116-S7P01`
- Status: `phase_7_1_contract_created_pending_stage_review`

## Required Checks

Stage 7 Phase 1 passes only when the product contract and records prove all of
the following:

1. `memory_starfield`, `nebula_field`, `flow_field`, `trajectory_trails`,
   `gravity_sources`, `black_hole_core`, `proto_star_cloud`,
   `memory_terrain_layer`, `cluster_constellations` and
   `ambient_depth_particles` are all required.
2. Required interactions include `orbit_pan_zoom`, `hover_card`,
   `click_inspector`, `focus_cluster`, `jump_from_search`, `jump_from_river`,
   `presentation_analysis_toggle`, `keyboard_navigation` and `reduced_motion`.
3. Starfield items include `starfield_item_id`, `item_type`, `theme_id`,
   `topic_state`, `gravity_mass`, `orbit_radius`, `trajectory_refs`,
   `terrain_value`, `importance`, `confidence`, `evidence_count`,
   `evidence_refs`, `source_scope`, `linked_river_range`, `inspector_link` and
   `proposal_hint`.
4. The contract explicitly fails dots-only, nodes-and-edges-only,
   Obsidian-like, chart-like, missing nebula, missing flow field, missing
   trajectories, missing gravity sources, missing black hole, missing
   proto-star, missing terrain, blank fallback and unsafe private text exposure.
5. The phase remains contract-only: no runtime UI, no CSS, no screenshot run, no
   experiment import, no feature flag switch, no direct writeback and no GitHub
   main upload.

## Required Responsive Evidence

Future runtime implementation must capture:

- Desktop 1440x900
- Tablet 768x1024
- Mobile 390x844
- Nonblank WebGL canvas or fallback canvas
- Reduced-motion state

This phase only creates the contract and acceptance file, so screenshots and
canvas checks are future implementation requirements, not evidence for this
phase.

## Failure Conditions

Fail the future implementation if:

- The view is only points.
- The view is only node-link edges.
- The view looks like a generic Obsidian Graph.
- The view lacks nebula, flow field, trails or visible gravity.
- The view lacks `black_hole_core`, `proto_star_cloud` or
  `memory_terrain_layer`.
- Search 2.0 or Memory River links cannot focus the correct starfield target.
- Clicking a memory object or lifecycle marker does not open Inspector.
- Presentation mode exposes dense analysis terrain by default.
- Reduced motion is ignored.
- WebGL failure or low-quality mode renders blank.
- Raw/private/cookie/session/secret text appears in hover cards or Inspector
  handoff.

## Safety

- No runtime UI.
- No CSS change.
- No experiment directory import.
- No feature flag default switch.
- No raw/private data read.
- No raw/private/cookie/session/secret payload.
- No direct writeback.
- No agent apply.
- No Stage 8, Stage 9 or Stage 10 work.
- No GitHub main upload.

Machine-readable boundary summary: No runtime UI; No raw/private data read; No
direct writeback; No GitHub main upload.

## Validation

Required local validator:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.6-stage7-phase1
```

The validator must verify this file, the product contract, package script,
delivery record, model parameters, feature list, development record, model
parameter file, changelog, changed-path scope and runtime/writeback boundary.
