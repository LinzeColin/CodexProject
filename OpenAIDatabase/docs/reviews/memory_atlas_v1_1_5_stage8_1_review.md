# Memory Atlas v1.1.5 Stage 8.1 Local App Packaging Review

Date: 2026-07-01

Stage 8.1 is review-passed.

## Scope

Phase 8.1 covers local app packaging only:

- 8.1.1 local build.
- 8.1.2 launcher check.
- 8.1.3 default route check.

It does not include Stage 8.2 release safety, Cloudflare live deploy, Access
policy changes, raw/private data access, or direct active-memory writeback.

## Acceptance Matrix

| Item | Requirement | Evidence | Result |
|---|---|---|---|
| 8.1.1 local build | Production build creates local runtime files | `validate:stage8-local-app`, installer runtime build | PASS |
| 8.1.2 launcher check | Launcher opens one status page, redirects to ready local app, and can self-release | `validate:stage8-local-app`, installed launcher grep, local app audit | PASS |
| 8.1.3 default route | Startup route is `记忆总览` / `home` | real-browser production preview in `validate:stage8-local-app` | PASS |
| Local app bundles | Downloads and `/Applications` bundles exist and are valid | `audit_memory_atlas_acceptance.py --require-local-apps` | PASS |
| Runtime safety | Runtime contains release-safe static files and manifest matches git HEAD | release audit, acceptance audit, `memory_atlas_build.json` | PASS |
| Cleanup | Preview validation leaves no 4177 listener | `validate:stage8-local-app`, final `lsof` | PASS |

## Observed Validation

1. `python3 -m unittest OpenAIDatabase.tests.test_memory_atlas_launcher -q`:
   PASS, 1 test.
2. `pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:stage8-local-app`:
   PASS, 11/11 checks. Output directory:
   `/var/folders/w9/fnb1wnyd3dg6npzvt909scm80000gn/T/memory-atlas-stage8-local-app-dSgSCj`.
3. `validate:stage8-local-app` real-browser default route screenshot:
   `stage8-local-app-default-home.png`, `504546` bytes.
4. `python3 OpenAIDatabase/scripts/install_memory_atlas_app.py --repo-root OpenAIDatabase`:
   PASS. Installed:
   - `/Users/linzezhang/Library/Application Support/OpenAIDatabase/MemoryAtlas/runtime`
   - `/Users/linzezhang/Downloads/Memory Atlas.app`
   - `/Applications/Memory Atlas.app`
5. Installer used pnpm fallback successfully when npm was unavailable in the
   Codex shell. Build completed with the existing Vite `GalaxyScene` chunk
   warning.
6. `python3 OpenAIDatabase/scripts/audit_memory_atlas_acceptance.py --repo-root OpenAIDatabase --publish-dir "$HOME/Library/Application Support/OpenAIDatabase/MemoryAtlas/runtime" --require-local-apps`:
   PASS.
7. `python3 OpenAIDatabase/scripts/audit_memory_atlas_release.py --repo-root OpenAIDatabase --publish-dir "$HOME/Library/Application Support/OpenAIDatabase/MemoryAtlas/runtime"`:
   PASS, 7 runtime files.
8. Runtime build manifest:
   `git_commit = bb4cbd9d4eedbdfe9d95a5850994a293488fa742`,
   `snapshot_generated_at = 2026-07-01T02:16:47.916Z`.
9. Installed launcher grep confirmed `CODEX_NODE_BIN`, `pnpm --dir`,
   `MEMORY_ATLAS_PID_FILE`, and `path.unlink()` in both Downloads and
   `/Applications` app bundles.
10. Final 4177 listener check: no listener remained.

## Fixes Made

| Finding | Fix | Result |
|---|---|---|
| `python3 scripts/install_memory_atlas_app.py` failed when system Python lacked Pillow. | Added a standard-library `.icns` fallback while preserving the Pillow/iconutil path. | FIXED |
| Installer and launcher assumed `npm` was available. | Added npm-first, pnpm fallback dependency install/build paths and Codex bundled runtime PATH injection. | FIXED |
| Dependency readiness assumed npm's flat `node_modules/lightningcss`. | Added pnpm `.pnpm/.../node_modules/lightningcss` readiness support. | FIXED |
| Managed server pid file was not removed on normal runtime shutdown. | Added `MEMORY_ATLAS_PID_FILE` cleanup in the generated runtime server. | FIXED |
| Stage 8.1 lacked a dedicated repeatable validator. | Added `validate:stage8-local-app`. | FIXED |

## Boundaries

No Cloudflare deployment or Access policy change was performed.

No raw/private/cookie/session/secret fields were introduced. Memory Atlas still
serves redacted derived visualization data only.

No direct frontend writeback was added. Writeback remains proposal-only.

## Next Gate

Stage 8.2: Release Safety.
