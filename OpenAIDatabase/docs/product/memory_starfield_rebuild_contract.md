# Memory Atlas 记忆星系重做合同

- Version: v1.1.6 Stage 7 Phase 1
- Contract ID: `memory_starfield_rebuild_contract`
- Task ID: `MA-V116-S7P01`
- Status: `phase_7_1_contract_created_pending_stage_review`

## Goal

Stage 7 treats the existing Galaxy as insufficient for the v1.1.6 visual
roadmap. The default 记忆星系 must communicate memory gravity, emergence,
decay, opportunity and terrain at first glance. A plain node graph, Obsidian-like
dots-and-lines map, static scatterplot or chart-looking network is not
acceptable.

This phase creates the product and acceptance contract only. It does not replace
the current renderer, import experiment code, change runtime UI, change CSS,
start browser screenshot validation or switch feature flags.

## Required Visual Layers

The Memory Starfield must define these visible layers:

1. `memory_starfield`: a spatial memory field with depth, scale and luminance.
2. `nebula_field`: colored memory-cloud structure around active themes.
3. `flow_field`: visible directional flow showing theme movement and pull.
4. `trajectory_trails`: arcs or trails that show memory movement and history.
5. `gravity_sources`: dominant theme attractors that visibly bend nearby memory.
6. `black_hole_core`: low-value loop, stale or risk collapse region.
7. `proto_star_cloud`: emerging opportunity and growth cloud.
8. `memory_terrain_layer`: analysis-mode terrain for density, risk and
   opportunity gradients.
9. `cluster_constellations`: readable groupings without reducing the view to a
   generic graph.
10. `ambient_depth_particles`: non-data decorative depth that never replaces
    real memory objects.

## Required Interactions

The Memory Starfield must support:

- `orbit_pan_zoom`: inspect space without losing current cluster context.
- `hover_card`: show redacted summary, source scope, confidence and evidence
  count.
- `click_inspector`: open Inspector for memory object, cluster, gravity source,
  black hole, proto-star or terrain region.
- `focus_cluster`: isolate a cluster while preserving surrounding gravity
  context.
- `jump_from_search`: focus the starfield target from Search 2.0 result actions.
- `jump_from_river`: focus the same theme or time-linked memory from Memory
  River selections.
- `presentation_analysis_toggle`: keep presentation mode visually clean and
  reveal terrain/diagnostics only in analysis mode.
- `keyboard_navigation`: reach core objects and Inspector handoff without
  pointer-only interaction.
- `reduced_motion`: reduce continuous motion, orbit drift and particle feedback.

## Required Data Fields

Every visible memory object, cluster or lifecycle marker must be backed by
redacted derived fields:

- `starfield_item_id`
- `item_type`
- `theme_id`
- `theme_label`
- `topic_state`
- `gravity_mass`
- `orbit_radius`
- `trajectory_refs`
- `terrain_value`
- `importance`
- `confidence`
- `evidence_count`
- `evidence_refs`
- `source_scope`
- `linked_river_range`
- `linked_asset_ids`
- `linked_action_ids`
- `inspector_link`
- `proposal_hint`

## Anti-Regression Rules

Fail the future implementation if:

- The default view is only dots.
- The default view is only nodes and edges.
- The visual result looks like a generic Obsidian Graph.
- The visual result reads as a chart instead of a memory environment.
- `nebula_field` is absent.
- `flow_field` is absent.
- `trajectory_trails` are absent.
- `gravity_sources` are absent.
- `black_hole_core` is absent.
- `proto_star_cloud` is absent.
- `memory_terrain_layer` is absent from analysis mode.
- Hover cards expose raw/private/cookie/session/secret text.
- Inspector handoff is missing.
- Reduced motion still plays continuous orbit or particle motion.
- WebGL failure or low-quality mode becomes blank.

## Safety Boundary

- `redacted_summary_only`
- No raw/private/cookie/session/secret payloads.
- No direct active-memory writeback.
- No direct writeback.
- No agent apply.
- No runtime UI implementation.
- No CSS change.
- No browser screenshot run in this phase.
- No experiment directory import.
- No feature flag default switch.
- No Stage 8, Stage 9 or Stage 10 work.
- No GitHub main upload.

Machine-readable boundary summary: No runtime UI; No raw/private data read; No
direct writeback; No GitHub main upload.

本 phase 不修改运行时，不读取 raw/private，不直接写长期记忆，不进入 Stage 7
整体复审，不上传 GitHub main。

## Acceptance Hook

Future implementation phases must provide screenshots and canvas checks for:

- Desktop 1440x900
- Tablet 768x1024
- Mobile 390x844
- Nonblank WebGL canvas or nonblank fallback canvas
- Reduced motion

This contract only defines the Memory Starfield rebuild product and acceptance
boundary.
