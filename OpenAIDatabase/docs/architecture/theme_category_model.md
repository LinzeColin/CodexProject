# Memory Atlas Theme Category Model

- Contract ID: `theme_category_model_v1_1_7_stage1_phase4`
- Task ID: `MA-V117-S1P04`
- Acceptance ID: `ACC-MA-V117-S1P04`
- Status: `phase_1_4_topic_classification_detail_completed_pending_stage1_review`
- Validator: `validate:v1.1.7-stage1-phase4`

## Purpose

The Topic Classification model turns topic aggregates into concrete, inspectable
theme details. It prevents the Home Overview from showing only topic counts by
exposing why a topic matters, whether it is dominant, rising, declining,
emerging, conflicting, stale or becoming a Black Hole, and how the user can move
from the topic into Starfield, River, linked assets and linked actions.

This phase implements Topic Classification visibility and the `ThemeDetailPanel`
only. It does not implement proposal editor, Search 2.0, Review workflow, Data
Map 2.0, production build, app reinstall, deploy or GitHub main upload.

## Topic States

Allowed `topic_state` values:

| State | Meaning | Runtime source |
|---|---|---|
| `dominant` | Topic has the strongest visible record mass | largest redacted topic group |
| `rising` | Topic has more recent signals than previous comparable window | recent vs previous window |
| `declining` | Topic has fewer recent signals than previous comparable window | previous vs recent window |
| `emerging` | Topic has proto-star or low-count recent opportunity signals | proto-star candidates |
| `conflict` | Topic includes conflict wording or conflicting evidence | conflict label heuristic |
| `black_hole` | Topic is dominated by stale or low-value loop candidates | stale node ratio |
| `stale` | Topic includes stale candidates but is not dominated by them | stale node presence |

## Required Fields

Each Topic Classification detail must expose:

| Field | Required | Source | Display |
|---|---|---|---|
| `topic_id` | yes | deterministic topic builder | card, panel, Inspector handoff |
| `topic_label` | yes | compact theme label | card, panel |
| `parent_topic` | yes | parent-topic fallback rule | panel |
| `category` | yes | top semantic category | card, panel |
| `topic_state` | yes | state classifier | card, panel |
| `topic_strength` | yes | topic mass plus ROI and recency | card, panel |
| `trend` | yes | up/stable/down recent comparison | card, panel, River handoff |
| `roi_score` | yes | average redacted ROI | panel |
| `conflict_score` | yes | conflict or stale ratio | panel |
| `confidence` | yes | average visible confidence | panel |
| `record_count` | yes | visible records in topic | card, panel |
| `recent_count` | yes | visible recent records | card, panel, River handoff |
| `representative_record_ids` | yes | redacted IDs only | panel |
| `evidence_refs` | yes | redacted refs only | panel |
| `matched_reason` | yes | human-readable reason | card, panel |
| `linked_asset_ids` | yes | Level Asset map | panel, Data Map |
| `linked_action_ids` | yes | Next Action map | panel |
| `starfield_handoff` | yes | focus target for Memory Starfield | panel |
| `river_handoff` | yes | focus target for Memory River | panel |
| `proposal_hint` | yes | proposal_recommended/proposal_not_needed | panel |
| `rollback_hint` | yes | proposal-only rollback rule | panel |
| `proposal_only` | yes | must be true | card, panel |

## Sort Model

The runtime function `topicClassificationSortScore` ranks topic candidates with:

```text
sort_score =
  topic_strength * strength_weight
  + trend_score * trend_weight
  + confidence * confidence_weight
  - conflict_score * conflict_penalty_weight
```

Default v1.1.7 weights:

| Weight | Value |
|---|---:|
| `strength_weight` | 0.38 |
| `trend_weight` | 0.24 |
| `confidence_weight` | 0.22 |
| `conflict_penalty_weight` | 0.16 |

The list is capped at Top 10. If fewer than ten matching topics exist, the
model shows available derived topics and explains the empty state instead of
inventing mock topics.

## Runtime Mapping

| Runtime surface | Requirement |
|---|---|
| Home Topic Classification | Show topic cards with label, state, strength, trend, category, record count and matched reason. |
| `ThemeDetailPanel` | Show parent topic, state, trend, ROI, conflict, confidence, record counts, evidence refs, representative records, linked assets, linked actions and safety hints. |
| Starfield handoff | `starfield_handoff` points to the topic focus target for future Memory Starfield integration. |
| River handoff | `river_handoff` points to the topic lane and recent count for future Memory River integration. |
| Proposal safety | Topics may recommend proposal-only follow up but cannot write proposal JSON or active memory in this phase. |

## Safety Boundary

- `proposal_only` must be true for every generated Topic Classification detail.
- No raw/private/cookie/session/secret/plaintext transcript data may be read or
  displayed.
- No direct writeback is allowed.
- No proposal write is allowed in Phase 1.4.
- No GitHub main upload is allowed before whole Stage 0-8 completion.

## Rollback

Revert the Stage 1 Phase 1.4 commit. This removes the model, panel, validator,
package script and records without migrating data or changing active memory.
