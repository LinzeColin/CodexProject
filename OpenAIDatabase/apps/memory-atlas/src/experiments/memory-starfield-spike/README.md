# Memory Starfield Spike

## v1.1.7 Stage 4 Phase 4.2 C3 Starfield Spike

- Task ID: `MA-V117-S4P02`
- Acceptance ID: `ACC-MA-V117-S4P02`
- Status: `phase_4_2_c3_starfield_spike_completed_pending_stage4_review`
- Spike version: `memory_starfield_c3_spike.v1_1_7_stage4_phase2`
- Static validator: `validate:v1.1.7-stage4-phase2`
- Browser validator: `validate:memory-starfield-spike-browser`

This phase upgrades the isolated prototype against the v1.1.7 Stage 4.1 Visual
Contract. It remains an experiment-only C3 Starfield Spike and does not replace
the production Galaxy renderer.

Stage 4.2 task coverage:

1. GPU particle spike: the default `mid` quality keeps `10000` particles and
   uses a WebGL `ShaderMaterial`.
2. Flow Field / Curl Noise: `shaders/flowField.ts` defines
   `FLOW_FIELD_SHADER_CONTRACT`, CPU fallback vectors and shader snippets.
3. Cluster Gravity: particle updates use cluster mass, minimum distance clamp
   and orbit damping so particles orbit instead of collapsing.
4. Hover Cards B2: cluster hover shows topic, redacted summary, importance,
   priority, terrain class, confidence and evidence count.

Browser acceptance for this phase requires `>=10k particles`, `>=30 FPS`,
`curl_noise_shader`, at least `256` particle trails, at least six gravity
sources, Hover Cards B2 and a screenshot from the standalone experiment page.

Boundary: No production Galaxy replacement, No production route/navigation
change, No feature flag default switch, No raw/private/cookie/session/secret
data read, No direct active-memory writeback, No agent apply, No Stage 4 review
and No GitHub main upload before the whole Stage 0-10 project is complete.

- Product target: Memory Atlas v1.1.5
- Stage: 1 C3 isolated prototypes
- Current phase contribution: Task 1.1 记忆星系 Spike
- Status: isolated runnable spike; no production integration
- Last updated: 2026-06-30

## Goal

This directory contains the C3 isolated prototype of “记忆星系”.
The spike tests whether the Phase 0.2 visual contract can support a deep-space
nebula, Flow Field, gravitational disk, Black Hole, Proto-Star and Memory
Terrain without regressing into an ordinary point-line graph.

## Phase 0.3 Scaffold Continuity

This runnable Stage 1 spike preserves and supersedes the original Phase 0.3
scaffold evidence for the Memory Starfield workspace: isolated directory,
README contract, redacted fixture boundary, acceptance criteria and rollback.
Its existence is not production integration; production must still import this
directory only through a later explicit integration run.

Part 2 review marker: the Stage 1.1 spike preserves deep-space nebula, Flow
Field, gravitational disk, Black Hole, Proto-Star, Memory Terrain,
reduced-motion control, hover instrumentation and smoke instrumentation without
production integration.

