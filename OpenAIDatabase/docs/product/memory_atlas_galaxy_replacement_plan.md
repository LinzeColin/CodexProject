# Memory Atlas v1.1.5 Stage 2.2 Galaxy Replacement Plan

- Date: 2026-06-30
- Stage source: `memory_atlas_final_taskpack_v1.md` Stage 2 / Task 2.2
- Run mode: integration planning only
- Current production Galaxy status: existing `GalaxyScene` remains active
- Implementation status: not started in this phase

## Goal

Replace the current Galaxy board with the new `记忆星系` starfield experience
while keeping the old Galaxy renderer behind a feature flag for fast rollback.

This phase produces the replacement plan only. It does not import the isolated
spike into production, create a runtime flag, change navigation, or replace the
current Galaxy board.

## Verified Current State

| Area | Current evidence | Impact |
|---|---|---|
| Production Galaxy | `apps/memory-atlas/src/components/GalaxyScene.tsx` is imported lazily by `App.tsx` for `activeView === "galaxy"` | Replacement should stay inside the existing Galaxy board instead of adding a second nav item |
| Current visual behavior | Production Galaxy already uses Three.js, nebula texture, ambient points, focus edges, hover preview and `__memoryAtlasGalaxySignal` | It can serve as the legacy fallback and comparison baseline |
| Spike evidence | `apps/memory-atlas/src/experiments/memory-starfield-spike/` renders 10k default particles, Flow Field, cluster gravity, Black Hole, Proto-Star, LOD and hover card | Production integration should extract patterns, not import the experiment directory directly |
| Feature flag state | No Memory Atlas visual feature flag config currently exists | Stage 4.1.1 should introduce a small typed flag boundary before any renderer replacement |
| Data boundary | Both production app and spike are documented as redacted-only and proposal-only | New renderer must use `memory_atlas.json` and Universe State data only |

## Replacement Strategy

Use a wrapper strategy rather than replacing all Galaxy code in one step.

Future production shape:

```text
App.tsx
  activeView === "galaxy"
    -> GalaxyView
       -> if featureFlags.memoryStarfield.enabled
            MemoryStarfieldScene
          else
            LegacyGalaxyScene
```

The existing `GalaxyScene` should be treated as `LegacyGalaxyScene` during the
integration. The new starfield should be a separate production component, not a
direct import from `src/experiments/memory-starfield-spike`.

## Feature Flag Plan

Recommended file:

```text
apps/memory-atlas/src/config/visualFeatureFlags.ts
```

Recommended flags:

| Flag | Default | Purpose |
|---|---:|---|
| `memoryStarfield.enabled` | `false` during first integration | Switch between legacy Galaxy and new starfield |
| `memoryStarfield.allowUrlOverride` | `true` in local/dev only | Allow `?memoryStarfield=1` for screenshot comparison |
| `memoryStarfield.quality` | `mid` | Default LOD for local app and preview |
| `memoryStarfield.analysisModeDefault` | `false` | Keep Presentation Mode clean by default |

Default policy:

1. First production commit: flag exists and defaults to legacy Galaxy.
2. Renderer integration commit: new starfield can be enabled by local/dev flag.
3. Acceptance commit: default can switch to new starfield only after visual,
   performance, fallback and privacy checks pass.
4. Rollback: set `memoryStarfield.enabled=false`.

## Proposed Implementation Sequence

### Stage 4.1.1 New/Old Galaxy Feature Flag

Files likely touched:

- `apps/memory-atlas/src/config/visualFeatureFlags.ts`
- `apps/memory-atlas/src/App.tsx`
- `apps/memory-atlas/src/components/GalaxyScene.tsx`
- `apps/memory-atlas/src/components/GalaxyView.tsx`

Steps:

1. Add typed visual feature flags with legacy default.
2. Introduce `GalaxyView` as the stable board-level component.
3. Keep existing `GalaxyScene` active as the legacy renderer.
4. Add local/dev URL override for controlled screenshots.
5. Add hidden debug signal exposing active renderer name.

Acceptance:

- Flag off renders current Galaxy.
- Flag on can route to a placeholder starfield shell without breaking nav.
- Left sidebar label and `ViewKey` remain unchanged.
- Rollback is one flag change.

Rollback:

- Set flag default to `false`.
- Remove URL override if it causes ambiguity.

### Stage 4.1.2 Flow Field Renderer Integration

Files likely touched:

