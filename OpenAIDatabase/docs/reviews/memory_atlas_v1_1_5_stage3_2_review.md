# Memory Atlas v1.1.5 Stage 3.2 Review

- Review date: 2026-06-30
- Worktree: canonical project-level `CodexProject` Memory Atlas worktree
- Branch: `codex/memory-atlas`
- Stage/phase scope: Stage 3.2 Preview Widgets
- Runtime status: `记忆总览` remains the default app board; preview widgets
  deep-link into existing Galaxy, Timeline and Search/Inspector surfaces.

## Review Result

Stage 3.2 is review-passed.

The implementation satisfies the phase acceptance target: the Home Overview now
shows a lightweight Mini Starfield preview, recent River Pulse topic changes,
and Inspector deep links. Each click preserves the selected memory focus before
switching to the target board, and the preview starfield is SVG/CSS only rather
than a second WebGL scene.

## Acceptance Review

| Task | Evidence | Review status |
|---|---|---|
| 3.2.1 Mini Starfield Preview | `HomeOverviewView` renders `Mini Starfield` with static SVG points from `buildMiniStarfieldPreview`; click calls `jumpToPreview(model.miniStarfieldFocus, "galaxy")`. | PASS |
| 3.2.2 River Pulse Preview | `River Pulse` compares recent and previous windows through `buildRiverPulsePreview`; rows expose rising/declining deltas and click into Timeline with synchronized focus. | PASS |
| 3.2.3 Inspector Deep Link | `buildHomeInspectorLinks` selects up to four representative memory nodes; each button calls `jumpToPreview(link.node, "search")` before showing the detail/search surface. | PASS |

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
rg -n "Mini Starfield|River Pulse|Inspector Deep Link|点击进入记忆星系|点击进入时间河" \
  OpenAIDatabase/apps/memory-atlas/dist/assets
lsof -nP -iTCP:4177 -sTCP:LISTEN
```

Observed results:

1. `git diff --check`: PASS.
2. `pnpm lint`: PASS.
3. `pnpm build`: PASS, with the existing Vite warning that the GalaxyScene
   chunk is larger than 500 kB.
4. Visual acceptance audit: PASS, 26/26 checks, including
   `memory_home_preview_widgets_ready`.
5. Memory Atlas acceptance audit: PASS.
6. Local preview returned `HTTP/1.1 200 OK`.
7. Built asset bundle contains `Mini Starfield`, `River Pulse`,
   `Inspector Deep Link`, `点击进入记忆星系` and `点击进入时间河`.
8. Port `4177` had no listener after preview shutdown.

## Boundary Review

Stage 3.2 did not:

1. Replace Galaxy or Timeline.
2. Add a second WebGL renderer to the Home Overview.
3. Import `src/experiments` spike code into production.
4. Read raw exports, cookies, sessions, browser state, plaintext secrets or
   private local paths.
5. Add ingestion or direct writeback.
6. Upload to Cloudflare or change Access policy.

## Residual Risks

1. The preview widgets are summaries derived from the current redacted atlas
   slice, not a persisted `home_preview` data contract.
2. River Pulse uses the latest available atlas date as its observation anchor;
   future data refreshes can change the displayed topics without code changes.
3. The existing GalaxyScene chunk-size warning remains unchanged.

## Upload Gate

Before pushing Stage 3.2 to GitHub main:

1. Rebase on the latest `origin/main` if remote advanced.
2. Re-run lint, build, visual acceptance, Memory Atlas acceptance and diff
   checks.
3. Confirm the final commit range contains only intended Stage 3.2
   implementation, acceptance-script and review files.
4. Push to the canonical `LinzeColin/CodexProject` main tree.
