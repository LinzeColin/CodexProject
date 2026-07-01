# Memory River Spike

- Product target: Memory Atlas v1.1.5
- Stage: 1 C3 isolated prototypes
- Current phase contribution: Task 1.2 记忆时间河 Spike
- Status: isolated runnable spike; no production integration
- Last updated: 2026-06-30

## Goal

This directory contains the C3 isolated prototype of “记忆时间河”.
The spike tests whether the Phase 0.2 interaction contract can support a
dynamic time river with D3 time scale, zoom, brush, theme lanes, Black Hole
band, Proto-Star marker, pseudo-haptic feedback and reduced motion.

## Phase 0.3 Scaffold Continuity

This runnable Stage 1 spike preserves and supersedes the original Phase 0.3
scaffold evidence for the Memory River workspace: isolated directory, README
contract, redacted fixture boundary, acceptance criteria and rollback. Its
existence is not production integration; production must still import this
directory only through a later explicit integration run.

Open locally through Vite:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas dev
```

Then open:

```text
http://127.0.0.1:5173/src/experiments/memory-river-spike/index.html
```

## Boundary

This directory must stay isolated from the production Memory Atlas app until a
future integration run explicitly imports it.

Hard boundaries:

1. Do not import files from this directory in `src/App.tsx`, `src/main.tsx` or
   production components.
2. Do not add a route, navigation item, feature flag or runtime dependency from
   this directory in the production app during Stage 1.
3. Do not replace the existing Timeline view from this directory.
4. Do not read raw transcripts, hidden sessions, cookies, tokens, browser
   state, plaintext secrets or private full-message exports.
5. Do not write active memory or writeback proposals from the spike.

## Input Fixture Contract

Spike code may use only checked-in, redacted fixture data or generated fixture
data derived from public-safe Memory Atlas snapshots.

Allowed fixture shape:

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

## Spike Questions

The C3 prototype answers:

1. Can zoom preserve accurate event-date positioning and readable labels?
2. Can brush selection update a clear date range without breaking shared state?
3. Can theme lanes explain project, topic and category evolution better than a
   table, list or static scatter?
4. Can Black Hole band and Proto-Star marker remain visible in Presentation Mode
   and explainable in Analysis Mode?
5. Can pseudo-haptic feedback feel useful while staying subtle and disabled or
   simplified under reduced motion?

## Feature List

Implemented in this isolated spike:

1. Standalone Vite page with a full-screen SVG river surface.
2. `d3.scaleUtc` time scale with UTC date mapping.
3. Multi-lane river bands for macro, meso and micro themes.
4. `d3.zoom` horizontal zoom and pan.
5. `d3.brushX` range selection with readable date output.
6. Event pulses with hover summary cards.
7. Black Hole band and Proto-Star markers.
8. Presentation / Analysis mode label density control.
9. Reduced-motion toggle that disables continuous river feedback animation.
10. Hidden smoke status hook for automated browser checks.

## Visual And Model Parameters

Current spike parameters:

1. Time window: `2026-01-01` to `2026-06-30`, expanded by seven days on each
   side for visual padding.
2. D3 zoom scale extent: `1x` to `10x`.
3. Brush height: `54px`; brush selection uses the current zoomed UTC scale.
4. Lane count: `5`; lane levels: `macro`, `meso`, `micro`.
5. Event count: `9`; event intensity range: `0.52` to `0.92`.
6. River width model: weekly samples, exponential decay over `28` days, capped
   to lane height.
7. Black Hole band: visible interval with intensity-driven opacity.
8. Proto-Star marker: date-specific star symbol with confidence and evidence
   count.
9. Pseudo-haptic feedback: visual pulse only when brush crosses a Black Hole
   band or Proto-Star marker; no audio or vibration.
10. Input data: `fixture.ts` only, with `rawPrivateDataIncluded=false`,
    `plaintextSecretsIncluded=false`, `localAbsolutePathsIncluded=false` and
    `writebackAllowed=false`.

## Acceptance Criteria

This Stage 1 spike is accepted when:

1. The path exists at
   `apps/memory-atlas/src/experiments/memory-river-spike/README.md`.
2. The page renders a multi-lane time river from redacted temporal fixture data.
3. D3 UTC time scale positions events on the correct date range.
4. Zoom changes the visible time scale and keeps ticks readable.
5. Brush selects a readable time window.
6. Hovering a lane, event, Black Hole band or Proto-Star marker shows a
   redacted summary card.
7. Black Hole band and Proto-Star markers are visible.
8. Reduced motion disables continuous river animation while keeping zoom, brush
   and hover usable.
9. The production app does not import this directory.
10. The spike explicitly bars raw/private/session/cookie/secret data and
    writeback.

## Development Record

2026-06-30 phase result:

1. Built runnable files: `index.html`, `main.ts` and `fixture.ts`.
2. Added `d3` and `@types/d3` to the Memory Atlas app package to satisfy the
   explicit D3 time scale, zoom and brush requirement.
3. Kept the spike isolated under
   `apps/memory-atlas/src/experiments/memory-river-spike/`.
4. Did not import the spike from production `src/App.tsx`, `src/main.tsx` or
   production components.
5. Build command passed:
   `pnpm --dir OpenAIDatabase/apps/memory-atlas build`.
6. Static acceptance checks passed for D3 scale, zoom, brush, lanes, Black Hole,
   Proto-Star, reduced motion, hover cards, development record and safety
   flags.
7. Production isolation check passed: no production `src` file imports or
   references `memory-river-spike`.
8. Vite dev route served standalone HTML, main module and redacted fixture.
9. CDP browser validation passed:
   `hoveredId=evt-scope-freeze`, brush range `2026-01-30 -> 2026-03-28`,
   zoom `2.06x`, reduced motion `true`, and all source safety flags `false`.
10. Port cleanup passed for TCP `5173` and `4177`.

## Rollback

Delete `apps/memory-atlas/src/experiments/memory-river-spike/` and remove the
`d3` / `@types/d3` package entries if no later phase uses them. No production
app code rollback is required while this directory remains unimported.
