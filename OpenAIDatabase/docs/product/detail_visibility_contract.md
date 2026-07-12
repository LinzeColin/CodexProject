# Memory Atlas v1.1.7 Stage 0 Phase 3 Detail Visibility Field Contract

Contract ID: `memory_atlas_v1_1_7_stage0_phase3_detail_visibility_contract`

Stage: `v1.1.7 Stage 0`

Phase: `0.3`

Task ID: `MA-V117-S0P03`

Acceptance ID: `ACC-MA-V117-S0P03`

Status: `phase_0_3_detail_visibility_contract_completed_pending_stage0_review`

Machine-readable boundary summary: No runtime UI; No raw/private data read; No
direct writeback; No proposal write; No GitHub main upload.

## Purpose

Stage 0 Phase 0.3 defines the field contract for the three detail objects that
must become visible in later implementation phases:

1. `suggested_action_detail`
2. `tier_asset_detail`
3. `topic_classification_detail`

The contract answers four questions for every object: what fields must exist,
where the values come from, where users should see them and whether the field is
read-only or proposal-only editable. This phase does not implement React UI,
CSS, data generation, Search 2.0, Review workflow, Data Map 2.0, Memory River,
Memory Starfield, agent apply, screenshot evidence, build, deploy or GitHub
main upload.

## Shared Rules

| Rule | Requirement |
|---|---|
| `source_scope` | Values must be derived from Memory Atlas low-sensitivity snapshots, Universe State outputs, redacted evidence refs or local fixture contracts. No raw/private export, cookie, session, secret or plaintext transcript may be required. |
| `display_surface` | Every field must name at least one target surface: overview, detail workbench, Inspector, Search Review, Data Map, Starfield handoff, River handoff or proposal preview. |
| `edit_permission` | Fields are either `read_only`, `proposal_only`, or `system_generated`. No field may allow direct active-memory mutation from the frontend. |
| `evidence_policy` | Evidence must be redacted refs, counters or summaries. Raw evidence text and local absolute private paths are forbidden. |
| `fallback_policy` | Missing required values must render an empty/error explanation and must not be replaced with mock data. |

## Suggested Action Detail

Object key: `suggested_action_detail`

Purpose: make every suggested action explainable enough for a user to decide
whether to act, defer, review, consolidate or create a proposal-only adjustment.

| Field | Required | Source | Display surface | Edit permission |
|---|---|---|---|---|
| `action_id` | yes | deterministic action model or Universe State `next_actions` | overview, detail workbench, Inspector, Search Review | system_generated |
| `title` | yes | action model summary | overview, detail workbench, Search Review | proposal_only |
| `action_type` | yes | action model classification | detail workbench, Inspector | proposal_only |
| `reason` | yes | model explanation, matched memory summary or review rule | detail workbench, Inspector | read_only |
| `roi_score` | yes | ROI or value heuristic output | overview, detail workbench, Inspector | proposal_only |
| `effort_cost` | yes | action model estimate | detail workbench, Inspector | proposal_only |
| `urgency` | yes | action model time window | overview, detail workbench | proposal_only |
| `confidence` | yes | evidence strength and model certainty | detail workbench, Inspector | proposal_only |
| `evidence_count` | yes | redacted evidence refs count | overview, detail workbench | system_generated |
| `evidence_refs` | yes | redacted evidence refs | Inspector, proposal preview | read_only |
| `matched_reason` | yes | search/review match explanation | Search Review, Inspector | read_only |
| `linked_topic_ids` | yes | Universe State topic map | detail workbench, Starfield handoff | system_generated |
| `linked_asset_ids` | yes | tier asset model map | detail workbench, Data Map | system_generated |
| `next_step` | yes | action model recommendation | overview, detail workbench, Search Review | proposal_only |
| `recommended_time_window` | yes | action model schedule hint | overview, detail workbench | proposal_only |
| `proposal_hint` | yes | writeback policy and confidence rule | proposal preview, Inspector | system_generated |
| `rollback_hint` | yes | proposal-only rollback rule | proposal preview, Inspector | system_generated |

Minimum visible summary: title, reason, ROI, effort cost, urgency, evidence
count and next step.

## Tier Asset Detail

Object key: `tier_asset_detail`

Purpose: expose the concrete assets behind high-level memory tiers so a user can
see which profile facts, projects, decisions, workflows, knowledge items,
opportunities or stale assets deserve attention.

Allowed `asset_tier` values:

- `core_profile`
- `project`
- `decision`
- `workflow`
- `knowledge`
- `opportunity`
- `stale`

