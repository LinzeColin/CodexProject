# Cloudflare L2 Compatibility Envelope Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:executing-plans` in this single-agent run. The approved task contract forbids subagent delegation and temporary branches; implementation is directly on the canonical `main` checkouts.

**Goal:** Deliver six truthful Cloudflare L2 surfaces, protect every private core, and synchronize verified deployment facts to the three GitHub `main` branches.

**Architecture:** CodexProject owns a JSON-compatible YAML compatibility registry, deterministic validators, three static public adapters, and the existing MemoryAtlas static build. Archive owns the migrated NAB static surface. LinzeHomeHub consumes a synchronized deployment snapshot and renders it as its existing project-planet system.

**Tech Stack:** Python 3 standard library, Node.js 25 standard library, Vite/React only for existing MemoryAtlas and HomeHub, Cloudflare Wrangler 4.110.0, HTML/CSS with no runtime dependency for new adapters.

## Global Constraints

- Acceptance ID is `ACC-CF-L2-20260710`.
- Work is serial and remains on the three canonical `main` checkouts.
- No secret, account identifier, private export, raw archive, cookie, session, local absolute path, broker credential, or external action enters a public dist.
- Dry-run evidence never implies deployed; HTTP verification is required before setting `actual_url`.
- EEI A209/A210, PFI financial core, OpenAIDatabase raw/core, and Serenity production integrations remain outside this task's completion claims.

---

### Task 1: Test-first compatibility governance

**Files:**

- Create: `tests/cloudflare/__init__.py`
- Create: `tests/cloudflare/test_compatibility_envelope.py`
- Create: `scripts/cloudflare/validate_compatibility_envelope.py`
- Create: `scripts/cloudflare/scan_public_dist.py`
- Create: `scripts/cloudflare/build_static_surface.mjs`
- Create: `governance/cloudflare/projects.yaml`
- Create: `governance/cloudflare/deployments.json`

**Interfaces:**

- `validate_compatibility_envelope.py --projects <path> --deployments <path>` returns 0 only for a complete, truthful registry.
- `scan_public_dist.py --all-required-deployments` returns 0 only when every required output exists and contains no forbidden file or credential pattern.
- `build_static_surface.mjs --source <dir> --output <dir>` replaces only the requested output directory and copies the static source deterministically.

- [ ] Write unittest fixtures proving missing projects, required L1 status, false deployed URLs, missing outputs, local paths, private-key markers, and valid safe fixtures.
- [ ] Run `python3 -m unittest tests.cloudflare.test_compatibility_envelope -v`; verify failures are caused by missing scripts.
- [ ] Implement the three minimal tools and initial registry.
- [ ] Re-run the focused unittest module and `python3 scripts/cloudflare/validate_compatibility_envelope.py`; require PASS.
- [ ] Commit with `feat(cloudflare): add compatibility governance gates` after Task 2's migration facts are included.

**Rollback:** remove the new isolated `cloudflare` directories; no existing project runtime is touched.

### Task 2: Migrate nab to Archive without loss

**Files:**

- Create: `LinzeColin/Archive/nab/README.md`
- Create: `LinzeColin/Archive/nab/public/index.html` from the exact CodexProject `nab.html` bytes
- Create: `LinzeColin/Archive/nab/wrangler.jsonc`
- Modify: `LinzeColin/Archive/README.md`
- Delete after checksum and dry run: `CodexProject/nab.html`
- Delete after checksum and dry run: `CodexProject/wrangler.jsonc`

**Interfaces:** `Archive/nab/wrangler.jsonc` deploys Worker `nab` from `./public` with SPA fallback.

- [ ] Record the source SHA256 and copy `nab.html` to `Archive/nab/public/index.html` mechanically.
- [ ] Verify source and destination SHA256 are identical.
- [ ] Add the self-contained README and Wrangler config.
- [ ] Run `npx --yes wrangler@4.110.0 deploy --dry-run --config wrangler.jsonc` from `Archive/nab`.
- [ ] Only after PASS, remove the two root CodexProject NAB deploy files and update the registry.
- [ ] Commit and push Archive `main`; verify the remote tree before the CodexProject removal commit is pushed.

**Rollback:** restore the two CodexProject files from the pre-task `main` commit or redeploy the prior Cloudflare deployment.

### Task 3: Build four safe L2 surfaces

**Files:**

