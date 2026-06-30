# Memory Atlas v1.1.5 Stage 4 Whole-Stage Review

- Review date: 2026-07-01
- Worktree: canonical project-level `CodexProject` Memory Atlas worktree
- Branch: `codex/memory-atlas`
- Stage scope: visual roadmap Stage 4, `记忆星系生产集成`
- Stage result: PASS

## Scope Clarification

This review covers the visual roadmap Stage 4 goal:

> 用真正的 Flow Field 记忆宇宙替换旧 Galaxy：默认视觉必须是深空星云、粒子流场、引力源、黑洞、新生星云和记忆地形层，而不是点线图。

The final taskpack also has a broad "Stage 4: Acceptance and Hardening"
section that mentions both Memory Starfield and Memory River. Memory River is
roadmap Stage 5 and was not implemented in this Stage 4 run. This review does
not claim Memory River screenshot, FPS, marker or runtime cleanup completion.

## Stage Review Result

Stage 4 is review-passed for Memory Starfield production integration.

Completed phases:

| Phase | Review file | Status |
|---|---|---|
| 4.1 Rendering Integration | `docs/reviews/memory_atlas_v1_1_5_stage4_1_review.md` | PASS |
| 4.2 Data Mapping | `docs/reviews/memory_atlas_v1_1_5_stage4_2_review.md` | PASS |
| 4.3 Starfield Interaction | `docs/reviews/memory_atlas_v1_1_5_stage4_3_review.md` | PASS |

## Requirement Audit

| Requirement | Evidence | Result |
|---|---|---|
| New/old Galaxy feature flag and rollback | `visualFlags.ts` defaults to `memory-starfield`; App exposes `Flow Field` / `Legacy` toggle; built asset includes rollback strings. | PASS |
| Production Flow Field renderer | `GalaxyScene.tsx` renders Three.js nebula plane, points, Flow Field motion, trajectory lines, semantic markers and terrain rings. | PASS |
| WebGL fallback and low-quality mode | Existing static nebula fallback remains; quality tabs expose high/mid/low; `fallbackMode` reports low-quality mode. | PASS |
| Cluster mass mapping | `model_parameters.memory_starfield.yaml` defines `mapping.cluster_mass`; `memoryStarfieldMass` reads `MEMORY_STARFIELD_PARAMS`. | PASS |
| Particle attribute mapping | `memoryStarfieldParticleAttributes` maps recency, confidence and interaction density into size, brightness, color and trail strength. | PASS |
| Memory Terrain layer | `memoryTerrainType`, `memory-starfield-terrain-layer-*`, `galaxy-terrain-panel` and Analysis mode explain ridge, shoreline, valley, basin and fault-line. | PASS |
| Hover preview | `updateHoverPreview` updates transient hover state only; `onPointerUp` remains the selection path. | PASS |
| Click focus | `updateCameraFocus`, capped focused-neighborhood constants, focus edges, pulse group and inner-neighbor cards keep high-degree nodes controlled. | PASS |
| Freeze / Resume Flow | `flowPaused`, `flowPausedRef`, `dataset.flowFrozen`, `Freeze Flow Field`, `Resume Flow Field` pause flow-time and animation while preserving inspection. | PASS |
| Presentation / Analysis mode | `StarfieldViewMode`, `Starfield mode selector`, formula summary, terrain legend and Inspector strip separate clean presentation from explanation. | PASS |
| Data safety | Release acceptance reports no tracked live raw exports, app bundles, env/key files, cookies, live sessions or auth files; app consumes redacted `memory_atlas.json`. | PASS |
| Runtime cleanup | `runtime_tab_close_cache_cleanup_contract` remains PASS; local preview cleanup confirms no `4177` listener after shutdown. | PASS |
| Desktop browser evidence | Chrome CDP desktop run confirms WebGL canvas, nonblank bounded pixel sample and motion. | PASS |
| Mobile browser evidence | Chrome CDP visible-mobile run confirms 390x844 layout without horizontal overflow, full scene visibility, nonblank WebGL canvas and motion. | PASS |

## Validation Evidence

Fresh commands run from the CodexProject worktree root:

```bash
git diff --check

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas validate:memory-starfield-interaction

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
python3 - <<'PY'
from pathlib import Path
text = ''.join(p.read_text(encoding='utf-8', errors='ignore') for p in Path('OpenAIDatabase/apps/memory-atlas/dist/assets').glob('*.js'))
for needle in ['Freeze Flow Field', 'Resume Flow Field', 'Starfield mode selector', 'Starfield formula summary', 'Analysis inspector summary', 'flowPaused', 'starfieldMode']:
    print(f'{needle}: {needle in text}')
PY
lsof -nP -iTCP:4177 -sTCP:LISTEN
```

