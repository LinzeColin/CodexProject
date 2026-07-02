# Memory Atlas Data Map C3 隔离原型验收

- Version: v1.1.6 Stage 9 Phase 3
- Contract ID: `data_map_c3_spike_contract`
- Task ID: `MA-V116-S9P03`
- Status: `phase_9_3_data_map_c3_spike_ready_pending_stage_review`

## Required Checks

Stage 9 Phase 3 passes only when:

1. The Data Map spike directory contains `README.md`, `index.html`, `main.ts`
   and `fixture.ts`.
2. `main.ts` exposes `window.__dataMapSpike`, renders `source_layer`,
   `topic_layer`, `asset_layer` and `action_layer`, draws
   `source_to_topic_edges`, `topic_to_asset_edges` and
   `asset_to_action_edges`, and includes `data_to_action_flow`.
3. Every map card includes `label`, `type`, `strength`, `trend`,
   `evidence_count`, `action_count` and `inspector_link`.
4. Edges preserve `evidence_refs`, `confidence`, `matched_reason` and
   `source_scope`.
5. Inspector, Search, Review and proposal-only handoff labels are visible:
   `open_inspector`, `jump_to_search`, `jump_to_review`,
   `proposal_candidate`.
6. `fixture.ts` has `rawPrivateDataIncluded: false`,
   `plaintextSecretsIncluded: false`, `localAbsolutePathsIncluded: false`,
   `writebackAllowed: false` and `proposalOnly: true`.
7. Production `src` files outside the experiment directory do not import or
   reference `data-map-spike`.
8. The spike README contains a v1.1.6 Stage 9 Phase 3 continuity section and
   keeps the no-production-integration boundary.
9. Delivery, feature, development, model parameter, changelog and package
   records all expose `validate:v1.1.6-stage9-phase3`.
10. The phase does not modify production runtime UI, CSS, routing, app bundles,
    raw/private data, direct writeback, Stage 9 review, Stage 10 or GitHub main
    upload.

## Failure Conditions

Fail this phase if:

- the spike directory is missing a required file;
- four-layer workflow, data_to_action_flow, map cards, edge reasons,
  Inspector/Search/Review handoffs, proposal-only status, reduced motion or
  smoke hook evidence is removed;
- fixture safety flags are not all false except `proposalOnly: true`;
- fixture text contains local absolute paths, plaintext secrets or raw
  transcript wording;
- production code imports or references the experiment directory;
- this phase runs production build, installer, local app install, Cloudflare
  deploy or Access policy changes;
- this phase claims Stage 9 review or Stage 10 work is complete.

## Safety

- No production runtime integration.
- No production route or navigation change.
- No feature flag default switch.
- No production build.
- No browser screenshot run.
- No local app install or rebuild.
- No Cloudflare live deploy.
- No Access policy change.
- No raw/private data read.
- No direct writeback.
- No proposal write.
- No agent apply.
- No Stage 9 review.
- No Stage 10 work.
- No GitHub main upload.

Machine-readable boundary summary: No production integration; No raw/private
data read; No direct writeback; No GitHub main upload.

## Validation

Required local validator:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.6-stage9-phase3
```

The validator must verify the product contract, acceptance file, spike README,
spike source and fixture, production isolation, package script, records,
changed-path scope and safety boundary.
