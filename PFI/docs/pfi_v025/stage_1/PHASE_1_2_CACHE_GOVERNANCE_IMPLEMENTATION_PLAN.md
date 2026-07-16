# PFI v0.2.5 Stage 1 Phase 1.2 Cache Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` for independent review work and `superpowers:test-driven-development` for implementation. Execute this plan as one bounded controlled run; do not enter Phase 1.3.

**Goal:** Complete `S1-P2-T1` through `S1-P2-T4` so every cache layer has an evidence-backed state, old browser/runtime processes cannot silently serve an obsolete PFI shell, and bfcache restoration revalidates both release identity and the Streamlit read-model cache namespace before revealing the UI.

**Acceptance target:** `ACC-PFI-V025-S1-P12-CACHE-GOVERNANCE`

**Phase base:** `1a995226d34822b5e98191a716bca665136e300f`

**Architecture:** The canonical PFI shell is rendered as inline `srcdoc`, so its JS/CSS has no independent browser cache entry. At launcher start, a deterministic asset verifier recomputes the actual inline-source bundle and backend hashes against `release_manifest.json`. The Streamlit host wrapper runs in the same Python process, applies fail-closed Tornado cache headers, binds the official read-model builder to a public `st.cache_data` adapter with an explicit composite key and TTL, and forces a per-process ephemeral runtime API port. The runtime API recomputes a stable semantic cache policy without financial values. The frontend first removes legacy same-origin Service Workers/CacheStorage, then validates manifest plus cache policy; `pageshow.persisted` repeats the entire gate while the shell is hidden.

**Tech stack:** zsh, Python 3.12, Streamlit 1.35 current runtime with 1.54 compatibility guards, Tornado `StaticFileHandler`, `ThreadingHTTPServer`, browser JavaScript, Node `node:test`, pytest, cached Playwright 1.61.1/Chromium, JSON Schema 2020-12, SHA-256, and Git commit-object verification.

## Global Constraints

- Execute exactly one Phase: Stage 1 / Phase 1.2. Do not implement Phase 1.3 installation/Finder acceptance or Stage 2.
- Do not push, fetch, merge, rebase, install an App, modify `/Applications`, Desktop, Downloads, ports 8501/8502, private data, SQLite, model logic, formula logic, or parameter values.
- Preserve the standing authorization text `在最终验收前我全部都同意授权，不允许block`. It removes intermediate permission prompts but does not waive technical gates, the one-Phase limit, or final Stage 12 human acceptance.
- Do not edit `PFI/src/pfi_os/app/streamlit_app.py`. The runtime adapter must live in the allowed startup/diagnostic script boundary and fail closed when its expected Streamlit interfaces are absent.
- Do not claim that PFI-owned JS/CSS uses hash URLs. In the official Streamlit path those bytes are inline `srcdoc`; the hashed immutable URL claim applies only to URL-addressable Streamlit framework assets.
- Do not use the existing `build_v024_read_model_status().read_model_hash` directly because it contains a volatile generation time. Derive a stable semantic hash from whitelisted status fields and exclude timestamps, absolute paths, values, and the legacy hash.
- The actual `st.cache_data` adapter key must include the composite cache key as an explicit function argument. The composite must include at least build, data, parameter, formula, FX snapshot, and stable read-model dimensions; it also includes release source hashes, Streamlit version, and requirements-lock hash.
- Cache policy output and evidence may contain only public identifiers, hashes, counts, dates, versions, and statuses. It must not contain financial rows, amounts, FX rates, credentials, PIDs, or absolute home paths.
- Canonical launchers force `PFI_V021_RUNTIME_API_PORT=0`, allowing the runtime API to bind an OS-selected per-process port. A new process must never fall back to an old owner on fixed port 8766.
- Service Worker policy is explicit disablement: unregister same-origin registrations and delete only the dedicated PFI origin's caches. Any failure or surviving controller is fail-closed with Chinese restart/reinstall/cache-clearing actions.
- Static `file://` source mode is valid only when both `releaseManifestApi:false` and `releaseCachePolicyApi:false` are explicitly present. Dynamic Streamlit mode requires both APIs.
- The final tracked state uses a content/binding commit pair. `release_manifest.json.git_commit` points to the final reviewed content commit; its direct binding successor changes only identity/evidence/governance surfaces that do not invalidate the recorded frontend/backend hashes. An external attestation binds that successor without tracked self-reference.
- Stage 1 remains `in_progress` after this Phase. Phase 1.3, canonical install, Finder launch, new-profile acceptance, push, production acceptance, and final human acceptance remain not done.

## Cache Topology Truth

