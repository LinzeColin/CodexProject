# Memory Atlas v1.1.5 Stage 4.1 Review

- Review date: 2026-06-30
- Worktree: canonical project-level `CodexProject` Memory Atlas worktree
- Branch: `codex/memory-atlas`
- Stage/phase scope: Stage 4.1 Rendering Integration
- Runtime status: `记忆星系` uses the new `memory-starfield` renderer by
  default, with `legacy` retained as the rollback mode.

## Review Result

Stage 4.1 is review-passed with one browser-automation caveat.

The implementation satisfies the phase acceptance target: the Galaxy board has
a production feature flag, a Flow Field rendering path, trajectory lines,
semantic signal markers, quality controls and low-quality fallback mode, while
legacy Galaxy remains reachable for rollback.

Stage 4 is not complete. Stage 4.2 Data Mapping and Stage 4.3 Starfield
Interaction remain future phases.

## Acceptance Review

| Task | Evidence | Review status |
|---|---|---|
| 4.1.1 新旧 Galaxy Feature Flag | `visualFlags.ts` defines `DEFAULT_GALAXY_RENDERER_MODE = "memory-starfield"` and supports URL/localStorage/env overrides; Galaxy heading exposes `Flow Field` and `Legacy` toggle buttons. | PASS |
| 4.1.2 集成 Flow Field Renderer | `GalaxyScene` enables production `memory-starfield` mode with dynamic Flow Field motion, `memory-starfield-flow-field-trajectories`, semantic signal meshes and renderer debug fields. | PASS |
| 4.1.3 WebGL Fallback | Existing static nebula WebGL fallback remains; the new renderer exposes high/mid/low quality tabs, with `low` reported as `low-quality` fallback mode. | PASS |

## Validation Evidence

Commands run from the CodexProject worktree root:

```bash
git diff --check

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas lint

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas build

python3 OpenAIDatabase/scripts/audit_memory_atlas_visual_acceptance.py --repo-root OpenAIDatabase
python3 OpenAIDatabase/scripts/audit_memory_atlas_acceptance.py --publish-dir OpenAIDatabase/apps/memory-atlas/dist

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas preview --port 4177
curl -sS -I http://127.0.0.1:4177/
python3 - <<'PY'
from pathlib import Path
text = ''.join(p.read_text(encoding='utf-8', errors='ignore') for p in Path('OpenAIDatabase/apps/memory-atlas/dist/assets').glob('*.js'))
for needle in [
    'memory-atlas.galaxy-renderer',
    'VITE_MEMORY_ATLAS_GALAXY_RENDERER',
    'memory-starfield-flow-field-trajectories',
    'Production Memory Starfield Flow Field',
    'Flow Field quality selector',
    '低质量 fallback 模式',
    'Legacy',
]:
    print(f'{needle}: {needle in text}')
PY
lsof -nP -iTCP:4177 -sTCP:LISTEN
```

Observed results:

1. `git diff --check`: PASS.
2. `pnpm lint`: PASS.
3. `pnpm build`: PASS, with the existing Vite warning that the GalaxyScene
   chunk is larger than 500 kB.
4. Visual acceptance audit: PASS, 27/27 checks, including
   `galaxy_stage4_1_rendering_integration_ready`.
5. Memory Atlas acceptance audit: PASS.
6. Local preview returned `HTTP/1.1 200 OK`.
7. Built asset bundle contains the Galaxy renderer storage key, env flag,
   Flow Field trajectory marker, production Memory Starfield marker, quality
   selector, low-quality fallback text and Legacy rollback text.
8. Port `4177` had no listener after preview shutdown.

Browser-automation caveat: Python Playwright is not installed in this local
environment (`No module named 'playwright'`), so this review does not claim a
fresh screenshot or FPS reading. The phase is covered by source contract,
TypeScript build, deterministic visual audit, release acceptance, preview HTTP
and built-asset evidence. A later Stage 7 visual acceptance pass should rerun
real browser screenshot/FPS evidence.

## Boundary Review

Stage 4.1 did not:

1. Enter Stage 4.2 Data Mapping.
2. Enter Stage 4.3 Starfield Interaction.
3. Replace Timeline.
4. Read raw exports, cookies, sessions, browser state, plaintext secrets or
   private local paths.
5. Add ingestion or direct writeback.
6. Upload to Cloudflare or change Access policy.

## Residual Risks

1. Browser screenshot/FPS evidence remains pending until a browser automation
   environment is available.
2. Stage 4.1 intentionally uses existing redacted atlas node metadata for
   semantic signal markers. Full cluster/terrain mapping is deferred to Stage
   4.2.
3. The existing GalaxyScene chunk-size warning remains and increased slightly
   after integrating the new production renderer controls.

## Next Phase Gate

Stage 4.2 may start only after this Stage 4.1 review commit is on canonical
GitHub main. Stage 4.2 should stay bounded to Data Mapping and should not
bundle Timeline replacement, writeback apply, Cloudflare deploy or raw/private
data recovery.