Open locally through Vite:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas dev
```

Then open:

```text
http://127.0.0.1:5173/src/experiments/memory-starfield-spike/index.html
```

## Boundary

This directory must stay isolated from the production Memory Atlas app until a
future integration run explicitly imports it.

Hard boundaries:

1. Do not import files from this directory in `src/App.tsx`, `src/main.tsx` or
   production components.
2. Do not add a route, navigation item, feature flag or runtime dependency from
   this directory in the production app during Stage 1.
3. Do not replace the existing Galaxy view from this directory.
4. Do not read raw transcripts, hidden sessions, cookies, tokens, browser
   state, plaintext secrets or private full-message exports.
5. Do not write active memory or writeback proposals from the spike.

## Input Fixture Contract

Spike code may use only checked-in, redacted fixture data or generated fixture
data derived from public-safe Memory Atlas snapshots.

Allowed fixture shape:

1. `Universe State Snapshot` sample with dominant, rising and declining
   clusters.
2. Redacted cluster summaries with labels, counts, scores and relationships.
3. Aggregated theme/source/time metadata.
4. Black Hole and Proto-Star sample objects with evidence counts, not raw
   evidence text.
5. Visual parameter fixture for particle counts, level-of-detail thresholds,
   motion caps and reduced-motion mode.

Fixture data must be small, deterministic and committed only if it contains no
raw/private content.

## Spike Questions

The C3 prototype answers:

1. Can the starfield render nebula, Flow Field and gravitational disk at usable
   frame rates?
2. Can Black Hole and Proto-Star signals be visually distinct and explainable?
3. Can Presentation Mode stay immersive while Analysis Mode exposes formulas,
   parameters and Inspector-ready evidence summaries?
4. Can reduced-motion mode preserve readability without continuous animation?
5. Can the spike avoid becoming a static scatter plot or ordinary node-link
   graph?

## Feature List

Implemented in this isolated spike:

1. Standalone Vite page with a full-screen Three.js WebGL canvas.
2. Particle starfield with high, mid and low LOD counts.
3. CPU-updated Flow Field plus cluster gravity over deterministic redacted
   fixture clusters.
4. Gravitational disk, nebula dust, Black Hole marker and Proto-Star halo.
5. HUD for particle count, FPS and active quality.
6. Quality selector, Flow Field strength slider and reduced-motion toggle.
7. Raycaster-driven hover card with redacted label, summary, kind, confidence
   and evidence count.
8. Hidden smoke status hook for automated browser checks.

## Visual And Model Parameters

Current spike parameters:

1. Particle counts: `high=12000`, `mid=10000`, `low=8000`.
2. Default quality: `mid`, so the default acceptance path starts at 10k
   particles.
3. Nebula dust count: `1800` low-cost background points.
4. Smoke mode: `?smoke=1`, capped at `96` frames for browser automation.
5. Particle update cadence: every second animation frame, using doubled delta
   for lower CPU pressure.
6. Cluster gravity: inverse-distance attraction weighted by fixture mass, with
   higher pull around Black Hole clusters.
7. Flow Field: sinusoidal curl terms modulated by the UI slider and reduced to
   25% when reduced-motion is enabled.
8. Input data: `fixture.ts` only, with `rawPrivateDataIncluded=false`,
   `plaintextSecretsIncluded=false` and `localAbsolutePathsIncluded=false`.

## Acceptance Criteria

This Stage 1 spike is accepted when:

1. The path exists at
   `apps/memory-atlas/src/experiments/memory-starfield-spike/README.md`.
2. The page renders at least 10k particles.
3. FPS overlay reports at least 30 FPS in a local browser on the current
   machine.
4. First view shows starfield depth, nebula dust, Flow Field motion and a
   gravitational disk.
5. Hovering a cluster shows a redacted summary card.
6. Black Hole and Proto-Star markers are visible and distinct.
7. LOD controls can reduce particle quality without blanking the canvas.
8. The production app does not import this directory.
9. The spike explicitly bars raw/private/session/cookie/secret data.

## Development Record

2026-06-30 phase result:

1. Built runnable files: `index.html`, `main.ts` and `fixture.ts`.
2. Kept the spike isolated under
   `apps/memory-atlas/src/experiments/memory-starfield-spike/`.
3. Did not import the spike from production `src/App.tsx`, `src/main.tsx` or
   production components.
4. Local Chrome foreground screenshot showed a nonblank WebGL canvas, 10,000
   particles, `mid` quality and FPS overlay at `120`.
5. CDP hover check dispatched a mouse event and observed
   `hoveredClusterId=cluster-agent-governance` with a populated redacted card.
6. Headless CDP rendered slowly in this environment, so performance acceptance
   is based on foreground Chrome HUD evidence, not headless FPS.
7. Build command passed:
   `pnpm --dir OpenAIDatabase/apps/memory-atlas build`.
8. Vite dev route served the standalone HTML, main module and redacted fixture.

## Rollback

Delete `apps/memory-atlas/src/experiments/memory-starfield-spike/`. No
production app code rollback is required while this directory remains
unimported.

## v1.1.6 Stage 9 Phase 1 Continuity

- Task ID: `MA-V116-S9P01`
- Status: `phase_9_1_memory_starfield_c3_spike_ready_pending_stage_review`
- Validator: `validate:v1.1.6-stage9-phase1`

This v1.1.6 phase reuses the existing isolated C3 Memory Starfield spike as the
first prototype checkpoint after the Stage 6-8 contracts. The accepted evidence
is the isolated spike directory, redacted fixture, Three.js particle canvas,
nebula dust, Flow Field, gravitational disk, Black Hole marker, Proto-Star
marker, Memory Terrain cluster, hover card, reduced-motion control and smoke
status hook.

No production integration is allowed in this phase:

1. Do not import `memory-starfield-spike` from production `src/App.tsx`,
   `src/main.tsx` or production components.
2. Do not add a production route, navigation item, renderer import or feature
   flag default switch.
3. Do not run production build, installer, local app install, Cloudflare deploy
   or Access policy changes as acceptance for this phase.
4. Do not read raw/private/cookie/session/secret data.
5. Do not write active memory or proposals from the spike.
6. No Stage 9 review, Stage 10 work or GitHub main upload is included here.
7. No GitHub main upload is part of this phase.
