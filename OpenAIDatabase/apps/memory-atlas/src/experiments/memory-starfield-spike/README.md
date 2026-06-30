# Memory Starfield Spike

- Product target: Memory Atlas v1.1.5
- Stage: 0 合同与边界冻结
- Current phase contribution: 0.3.1 星系 Spike 目录
- Status: isolated spike workspace only; no production integration
- Last updated: 2026-06-30

## Goal

This directory is reserved for a future C3 isolated prototype of “记忆星系”.
The spike may later test whether the Phase 0.2 visual contract can support a
deep-space nebula, Flow Field, gravitational disk, Black Hole, Proto-Star and
Memory Terrain without regressing into an ordinary point-line graph.

This phase only creates the workspace contract. It does not implement the
prototype.

## Boundary

This directory must stay isolated from the production Memory Atlas app until a
future run explicitly integrates it.

Hard boundaries:

1. Do not import files from this directory in `src/App.tsx`, `src/main.tsx` or
   production components.
2. Do not add a route, navigation item, feature flag or runtime dependency from
   this directory in Stage 0.
3. Do not replace the existing Galaxy view from this directory.
4. Do not read raw transcripts, hidden sessions, cookies, tokens, browser
   state, plaintext secrets or private full-message exports.
5. Do not write active memory or writeback proposals from the spike.

## Input Fixture Contract

Future spike code may use only checked-in, redacted fixture data or generated
fixture data derived from public-safe Memory Atlas snapshots.

Allowed future fixture shape:

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

## Expected Future Spike Questions

The future C3 prototype should answer:

1. Can the starfield render nebula, Flow Field and gravitational disk at usable
   frame rates?
2. Can Black Hole and Proto-Star signals be visually distinct and explainable?
3. Can Presentation Mode stay immersive while Analysis Mode exposes formulas,
   parameters and Inspector-ready evidence summaries?
4. Can reduced-motion mode preserve readability without continuous animation?
5. Can the spike avoid becoming a static scatter plot or ordinary node-link
   graph?

## Acceptance Criteria

This Stage 0 directory is accepted when:

1. The path exists at
   `apps/memory-atlas/src/experiments/memory-starfield-spike/README.md`.
2. The README states goal, boundary, input fixture contract, future validation
   questions, acceptance and rollback.
3. The README explicitly says the spike is not imported by production app code.
4. The README explicitly bars raw/private/session/cookie/secret data.
5. The production build remains unaffected because no source file imports this
   directory.

## Rollback

Delete `apps/memory-atlas/src/experiments/memory-starfield-spike/`. No app code
rollback is required while this directory remains unimported.
