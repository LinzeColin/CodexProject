# Data Map Spike

- Product target: Memory Atlas v1.1.6
- Stage: 9 C3 isolated prototypes
- Current phase contribution: `MA-V116-S9P03 Data Map C3 Spike`
- Status: isolated runnable spike; no production integration
- Last updated: 2026-07-02

## Goal

This directory contains the C3 isolated prototype for Data Map 2.0. The spike
tests whether the Roadmap v2 Data Map contract can render a clear
data-to-action workflow from redacted fixture data:

```text
source_layer -> topic_layer -> asset_layer -> action_layer
```

The spike must prove that Data Map is not a static structure diagram. It must
show map cards, edge reasons, evidence counts, confidence, Inspector handoff,
Search/Review handoff labels and proposal-only status.

## v1.1.6 Stage 9 Phase 3 Continuity

- Task ID: `MA-V116-S9P03`
- Contract ID: `data_map_c3_spike_contract`
- Status: `phase_9_3_data_map_c3_spike_ready_pending_stage_review`
- Validator: `validate:v1.1.6-stage9-phase3`

This v1.1.6 phase creates the standalone Data Map spike as C3 isolated
prototype evidence. The phase validates static prototype coverage, redacted
fixture safety, production isolation and governance continuity only.

Open locally through Vite:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas dev
```

Then open:

```text
http://127.0.0.1:5173/src/experiments/data-map-spike/index.html
```

Smoke path:

```text
http://127.0.0.1:5173/src/experiments/data-map-spike/index.html?smoke=1
```

## Feature List

Implemented in this isolated spike:

1. Standalone Vite page with a four-layer workflow map.
2. `source_layer`, `topic_layer`, `asset_layer` and `action_layer`.
3. `source_to_topic_edges`, `topic_to_asset_edges` and
   `asset_to_action_edges`.
4. Visible `data_to_action_flow`.
5. `map_card` fields: `label`, `type`, `strength`, `trend`,
   `evidence_count`, `action_count` and `inspector_link`.
6. `matched_reason`, `confidence`, `evidence_refs` and `source_scope` on
   edges.
7. `open_inspector`, `jump_to_search`, `jump_to_review` and
   `proposal_candidate` handoff labels.
8. Analysis / Presentation mode.
9. Reduced-motion mode for flow animation.
10. Hidden smoke status hook for automated checks.

## Fixture Contract

Input data is `fixture.ts` only. It is deterministic and redacted:

- `rawPrivateDataIncluded=false`
- `plaintextSecretsIncluded=false`
- `localAbsolutePathsIncluded=false`
- `writebackAllowed=false`
- `proposalOnly=true`

The fixture may contain only redacted source summaries, derived topic labels,
asset summaries, action summaries, evidence references, confidence scores and
matched reasons. It must not contain raw transcripts, cookies, sessions,
tokens, local private paths, plaintext secrets or active-memory writeback
permission.

## Boundary

- No production integration.
- No production Data Map replacement.
- No production route, navigation item or feature flag default.
- No import from `src/App.tsx`, `src/main.tsx` or production components.
- No raw/private/cookie/session/secret data read.
- No direct writeback or proposal write.
- No production build, browser screenshot run, installer, local app rebuild,
  Cloudflare deploy or Access policy change.
- No Stage 9 review.
- No Stage 10 work.
- No GitHub main upload.

## Acceptance Criteria

This Stage 9 Phase 3 spike is accepted when:

1. `README.md`, `index.html`, `main.ts` and `fixture.ts` exist.
2. The page exposes a four-layer source/topic/asset/action workflow.
3. Every visible map card carries `label`, `type`, `strength`, `trend`,
   `evidence_count`, `action_count` and `inspector_link`.
4. Edges preserve `evidence_refs`, `confidence`, `matched_reason` and
   `source_scope`.
5. Inspector, Search, Review and proposal-only handoff labels are visible.
6. Reduced motion keeps the map usable without animated flow.
7. Fixture safety flags are all false except `proposalOnly=true`.
8. Production app does not import this directory.
9. The phase is recorded through `validate:v1.1.6-stage9-phase3`.

## Rollback

Delete `apps/memory-atlas/src/experiments/data-map-spike/` and remove the
Phase 9.3 validator, package script, product/acceptance docs and governance
record entries. No production app rollback is required while this directory
remains unimported.
