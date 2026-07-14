# Universe State Snapshot Architecture

- Product target: Memory Atlas v1.1.5
- Stage: 0 C2 contracts and spike directories
- Current task contribution: Task 0.4 Universe State Architecture
- Status: architecture contract only; no generator implementation
- Last updated: 2026-06-30

## Purpose

Universe State Snapshot is the shared state layer for Memory Atlas v1.1.5. It
turns the existing redacted Memory Atlas visualization snapshot into one
auditable state object consumed by 记忆总览、记忆星系、记忆时间河、Inspector and
ROI Dashboard.

The goal is to prevent each surface from recomputing its own truth. The state
layer must make current memory weather, dominant clusters, rising clusters,
declining clusters, Black Hole risks, Proto-Star opportunities, stale orbits,
river pulse and next actions consistent across the app.

This document is not an implementation. It freezes the v1 shape, field
semantics, source boundaries, consumer mapping and lifecycle before generator
work begins.

## Source Inputs

Universe State v1 may read only redacted derived Memory Atlas data.

Allowed current input:

- `data/derived/visualization/memory_atlas.json`

Observed safe input surfaces in the current snapshot:

| Input key | Current shape | Allowed usage |
|---|---:|---|
| `overview` | object | counts, generated timestamp, coverage metadata |
| `nodes` | list | redacted memory/theme nodes and visual metadata |
| `edges` | list | redacted relationship weights |
| `timeline` | list | redacted event dates and labels |
| `metrics` | list | aggregate tier/category/theme counts |
| `contribution` | object | aggregate activity density by date bucket |
| `data_sources` | list | active source scope and coverage |
| `agent_recommendations` | object | redacted next-action candidates |
| `source_contract` | object | public redacted read-only and writeback policy |
| `visual_layers` | object | current view/layer hints |

Disallowed inputs:

1. Raw OpenAI exports.
2. Raw transcript text and full transcripts.
3. Cookies, browser state, sessions or auth files.
4. Plaintext secrets, private keys or local absolute private paths.
5. Unredacted source refs that would allow reconstructing private messages.
6. Frontend writeback proposals as accepted memory truth.

## Snapshot Envelope

Universe State v1 should be a deterministic JSON-like object with this envelope:

```json
{
  "schema_version": "universe_state_snapshot.v1",
  "generated_at": "ISO-8601 UTC timestamp",
  "source_snapshot": {
    "schema_version": "memory_atlas snapshot version",
    "generated_at": "source overview generated_at",
    "source_scope": "all|chatgpt|codex",
    "time_range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
    "redaction_mode": "public_redacted_read_only_visualization"
  },
  "state": {},
  "consumer_map": {},
  "diagnostics": {}
}
```

The object must be reproducible from the same redacted input and parameter
version. It must not depend on browser state or live local files outside the
allowed derived snapshot.

## Core Fields

### `memory_weather`

Human-readable summary of current cognitive state.

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `label` | string | weather label such as clear, storm, black_hole_warning, proto_star_cloud |
| `summary` | string | one sentence for humans |
| `drivers` | list | dominant signals causing the label |
| `confidence` | number | 0..1 confidence |
| `coverage` | object | source scope and time range |

### `dominant_clusters`

Clusters with the strongest current mass or leverage.

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `cluster_id` | string | stable derived ID |
| `label` | string | human-readable label |
| `theme_id` | string | theme grouping |
| `mass_score` | number | normalized importance/activity mass |
| `evidence_count` | integer | redacted supporting record count |
| `source_scope` | string | source selection scope |
| `recommended_action` | string | overview action hint |

### `rising_clusters`

Clusters with recent growth or increasing cross-signal evidence.

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `cluster_id` | string | stable derived ID |
| `growth_score` | number | normalized 0..1 growth |
| `recent_signal_count` | integer | recent redacted event count |
| `related_proto_star_ids` | list | linked opportunity IDs |
| `explanation` | string | human-readable reason |

### `declining_clusters`

Clusters losing activity, confidence or decision momentum.

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `cluster_id` | string | stable derived ID |
| `decline_score` | number | normalized 0..1 decline |
| `inactive_days` | integer | days since latest signal when available |
| `stale_orbit_id` | string | linked stale-orbit signal |
| `recommended_action` | string | refresh, archive or defer |

### `conflict_zones`

Clusters or periods with contradiction, repeated switching or unresolved
decision conflict.

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `zone_id` | string | stable derived ID |
| `related_cluster_ids` | list | affected clusters |
| `conflict_score` | number | normalized 0..1 conflict |
| `evidence_count` | integer | redacted evidence count |
| `inspector_summary` | string | short explanation |

### `black_holes`

Low-value loops, repeated mistakes, attention sinks or unresolved conflict
zones. Detailed scoring is defined in
`memory_weather_black_hole_proto_star.md`.

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `black_hole_id` | string | stable derived ID |
| `score` | number | normalized 0..1 Black Hole score |
| `severity` | string | watch, warning or critical |
| `related_cluster_ids` | list | affected clusters |
| `time_band` | object | start/end when temporal evidence exists |
| `recommended_reduction_action` | string | proposal-only action |