| Layer | Current truth | Phase 1.2 target |
|---|---|---|
| Streamlit host HTML | `no-cache`; missing `private` | `no-cache, private` plus ETag, Last-Modified, conditional 304 |
| Streamlit framework assets | content-hashed URLs; current 1.35 only sends `public` | hash-named assets get one-year immutable; unhashed assets revalidate privately |
| PFI shell JS/CSS | disk sources transformed to inline `srcdoc` | no independent HTTP cache; launch-time actual-byte bundle hash verification |
| Service Worker | no current source registration, historical browser state unknown | explicit unregister/cache cleanup; surviving controller blocks |
| bfcache | no `pageshow.persisted` recheck | synchronous pending state plus complete async identity/cache-policy recheck |
| Streamlit read model | direct uncached builder; legacy hash volatile | `st.cache_data` adapter, 30-second TTL, explicit composite key, runtime invalidation gate |
| Runtime API ownership | default fixed 8766 can belong to an old process | OS-selected per-process port 0, current process backend hash captured at import |
| Launcher reuse | release identity marker only | marker additionally binds cache key and rejects old/incomplete markers |

## Planned Files

### Product/cache handshake and launch boundary

- `PFI/config/release_manifest.json`
- `PFI/web/index.html`
- `PFI/web/app/version.js`
- `PFI/src/pfi_v02/stage_v021_runtime_api.py`
- `PFI/StartPFI.command`
- `PFI/scripts/startPFI.sh`
- `PFI/scripts/pfiReleaseIdentity.sh`
- `PFI/scripts/v025/release_cache_contract.py`
- `PFI/scripts/v025/run_streamlit_with_release_cache.py`

### Test, verifier, browser validation, and plan

- `PFI/docs/pfi_v025/stage_1/PHASE_1_2_CACHE_GOVERNANCE_IMPLEMENTATION_PLAN.md`
- `PFI/tests/test_v025_stage1_cache_policy.py`
- `PFI/web/tests/v025/stage1_release_identity.test.mjs`（仅适配新增 cache-policy 路由夹具）
- `PFI/web/tests/v025/stage1_cache_policy.test.mjs`
- `PFI/scripts/v025/browser_validate_stage1_phase12.mjs`
- `PFI/scripts/v025/verify_stage1_phase12.py`

### Evidence

- `PFI/reports/pfi_v025/stage_1/phase_1_2/cache_audit.md`
- `PFI/reports/pfi_v025/stage_1/phase_1_2/cache_headers.json`
- `PFI/reports/pfi_v025/stage_1/phase_1_2/service_worker_audit.md`
- `PFI/reports/pfi_v025/stage_1/phase_1_2/streamlit_cache_policy.json`
- `PFI/reports/pfi_v025/stage_1/phase_1_2/browser_validation.json`
- `PFI/reports/pfi_v025/stage_1/phase_1_2/bfcache_mismatch.png`
- `PFI/reports/pfi_v025/stage_1/phase_1_2/playwright_trace.zip`
- `PFI/reports/pfi_v025/stage_1/phase_1_2/evidence.json`
- `PFI/reports/pfi_v025/stage_1/phase_1_2/terminal.log`
- `PFI/reports/pfi_v025/stage_1/phase_1_2/changed_files.txt`
- `PFI/reports/pfi_v025/stage_1/phase_1_2/risk_and_rollback.md`
- `PFI/reports/pfi_v025/stage_1/phase_1_2/privacy_scan.txt`

### Governance companions

- `PFI/CHANGELOG.md`
- `PFI/docs/governance/DEVELOPMENT_LEDGER.md`
- `PFI/docs/governance/development_events.jsonl`
- `PFI/docs/governance/delivery_tasks.yaml`
- `PFI/docs/governance/TRACEABILITY_MATRIX.csv`
- `PFI/docs/governance/VERSION_MATRIX.yaml`
- `PFI/docs/governance/STATUS.md`
- `PFI/docs/governance/OWNER_STATUS.md`

## Task 1: Add focused tests and prove valid RED

- [ ] Create Python tests for stable semantic hashing, every cache-key dimension, privacy-safe output, actual `st.cache_data` hit/miss/TTL binding, marker behavior, ephemeral runtime API ownership, API headers, launch-time asset verification, and an isolated minimal Streamlit HTTP server.
- [ ] Create Node tests with URL-routed fetch mocks, event listeners, Service Worker/CacheStorage fakes, run epochs, static paired opt-out, cache-policy validation, and `pageshow.persisted` revalidation.
- [ ] Run both new suites before production implementation. The RED must be missing contract behavior, not import, collection, syntax, dependency, or fixture failure.
- [ ] Record commands, exit codes, and concise failures in `terminal.log` without private values.

## Task 2: Implement the backend cache contract and actual Streamlit adapter

