# Memory Atlas v1.1.7 Stage 0 Phase 3 Detail Visibility Acceptance

Acceptance ID: `ACC-MA-V117-S0P03`

Task ID: `MA-V117-S0P03`

Required validator: `validate:v1.1.7-stage0-phase3`

Status: `phase_0_3_detail_visibility_contract_completed_pending_stage0_review`

## Acceptance Checklist

| Check | Pass condition |
|---|---|
| Contract exists | `docs/product/detail_visibility_contract.md` defines `memory_atlas_v1_1_7_stage0_phase3_detail_visibility_contract`. |
| Suggested action fields | Contract covers `action_id`, `title`, `action_type`, `reason`, `roi_score`, `effort_cost`, `urgency`, `confidence`, `evidence_count`, `evidence_refs`, `matched_reason`, `linked_topic_ids`, `linked_asset_ids`, `next_step`, `recommended_time_window`, `proposal_hint` and `rollback_hint`. |
| Tier asset fields | Contract covers `asset_id`, `asset_tier`, `title`, `summary`, `importance`, `priority`, `confidence`, `staleness_status`, `last_seen_range`, `evidence_count`, `evidence_refs`, `linked_action_ids`, `linked_topic_ids`, `recommended_asset_action`, `proposal_hint` and `rollback_hint`. |
| Topic classification fields | Contract covers `topic_id`, `topic_label`, `topic_state`, `topic_strength`, `trend`, `confidence`, `record_count`, `evidence_count`, `evidence_refs`, `matched_reason`, `linked_asset_ids`, `linked_action_ids`, `related_topic_ids`, `linked_starfield_cluster_id`, `linked_river_range`, `recommended_topic_action`, `proposal_hint` and `rollback_hint`. |
| Source and display | Every field table includes source, display surface and edit permission columns. |
| Edit permissions | Contract distinguishes `read_only`, `proposal_only` and `system_generated`; it forbids direct active-memory mutation. |
| Required values | Contract states that missing required values must render empty/error explanations and cannot use mock data. |
| Safety boundary | Contract forbids raw/private/cookie/session/secret/plaintext transcript requirements and GitHub main upload. |
| Records | Changelog, feature list, development record, model parameter files and delivery record register `MA-V117-S0P03`, `ACC-MA-V117-S0P03`, status and validator. |

## Deferred Proof

This acceptance is contract-only. It does not prove runtime UI, screenshot
quality, generated data availability, Stage 1 Universe State schema, Detail
Workbench implementation, Search 2.0, Review / Summary / Iteration, Data Map
2.0, Memory River, Memory Starfield, build, deploy or GitHub main upload.

## Failure Conditions

- Any of the three detail objects is missing.
- Any object omits source, display surface or edit permission.
- The contract permits direct frontend writes to active memory or source data.
- Required values can be replaced with mock data instead of an empty/error
  explanation.
- Validation reads raw/private data, writes proposal JSON, performs agent apply
  or uploads to GitHub.

## Rollback

Revert the Stage 0 Phase 0.3 commit. No data migration rollback is required.