### `proto_stars`

Early opportunities, new themes or capability-growth candidates. Detailed
scoring is defined in `memory_weather_black_hole_proto_star.md`.

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `proto_star_id` | string | stable derived ID |
| `score` | number | normalized 0..1 Proto-Star score |
| `uncertainty` | number | normalized 0..1 uncertainty |
| `related_cluster_ids` | list | supporting clusters |
| `first_seen_date` | string | first derived event date if available |
| `validation_action` | string | proposal-only validation step |

### `stale_orbits`

Inactive or decaying themes that may need refresh, archive or lower priority.

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `stale_orbit_id` | string | stable derived ID |
| `cluster_id` | string | affected cluster |
| `stale_score` | number | normalized 0..1 stale score |
| `inactive_days` | integer | recency gap |
| `recommended_action` | string | refresh, archive, defer or keep |

### `memory_terrain`

Semantic terrain layer for 记忆星系.

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `terrain_id` | string | stable derived ID |
| `terrain_type` | string | ridge, valley, basin, fault_line or shoreline |
| `related_cluster_ids` | list | clusters forming the terrain feature |
| `strength` | number | normalized 0..1 |
| `presentation_hint` | string | subtle visual hint |
| `analysis_explanation` | string | explainable reason |

### `river_pulse`

Time evolution summary for 记忆总览 and 记忆时间河.

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `recent_window_days` | integer | analyzed recent window |
| `activity_density` | number | normalized 0..1 recent density |
| `dominant_lane_ids` | list | top theme lanes |
| `black_hole_band_ids` | list | linked Black Hole bands |
| `proto_star_marker_ids` | list | linked opportunity markers |
| `summary` | string | human-readable pulse summary |

### `mini_starfield`

Lightweight preview data for 记忆总览.

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `preview_cluster_ids` | list | clusters visible in overview preview |
| `black_hole_ids` | list | visible risk signals |
| `proto_star_ids` | list | visible opportunity signals |
| `density_hint` | number | normalized 0..1 preview density |
| `target_view` | string | memory_starfield |

### `recommended_next_actions`

Human-usable next actions derived from state signals.

Required fields:

| Field | Type | Meaning |
|---|---|---|
| `action_id` | string | stable derived ID |
| `action_type` | string | continue, review, consolidate, explore or defer |
| `label` | string | human-readable action |
| `reason` | string | why this action is recommended |
| `linked_state_ids` | list | state objects that support it |
| `proposal_only` | boolean | must be true |

## Consumer Matrix

| Field | 记忆总览 | 记忆星系 | 记忆时间河 | Inspector | ROI Dashboard |
|---|---|---|---|---|---|
| `memory_weather` | primary headline | ambient state tint | time-window label | explanation | status context |
| `dominant_clusters` | state cards | gravitational core | theme lane emphasis | evidence summary | leverage ranking |
| `rising_clusters` | opportunity cards | brightening clusters | upward pulses | evidence summary | invest/continue candidate |
| `declining_clusters` | review/archive cards | fading orbits | decaying lanes | evidence summary | refresh/defer candidate |
| `conflict_zones` | risk cards | fault lines | turbulent periods | cause and evidence | risk penalty context |
| `black_holes` | risk cards | black hole objects | black hole bands | score breakdown | reduce/defer candidate |
| `proto_stars` | opportunity cards | proto-star objects | proto-star markers | validation evidence | explore candidate |
| `stale_orbits` | stale cards | weak outer orbits | inactive lanes | stale reason | refresh/defer candidate |
| `memory_terrain` | summary hint | terrain layer | optional lane grouping | terrain explanation | not primary |
| `river_pulse` | preview module | time filter hint | primary current | selected-window details | activity context |
| `mini_starfield` | preview module | target view state | not primary | preview explanation | not primary |
| `recommended_next_actions` | action list | object callouts | range callouts | action evidence | action ranking |

## v1.1.7 Stage 1 Phase 1 Addendum

- Task ID: `MA-V117-S1P01`
- Acceptance ID: `ACC-MA-V117-S1P01`
- Status: `phase_1_1_universe_state_schema_completed_pending_stage1_review`
- Validator: `validate:v1.1.7-stage1-phase1`

Roadmap v2 requires Universe State to be the shared source for detail
visibility, Data Map 2.0, Search 2.0 and Review / Summary / Iteration, not only
the earlier overview, starfield and river surfaces. This addendum keeps the
existing `universe_state_snapshot.v1` schema version and deterministic
generator, but expands the required consumer map for v1.1.7 Stage 1.

Required v1.1.7 state fields for this phase:

1. `memory_weather`
2. `dominant_clusters`
3. `rising_clusters`
4. `declining_clusters`
5. `conflict_zones`
6. `black_holes`
7. `proto_stars`
8. `stale_orbits`
9. `memory_terrain`
10. `river_pulse`
11. `mini_starfield`
12. `recommended_next_actions`