Observed results:

1. `git diff --check`: PASS.
2. `validate:memory-starfield-interaction`: PASS, 5/5 checks.
3. `validate:memory-starfield-mapping`: PASS, 5/5 checks.
4. `pnpm lint`: PASS.
5. `pnpm build`: PASS, with the existing Vite warning that `GalaxyScene` is
   larger than 500 kB after minification.
6. Visual acceptance audit: PASS, 29/29 checks.
7. Memory Atlas release acceptance audit: PASS.
8. Preview `/` returned `HTTP/1.1 200 OK`.
9. Preview `/memory_atlas.json` returned `HTTP/1.1 200 OK`.
10. Built asset marker scan found Freeze, Resume, mode selector, formula
    summary, Inspector summary, `flowPaused` and `starfieldMode`.
11. Chrome CDP desktop evidence:
    `/tmp/memory-atlas-stage4-galaxy-webgl.png`, sha256
    `dae4d9d01459e829f2c770f772803bfe5fe634a460b8aaeabd22c2b4abd83cee`;
    `fallbackMode=webgl`, `width=1162`, `height=647`, `lit=69717`,
    `alpha=70400`, `max=765`, `frameDelta=24` over 1257.3 ms, approx
    19.09 FPS.
12. Chrome CDP interaction evidence:
    `/tmp/memory-atlas-stage4-galaxy-webgl-analysis.png`, sha256
    `36b7b87f30d93d42e130c63c026b3a4a4a5162dbc08f2dc510047fb589c1a7fb`;
    Freeze produced `frozenDelta=0`, `flowPaused=true`; Analysis produced
    `starfieldMode=analysis`; projected target lookup and neighbor cards
    remained live.
13. Chrome CDP visible-mobile evidence:
    `/tmp/memory-atlas-stage4-galaxy-webgl-mobile-visible.png`, sha256
    `fe243c9f03c2c011a4eda04c7e5bc38f1fa7d835748f0fa7b05f8272f04ae619`;
    390x844 viewport, `visibility=visible`, `docScrollWidth=390`,
    `bodyScrollWidth=390`, no overflow boxes, `sceneVisiblePixels=220`,
    `fallbackMode=webgl`, `width=720`, `height=440`, `lit=63292`,
    `frameDelta=25` over 1517.9 ms, approx 16.47 FPS.
14. Port `4177` had no listener after preview shutdown.

## Browser Evidence Note

Python Playwright is missing in both system Python and the bundled Python
runtime, and Node Playwright is unavailable. Browser evidence was therefore
collected through Chrome DevTools Protocol with isolated Chrome profiles and
SwiftShader WebGL flags. A hidden headless mobile target was explicitly
rejected for FPS evidence because `document.visibilityState=hidden` made
`requestAnimationFrame` stop; the accepted mobile FPS reading came from a
temporary visible Chrome target with `visibility=visible`.

## Boundary Review

Stage 4 did not:

1. Enter Stage 5 Memory River / Timeline replacement.
2. Read raw OpenAI exports, full transcripts, cookies, sessions, browser state,
   plaintext secrets or private local paths.
3. Add ingestion or direct active-memory writeback.
4. Deploy to Cloudflare or change Cloudflare Access policy.
5. Claim Memory River screenshot, FPS, marker or runtime-cleanup completion.

## Findings And Fixes

No blocking Stage 4 review findings remain after this pass.

Two review issues were found and fixed during Stage 4.3 verification:

1. The Stage 4.2 visual audit looked for the old terrain-only toggle after
   Stage 4.3 promoted that UI into the formal Presentation/Analysis selector.
   The audit now accepts the Stage 4.3 selector and still requires the terrain
   panel.
2. Mobile Galaxy inherited visual-focus desktop/tablet minimum grid widths and
   the five-card delta strip could push the scene horizontally and below the
   first viewport. The mobile CSS now constrains visual-focus grids to one
   column, compacts Galaxy delta cards, wraps Galaxy controls and hides the
   duplicate top stat strip for the Galaxy board.

## Residual Risks

1. `GalaxyScene` still emits the existing Vite chunk-size warning.
2. Memory Terrain remains parameter-backed and auditable, but not empirically
   calibrated.
3. Freeze/Resume intentionally leaves camera focus, hover and click interaction
   active so a frozen scene can still be inspected.

## Next Stage Gate

Stage 5 may start only after this Stage 4 reviewed state is committed and pushed
to canonical GitHub main. Stage 5 should stay bounded to Memory River /
Timeline replacement and should not revisit Stage 4 unless a regression appears.
