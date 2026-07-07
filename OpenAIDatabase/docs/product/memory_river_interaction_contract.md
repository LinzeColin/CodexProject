# Memory River Interaction Contract

- Product target: Memory Atlas v1.1.5
- Stage: 0 合同与边界冻结
- Current phase contribution: 0.2.3 记忆时间河 Interaction Contract
- Status: interaction contract only; no production UI implementation
- Last updated: 2026-06-30

## v1.1.7 Stage 5 Phase 5.1 Interaction Contract Addendum

- Contract version: `memory_river_interaction_contract.v1_1_7_stage5_phase1`
- Feedback contract version: `memory_river_feedback_contract.v1_1_7_stage5_phase1`
- Task ID: `MA-V117-S5P01`
- Acceptance ID: `ACC-MA-V117-S5P01`
- Status: `phase_5_1_interaction_contract_completed_pending_stage5_review`
- Validator: `validate:v1.1.7-stage5-phase1`

This addendum upgrades the earlier Memory River interaction contract to the
v1.1.7 Stage 5.1 roadmap boundary. It defines the required interaction and
feedback behavior before any C3 River Spike, Timeline replacement or production
integration work.

Stage 5.1 must keep Memory River clearly `not a date list`, `not a table` and
`not a static scatter`. The required interaction vocabulary is:

1. `zoom`: inspect year / month / week / day scale windows without shifting
   UTC event dates.
2. `brush`: select a time range and expose readable start/end date state.
3. `theme_lanes`: show theme, project, opportunity, conflict and asset
   trajectories as lanes rather than a flat list.
4. `event_points`: mark dated events, decisions, bursts and milestones with
   redacted summaries.
5. `status_bands`: show black-hole / proto-star / stale lifecycle intervals as
   candidate bands, not final claims.
6. `detail_panel`: open or synchronize a redacted detail panel / Inspector view
   for selected lane, event point or status band evidence.

The required feedback vocabulary is:

1. `visual_feedback`: highlight hover, lock, brush and density threshold states.
2. `optional_audio`: audio may exist only as an optional future setting.
3. `audio_default_off`: audio must be disabled by default.
4. `pseudo_haptic`: tactile feel may only be simulated through visual/timing
   feedback.
5. `vibration_not_required`: real platform vibration must never be required.
6. `reduced_motion`: reduced motion must disable continuous animation and
   suppress optional pseudo-haptic/audio effects.
7. `feedback_disable_control`: users must be able to disable dynamic feedback.

Boundary for this v1.1.7 phase:

- No C3 River Spike.
- No Timeline replacement.
- No Stage 5.2.
- No runtime UI implementation.
- No CSS change.
- No browser screenshot run in this phase.
- No raw/private/cookie/session/secret data access.
- No direct active-memory writeback.
- No agent apply.
- No deploy.
- No GitHub main upload before the whole Stage 0-10 project is complete.

## Purpose

“记忆时间河”是现有 Timeline 的目标升级形态。它必须把主题、项目、机会、冲突、低价值循环和行为变化随时间的形成、增强、衰退和迁移呈现为动态时间河，也就是 dynamic time river，而不是 table、list 或 static scatter。

This contract freezes required interaction behavior before spike and production integration.

## Hard Interaction Boundary

记忆时间河不得退回以下形态：

1. 静态事件列表。
2. 表格型流水账。
3. 只有点位的 static scatter。
4. 无缩放、无选择窗口、无主题层的时间图。
5. 只显示 activity count 而无法解释主题演化。

The river must be data-driven and synchronized with Memory Overview, Memory Starfield, Inspector and ROI Dashboard.

## River Model

The river is a time-based evolution view.

Required visual/semantic elements:

| Element | Meaning |
|---|---|
| Main current | overall memory/activity flow |
| Theme lanes | project/theme/category trajectories |
| Event pulses | records, decisions, bursts, milestones |
| Density backdrop | activity intensity over time |
| Black Hole band | repeated low-value loop or conflict period |
| Proto-Star marker | emerging opportunity or new theme |
| River widening | expansion of active context |
| River narrowing | consolidation or inactivity |

## Required Interactions

