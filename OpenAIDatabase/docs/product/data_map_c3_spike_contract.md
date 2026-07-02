# Memory Atlas Data Map C3 隔离原型合同

- Version: v1.1.6 Stage 9 Phase 3
- Contract ID: `data_map_c3_spike_contract`
- Task ID: `MA-V116-S9P03`
- Status: `phase_9_3_data_map_c3_spike_ready_pending_stage_review`

## Goal

Stage 9 Phase 3 creates the Data Map spike as the third runnable C3 isolated
prototype evidence for Roadmap v2. It verifies that Data Map 2.0 can move from
a static structure diagram toward an explainable workflow map that shows how
redacted sources become topics, how topics become assets, and how assets become
suggested actions.

This phase validates and documents the isolated prototype. It does not replace
the production Data Guide / Data Map, import the experiment directory into the
app shell, run a production build, start browser screenshot acceptance, deploy
Cloudflare, modify Access policy, read raw/private data, write proposals or
write active memory.

## Prototype Surface

The C3 Data Map spike surface is:

- `apps/memory-atlas/src/experiments/data-map-spike/README.md`
- `apps/memory-atlas/src/experiments/data-map-spike/index.html`
- `apps/memory-atlas/src/experiments/data-map-spike/main.ts`
- `apps/memory-atlas/src/experiments/data-map-spike/fixture.ts`

The prototype must stay reachable as a standalone Vite experiment path and
must not become a production route, navigation item, feature flag default, Data
Map renderer import or shared runtime dependency in this phase.

## Required Prototype Features

The spike must continue to expose:

1. `source_layer`: source registry and redacted source summaries.
2. `topic_layer`: topic clusters and topic states.
3. `asset_layer`: tier assets and memory capability groups.
4. `action_layer`: suggested actions, review backlog and proposal candidates.
5. `source_to_topic_edges`: source evidence grouped into topics.
6. `topic_to_asset_edges`: topics promoted or connected to assets.
7. `asset_to_action_edges`: assets converted into suggested actions.
8. `data_to_action_flow`: visible explanation from source to topic to asset to
   action.
9. `map_card`: visible cards with required explanatory fields.
10. `open_inspector`, `jump_to_search`, `jump_to_review` and
    `proposal_candidate` handoffs.
11. `reduced_motion`: reduced-motion mode that keeps the map usable.
12. `smoke_status_hook`: hidden automation hook for future browser checks.

## Required Map Card Contract

Every visible `map_card` must include:

- `label`
- `type`
- `strength`
- `trend`
- `evidence_count`
- `action_count`
- `inspector_link`

Every edge must preserve:

- `evidence_refs`
- `confidence`
- `matched_reason`
- `source_scope`

## Required Fixture Contract

`fixture.ts` may contain only deterministic redacted derived fixture data. It
must include:

- `schemaVersion`
- `source`
- `rawPrivateDataIncluded: false`
- `plaintextSecretsIncluded: false`
- `localAbsolutePathsIncluded: false`
- `writebackAllowed: false`
- `proposalOnly: true`
- four layers: `source_layer`, `topic_layer`, `asset_layer`, `action_layer`
- edge groups: `source_to_topic_edges`, `topic_to_asset_edges`,
  `asset_to_action_edges`
- workflow handoffs: `open_inspector`, `jump_to_search`, `jump_to_review`,
  `proposal_candidate`

Forbidden fixture payload:

- raw transcripts
- cookies, sessions, browser state or tokens
- plaintext secrets or private keys
- local absolute paths
- writeback permission or direct active-memory mutation

## Isolation Rules

Fail this phase if:

- production `src/App.tsx`, `src/main.tsx` or production components import or
  reference `data-map-spike`;
- a navigation item, route, feature flag default or production Data Map points
  to this experiment;
- the spike reads raw/private/cookie/session/secret payloads;
- the spike writes active memory or proposals;
- the spike removes four-layer workflow, edge reason, map_card fields,
  Inspector/Search/Review handoffs, proposal-only status, reduced motion or
  smoke status evidence;
- the spike becomes a static structure diagram, plain table or unexplainable
  node-link graph.

## Safety Boundary

- No production runtime integration.
- No production route or navigation change.
- No feature flag default switch.
- No production build in this phase.
- No browser screenshot run in this phase.
- No local app install or rebuild.
- No Cloudflare live deploy.
- No Access policy change.
- No raw/private/cookie/session/secret data read.
- No raw/private data read.
- No direct writeback.
- No proposal write.
- No agent apply.
- No Stage 9 review, Stage 10 work or GitHub main upload.

Machine-readable boundary summary: No production integration; No raw/private
data read; No direct writeback; No GitHub main upload.

## Acceptance Hook

Future implementation phases may run browser smoke checks against:

```text
/src/experiments/data-map-spike/index.html?smoke=1
```

This phase validates the static contract, standalone prototype files, fixture
safety, production isolation and governance records.
