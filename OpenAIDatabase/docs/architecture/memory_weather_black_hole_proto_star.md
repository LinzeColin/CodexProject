# Memory Weather, Black Hole and Proto-Star Score Contract

- Product target: Memory Atlas v1.1.5
- Stage: 0 C2 contracts and spike directories
- Current task contribution: Task 0.4 Universe State Architecture
- Status: score contract only; no generator implementation
- Last updated: 2026-06-30

## Purpose

This document defines the semantic score layer behind Universe State Snapshot.
It describes how Memory Weather, Black Hole, Proto-Star and stale signals should
be calculated from redacted derived Memory Atlas data.

The formulas are v1 heuristic contracts. They are intentionally explicit,
auditable and parameterized so Task 0.5 can move the numeric constants into
version-controlled YAML templates.

## Shared Input Policy

All scores may use only redacted derived inputs:

1. Aggregate counts from `overview`, `metrics`, `contribution` and
   `data_sources`.
2. Redacted `nodes`, `edges` and `timeline` records.
3. Source scope and writeback policy from `source_contract`.
4. Agent recommendation summaries that already exclude raw/private data.
5. Existing score-like fields that are public-redacted and documented.

No score may use raw transcript text, private full messages, cookies, browser
state, hidden sessions, plaintext secrets or local absolute paths.

All score outputs must be normalized to `0..1` and should carry enough
diagnostics for Inspector to explain them without exposing private source text.

## Normalization Helpers

Use simple deterministic helper functions:

```text
clamp01(x) = min(1.0, max(0.0, x))
safe_div(n, d) = 0.0 when d <= 0 else n / d
norm_count(x, p95) = clamp01(safe_div(x, max(1, p95)))
recency_signal(days, half_life_days) = 0.5 ** (days / half_life_days)
staleness_signal(days, threshold_days) = clamp01(days / threshold_days)
```

Any missing input must emit a diagnostic and fall back to `0.0` for positive
evidence signals or `0.5` for uncertainty when the score needs a neutral
penalty.

## Black Hole Score

Black Hole identifies low-value loops, repeated mistakes, attention sinks,
repeated unresolved conflict or high-activity/low-progress zones.

V1 formula:

```text
black_hole_score = clamp01(
  interaction_signal * 0.28
  + recency_signal * 0.22
  + repetition_signal * 0.25
  + roi_penalty_signal * 0.15
  + growth_penalty_signal * 0.10
)
```

Signal meanings:

| Signal | Meaning | Candidate redacted inputs |
|---|---|---|
| `interaction_signal` | high interaction density around the same low-value area | timeline count, edge density, contribution density |
| `recency_signal` | risk is recent enough to matter | latest derived event date |
| `repetition_signal` | same pattern repeats across sessions or dates | repeated category/theme labels, repeated related nodes |
| `roi_penalty_signal` | low leverage or weak action value | ROI/staleness derived fields when available |
| `growth_penalty_signal` | activity is not producing rising/dominant progress | low growth versus high activity |

Severity thresholds:

| Score range | Severity | UI meaning |
|---|---|---|
| `< 0.45` | watch | show only in Analysis Mode or Inspector |
| `0.45..0.65` | warning | visible risk cue |
| `>= 0.65` | critical | Black Hole object/band is visible by default |

Inspector explanation must include top contributing signals, evidence count,
time band, affected clusters and recommended reduction action. It must not
include raw evidence text.

## Proto-Star Score

Proto-Star identifies early opportunities, new capability growth, emerging
projects or promising cross-signal themes.

V1 formula:

```text
proto_star_score = clamp01(
  recency_growth_signal * 0.30
  + cross_signal * 0.20
  + capability_relation_signal * 0.25
  + roi_potential_signal * 0.20
  - uncertainty_penalty * 0.05
)
```

Signal meanings:

| Signal | Meaning | Candidate redacted inputs |
|---|---|---|
| `recency_growth_signal` | recent increase in activity or evidence | recent timeline count versus prior window |
| `cross_signal` | appears across multiple sources, categories or linked themes | source scope, edges, category diversity |
| `capability_relation_signal` | relates to skills, projects or long-lived goals | theme labels, category, existing core clusters |
| `roi_potential_signal` | likely to create leverage or useful next action | recommended actions, ROI summaries |
| `uncertainty_penalty` | evidence is too sparse or volatile | low evidence count, low confidence, one-off burst |

