# Memory Atlas Data Map 2.0 工作流验收

- Version: v1.1.6 Stage 5 Phase 1
- Contract ID: `data_map_2_0_workflow`
- Task ID: `MA-V116-S5P01`
- Status: `phase_5_1_contract_created_pending_stage_review`

## Required Checks

Data Map 2.0 passes this contract phase only when the product contract and
records prove all of the following:

1. `source_layer`, `topic_layer`, `asset_layer` and `action_layer` are all
   present.
2. `data_to_action_flow` explains source to topic to asset to action.
3. Every `map_card` contains `label`, `type`, `strength`, `trend`,
   `evidence_count`, `action_count` and `inspector_link`.
4. Cross-workflow handoffs include `open_inspector`, `jump_to_search` and
   `jump_to_review`.
5. `proposal_candidate` exists but remains proposal-only.
6. `source_to_topic_edges`, `topic_to_asset_edges` and `asset_to_action_edges`
   retain redacted evidence references and confidence.

## Required Responsive Evidence

Future runtime implementation must capture:

- Desktop 1440x900
- Tablet 768x1024
- Mobile 390x844

This phase only creates the contract and acceptance file, so screenshots are a
future implementation requirement, not evidence for this phase.

## Failure Conditions

Fail the future implementation if:

- The page is only a `static structure diagram`.
- The map does not show how data becomes suggested actions.
- Cards omit `strength`, `trend`, `evidence_count`, `action_count` or
  `inspector_link`.
- Search 2.0 and Review / Summary / Iteration handoffs are absent.
- Proposal output directly writes active memory.
- Any raw/private/cookie/session/secret text is exposed.
- The view becomes a plain table instead of a workflow map.

## Safety

- No runtime UI.
- No raw/private data read.
- No direct writeback.
- No agent apply.
- No GitHub main upload.

Machine-readable boundary summary: No runtime UI; No raw/private data read; No
direct writeback; No GitHub main upload.

## Validation

Required local validator:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.6-stage5-phase1
```

The validator must verify this file, the product contract, package script,
delivery record, model parameters, feature list, development record, model
parameter file, changelog, changed-path scope and runtime/writeback boundary.
