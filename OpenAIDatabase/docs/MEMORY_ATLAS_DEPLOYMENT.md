# Memory Atlas Deployment

Memory Atlas has two supported delivery modes:

1. Local first: `/Applications/Memory Atlas.app` and `~/Downloads/Memory Atlas.app`.
2. Cloudflare Pages + Access: static visual app protected by Cloudflare Zero Trust.

The deployed app must consume only `data/derived/visualization/memory_atlas.json`.
It must not deploy raw exports, active memory mutation code, SQLite indexes, local
secret stores, cookies, sessions, private keys, or plaintext high-risk secrets.

For the step-by-step Cloudflare deployment and Access verification runbook, use
`docs/MEMORY_ATLAS_CLOUDFLARE_RUNBOOK.md`.

## Local App

Build and install the macOS launchers:

```bash
python3 scripts/install_memory_atlas_app.py
python3 scripts/audit_memory_atlas_acceptance.py --require-local-apps
python3 scripts/audit_memory_atlas_goal_completion.py --require-local-apps
```

The launcher serves the built static app from:

```text
~/Library/Application Support/OpenAIDatabase/MemoryAtlas/runtime
```

It opens:

```text
http://127.0.0.1:4177
```

Force a fresh visualization snapshot before opening:

```bash
MEMORY_ATLAS_REFRESH=1 open "/Applications/Memory Atlas.app"
```

## Cloudflare Pages

Recommended Pages project settings:

```text
Framework preset: None / Vite-compatible custom build
Root directory: repository root
Build command: npm ci --prefix apps/memory-atlas && npm run build --prefix apps/memory-atlas
Build output directory: apps/memory-atlas/dist
```

The repository includes `wrangler.jsonc` with:

```json
{
  "name": "openai-memory-atlas",
  "pages_build_output_dir": "apps/memory-atlas/dist",
  "compatibility_date": "2026-06-16"
}
```

Manual deploy after building locally:

```bash
npm ci --prefix apps/memory-atlas
npm run build --prefix apps/memory-atlas
python3 scripts/audit_memory_atlas_release.py --publish-dir apps/memory-atlas/dist
python3 scripts/audit_memory_atlas_visual_acceptance.py
python3 scripts/audit_memory_atlas_acceptance.py --publish-dir apps/memory-atlas/dist
python3 scripts/audit_memory_atlas_goal_completion.py --publish-dir apps/memory-atlas/dist
python3 scripts/preflight_cloudflare_pages_access.py --publish-dir apps/memory-atlas/dist
python3 scripts/deploy_memory_atlas_cloudflare.py
npx wrangler pages deploy apps/memory-atlas/dist --project-name openai-memory-atlas
```

Do not run `wrangler pages deploy` until the redacted snapshot has been audited:

```bash
python3 scripts/build_memory_atlas_data.py \
  --database-dir . \
  --output data/derived/visualization/memory_atlas.json

git ls-files | rg '(OpenAI-export\.zip|chatgpt_memory_vault_codex_pack\.zip|\.local_keys|\.env|\.key$|cookies|session|auth\.json)'
```

The second command should return no tracked files.

The release audit is mandatory before local app install and before Cloudflare
Pages deploy. It checks the publish directory for raw exports, SQLite files,
JSONL memory files, private-key material, source refs, record hashes, local
absolute paths, and missing writeback safety flags.

The visual acceptance audit locks the UI contracts that should not regress:
Galaxy WebGL uses an opaque cleared canvas, includes a procedural nebula texture
layer for spiral arms, core glow, dust lanes, and cloud knots, and does not get
a visible HTML-dot ghost layer. Graph nodes do not show internal text labels,
and Contribution Grid keeps the full-year/two-year layout visible first by
merging scale controls with delta stats, reserving the main row for the
panorama grid, and preventing desktop control minimum widths from clipping the
mobile panorama.

The acceptance audit is the higher-level gate. It verifies required files,
tracked-file safety, the redacted atlas contract, proposal-only writeback,
runtime `/memory_atlas.json` loading, Chinese-first UI, Galaxy fallback rules,
contribution-grid time scales, Cloudflare Pages + Access readiness, CI gates,
and local `.app` bundles when `--require-local-apps` is used.

The Cloudflare preflight audit validates `wrangler.jsonc`, the Pages direct
upload template, the Access self-hosted application template, official
Cloudflare documentation links, the explicit authorization boundary, and the
audited publish directory. It does not perform a deploy.

The goal-completion audit distinguishes local readiness from real external
completion. Before live deploy evidence exists it should report:

```text
LOCAL_PASS_EXTERNAL_AUTHORIZATION_REQUIRED
```

Run it with `--publish-dir apps/memory-atlas/dist` before local installer
cleanup when checking a deploy artifact. Run it without `--publish-dir` and with
`--require-local-apps` after `scripts/install_memory_atlas_app.py`, because the
installer cleans transient build folders after refreshing the local runtime.
If a cleaned workspace no longer has `apps/memory-atlas/dist`, omit
`--publish-dir`; passing a missing publish directory is treated as an explicit
artifact-audit failure with a cleanup hint.

The generated macOS launcher opens only the local startup page, lets that page
redirect when ready, starts a local static server on `http://127.0.0.1:4177`,
records `server.pid` under
`~/Library/Application Support/OpenAIDatabase/MemoryAtlas`, and schedules a
watchdog to stop that server after two hours by default. Override the lifetime
with `MEMORY_ATLAS_TTL_SECONDS=<seconds>` or disable auto-stop with
`MEMORY_ATLAS_TTL_SECONDS=0`. The runtime includes `memory_atlas_build.json`.
When the launcher sees that the cached runtime commit does not match the current
repository HEAD, it stops the stale local server, rebuilds the static runtime,
and only then redirects the browser. When the cached runtime must be rebuilt
from the launcher, it removes `node_modules`, `dist`, and `*.tsbuildinfo`
afterward and fails if those transient files remain. On macOS the installer
also fails if the custom `.icns` icon cannot be generated, and
`--require-local-apps` verifies the installed icon file plus runtime commit
manifest.

After an authorized Cloudflare deploy and Access verification, record sanitized
operator evidence using `config/cloudflare/live_deploy_evidence.template.json`
and run:

```bash
python3 scripts/audit_memory_atlas_goal_completion.py \
  --publish-dir apps/memory-atlas/dist \
  --live-evidence /path/to/sanitized_live_evidence.json \
  --require-complete
```

## Cloudflare Access

After Pages deploy:

1. Add the Pages hostname or custom domain to Cloudflare Zero Trust Access as a self-hosted application.
2. Require identity authentication before the Memory Atlas hostname can be opened.
3. Start with an allowlist policy for the user account only.
4. Keep the app read-only. Any writeback must remain a JSON change proposal that a trusted agent applies later.
5. Add finance/trading agents only if they need the redacted memory graph. They should request local secret authorization separately and fail closed before any broker, payment, or trading action.

## Writeback And Rollback

The frontend can create local writeback proposals, but it cannot mutate active
memory. A valid writeback flow is:

1. User selects a memory in Memory Atlas.
2. User saves a versioned proposal in the Inspector.
3. User exports the proposal JSON.
4. A trusted agent reloads the current repository state.
5. The agent checks conflicts, stale source context, sensitivity, and policy.
6. The agent commits proposal/history files before active memory changes.
7. The agent updates derived reports and the visualization snapshot.

Rollback unit:

```text
per-memory proposal history + git commit
```

This keeps the visualization independent from the database base layer while still
allowing future controlled writeback.