Promotion thresholds:

| Score range | Status | UI meaning |
|---|---|---|
| `< 0.45` | weak_signal | Inspector only |
| `0.45..0.58` | candidate | show as subtle opportunity |
| `>= 0.58` | proto_star | visible Proto-Star marker/object |

Proto-Star must remain explicitly uncertain until later evidence promotes it to
a rising or dominant cluster. It is an exploration signal, not a commitment.

## Stale Score

Stale score identifies decaying clusters or stale orbits.

V1 formula:

```text
stale_score = clamp01(
  inactive_days_signal * 0.55
  + low_recent_usage_signal * 0.25
  + confidence_decay_signal * 0.20
)
```

Signal meanings:

| Signal | Meaning |
|---|---|
| `inactive_days_signal` | normalized time since last redacted event |
| `low_recent_usage_signal` | recent window has weak activity compared with historical baseline |
| `confidence_decay_signal` | state confidence decays when evidence is old or sparse |

Stale output should recommend refresh, archive, defer or keep. It must not
delete memory.

## Memory Weather

Memory Weather is the top-level summary label used by 记忆总览 and optional
ambient cues in 记忆星系 and 记忆时间河.

Required weather labels:

| Label | Trigger logic | Human meaning |
|---|---|---|
| `clear` | no major Black Hole or conflict risk; dominant/rising clusters are coherent | system is coherent and actionable |
| `storm_conflict` | conflict score or Black Hole score exceeds `0.72` | repeated conflict or high-risk loop needs review |
| `black_hole_warning` | max Black Hole score exceeds `0.65` | low-value loop or attention sink is material |
| `proto_star_cloud` | max Proto-Star score exceeds `0.58` and Black Hole risk is below warning | new opportunity is forming |
| `cold_stale` | stale score dominates and recent activity is weak | memory area is cooling or neglected |
| `mixed_front` | both opportunity and risk are elevated | decide what to continue and what to reduce |

Weather selection order:

1. If any critical conflict or Black Hole risk exists, prefer
   `storm_conflict` or `black_hole_warning`.
2. Else if Proto-Star opportunity is high, use `proto_star_cloud`.
3. Else if stale score dominates, use `cold_stale`.
4. Else if high opportunity and moderate risk coexist, use `mixed_front`.
5. Else use `clear`.

Memory Weather must include:

1. `label`
2. `summary`
3. `driver_ids`
4. `confidence`
5. `coverage`
6. `inspector_explanation`

## Memory Terrain

Memory Terrain is derived from the same state layer but rendered primarily by
记忆星系.

Terrain mapping:

| Terrain type | Trigger logic | Meaning |
|---|---|---|
| `ridge` | high dominant mass and stable repeated evidence | persistent high-ROI theme |
| `valley` | low activity and low confidence | underdeveloped area |
| `basin` | elevated Black Hole score | repeated low-value loop |
| `fault_line` | elevated conflict score | contradiction or unresolved decision |
| `shoreline` | Proto-Star near mature cluster | boundary between mature and emerging topics |

Presentation Mode should show Memory Terrain only as a subtle hint. Analysis
Mode may show terrain type, formula signals and Inspector explanation.

## Lifecycle and Review

Score outputs have four review states:

1. `computed`: generated from current redacted snapshot.
2. `explainable`: has driver signals and evidence counts.
3. `review_ready`: ready for human/agent review.
4. `expired`: source snapshot or parameter version changed.

Any score missing required inputs must carry `diagnostics.missing_inputs` and
must not be used as a critical visual signal.

## Safety Rules

1. Scores are decision-support signals, not commands.
2. Black Hole never deletes memory and never applies writeback.
3. Proto-Star never creates a project or active memory by itself.
4. Memory Weather must not hide uncertainty.
5. Inspector explanations must reference derived IDs, counts and summaries, not
   raw/private text.
6. All recommended actions remain proposal-only.

## Acceptance Criteria

Task 0.4 score architecture is accepted when this document defines:

1. Black Hole score formula.
2. Proto-Star score formula.
3. Stale score formula.
4. Memory Weather labels and threshold logic.
5. Memory Terrain mapping.
6. Source inputs and safety boundaries.
7. Lifecycle and missing-input behavior.

## Rollback

Delete this document before generator implementation begins. No production code
rollback is required because this contract does not change runtime behavior.