- `apps/memory-atlas/src/components/MemoryStarfieldScene.tsx`
- `apps/memory-atlas/src/components/GalaxyView.tsx`
- `apps/memory-atlas/src/styles.css`
- `apps/memory-atlas/src/models/universeState.ts`

Steps:

1. Extract production-safe renderer ideas from the spike:
   - particle field
   - Flow Field
   - cluster gravity
   - gravitational disk
   - Black Hole marker
   - Proto-Star halo
   - hover card
2. Use production `AtlasNode` / `AtlasEdge` inputs first.
3. Add optional Universe State enrichment only through redacted sample/runtime
   data.
4. Keep `__memoryAtlasGalaxySignal` or compatible signal for pixel/FPS checks.
5. Clean up RAF, textures, geometries and event listeners on unmount.

Acceptance:

- Canvas is nonblank.
- Flow Field, starfield depth, gravitational disk and markers are visible.
- Hover preview is redacted and read-only.
- No raw/private/cookie/session/secret fields are fetched or rendered.

Rollback:

- Disable `memoryStarfield.enabled`.
- Leave legacy `GalaxyScene` unchanged.

### Stage 4.1.3 WebGL Fallback and LOD

Files likely touched:

- `apps/memory-atlas/src/components/MemoryStarfieldScene.tsx`
- `apps/memory-atlas/src/components/GalaxyFallbackCanvas.tsx`
- `apps/memory-atlas/src/styles.css`

Steps:

1. Detect WebGL renderer creation failure.
2. Render a static but data-driven nebula fallback when WebGL fails.
3. Add quality levels: `high`, `mid`, `low`.
4. Respect `prefers-reduced-motion`.
5. Cap particle counts and animation work under low quality.

Acceptance:

- Low-quality mode is not blank.
- WebGL failure still shows readable clusters.
- Reduced motion reduces continuous movement.

Rollback:

- Force legacy renderer while fallback is repaired.

## Data Mapping Plan

Production `MemoryStarfieldScene` should map existing redacted fields before
adding new data contracts.

| Source | Starfield use |
|---|---|
| `AtlasNode.visual.color` | cluster / particle color |
| `AtlasNode.visual.size` | object scale |
| `AtlasNode.visual.brightness` | luminance and opacity |
| `AtlasNode.metrics.weight_score` | mass and gravity strength |
| `AtlasNode.metrics.roi.staleness_status` | stale orbit / cooler visual |
| `AtlasEdge.weight` | trajectory or relationship intensity |
| `UniverseStateSnapshot.black_holes` | Black Hole distortion marker |
| `UniverseStateSnapshot.proto_stars` | Proto-Star opportunity marker |
| `UniverseStateSnapshot.memory_terrain` | Analysis Mode terrain legend |

Do not add new raw evidence fields to the renderer. If a field is missing,
degrade visual intensity rather than inventing data.

## Validation Plan

Run after each future implementation commit:

```bash
PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas lint

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas build

python3 scripts/audit_memory_atlas_visual_acceptance.py --publish-dir apps/memory-atlas/dist
python3 scripts/audit_memory_atlas_acceptance.py --publish-dir apps/memory-atlas/dist
```

Browser comparison for the feature flag stage:

1. Open Galaxy with flag off.
2. Capture screenshot and `__memoryAtlasGalaxySignal`.
3. Open Galaxy with flag on.
4. Capture screenshot, FPS and console errors.
5. Confirm both renderers are nonblank.
6. Confirm flag off immediately restores the old renderer.

## Stop Conditions

Stop and do not proceed if any of the following occurs:

1. The new starfield requires importing directly from `src/experiments`.
2. The old Galaxy renderer cannot remain available behind a flag.
3. The new renderer reads raw exports, sessions, cookies, secrets or private
   full-message data.
4. The replacement removes the left sidebar or changes the `galaxy` board key.
5. The new renderer drops to a blank canvas in low-quality or WebGL-failure
   conditions.
6. Hover or click interaction writes active memory or writeback proposals.

## Stage 2.2 Completion Criteria

This planning phase is complete when:

1. The current Galaxy renderer and starfield spike evidence are documented.
2. Feature flag strategy is explicit.
3. Replacement sequence is broken into safe implementation tasks.
4. Rollback is one flag change.
5. Validation covers screenshot comparison, nonblank canvas, console errors,
   fallback, privacy and acceptance audits.

Runtime Galaxy replacement remains a later Stage 4 implementation item.