- [ ] In `stage_v021_runtime_api.py`, add pure helpers for stable semantic read-model hashing, release asset recomputation, cache dimensions, composite key, and policy validation.
- [ ] Capture the running backend source hash at module import and expose `/api/release-cache-policy` with `Cache-Control: no-store, private`, ETag, Last-Modified, conditional response support, and only sanitized fields.
- [ ] Make `/api/release-manifest` use the same no-store/private validators and include the running backend source hash so disk manifest changes cannot impersonate old imported code.
- [ ] Add `release_cache_contract.py` to print a machine-safe key/JSON policy and fail when actual bundle/backend bytes do not match the manifest.
- [ ] Add `run_streamlit_with_release_cache.py`. Before entering Streamlit CLI in the same process, it must install the strict header policy, force/verify Tornado mode, and replace the official read-model status function with an `st.cache_data(ttl=30)` adapter whose explicit argument is `PFI_STREAMLIT_CACHE_KEY`.
- [ ] The adapter exposes deterministic diagnostics for tests, never changes financial calculations, and uses Streamlit's non-persistent cache mode.

## Task 3: Bind both launchers to the cache namespace and unique runtime API

- [ ] Extend `pfiReleaseIdentity.sh` to compute/export `PFI_STREAMLIT_CACHE_KEY` through the contract CLI and include it in marker equality/lines.
- [ ] Recompute and verify actual frontend/backend hashes before any existing service is reused.
- [ ] Make both launchers run the same-process wrapper instead of `python -m streamlit` and force `PFI_V021_RUNTIME_API_PORT=0` for every new canonical process.
- [ ] Keep all seven existing launcher URL query keys exactly compatible; do not add cache key to the URL.
- [ ] Old markers lacking the cache key must fail reuse. Existing 8501/8502 and 8766 owners remain untouched during this Phase.

## Task 4: Implement Service Worker cleanup and bfcache revalidation

- [ ] Add pure `applyPendingState`, `disableLegacyServiceWorkers`, `validateReleaseCachePolicy`, and epoch-aware revalidation helpers to `version.js`.
- [ ] Dynamic boot order is pending → unregister/delete audit → manifest and cache-policy `no-store` fetch → ready or Chinese blocked state.
- [ ] A current controller, unregister/delete false, exception, malformed/mismatched policy, old process cache key, or running backend hash mismatch must remain blocked.
- [ ] Install one `pageshow` listener. `persisted:false` is a no-op; `persisted:true` immediately hides the shell, starts a new epoch, updates `window.PFI_RELEASE_IDENTITY_READY`, and repeats the complete gate.
- [ ] Prevent an earlier slow success from overriding a later blocked result.
- [ ] Add `releaseCachePolicyApi:false` beside the static manifest opt-out in `index.html`; single-sided opt-out fails closed.

## Task 5: Turn GREEN and capture isolated runtime/browser evidence

- [ ] Run new Python and Node suites until GREEN, then rerun the Phase 1.1 regression suites.
- [ ] Start only a minimal temporary Streamlit app through the wrapper with isolated HOME, random ports, and a disposable process group. Verify HTML headers, validators/304, hashed immutable assets, and unhashed private revalidation.
- [ ] Use the cached Playwright package and headless Chromium without installation. Exercise Service Worker cleanup, synthetic `pageshow.persisted` logic, real back/forward navigation telemetry, mismatch fail-visible behavior, screenshot, and trace.
- [ ] Record actual `pageshow.persisted`; do not label a synthetic event as a real bfcache hit.
- [ ] Verify PFI shell source requests are inline/no independent cache entries and no request touches ports 8501/8502.

## Task 6: Create the final content and identity-binding commit pair

- [x] The initial content/binding pair `5edd3788` / `df7e2add` was created and independently reviewed.
- [x] That pair was rejected and explicitly superseded after the combined review result `C0/I4/M0`; it must never receive an attestation.
- [x] Commit the four-finding remediation as a new content successor without rewriting the rejected history (`b3885f15cd2e983c0839be6a20d7e4a9391c6324`).
- [x] Compute frontend/backend hashes from the new content commit using the Phase 1.1 canonical algorithm.
- [x] Update only `release_manifest.json` and its embedded `index.html` object with `git_commit=<final-content-commit>` and the recomputed hashes; if any hashed source changes afterward, create another content successor and recompute.
- [ ] Regenerate final evidence/governance records and commit them with the direct identity-binding successor.
- [ ] Verify the binding commit is the direct successor of the final content commit and its manifest hashes still resolve to that content.

## Task 7: Exact verifier, independent review, remediation, and attestation

