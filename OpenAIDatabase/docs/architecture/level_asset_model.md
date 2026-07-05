# Memory Atlas Level Asset Model

- Contract ID: `level_asset_model_v1_1_7_stage1_phase3`
- Task ID: `MA-V117-S1P03`
- Acceptance ID: `ACC-MA-V117-S1P03`
- Status: `phase_1_3_tier_asset_detail_completed_pending_stage1_review`
- Validator: `validate:v1.1.7-stage1-phase3`

## Purpose

The Level Asset model turns Memory Atlas memory tiers and semantic categories
into concrete assets a user can inspect. It prevents the Home Overview from
showing only tier counts by exposing what the asset is, why it matters, which
theme it belongs to, when it was last seen, what evidence supports it and which
proposal-only next step is safe.

This phase implements tier asset visibility and the `AssetDetailPanel` only. It
does not implement topic classification detail, proposal editor, agent apply,
production build, app reinstall, deploy or GitHub main upload.

## Asset Tiers

Allowed `asset_tier` values:

| Tier | Meaning | Runtime source |
|---|---|---|
| `core_profile` | Durable identity, preference, safety or answering-rule memory | core profile tier or rule-like category |
| `project` | Project or ongoing delivery context | project node or project-like category |
| `decision` | Explicit choice, boundary or governance decision | decision node or category |
| `workflow` | Repeatable operating procedure, tool flow or run contract | workflow/process/rule category |
| `knowledge` | Useful but not yet action-bound knowledge asset | remaining non-stale memory |
| `opportunity` | Recent high-value proto-star candidate | proto-star rule |
| `stale` | Old, low-value or review-needed asset | black-hole/staleness rule |

## Required Fields

Each tier asset detail must expose:

| Field | Required | Source | Display |
|---|---|---|---|
| `asset_id` | yes | deterministic tier asset builder | card, panel, Inspector handoff |
| `asset_tier` | yes | tier asset classifier | card, panel |
| `title` | yes | redacted node title | card, panel |
| `summary` | yes | redacted memory synthesis | panel |
| `theme` | yes | compact theme label | card, panel, Starfield handoff |
| `value_score` | yes | ROI / weight heuristic | card, panel |
| `updated_at` | yes | node date or latest visible range | panel |
| `importance` | yes | value score bucket | card, panel |
| `priority` | yes | lifecycle priority bucket | card, panel |
| `confidence` | yes | parsed confidence or fallback | panel |
| `staleness_status` | yes | current/needs_review/stale/unknown | card, panel |
| `last_seen_range` | yes | redacted timestamp range | panel, River handoff |
| `evidence_count` | yes | redacted evidence refs count | card, panel |
| `evidence_refs` | yes | redacted refs only | panel |
| `source_scope` | yes | derived/redacted source scope | panel |
| `linked_action_ids` | yes | Next Action map | panel, Data Map |
| `linked_topic_ids` | yes | compact topic IDs | panel, Starfield handoff |
| `recommended_asset_action` | yes | keep/review/consolidate/lower_priority/validate/defer | card, panel |
| `proposal_hint` | yes | proposal_recommended/proposal_not_needed | panel |
| `rollback_hint` | yes | proposal-only rollback rule | panel |
| `proposal_only` | yes | must be true | card, panel |

## Sort Model

The runtime function `tierAssetSortScore` ranks asset candidates with:

```text
sort_score =
  value_score * value_weight
  + importance_score * importance_weight
  + confidence * confidence_weight
  - staleness_penalty * staleness_penalty_weight
```

Default v1.1.7 weights:

| Weight | Value |
|---|---:|
| `value_weight` | 0.35 |
| `importance_weight` | 0.25 |
| `confidence_weight` | 0.25 |
| `staleness_penalty_weight` | 0.15 |

The list is capped at Top 7. If fewer than seven matching assets exist, the
model shows available derived assets and explains the empty state instead of
inventing mock assets.

## Runtime Mapping

| Runtime surface | Requirement |
|---|---|
| Home Level Assets | Show grouped asset cards with tier, title, theme, value, priority, staleness, confidence, evidence count and recommended action. |
| `AssetDetailPanel` | Show summary, source scope, linked actions, linked topics, last seen range, updated at, evidence refs, proposal hint and rollback hint. |
| Inspector handoff | Selecting an asset can synchronize the current focus node before opening Search/Inspector context. |
| Proposal safety | Assets may recommend proposal-only follow up but cannot write proposal JSON or active memory in this phase. |

## Safety Boundary

- `proposal_only` must be true for every generated tier asset.
- No raw/private/cookie/session/secret/plaintext transcript data may be read or
  displayed.
- No direct writeback is allowed.
- No proposal write is allowed in Phase 1.3.
- No GitHub main upload is allowed before whole Stage 0-8 completion.

## Rollback

Revert the Stage 1 Phase 1.3 commit. This removes the model, panel, validator,
package script and records without migrating data or changing active memory.
