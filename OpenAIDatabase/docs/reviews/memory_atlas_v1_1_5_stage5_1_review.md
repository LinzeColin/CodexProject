# Memory Atlas v1.1.5 Stage 5.1 Review

- Review date: 2026-07-01
- Worktree: canonical project-level `CodexProject` Memory Atlas worktree
- Branch: `codex/memory-atlas`
- Stage/phase scope: Stage 5.1 Memory River Rendering
- Runtime status: `时间轴` now defaults to the `memory-river` renderer and can
  roll back to the legacy Timeline through feature flag, URL/env/localStorage,
  or the in-app renderer toggle.

## Review Result

Stage 5.1 is review-passed.

The implementation satisfies the phase acceptance target: the new Memory River
renderer is behind a reversible feature flag, the time scale uses explicit UTC
day parsing and UTC millisecond positioning, and the production Timeline view
renders Macro / Meso / Micro river levels with theme/project/category lanes and
black-hole / proto-star / event markers.

This review does not complete Stage 5. Stage 5.2 interaction work remains
separate and must not be treated as implemented by this phase.

## Acceptance Review

| Task | Evidence | Review status |
|---|---|---|
| 5.1.1 Timeline Feature Flag | `TimelineRendererMode`, `DEFAULT_TIMELINE_RENDERER_MODE`, URL/env/localStorage parsing, `timeline-renderer-toggle`, and browser toggle evidence confirm `memory-river` default plus `legacy` rollback. | PASS |
| 5.1.2 UTC Time Scale | `parseTimelineUtcDay`, `timelineUtcMs`, `data-utc-time-scale="true"`, UTC cursor text, and browser evidence confirm UTC day scale contract. | PASS |
| 5.1.3 Theme River Lanes | `buildMemoryRiverLayout`, Macro/Meso/Micro level specs, lane grouping, river paths, marker kinds, dedicated CSS, and screenshot evidence confirm production river rendering. | PASS |
| Model Parameters | `config/visualization/model_parameters.memory_river.yaml` now records Stage 5.1 UTC, lane, score, marker, rollback and deferred Stage 5.2 interaction parameters. | PASS |

## Validation Evidence

Commands run from the CodexProject worktree root:

```bash
git diff --check

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas validate:memory-river-rendering

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas lint

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas build

python3 OpenAIDatabase/scripts/audit_memory_atlas_visual_acceptance.py --repo-root OpenAIDatabase
python3 OpenAIDatabase/scripts/audit_memory_atlas_release.py --publish-dir OpenAIDatabase/apps/memory-atlas/dist
python3 OpenAIDatabase/scripts/audit_memory_atlas_acceptance.py --publish-dir OpenAIDatabase/apps/memory-atlas/dist

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas preview --port 4177 --host 127.0.0.1
```

Observed results:

1. `validate:memory-river-rendering`: PASS, including feature flag, UTC time
   scale, Macro/Meso/Micro lanes, audit wiring and Memory River parameters.
2. `pnpm lint`: PASS.
3. `pnpm build`: PASS, with the existing Vite warning that `GalaxyScene` is
   larger than 500 kB after minification.
4. Visual acceptance audit: PASS, 30/30 checks, including
   `timeline_stage5_1_river_rendering_ready`.
5. Release audit: PASS, 6 publish files audited.
6. Overall acceptance audit: PASS, including `memory_atlas_visual_acceptance`
   30 checks passed.
7. Chrome CDP desktop evidence: screenshot
   `/tmp/memory-atlas-stage5-1-memory-river.png`, sha256
   `8265d618ced0866d6c482e998ae1cfaa58455a661afedf1b1bebd3ac194b4ec4`;
   `renderer=memory-river`, `utcScale=true`, levels
   `Macro/Meso/Micro`, `laneCount=9`, `markerCount=64`,
   `overflowX=false`, canvas rect `1162x495`.
8. Chrome CDP toggle evidence: switching to `Legacy` produced
   `renderer=legacy`, `hasLegacyTimeline=true`, `hasMemoryRiver=false`;
   switching back produced `renderer=memory-river`, `hasMemoryRiver=true`.
9. Preview cleanup: `lsof -nP -iTCP:4177 -sTCP:LISTEN` returned no listener
   after shutdown; Chrome CDP port `9227` also had no listener.

## Boundary Review

Stage 5.1 did not:

1. Implement Stage 5.2 brush selection, hover/click event cards, or multimodal
   feedback.
2. Read raw exports, cookies, sessions, browser state, plaintext secrets or
   private local paths.
3. Add ingestion or direct writeback.
4. Upload to Cloudflare or change Access policy.

## Residual Risks

1. The existing GalaxyScene chunk-size warning remains unrelated to this phase.
2. Memory River lane parameters are heuristic and source/browser validated, but
   not empirically calibrated.
3. The renderer currently inherits legacy Timeline zoom/playback controls; the
   dedicated river brush and event-card interactions are deferred to Stage 5.2.

## Next Gate

Proceed to Stage 5.2 only after this phase is committed. Stage 5.2 should add
Memory River interaction controls: zoom/pan refinement, brush selection,
hover/click event cards, Inspector sync and reduced/multimodal feedback guards.