- [ ] `verify_stage1_phase12.py` checks pinned Roadmap/Task Pack hashes, ZIP integrity, exact Phase changed paths, content/binding parentage, manifest/asset hashes, RED/GREEN ledger, cache policy, HTTP/browser artifacts, privacy, and every explicit not-done boundary.
- [ ] Run focused tests, syntax checks, `git diff --check`, changed-scope governance, and the verifier against the clean final binding commit object.
- [ ] Dispatch three independent read-only reviews: implementation/cache correctness, Roadmap acceptance, and evidence/governance/privacy.
- [x] Remediate every initial Critical/Important/Minor finding and rerun affected tests; fresh review must still report `C0/I0/M0` before attestation.
- [ ] Write the final external attestation under `<git-common-dir>/codex-review/pfi-v025/stage_1/phase_1_2/<binding-commit>/phase_1_2_attestation.json`; do not add it to Git.
- [ ] Re-run the candidate verifier requiring that attestation, confirm the worktree is clean, and stop at Phase 1.2 with Stage 1 still in progress.

### Independent review remediation record

The initial three-way review found no Critical issue and four Important issues. The remediation acceptance is all-or-nothing:

1. The same-process wrapper must prestart `ensure_v021_runtime_api_server()` while `PFI_V021_RUNTIME_API_PORT` is exactly `0`, verify a non-8766 loopback owner, and fail before Streamlit CLI on any error.
2. Stable read-model hashing must exclude financial values/amounts/rates while still changing for semantic status, evidence hash, count, as-of, and formula changes.
3. Release endpoint validators must honor `If-None-Match` precedence over `If-Modified-Since`, including weak/list/wildcard matching; non-release routes must keep their original non-validator semantics.
4. Browser trace ZIP members must be sanitized, remain readable, and be scanned after decompression; a container-only privacy scan is insufficient.

The superseded pair remains evidence of the rejected attempt. Only a new pair that passes fresh three-way review at `C0/I0/M0` may receive the external attestation.

## Validation Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=PFI/src \
  PFI/.venv/bin/python -B -m pytest -p no:cacheprovider \
  PFI/tests/test_v025_stage1_cache_policy.py \
  PFI/tests/test_v025_stage1_release_identity.py -q

node --test \
  PFI/web/tests/v025/stage1_cache_policy.test.mjs \
  PFI/web/tests/v025/stage1_release_identity.test.mjs

node --check PFI/web/app/version.js
zsh -n PFI/StartPFI.command PFI/scripts/startPFI.sh PFI/scripts/pfiReleaseIdentity.sh
PFI/.venv/bin/python -m py_compile \
  PFI/src/pfi_v02/stage_v021_runtime_api.py \
  PFI/scripts/v025/release_cache_contract.py \
  PFI/scripts/v025/run_streamlit_with_release_cache.py \
  PFI/scripts/v025/verify_stage1_phase12.py
git diff --check -- PFI
```

Browser validation uses the already cached Playwright module supplied through `PFI_PLAYWRIGHT_MODULE_DIR` and its installed Chromium. It must not run `npm install`, `npx` download, or modify project dependencies.

## Risk, Rollback, and Stop Conditions

- **Private Streamlit HTTP hook drift:** wrapper validates the target class/signature and Tornado mode before launch; unsupported runtime fails closed. Roll back the wrapper/launcher files to Phase base.
- **Read-model adapter drift:** wrapper uses public `st.cache_data`, preserves the original builder call and arguments, and has isolated hit/miss tests. If equivalence cannot be proven, do not claim Phase pass.
- **Old runtime API owner:** every new canonical process uses port 0. If runtime config still resolves to 8766 or an old backend hash, keep UI blocked and do not stop the old process in this Phase.
- **Legacy Service Worker controller:** unregister/cache cleanup may require one reload before controller loss. Keep the current page blocked with Chinese recovery; never auto-reload in a loop.
- **bfcache non-determinism:** record the real browser result honestly and retain deterministic event-path coverage. A missing real hit is not rewritten as a pass, but mismatch detection must still be demonstrated.
- **Identity hash cycle:** preserve final content/binding separation. Any post-content source edit invalidates the binding and requires a new content commit/hash calculation.
- **Scope expansion:** any requirement to edit `streamlit_app.py`, stop live ports, install the App, mutate data/DB, push, or enter Phase 1.3 stops that action and leaves it explicitly not done.

Rollback is the local inverse of the Phase content/binding commits or restoration of the Phase-base versions of the files above. No data migration or user-data rollback exists because this Phase performs no data/DB mutation.

## Completion Record

The Phase may be called `candidate_pass` only when focused suites, isolated HTTP/browser evidence, exact verifier, three independent reviews, and external attestation all pass at `C0/I0/M0`. The final report must state:

- Stage 1 / Phase 1.2 complete; Stage 1 remains `in_progress`.
- Phase 1.3 install/Finder acceptance, push, production acceptance, and final human acceptance are not done.
- Current installed/runtime Streamlit is 1.35.0 while the lock declares 1.54.0; Phase 1.3 must revalidate the actual installed environment after canonical reinstall.
- No live service, private data, model/formula/parameter semantics, App installation, or remote Git state was changed.
