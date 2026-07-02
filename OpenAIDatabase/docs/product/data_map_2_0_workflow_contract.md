# Memory Atlas Data Map 2.0 工作流合同

- Version: v1.1.6 Stage 5 Phase 1
- Contract ID: `data_map_2_0_workflow`
- Task ID: `MA-V116-S5P01`
- Status: `phase_5_1_contract_created_pending_stage_review`

## Goal

Data Map 2.0 turns the old static 数据导图 into an explainable workflow that
shows how redacted sources become topics, how topics form memory assets, and how
assets produce suggested actions. It must help a user inspect why a next action
exists, not merely display a structure diagram.

## Required Layers

Data Map 2.0 must expose four layers:

1. `source_layer`: source registry and redacted source summaries.
2. `topic_layer`: topic clusters and topic states.
3. `asset_layer`: tier assets such as core profile, project, decision,
   workflow, knowledge, opportunity and stale memory.
4. `action_layer`: suggested actions, next actions, review backlog and
   proposal candidates.

## Required Flow

The workflow must make the data-to-action path explicit:

- `source_to_topic_edges`: source evidence grouped into topics.
- `topic_to_asset_edges`: topics promoted or connected to tier assets.
- `asset_to_action_edges`: assets converted into suggested actions.
- `data_to_action_flow`: a visible explanation from source to topic to asset to
  action.

Each edge must preserve `evidence_refs`, `confidence`, `matched_reason` and
`source_scope` so the Inspector can explain the recommendation without exposing
raw/private content.

## Map Card

Every visible `map_card` must include:

- `label`
- `type`
- `strength`
- `trend`
- `evidence_count`
- `action_count`
- `inspector_link`

Additional allowed fields:

- `card_id`
- `layer`
- `summary`
- `confidence`
- `evidence_refs`
- `matched_reason`
- `linked_topic_ids`
- `linked_asset_ids`
- `linked_action_ids`
- `proposal_candidate`

## Workflow Actions

Data Map 2.0 must provide these handoffs:

- `open_inspector`: open the selected source, topic, asset, edge or action.
- `jump_to_search`: run or open a Search 2.0 view for the same card or edge.
- `jump_to_review`: open Review / Summary / Iteration for the same theme or
  action context.
- `proposal_candidate`: show whether the map recommends a proposal-only change.

## States

The contract must support:

- `empty_state`
- `low_evidence_state`
- `conflict_state`
- `stale_state`
- `error_state`
- `loading_state`

None of these states may hide the reason why the map is incomplete. They must
show the missing evidence type or next safe step.

## Safety Boundary

- `redacted_summary_only`
- No raw/private/cookie/session/secret payloads.
- No direct active-memory writeback.
- No agent apply.
- No runtime UI implementation.
- No runtime Data Map renderer implementation.
- No CSS change.
- No browser screenshot run in this phase.
- No GitHub main upload.

Machine-readable boundary summary: No runtime UI; No raw/private data read; No direct writeback; No GitHub main upload.

本 phase 不修改运行时，不读取 raw/private，不直接写长期记忆，不进入 Stage 5
整体复审，不上传 GitHub main。

## Acceptance Hook

Future implementation phases must provide screenshots for:

- Desktop 1440x900
- Tablet 768x1024
- Mobile 390x844

This contract only defines Data Map 2.0 product and acceptance boundaries.