Required v1.1.7 consumer map:

| Consumer | Required fields | Deferred enrichment |
|---|---|---|
| `memory_overview` | `memory_weather`, `dominant_clusters`, `proto_stars`, `black_holes`, `river_pulse`, `recommended_next_actions` | Full default-home replacement belongs to Stage 3. |
| `memory_starfield` | `dominant_clusters`, `rising_clusters`, `declining_clusters`, `black_holes`, `proto_stars`, `stale_orbits`, `memory_terrain` | Production visual integration belongs to Stage 4. |
| `memory_river` | `river_pulse`, `dominant_clusters`, `black_holes`, `proto_stars`, `conflict_zones`, `stale_orbits` | Production river integration belongs to Stage 5. |
| `data_map_2_0` | `source_snapshot`, `dominant_clusters`, `rising_clusters`, `declining_clusters`, `stale_orbits`, `memory_terrain`, `recommended_next_actions` | Tier asset expansion belongs to Phase 1.3 and Stage 6. |
| `search_2_0` | `source_snapshot`, `memory_weather`, `dominant_clusters`, `rising_clusters`, `declining_clusters`, `conflict_zones`, `black_holes`, `proto_stars`, `stale_orbits`, `recommended_next_actions` | Search result UI and saved review state belong to Stage 7. |
| `review_summary_iteration` | `memory_weather`, `rising_clusters`, `declining_clusters`, `conflict_zones`, `black_holes`, `proto_stars`, `stale_orbits`, `recommended_next_actions` | Proposal export and iteration closure belong to Stage 8. |
| `inspector` | `memory_weather`, `conflict_zones`, `black_holes`, `proto_stars`, `stale_orbits`, `memory_terrain` | Inspector 2.0 synchronization belongs to Stage 9. |
| `roi_dashboard` | `dominant_clusters`, `rising_clusters`, `declining_clusters`, `black_holes`, `recommended_next_actions` | Ranking UI changes are out of this phase. |

Phase 1.1 is accepted only when `universe_state.schema.json`,
`universe_state.sample.json`, `src/models/universeState.ts` and
`model_parameters.universe_state.yaml` all preserve this map, the sample still
matches deterministic generator output, and all `recommended_next_actions`
remain `proposal_only: true`.

This phase does not implement Phase 1.2 suggested-action detail UI, Phase 1.3
tier asset model, Phase 1.4 topic detail model, proposal editing, direct
writeback, browser screenshots, production build, deploy or GitHub main upload.
No raw/private/cookie/session/secret data is allowed in this phase.

## Lifecycle

Universe State v1 has five lifecycle states:

1. `draft_generated`: generated from a redacted Memory Atlas snapshot.
2. `contract_validated`: schema, privacy and consumer mapping pass.
3. `review_ready`: summary and diagnostics are ready for human/agent review.
4. `published_runtime`: emitted into the runtime snapshot for the app.
5. `expired`: source snapshot or parameter version changed and regeneration is
   required.

Invalidation triggers:

1. New `memory_atlas.json` generated_at timestamp.
2. Source selector or time range changes.
3. Parameter template version changes.
4. Consumer contract changes.
5. Redaction or source-contract mode changes.

## Safety Boundary

Universe State must remain a redacted derived object.

Allowed references:

1. Stable derived IDs.
2. Counts, normalized scores and labels.
3. Short human-readable summaries already safe for public-redacted view.
4. Aggregated source scope and time windows.

Disallowed references:

1. Raw text excerpts from private transcripts.
2. Local absolute paths.
3. Secret values or secret-adjacent hints.
4. Browser or session identifiers.
5. Hidden source file paths that expose private storage layout.

If a required field cannot be generated without unsafe data, emit
`status: "insufficient_redacted_evidence"` for that item and exclude the unsafe
field.

The shorthand audit phrase for this boundary is: no raw transcript data in
Universe State.

## Minimal V1 vs Extensions

Minimal v1 must include:

1. `memory_weather`
2. `dominant_clusters`
3. `rising_clusters`
4. `declining_clusters`
5. `black_holes`
6. `proto_stars`
7. `river_pulse`
8. `mini_starfield`
9. `recommended_next_actions`
10. `consumer_map`
11. `diagnostics.privacy_status`

Optional extensions:

1. `memory_terrain`
2. `stale_orbits`
3. `conflict_zones`
4. richer ROI rationale
5. per-source comparison summaries

## Acceptance Criteria

Task 0.4 architecture is accepted when this document defines:

1. Universe State fields.
2. Source files and data boundaries.
3. Safety/privacy rules.
4. Consumer mapping for 记忆总览、记忆星系、记忆时间河、Inspector and ROI Dashboard.
5. Lifecycle and invalidation rules.
6. Minimal v1 scope that can be implemented without raw/private data.

## Rollback

Delete this document before generator implementation begins. No production code
rollback is required because this contract does not change runtime behavior.
