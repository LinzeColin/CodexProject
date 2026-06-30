# Memory Atlas v1.1.5 Stage 2.3 Timeline Replacement Plan

- Date: 2026-06-30
- Stage source: `memory_atlas_final_taskpack_v1.md` Stage 2 / Task 2.3
- Run mode: integration planning only
- Current production Timeline status: existing `TimelineView` remains active
- Implementation status: not started in this phase

## Goal

Replace the current Timeline board with the new `记忆时间河` experience while
keeping the old Timeline renderer behind a feature flag for fast rollback.

This phase produces the replacement plan only. It does not import the isolated
river spike into production, create a runtime flag, change navigation, or
replace the current Timeline board.

## Verified Current State

| Area | Current evidence | Impact |
|---|---|---|
| Production Timeline | `apps/memory-atlas/src/App.tsx` renders `TimelineView` when `activeView === "timeline"` | Replacement should stay inside the existing `timeline` board key |
| Current interactions | Production Timeline has zoom controls, center slider, playback cursor, density track, hover detail and click-to-Inspector sync | It can serve as the legacy fallback and comparison baseline |
| Missing river features | Production Timeline does not expose D3 brush, multi-lane river currents, Black Hole bands, Proto-Star markers or pseudo-haptic feedback | These become the production river integration targets |
| Spike evidence | `apps/memory-atlas/src/experiments/memory-river-spike/` uses `d3.scaleUtc`, `d3.zoom`, `d3.brushX`, theme lanes, Black Hole band, Proto-Star marker and reduced motion | Production integration should extract patterns, not import the experiment directory directly |
| Feature flag state | No Memory Atlas visual feature flag config currently exists | Stage 5.1.1 should share the same visual flag boundary planned for Galaxy |
| Data boundary | Current app and river spike are redacted-only and proposal-only | New renderer must use `memory_atlas.json`, timeline records and Universe State data only |

Safety shorthand for future checks: no `raw/private/cookie/session/secret`
input or output is allowed in the Timeline replacement.

## Replacement Strategy

Use a wrapper strategy rather than replacing Timeline internals in one step.

Future production shape:

```text
App.tsx
  activeView === "timeline"
    -> TimelineBoard
       -> if featureFlags.memoryRiver.enabled
            MemoryRiverView
          else
            LegacyTimelineView
```

The existing `TimelineView` should be treated as `LegacyTimelineView` during the
integration. The new river should be a separate production component, not a
direct import from `src/experiments/memory-river-spike`.

## Feature Flag Plan

Recommended file shared with the Galaxy plan:

```text
apps/memory-atlas/src/config/visualFeatureFlags.ts
```

Recommended flags:

| Flag | Default | Purpose |
|---|---:|---|
| `memoryRiver.enabled` | `false` during first integration | Switch between legacy Timeline and new Memory River |
| `memoryRiver.allowUrlOverride` | `true` in local/dev only | Allow `?memoryRiver=1` for interaction comparison |
| `memoryRiver.defaultMode` | `presentation` | Keep the first view readable and restrained |
| `memoryRiver.feedbackEnabled` | `false` by default | Prevent sound/vibration-style feedback from becoming required |
| `memoryRiver.reducedMotion` | browser preference | Respect reduced-motion before animation starts |

Default policy:

1. First production commit: flag exists and defaults to legacy Timeline.
2. River shell commit: new river can be enabled by local/dev flag.
3. Interaction commit: zoom, brush, hover and click are tested behind flag.
4. Acceptance commit: default can switch to river only after visual,
   interaction, fallback, reduced-motion and privacy checks pass.
5. Rollback: set `memoryRiver.enabled=false`.

## Proposed Implementation Sequence

### Stage 5.1.1 Timeline Feature Flag

Files likely touched:

- `apps/memory-atlas/src/config/visualFeatureFlags.ts`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/components/TimelineBoard.tsx`

Steps:

1. Add typed visual feature flags with legacy default.
2. Extract existing `TimelineView` into `LegacyTimelineView` or a board wrapper.
3. Keep `timeline` as the stable `ViewKey` and sidebar item.
4. Add local/dev URL override for controlled interaction testing.
5. Add a hidden debug signal exposing active renderer name and selected range.

Acceptance:

- Flag off renders the current Timeline exactly.
- Flag on can route to a river shell without breaking nav.
- Sidebar label and `ViewKey` remain unchanged.
- Rollback is one flag change.

Rollback:

- Set `memoryRiver.enabled=false`.
- Remove URL override if it causes ambiguity.

### Stage 5.1.2 UTC Time Scale

Files likely touched:

- `apps/memory-atlas/src/components/MemoryRiverView.tsx`
- `apps/memory-atlas/src/utils/timeScale.ts`
- `apps/memory-atlas/src/styles.css`

Steps:

1. Extract a UTC time-scale utility based on `d3.scaleUtc`.
2. Use production `timeline` records as the first data source.
3. Preserve accurate event-date positioning across zoom and pan.
4. Keep tick labels readable with level-of-detail rules.
5. Add deterministic tests for date-to-position mapping.

Acceptance:

- Timeline events appear on the correct UTC date range.
- Zoom does not shift event dates.
- Date labels remain readable.

Rollback:

- Keep legacy Timeline active while the UTC scale is repaired.

### Stage 5.1.3 Theme River Lanes

Files likely touched:

- `apps/memory-atlas/src/components/MemoryRiverView.tsx`
- `apps/memory-atlas/src/data/atlas.ts`
- `apps/memory-atlas/src/models/universeState.ts`
- `apps/memory-atlas/src/styles.css`

Steps:

1. Group redacted timeline records by theme, category or Universe State lane.
2. Render macro, meso and micro lanes with stable ordering.
3. Draw river widths from activity density and evidence count.
4. Keep lane hover redacted and read-only.
5. Use top lanes first to avoid visual overcrowding.

Acceptance:

- Macro / Meso / Micro layer hierarchy is visible.
- Lane hover shows a human-readable summary and evidence count.
- Sparse data degrades to a simple readable lane, not a blank view.

Rollback:

- Render top lanes only or return to legacy Timeline.

### Stage 5.2 Zoom, Brush and Event Cards

Files likely touched:

- `apps/memory-atlas/src/components/MemoryRiverView.tsx`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/styles.css`