- Create: `EEI/apps/cloudflare-public/{package.json,wrangler.jsonc,public/index.html,public/styles.css,public/public-surface.json}`
- Modify: `OpenAIDatabase/wrangler.jsonc`
- Modify: `OpenAIDatabase/apps/memory-atlas/src/App.tsx`
- Modify: `OpenAIDatabase/apps/memory-atlas/src/styles.css`
- Create: `PFI/web/cloudflare-public/{package.json,wrangler.jsonc,public/index.html,public/styles.css,public/public-surface.json}`
- Create: `Serenity-Alipay/app/cloudflare-public/{package.json,wrangler.jsonc,public/index.html,public/styles.css,public/public-surface.json}`
- Update: each project's `功能清单.md`, `开发记录.md`, and `模型参数文件.md`

**Interfaces:** every new package exposes `npm run build`; every config uses Workers Static Assets with SPA fallback; every public manifest declares `private_data_allowed_in_dist=false` and no data sources.

- [ ] Extend focused tests to require project-specific public manifest and safety copy.
- [ ] Run the tests and observe RED for missing adapters/config.
- [ ] Implement EEI from the approved research-cartography hero reference and build it.
- [ ] Keep MemoryAtlas's existing UI, migrate its Pages config to static assets, add the HomeHub return path, build it, and run its privacy/accessibility validator.
- [ ] Implement PFI from the approved redacted-product-shell reference and build it.
- [ ] Implement Serenity from the approved review-orbit reference and build it.
- [ ] Scan all four distributions and run four Wrangler dry runs.

**Rollback:** remove the three new adapter directories and restore the prior OpenAIDatabase Wrangler/App files; private cores are untouched.

### Task 4: Add HomeHub Launch Constellation

**Files:**

- Modify: `LinzeHomeHub/wrangler.jsonc`
- Modify: `LinzeHomeHub/src/data/projects.json`
- Modify: `LinzeHomeHub/src/types.ts`
- Modify: `LinzeHomeHub/src/ui/renderProjects.ts`
- Modify: `LinzeHomeHub/src/styles/layout.css`
- Modify: `LinzeHomeHub/scripts/validate-homehub.mjs`
- Modify: `LinzeHomeHub/{README.md,PRODUCT.md,DESIGN.md,功能清单.md,开发记录.md,模型参数文件.md}`

**Interfaces:** project cards expose `compatibilityLevel` and `deploymentStatus`; whole-card navigation remains `verified liveUrl || fallbackUrl`.

- [ ] Update the structural validator first to require EEI, MemoryAtlas/OpenAIDatabase, PFI, Serenity, and nab plus approved deployment statuses.
- [ ] Run `npm run validate` and observe RED against the old two-card registry.
- [ ] Implement the typed status fields, project data, status rendering, styling, and SPA fallback.
- [ ] Run `npm run validate`, `npm run build`, preview plus `npm run acceptance:visual`, and Wrangler dry run.
- [ ] After real URL verification, synchronize only verified URLs and rebuild once.

**Rollback:** revert the bounded HomeHub commit; existing two-card navigation is preserved in Git history.

### Task 5: Deploy, verify, record, and close

**Files:**

- Update: `governance/cloudflare/deployments.json`
- Create: `FINAL_ACCEPTANCE_BUNDLE/cloudflare_compatibility_envelope/{deployments.md,urls.json,FINAL_REPORT.md}`
- Update: `LinzeHomeHub/src/data/projects.json` with verified truth only

**Interfaces:** deployment entries include worker, preferred domain, workers.dev URL, custom-domain status, commit SHA, dry run, deploy result, private scan, HomeHub status, and manual steps.

- [ ] Resolve Cloudflare Workers auth through official Wrangler OAuth or a correctly scoped local token without printing or committing credentials.
- [ ] Deploy serially: nab → EEI → MemoryAtlas → PFI → Serenity → HomeHub.
- [ ] Smoke-check every returned URL and record HTTP/title markers; downgrade any unverifiable result.
- [ ] Run the global validator, private scan, changed-scope governance, repository secret scan, and targeted builds once.
- [ ] Push bounded commits to each `main`, verify `HEAD == origin/main`, and query GitHub for open PRs and non-main temporary branches.
- [ ] Remove `node_modules`, `.wrangler`, untracked `dist`, screenshots, and temporary logs, then verify clean worktrees.
- [ ] Write the final report with exact SHAs, URLs, tests, residual manual domain steps, and next-computer recovery commands.

**Rollback:** use Cloudflare deployment rollback for a live regression and revert the corresponding repository commit on `main`; never force-push.