| Field | Required | Source | Display surface | Edit permission |
|---|---|---|---|---|
| `asset_id` | yes | deterministic tier asset model | detail workbench, Inspector, Data Map | system_generated |
| `asset_tier` | yes | tier asset classifier | overview, detail workbench, Data Map | proposal_only |
| `title` | yes | asset model summary | overview, detail workbench, Search Review | proposal_only |
| `summary` | yes | redacted memory synthesis | detail workbench, Inspector | read_only |
| `importance` | yes | asset scoring or explicit memory importance | overview, detail workbench, Inspector | proposal_only |
| `priority` | yes | action/readiness prioritization | detail workbench, proposal preview | proposal_only |
| `confidence` | yes | evidence strength and model certainty | detail workbench, Inspector | proposal_only |
| `staleness_status` | yes | freshness/staleness rule | overview, detail workbench, Summary Iteration | proposal_only |
| `last_seen_range` | yes | redacted timestamp range | River handoff, Inspector | read_only |
| `evidence_count` | yes | redacted evidence refs count | detail workbench, Data Map | system_generated |
| `evidence_refs` | yes | redacted evidence refs | Inspector, proposal preview | read_only |
| `linked_action_ids` | yes | suggested action map | detail workbench, Data Map | system_generated |
| `linked_topic_ids` | yes | topic classification map | Starfield handoff, Data Map | system_generated |
| `recommended_asset_action` | yes | asset lifecycle rule | detail workbench, Summary Iteration | proposal_only |
| `proposal_hint` | yes | writeback policy and confidence rule | proposal preview, Inspector | system_generated |
| `rollback_hint` | yes | proposal-only rollback rule | proposal preview, Inspector | system_generated |

Minimum visible summary: asset tier, title, importance, priority, staleness,
confidence, evidence count and recommended asset action.

## Topic Classification Detail

Object key: `topic_classification_detail`

Purpose: make topic categories more than tag counts by showing strength, trend,
evidence, related assets and recommended next action.

Allowed `topic_state` values:

- `dominant`
- `rising`
- `declining`
- `emerging`
- `conflict`
- `black_hole`
- `stale`

| Field | Required | Source | Display surface | Edit permission |
|---|---|---|---|---|
| `topic_id` | yes | deterministic topic model | overview, detail workbench, Starfield handoff | system_generated |
| `topic_label` | yes | topic classifier | overview, detail workbench, Search Review | proposal_only |
| `topic_state` | yes | Universe State topic state | overview, detail workbench, Starfield handoff | system_generated |
| `topic_strength` | yes | topic strength score or bucket | overview, detail workbench, Data Map | system_generated |
| `trend` | yes | delta comparison over current time window | overview, River handoff, detail workbench | system_generated |
| `confidence` | yes | evidence strength and model certainty | detail workbench, Inspector | proposal_only |
| `record_count` | yes | redacted record count | overview, detail workbench | system_generated |
| `evidence_count` | yes | redacted evidence refs count | overview, detail workbench | system_generated |
| `evidence_refs` | yes | redacted evidence refs | Inspector, proposal preview | read_only |
| `matched_reason` | yes | classifier explanation | detail workbench, Inspector | read_only |
| `linked_asset_ids` | yes | tier asset map | detail workbench, Data Map | system_generated |
| `linked_action_ids` | yes | suggested action map | detail workbench, Data Map | system_generated |
| `related_topic_ids` | yes | topic relationship map | Starfield handoff, Search Review | system_generated |
| `linked_starfield_cluster_id` | yes | Starfield cluster map | Starfield handoff | system_generated |
| `linked_river_range` | yes | time window map | River handoff | system_generated |
| `recommended_topic_action` | yes | topic lifecycle rule | detail workbench, Summary Iteration | proposal_only |
| `proposal_hint` | yes | writeback policy and confidence rule | proposal preview, Inspector | system_generated |
| `rollback_hint` | yes | proposal-only rollback rule | proposal preview, Inspector | system_generated |

Minimum visible summary: topic label, topic strength, trend, confidence,
record count, evidence count, matched reason and recommended topic action.

## Proposal-Only Editable Fields

The frontend may only propose edits. The proposal layer may expose:

- suggested action: `title`, `action_type`, `roi_score`, `effort_cost`,
  `urgency`, `confidence`, `next_step`, `recommended_time_window`.
- tier asset: `asset_tier`, `title`, `importance`, `priority`, `confidence`,
  `staleness_status`, `recommended_asset_action`.
- topic classification: `topic_label`, `confidence`,
  `recommended_topic_action`.

The frontend must not directly mutate active memory, source snapshots, GitHub
data, model parameter files, generated evidence refs or long-term memory.

## Validation And Rollback

Required validator: `validate:v1.1.7-stage0-phase3`

Rollback: delete this contract, the matching Stage 0 Phase 0.3 acceptance file,
validator, package script and governance record entries. No runtime or data
rollback is required.