Steps:

1. Add horizontal zoom/pan based on the UTC scale.
2. Add brush range selection and readable selected start/end dates.
3. Keep brush range local until the shared selection store exists.
4. Hover event/lane/band/marker shows a redacted card.
5. Click event syncs the existing Inspector through `onSelectNode`.

Acceptance:

- Zoom and brush are usable.
- Selected range is readable.
- Hover cards do not show raw text.
- Click syncs Inspector without direct memory mutation.

Rollback:

- Disable brush first; then disable river flag if needed.

### Stage 5.3 Evidence Layers and Safe Feedback

Files likely touched:

- `apps/memory-atlas/src/components/MemoryRiverView.tsx`
- `apps/memory-atlas/src/models/universeState.ts`
- `apps/memory-atlas/src/styles.css`

Steps:

1. Render Black Hole lifecycle bands from Universe State.
2. Render Proto-Star lifecycle markers from Universe State.
3. Render stale/deprecated cooling layers in Analysis Mode first.
4. Add visual-only pseudo-haptic feedback for dense/important crossings.
5. Respect reduced-motion and keep audio/vibration disabled by default.

Acceptance:

- Black Hole bands and Proto-Star markers are visible and explainable.
- Feedback is visual-only by default.
- Reduced motion disables or shortens nonessential movement.

Rollback:

- Hide evidence layers behind Analysis Mode.
- Disable feedback independently from the river renderer.

## Data Mapping Plan

Production `MemoryRiverView` should map existing redacted fields before adding
new data contracts.

| Source | River use |
|---|---|
| `MemoryAtlas.timeline[].date` | UTC x-position |
| `MemoryAtlas.timeline[].node_id` | Inspector sync target |
| `MemoryAtlas.timeline[].memory_tier` | lane or pulse styling |
| `MemoryAtlas.timeline[].category` | lane grouping fallback |
| `ActivityBucket.activity_score` | density backdrop |
| `ActivityBucket.decision_count` | milestone pulse emphasis |
| `AtlasNode.visual.cluster` | theme lane grouping |
| `UniverseStateSnapshot.river_pulse` | overview/range summary |
| `UniverseStateSnapshot.black_holes` | Black Hole lifecycle bands |
| `UniverseStateSnapshot.proto_stars` | Proto-Star markers |
| `UniverseStateSnapshot.stale_orbits` | stale/deprecated cooling layer |

Do not add new raw evidence fields to the renderer. If a field is missing,
show a lower-confidence visual or empty state instead of inventing data.

## Validation Plan

Run from the CodexProject worktree root after each future implementation commit:

```bash
PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas lint

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas build

python3 OpenAIDatabase/scripts/audit_memory_atlas_visual_acceptance.py --repo-root OpenAIDatabase
python3 OpenAIDatabase/scripts/audit_memory_atlas_acceptance.py --publish-dir OpenAIDatabase/apps/memory-atlas/dist
```

Browser interaction checks for the feature-flagged river:

1. Open Timeline with flag off.
2. Capture screenshot and current legacy interaction state.
3. Open Timeline with flag on.
4. Confirm zoom changes the visible UTC time scale.
5. Brush a date range and confirm the readable start/end.
6. Hover an event, lane, Black Hole band and Proto-Star marker.
7. Click an event and confirm Inspector sync.
8. Turn on reduced motion and confirm zoom/brush/hover remain usable.
9. Confirm console errors are zero.
10. Confirm flag off immediately restores the old Timeline.

## Stop Conditions

Stop and do not proceed if any of the following occurs:

1. The new river requires importing directly from `src/experiments`.
2. The old Timeline renderer cannot remain available behind a flag.
3. The new renderer reads raw exports, sessions, cookies, secrets or private
   full-message data.
4. The replacement removes the left sidebar or changes the `timeline` board key.
5. Brush selection mutates persistent memory, active memory or writeback state.
6. Audio, vibration or continuous motion becomes required for comprehension.
7. Zoom or brush breaks event-date accuracy.

## Stage 2.3 Completion Criteria

This planning phase is complete when:

1. The current Timeline renderer and river spike evidence are documented.
2. Feature flag strategy is explicit.
3. Replacement sequence is broken into safe implementation tasks.
4. Rollback is one flag change.
5. Validation covers toggle testing, zoom, brush, hover, Inspector sync,
   reduced motion, privacy and acceptance audits.

Runtime Timeline replacement remains a later Stage 5 implementation item.
