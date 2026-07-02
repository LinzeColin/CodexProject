# Memory Atlas 记忆星系 C3 隔离原型合同

- Version: v1.1.6 Stage 9 Phase 1
- Contract ID: `memory_starfield_c3_spike_contract`
- Task ID: `MA-V116-S9P01`
- Status: `phase_9_1_memory_starfield_c3_spike_ready_pending_stage_review`

## Goal

Stage 9 starts the C3 isolated prototype pass after the Stage 6-8 contracts and
release boundary are uploaded. Phase 9.1 fixes the Memory Starfield spike as
the first runnable isolated prototype evidence for the Roadmap v2 galaxy
requirement. It must prove that the existing spike remains runnable, redacted,
inspectable and isolated from production before any future integration work.

This phase validates and documents the isolated prototype. It does not replace
the production Galaxy, import the experiment directory into the app shell, run a
production build, start browser screenshot acceptance, deploy Cloudflare,
modify Access policy, read raw/private data or write active memory.

## Prototype Surface

The C3 Memory Starfield spike surface is:

- `apps/memory-atlas/src/experiments/memory-starfield-spike/README.md`
- `apps/memory-atlas/src/experiments/memory-starfield-spike/index.html`
- `apps/memory-atlas/src/experiments/memory-starfield-spike/main.ts`
- `apps/memory-atlas/src/experiments/memory-starfield-spike/fixture.ts`

The prototype must stay reachable as a standalone Vite experiment path and must
not become a production route, navigation item, feature flag default, renderer
import or shared runtime dependency in this phase.

## Required Prototype Features

The spike must continue to expose:

1. `three_js_canvas`: standalone Three.js WebGL canvas.
2. `particle_lod`: high/mid/low particle counts with default mid count at
   least `10000`.
3. `nebula_dust`: background nebula layer.
4. `flow_field`: animated curl/flow field that can be reduced under reduced
   motion.
5. `gravity_disk`: cluster gravity and gravitational disk.
6. `black_hole_marker`: visible black-hole risk marker.
7. `proto_star_marker`: visible proto-star opportunity marker.
8. `memory_terrain_signal`: terrain cluster or terrain analysis evidence.
9. `hover_card`: redacted hover summary and selected cluster evidence.
10. `smoke_status_hook`: hidden automation hook for future browser checks.

## Required Fixture Contract

`fixture.ts` may contain only deterministic redacted derived fixture data. It
must include:

- `schemaVersion`
- `source`
- `rawPrivateDataIncluded: false`
- `plaintextSecretsIncluded: false`
- `localAbsolutePathsIncluded: false`
- clusters with `dominant`, `rising`, `declining`, `black_hole`, `proto_star`
  and `terrain` kinds
- redacted labels, summaries, confidence and evidence counts

Forbidden fixture payload:

- raw transcripts
- cookies, sessions, browser state or tokens
- plaintext secrets or private keys
- local absolute paths
- writeback permission or direct active-memory mutation

## Isolation Rules

Fail this phase if:

- production `src/App.tsx`, `src/main.tsx` or production components import or
  reference `memory-starfield-spike`;
- a navigation item, route, feature flag default or production renderer points
  to this experiment;
- the spike reads raw/private/cookie/session/secret payloads;
- the spike writes active memory or proposals;
- the spike removes Black Hole, Proto-Star, Memory Terrain, Flow Field, nebula
  or hover card evidence;
- the spike becomes a static scatter, dots-only canvas or ordinary node-link
  graph.

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
- No agent apply.
- No Stage 9 review, Stage 10 work or GitHub main upload.

Machine-readable boundary summary: No production integration; No raw/private
data read; No direct writeback; No GitHub main upload.

## Acceptance Hook

Future implementation phases may run browser smoke checks against:

```text
/src/experiments/memory-starfield-spike/index.html?smoke=1
```

This phase only validates the static contract, fixture safety, production
isolation and governance records.
