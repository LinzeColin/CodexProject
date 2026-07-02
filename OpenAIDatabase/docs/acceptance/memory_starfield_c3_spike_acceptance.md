# Memory Atlas 记忆星系 C3 隔离原型验收

- Version: v1.1.6 Stage 9 Phase 1
- Contract ID: `memory_starfield_c3_spike_contract`
- Task ID: `MA-V116-S9P01`
- Status: `phase_9_1_memory_starfield_c3_spike_ready_pending_stage_review`

## Required Checks

Stage 9 Phase 1 passes only when:

1. The Memory Starfield spike directory contains `README.md`, `index.html`,
   `main.ts` and `fixture.ts`.
2. `main.ts` uses Three.js, exposes `window.__memoryStarfieldSpike`, supports
   high/mid/low particle LOD, keeps default mid particle count at least
   `10000`, and includes nebula dust, flow field, gravity disk, Black Hole,
   Proto-Star, hover card, reduced motion and smoke status behavior.
3. `fixture.ts` has `rawPrivateDataIncluded: false`,
   `plaintextSecretsIncluded: false` and `localAbsolutePathsIncluded: false`.
4. The fixture includes `dominant`, `rising`, `declining`, `black_hole`,
   `proto_star` and `terrain` cluster kinds.
5. Production `src` files outside the experiment directory do not import or
   reference `memory-starfield-spike`.
6. The spike README contains a v1.1.6 Stage 9 Phase 1 continuity section and
   keeps the no-production-integration boundary.
7. Delivery, feature, development, model parameter, changelog and package
   records all expose `validate:v1.1.6-stage9-phase1`.
8. The phase does not modify production runtime UI, CSS, routing, app bundles,
   raw/private data, direct writeback, Stage 9 review, Stage 10 or GitHub main
   upload.

## Failure Conditions

Fail this phase if:

- the spike directory is missing a required file;
- default particles fall below `10000`;
- Black Hole, Proto-Star, Memory Terrain, Flow Field, nebula or hover evidence
  is removed;
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
- No agent apply.
- No Stage 9 review.
- No Stage 10 work.
- No GitHub main upload.

Machine-readable boundary summary: No production integration; No raw/private
data read; No direct writeback; No GitHub main upload.

## Validation

Required local validator:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.6-stage9-phase1
```

The validator must verify the product contract, acceptance file, spike README,
spike source and fixture, production isolation, package script, records,
changed-path scope and safety boundary.
