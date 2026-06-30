# Memory Atlas v1.1.5 Stage 3.1 Review

- Review date: 2026-06-30
- Worktree: canonical project-level `CodexProject` Memory Atlas worktree
- Branch: `codex/memory-atlas`
- Stage/phase scope: Stage 3.1 Home Information Architecture
- Runtime status: `记忆总览` is now the default app board; Galaxy and Timeline
  remain the existing production implementations.

## Review Result

Stage 3.1 is review-passed with one validation caveat.

The implementation satisfies the phase acceptance target: the left navigation
remains visible, the startup board is controllable through `activeView`, and
the default view now renders a Chinese-first Home Overview with Memory Weather,
Universe State cards and proposal-only next actions.

## Acceptance Review

| Task | Evidence | Review status |
|---|---|---|
| 3.1.1 Home page skeleton | `ViewKey` includes `home`, `views` includes `记忆总览`, `activeView` defaults to `home`, and `ViewRouter` renders `HomeOverviewView`. | PASS |
| 3.1.2 Universe State cards | Home shows Memory Weather, dominant topic, rising signal, declining orbit, Black Hole risk and Proto-Star opportunity cards derived from redacted atlas nodes. | PASS |
| 3.1.3 Next Best Actions | Home shows proposal-only action cards that navigate to existing ROI, Summary, Search and Timeline views without directly mutating long-term memory. | PASS |

## Validation Evidence

Commands run from the CodexProject worktree root:

```bash
PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas lint

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas build

python3 OpenAIDatabase/scripts/audit_memory_atlas_visual_acceptance.py --repo-root OpenAIDatabase
python3 OpenAIDatabase/scripts/audit_memory_atlas_acceptance.py --publish-dir OpenAIDatabase/apps/memory-atlas/dist

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas preview --port 4177
curl -sS -I http://127.0.0.1:4177/
rg -n "记忆总览|Memory Weather|Next Best Actions|proposal-only，不直接写长期记忆" \
  OpenAIDatabase/apps/memory-atlas/dist/assets
lsof -nP -iTCP:4177 -sTCP:LISTEN
```

Observed results:

1. `pnpm lint`: PASS.
2. `pnpm build`: PASS, with the existing Vite warning that the GalaxyScene
   chunk is larger than 500 kB.
3. Visual acceptance audit: PASS, 25/25 checks, including
   `memory_home_default_overview_ready`.
4. Memory Atlas acceptance audit: PASS.
5. Local preview returned `HTTP/1.1 200 OK`.
6. Built asset bundle contains `记忆总览`, `Memory Weather`, `Next Best Actions`
   and `proposal-only，不直接写长期记忆`.
7. Port `4177` had no listener after preview shutdown.

Browser screenshot caveat: system screenshot capture returned a black image in
this local session, Chrome has JavaScript-from-Apple-Events disabled, and Chrome
headless screenshot attempts timed out. No browser state or settings were
changed. This is a validation-tool limitation, not a detected app failure; the
default-home contract is covered by source, build, visual audit, acceptance
audit, preview HTTP and built-asset evidence.

Governance caveat: root-level `python -B scripts/lean_governance.py ...` could
not run because this sparse project worktree does not contain
`scripts/lean_governance.py`, and the macOS shell has no `python` shim. The
project app and Memory Atlas acceptance gates above were run with `python3`.

## Boundary Review

Stage 3.1 did not:

1. Replace Galaxy or Timeline.
2. Import `src/experiments` spike code into production.
3. Read raw exports, cookies, sessions, browser state, plaintext secrets or
   private local paths.
4. Add ingestion or direct writeback.
5. Upload to Cloudflare or change Access policy.

## Residual Risks

1. Browser screenshot automation should be retried in a browser environment
   with working screenshot support before a release-signoff stage.
2. Home status cards currently derive Universe State from the existing redacted
   atlas slice. A future stage may replace this with a persisted
   `universe_state` snapshot if that becomes the canonical data contract.
3. The existing GalaxyScene chunk-size warning remains unchanged.

## Upload Gate

Before pushing Stage 3.1 to GitHub main:

1. Rebase on the latest `origin/main` if remote advanced.
2. Re-run lint, build, visual acceptance, Memory Atlas acceptance and diff
   checks.
3. Confirm final commit range contains only intended Stage 3.1 implementation,
   acceptance-script and review files.
4. Push to the canonical `LinzeColin/CodexProject` main tree.
