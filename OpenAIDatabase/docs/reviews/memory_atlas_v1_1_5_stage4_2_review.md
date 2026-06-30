# Memory Atlas v1.1.5 Stage 4.2 Review

- Review date: 2026-07-01
- Worktree: canonical project-level `CodexProject` Memory Atlas worktree
- Branch: `codex/memory-atlas`
- Stage/phase scope: Stage 4.2 Data Mapping
- Runtime status: `记忆星系` keeps the Stage 4.1 `memory-starfield` renderer as
  default and now maps mass, particle attributes, flow strength and Memory
  Terrain from the v1.1.5 model parameter file.

## Review Result

Stage 4.2 is review-passed with one browser-automation caveat.

The implementation satisfies the phase acceptance target: cluster mass is
derived from importance, recency, usage, tier, kind and ROI parameters; particle
size, color, brightness and trajectory strength expose recency, confidence and
interaction density; Memory Terrain is subtle in Presentation and explainable
through an opt-in Analysis panel.

Stage 4 is not complete. Stage 4.3 Starfield Interaction remains the next
phase.

## Acceptance Review

| Task | Evidence | Review status |
|---|---|---|
| 4.2.1 Cluster Mass Mapping | `model_parameters.memory_starfield.yaml` defines `mapping.cluster_mass`; `memoryStarfieldMass` reads `MEMORY_STARFIELD_PARAMS.mapping.clusterMass` for tier, kind, ROI, importance, recency and usage. | PASS |
| 4.2.2 Particle Attribute Mapping | `memoryStarfieldParticleAttributes` maps recency, confidence and interaction density into size, brightness, color and `trailStrength`; Flow Field trajectories use those attributes. | PASS |
| 4.2.3 Memory Terrain Layer Mapping | `memoryTerrainType` maps ridge, shoreline, valley, basin and fault-line semantics; WebGL renders `memory-starfield-terrain-layer-*`; `galaxy-terrain-panel` explains counts and samples in Analysis mode. | PASS |

## Validation Evidence

Commands run from the CodexProject worktree root:

```bash
git diff --check

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas validate:memory-starfield-mapping

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas lint

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas build

python3 OpenAIDatabase/scripts/audit_memory_atlas_visual_acceptance.py --repo-root OpenAIDatabase
python3 OpenAIDatabase/scripts/audit_memory_atlas_acceptance.py --publish-dir OpenAIDatabase/apps/memory-atlas/dist

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas preview --port 4177 --host 127.0.0.1
curl -sS -I http://127.0.0.1:4177/
curl -sS -I http://127.0.0.1:4177/memory_atlas.json
lsof -nP -iTCP:4177 -sTCP:LISTEN
```

Observed results:

1. `git diff --check`: PASS.
2. `validate:memory-starfield-mapping`: PASS, 5/5 mapping contract checks.
3. `pnpm lint`: PASS.
4. `pnpm build`: PASS, with the existing Vite warning that `GalaxyScene` is
   larger than 500 kB after minification.
5. Visual acceptance audit: PASS, 28/28 checks, including
   `galaxy_stage4_2_data_mapping_ready`.
6. Memory Atlas acceptance audit: PASS.
7. Local preview returned `HTTP/1.1 200 OK`.
8. `/memory_atlas.json` returned `HTTP/1.1 200 OK`.
9. Built asset bundle contains the parameter source marker, terrain layer
   marker, Memory Terrain analysis panel marker, `terrainFeatureCount`, and
   Flow Field quality selector marker.
10. Port `4177` had no listener after preview shutdown.

Browser-automation caveat: Python Playwright is not installed in system Python
or the bundled Python runtime, Node Playwright is unavailable, and the in-app
browser control entry point was not exposed in this session. This review
therefore does not claim a fresh screenshot, mobile viewport screenshot, or FPS
reading. The phase is covered by TypeScript build, unit-style mapping contract,
deterministic visual audit, release acceptance, preview HTTP and built-asset
evidence. A later Stage 7 visual acceptance pass should rerun browser
screenshot, canvas-pixel and FPS evidence when browser automation is available.

## Boundary Review

Stage 4.2 did not:

1. Enter Stage 4.3 Starfield Interaction.
2. Replace Timeline.
3. Read raw exports, cookies, sessions, browser state, plaintext secrets or
   private local paths.
4. Add ingestion or direct writeback.
5. Upload to Cloudflare or change Access policy.

## Residual Risks

1. Browser screenshot, canvas-pixel and FPS evidence remains pending until a
   browser automation surface is available.
2. The Memory Terrain mapping uses current redacted atlas node fields and
   heuristic parameter thresholds. It is parameter-backed and auditable, but not
   empirically calibrated.
3. The existing GalaxyScene chunk-size warning remains.

## Next Phase Gate

Stage 4.3 may start only after this Stage 4.2 review commit is on canonical
GitHub main. Stage 4.3 should stay bounded to Starfield Interaction and should
not bundle Timeline replacement, writeback apply, Cloudflare deploy or
raw/private data recovery.
