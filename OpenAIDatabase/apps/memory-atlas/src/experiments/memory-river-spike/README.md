# Memory River Spike

- Product target: Memory Atlas v1.1.5
- Stage: 0 合同与边界冻结
- Current phase contribution: 0.3.2 时间河 Spike 目录
- Status: isolated spike workspace only; no production integration
- Last updated: 2026-06-30

## Goal

This directory is reserved for a future C3 isolated prototype of “记忆时间河”.
The spike may later test whether the Phase 0.2 interaction contract can support
a dynamic time river with zoom, brush, theme lanes, Black Hole band, Proto-Star
marker, pseudo-haptic feedback and reduced motion.

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
3. Do not replace the existing Timeline view from this directory.
4. Do not read raw transcripts, hidden sessions, cookies, tokens, browser
   state, plaintext secrets or private full-message exports.
5. Do not write active memory or writeback proposals from the spike.

## Input Fixture Contract

Future spike code may use only checked-in, redacted fixture data or generated
fixture data derived from public-safe Memory Atlas snapshots.

Allowed future fixture shape:

1. `Universe State Snapshot` sample with river pulse, Black Hole and Proto-Star
   objects.
2. Redacted timeline events with event date, theme, source scope, type,
   intensity and evidence count.
3. Aggregated activity density by time bucket.
4. Theme lane summaries with stable IDs and human-readable labels.
5. Interaction parameter fixture for zoom bounds, brush rules, lane ordering,
   pseudo-haptic thresholds and reduced-motion mode.

Fixture data must be small, deterministic and committed only if it contains no
raw/private content.

## Expected Future Spike Questions

The future C3 prototype should answer:

1. Can zoom preserve accurate event-date positioning and readable labels?
2. Can brush selection update a clear date range without breaking shared state?
3. Can theme lanes explain project, topic and category evolution better than a
   table, list or static scatter?
4. Can Black Hole band and Proto-Star marker remain visible in Presentation Mode
   and explainable in Analysis Mode?
5. Can pseudo-haptic feedback feel useful while staying subtle and disabled or
   simplified under reduced motion?

## Acceptance Criteria

This Stage 0 directory is accepted when:

1. The path exists at
   `apps/memory-atlas/src/experiments/memory-river-spike/README.md`.
2. The README states goal, boundary, input fixture contract, future validation
   questions, acceptance and rollback.
3. The README explicitly says the spike is not imported by production app code.
4. The README explicitly bars raw/private/session/cookie/secret data.
5. The production build remains unaffected because no source file imports this
   directory.

## Rollback

Delete `apps/memory-atlas/src/experiments/memory-river-spike/`. No app code
rollback is required while this directory remains unimported.
