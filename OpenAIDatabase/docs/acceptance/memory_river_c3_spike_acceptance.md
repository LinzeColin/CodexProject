# Memory Atlas 记忆时间河 C3 隔离原型验收

- Version: v1.1.6 Stage 9 Phase 2
- Contract ID: `memory_river_c3_spike_contract`
- Task ID: `MA-V116-S9P02`
- Status: `phase_9_2_memory_river_c3_spike_ready_pending_stage_review`

## Required Checks

Stage 9 Phase 2 passes only when:

1. The Memory River spike directory contains `README.md`, `index.html`,
   `main.ts` and `fixture.ts`.
2. `main.ts` uses D3, exposes `window.__memoryRiverSpike`, supports
   `d3.scaleUtc`, `d3.zoom`, `d3.brushX`, theme lanes, Black Hole bands,
   Proto-Star markers, event pulses, hover cards, reduced motion and smoke
   status behavior.
3. `fixture.ts` has `rawPrivateDataIncluded: false`,
   `plaintextSecretsIncluded: false`, `localAbsolutePathsIncluded: false` and
   `writebackAllowed: false`.
4. The fixture includes theme lanes, event pulses, Black Hole bands and
   Proto-Star markers with redacted labels, summaries, confidence and evidence
   counts.
5. Production `src` files outside the experiment directory do not import or
   reference `memory-river-spike`.
6. The spike README contains a v1.1.6 Stage 9 Phase 2 continuity section and
   keeps the no-production-integration boundary.
7. Delivery, feature, development, model parameter, changelog and package
   records all expose `validate:v1.1.6-stage9-phase2`.
8. The phase does not modify production runtime UI, CSS, routing, app bundles,
   raw/private data, direct writeback, Stage 9 review, Stage 10 or GitHub main
   upload.

## Failure Conditions

Fail this phase if:

- the spike directory is missing a required file;
- D3 UTC scale, zoom, brush, theme lanes, Black Hole band, Proto-Star marker,
  event pulses, hover card, reduced motion or smoke hook evidence is removed;
- fixture safety flags are not all false;
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
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.6-stage9-phase2
```

The validator must verify the product contract, acceptance file, spike README,
spike source and fixture, production isolation, package script, records,
changed-path scope and safety boundary.