### 1. Zoom

Zoom must allow the user to move between long-range and fine-grained time windows.

Required behavior:

1. Support horizontal time zoom.
2. Preserve selected source/filter/theme state.
3. Keep event-date positioning accurate.
4. Keep labels readable through level-of-detail changes.
5. Provide reduced-motion fallback for animated zoom.

### 2. Brush

Brush selects a time window and updates shared state.

Required behavior:

1. Drag/select a date range.
2. Display selected start/end dates.
3. Sync `time_range` or `brush_range` with Memory Overview and Inspector.
4. Keep selection visible after view changes.
5. Support clear/reset.

### 3. Theme Lanes

Theme lanes show topic/project/category evolution as separate but synchronized currents.

Required behavior:

1. Lanes must derive from Universe State or existing redacted cluster/theme data.
2. Lanes can be highlighted, collapsed or filtered.
3. Lane order must be explainable by relevance, activity, confidence or user filter.
4. Lane hover shows human-readable theme summary and evidence count.

### 4. Black Hole Band

Black Hole band marks periods where low-value loops, conflicts, repeated errors or attention sinks intensify.

Required behavior:

1. Show start/end or intensity range.
2. Distinguish from normal high activity.
3. Click opens Inspector with cause, evidence and suggested reduction action.
4. In Presentation Mode, use a restrained but visible signal.
5. In Analysis Mode, show score/explanation when available.

### 5. Proto-Star Marker

Proto-Star marker marks the first visible formation of emerging opportunities or new themes.

Required behavior:

1. Show approximate emergence date.
2. Link to evidence and related theme lane.
3. Mark uncertainty and early-stage status.
4. Click opens validation action or evidence review.

### 6. Pseudo-Haptic Feedback

Pseudo-haptic feedback means visual/timing feedback that makes interaction feel tactile without requiring platform haptics.

Allowed effects:

1. Slight snap or resistance when brush crosses dense regions.
2. Small pulse on selection lock.
3. Brief highlight when crossing Black Hole band or Proto-Star marker.
4. Cursor-adjacent feedback for zoom/brush thresholds.

Requirements:

1. Must be subtle and non-blocking.
2. Must have reduced-motion fallback.
3. Must not use audio or vibration as a required path.

### 7. Reduced Motion

Reduced motion must be a first-class interaction mode, not an afterthought.

Required behavior:

1. Disable or shorten continuous river animation.
2. Replace animated transitions with direct state changes or short fades.
3. Keep zoom, brush, lanes, Black Hole band and Proto-Star marker usable.
4. Respect browser/user preference where available.

## Shared State Sync

记忆时间河 must share and update:

1. `source_scope`
2. `time_range`
3. `brush_range`
4. `filters`
5. `selection_state`
6. `mode`: Presentation / Analysis
7. `inspector_focus`

Clicking river elements must sync Inspector. Selecting a range must make Memory Overview River Pulse and Memory Starfield filters reflect the same time window.

## Data Boundary

The river may use only:

1. Redacted derived timeline records.
2. Aggregated activity density.
3. `Universe State Snapshot`.
4. Existing visualization snapshot data.
5. Theme/project/category summaries and counts.

It must not use raw transcript text, tokens, cookies, browser state, hidden sessions, plaintext secrets or private full-message exports.

## Non-Goals

This phase does not:

1. Build a D3 or canvas spike.
2. Replace current Timeline production code.
3. Add playback cursor implementation.
4. Add feature flags.
5. Add ingestion or writeback.
6. Change navigation or default route.

## Acceptance Criteria

Phase 0.2.3 is accepted when this document:

1. Redefines Timeline as dynamic memory river, not list/table/static scatter.
2. Includes `zoom`.
3. Includes `brush`.
4. Includes `theme lanes`.
5. Includes `black hole band`.
6. Includes `proto-star marker`.
7. Includes `pseudo-haptic`.
8. Includes `reduced motion`.
9. Defines shared-state sync and Inspector handoff.
10. States privacy and non-implementation boundaries.

## Rollback

Delete this document before spike work begins or revert to the previous Timeline contract state. No production code rollback is required because this contract phase does not change runtime behavior.
