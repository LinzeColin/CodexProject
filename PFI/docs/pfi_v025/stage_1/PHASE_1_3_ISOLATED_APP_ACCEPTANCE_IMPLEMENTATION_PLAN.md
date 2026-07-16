# PFI v0.2.5 Stage 1 Phase 1.3 Isolated App Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete `S1-P3-T1` through `S1-P3-T4` by building and genuinely launching a disposable isolated `PFI.app`, validating its real runtime in a fresh browser profile, proving canonical entries were unchanged, and binding truthful evidence without performing the single canonical install reserved for Stage 12.

**Acceptance target:** `ACC-PFI-V025-S1-P13-ISOLATED-APP-ACCEPTANCE`

**Phase base:** `4065146761859b002f61b03387fa2c724a8ddf8a`

**Architecture:** Stage 0 override `PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE` is the controlling interpretation of Roadmap `S1-P3-T1/T3`. A preparer copies `PFI/macos/PFI.app` to a run-created `/private/tmp/pfi-v025-s1p13-*` root, injects a checkout binding plus strict isolation markers, compiles/signs the candidate, and snapshots canonical entries. Finder launches that exact candidate; `StartPFI.command` detects the signed candidate markers and routes HOME, data, runtime state, cache, browser opening and both ports into the disposable root. A cached Playwright Chromium uses a new persistent profile against the Finder-started runtime, then cleanup stops only the recorded isolated process, unregisters the candidate from LaunchServices, deletes the run-created root, and proves canonical before/after equality.

**Tech Stack:** zsh, Python 3.12, macOS `ditto`/`clang`/`codesign`/`plutil`/LaunchServices, Finder through Computer Use, Streamlit 1.35 current runtime, cached Playwright 1.61.1 Chromium, pytest, Node `node:test`, SHA-256 and Git commit-object verification.

## Global Constraints

- Execute exactly Stage 1 / Phase 1.3 and tasks `S1-P3-T1..T4`; do not run the Stage 1 whole-stage review or enter Stage 2 in this run.
- Preserve the standing authorization `在最终验收前我全部都同意授权，不允许block`; it removes permission prompts but does not waive technical gates, one-Phase scope, independent review, privacy, or final Stage 12 human acceptance.
- Apply `PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE` exactly: copy only `PFI/macos/PFI.app` to a run-created `$STAGE1_TEMP_ROOT/PFI.app`; candidate is disposable and never promoted.
- Do not modify, delete, move, relink, quarantine, register as canonical, or overwrite `/Applications/PFI.app`, `$HOME/Desktop/PFI.app`, or `$HOME/Downloads/PFI.app`. They are read-only census surfaces and remain honestly labeled as the existing v0.2.3 entries.
- Do not run `installPFIEntryApps.sh --all`, `--downloads-only`, or any equivalent canonical install. The one canonical install remains `S12-P2-T1`; the one GitHub main upload remains after `S12-P3-T4` acceptance.
- Do not fetch, pull, merge, rebase, push, tag, release, mutate remote refs, install dependencies, or download Playwright/browser assets.
- Do not access, stop, reuse or claim ports 8501/8502. Finder candidate uses two pre-reserved non-8501/8502 ephemeral loopback ports and cleanup targets only its recorded service.
- Candidate HOME, `PFI_DATA_HOME`, runtime/log/lock/cache directories, `TMPDIR`, Chromium user-data directory and ports must all resolve under `$STAGE1_TEMP_ROOT`.
- Candidate uses an empty isolated data home; no financial data, SQLite, model, formula or parameter value is read or changed. Evidence contains hashes, counts, versions, statuses, timestamps, symbolic canonical labels and sanitized process identity only.
- Do not write raw PID, absolute home paths, private values, credentials or browser history into tracked evidence. Raw runtime state remains only inside the disposable root; tracked evidence may store `pid_observed=true` and a SHA-256 digest.
- Browser/Finder evidence is first written to one pre-created owner-only `/private/tmp/pfi-v025-s1p13-evidence-*` directory outside both the repository and candidate root. Only sanitized, validated artifacts are copied into the Phase report directory after candidate finalization proves `git_status_unchanged`; this staging root is then deleted.
- Finder launch must be real: reveal the prepared candidate in Finder and activate that App, then prove its runtime marker and service derive from the candidate App path. An `open <URL>`-only flow is not acceptance.
- Browser acceptance must use the Finder-started service and a fresh persistent Chromium profile. It must cover first load, ordinary reload, cache-cleared reload, forward/back, manifest/cache-policy identity, console/page errors and the real observed `pageshow.persisted` value.
- Source App and canonical entry tree hashes, symlink targets, plist identity, executable hash and codesign status are captured before and after. Any canonical delta is a failed stop gate even if the App/browser checks pass.
- LaunchServices registration/unregistration and candidate-process cleanup must be recorded. Candidate temp-root deletion occurs only after evidence artifacts are copied and canonical post-state is captured.
- The final tracked state uses a release-content commit and direct binding successor. `release_manifest.json.git_commit` points to the Phase 1.3 release-content commit; the binding successor changes only manifest embedding/evidence/governance/verifier surfaces that do not invalidate frontend/backend hashes.
- Stage 1 remains `in_progress` after Phase 1.3. A separate next run performs fresh whole-Stage review, remediation, re-review and Codex acceptance before transition to Stage 2.

## Planned Files

### Runtime isolation and candidate tooling

- Modify `PFI/StartPFI.command`
- Modify `PFI/macos/PFI_launcher.c`
- Modify `PFI/scripts/pfiReleaseIdentity.sh`
- Modify `PFI/scripts/pfiRuntime.sh`
- Modify `PFI/scripts/v025/release_cache_contract.py`
- Modify `PFI/scripts/v025/run_streamlit_with_release_cache.py`
- Create `PFI/scripts/v025/stage1_phase13_candidate_env.sh`
- Create `PFI/scripts/v025/stage1_phase13_candidate.py`
- Create `PFI/scripts/v025/browser_validate_stage1_phase13.mjs`
- Create `PFI/scripts/v025/verify_stage1_phase13.py`
- Create `PFI/src/pfi_os/app/isolated_candidate_app.py`
- Modify `PFI/web/app/version.js`

### Tests and plan

- Create `PFI/tests/test_v025_stage1_isolated_app_acceptance.py`
- Modify `PFI/web/tests/v025/stage1_release_identity.test.mjs`
- Create `PFI/docs/pfi_v025/stage_1/PHASE_1_3_ISOLATED_APP_ACCEPTANCE_IMPLEMENTATION_PLAN.md`

### Binding and evidence

- Modify `PFI/config/release_manifest.json`
- Modify `PFI/web/index.html` only inside the embedded release-manifest block
- Create `PFI/reports/pfi_v025/stage_1/phase_1_3/candidate_app.json`
- Create `PFI/reports/pfi_v025/stage_1/phase_1_3/entry_matrix.json`
- Create `PFI/reports/pfi_v025/stage_1/phase_1_3/finder_launch.png`
- Create `PFI/reports/pfi_v025/stage_1/phase_1_3/browser_candidate.png`
- Create `PFI/reports/pfi_v025/stage_1/phase_1_3/browser_validation.json`
- Create `PFI/reports/pfi_v025/stage_1/phase_1_3/playwright_trace.zip`
- Create `PFI/reports/pfi_v025/stage_1/phase_1_3/launchservices_cleanup.json`
- Create `PFI/reports/pfi_v025/stage_1/phase_1_3/protected_metadata.json`
- Create `PFI/reports/pfi_v025/stage_1/phase_1_3/evidence.json`
- Create `PFI/reports/pfi_v025/stage_1/phase_1_3/terminal.log`
- Create `PFI/reports/pfi_v025/stage_1/phase_1_3/changed_files.txt`
- Create `PFI/reports/pfi_v025/stage_1/phase_1_3/risk_and_rollback.md`
- Create `PFI/reports/pfi_v025/stage_1/phase_1_3/privacy_scan.txt`

### Mandatory governance companions

- Modify `PFI/CHANGELOG.md`
- Modify `PFI/docs/governance/DEVELOPMENT_LEDGER.md`
- Modify `PFI/docs/governance/OWNER_STATUS.md`
- Modify `PFI/docs/governance/STATUS.md`
- Modify `PFI/docs/governance/TRACEABILITY_MATRIX.csv`
- Modify `PFI/docs/governance/VERSION_MATRIX.yaml`
- Modify `PFI/docs/governance/delivery_tasks.yaml`
- Modify `PFI/docs/governance/development_events.jsonl`

## Task 1: Write focused tests and prove valid RED

**Files:**

- Create: `PFI/tests/test_v025_stage1_isolated_app_acceptance.py`
- Inspect: `PFI/StartPFI.command`, `PFI/scripts/pfiRuntime.sh`, `PFI/macos/PFI.app`, canonical entry metadata read-only

**Interfaces:**

- Produces required callables `prepare_candidate(project_root: Path) -> dict`, `snapshot_canonical_entries(home: Path) -> dict`, `finalize_candidate(state_path: Path, evidence_dir: Path) -> dict`.
- Produces zsh callable `pfi_stage1_candidate_configure PROJECT_DIR` and exported `PFI_STAGE1_CANDIDATE_MODE`, `PFI_RUNTIME_DIR`, `PFI_STREAMLIT_PORT`, `PFI_HEARTBEAT_PORT`.

- [ ] **Step 1: Add RED tests for the missing candidate tooling**

```python
def test_candidate_module_exposes_prepare_snapshot_and_finalize() -> None:
    module = load_candidate_module()
    for name in ("prepare_candidate", "snapshot_canonical_entries", "finalize_candidate"):
        assert callable(getattr(module, name, None)), name

def test_stage1_candidate_rejects_canonical_roots_and_live_ports(tmp_path: Path) -> None:
    configure = load_candidate_env()
    assert configure(temp_root=Path("/Applications"), app_port=49152, heartbeat_port=49153).returncode != 0
    assert configure(temp_root=tmp_path, app_port=8501, heartbeat_port=49153).returncode != 0
    assert configure(temp_root=tmp_path, app_port=49152, heartbeat_port=8502).returncode != 0
```

- [ ] **Step 2: Add RED tests for `StartPFI.command` isolation and no-browser behavior**

```python
def test_finder_candidate_routes_every_mutable_surface_under_temp_root() -> None:
    source = (PFI_ROOT / "StartPFI.command").read_text()
    assert "pfi_stage1_candidate_configure" in source
    assert 'LOG_DIR="${PFI_RUNTIME_DIR:-$PROJECT_DIR/data/cache}"' in source
    assert 'PORT="${PFI_STREAMLIT_PORT:-8501}"' in source
    assert 'PFI_START_OPEN_BROWSER' in source
```

- [ ] **Step 3: Add RED tests for immutable canonical inventory and protected metadata**

```python
def test_entry_snapshot_uses_symbolic_labels_and_hashes_only() -> None:
    snapshot = snapshot_canonical_entries(Path.home())
    assert set(snapshot) == {"applications", "desktop", "downloads"}
    assert all("/Users/" not in json.dumps(row) for row in snapshot.values())
    assert all("tree_sha256" in row or row["kind"] in {"missing", "symlink"} for row in snapshot.values())
```

- [ ] **Step 4: Run the new suite and record valid RED**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=PFI/src \
  PFI/.venv/bin/python -B -m pytest -p no:cacheprovider \
  PFI/tests/test_v025_stage1_isolated_app_acceptance.py -q
```

Expected: failures are missing Phase 1.3 files/callables/isolation behavior, not import, fixture, dependency or syntax failures.

## Task 2: Implement strict candidate environment and launcher isolation

**Files:**

- Create: `PFI/scripts/v025/stage1_phase13_candidate_env.sh`
- Modify: `PFI/StartPFI.command`
- Modify: `PFI/scripts/pfiRuntime.sh`
- Test: `PFI/tests/test_v025_stage1_isolated_app_acceptance.py`

**Interfaces:**

- Candidate resource files: `PFI_STAGE1_ISOLATED_ROOT`, `PFI_STAGE1_STREAMLIT_PORT`, `PFI_STAGE1_HEARTBEAT_PORT`.
- `pfi_stage1_candidate_configure(project_dir)` returns normal-launch no-op when the marker is absent; when present, it validates exact `/private/tmp/pfi-v025-s1p13-*/PFI.app` ownership and exports every isolated path/port.

- [ ] **Step 1: Implement the candidate environment loader**

```zsh
pfi_stage1_candidate_configure() {
  local project_dir="$1"
  typeset -gx PFI_STAGE1_CANDIDATE_MODE=0
  local app_path="${PFI_LAUNCHER_APP_PATH:-}"
  local marker="$app_path/Contents/Resources/PFI_STAGE1_ISOLATED_ROOT"
  [[ -f "$marker" ]] || return 0
  # Resolve and require /private/tmp/pfi-v025-s1p13-*/PFI.app, then validate
  # separate numeric ports excluding 8501 and 8502 before exporting paths.
}
```

- [ ] **Step 2: Route `StartPFI.command` mutable state and ports through the exported environment**

Required source relationships:

```zsh
source "$PROJECT_DIR/scripts/v025/stage1_phase13_candidate_env.sh"
pfi_stage1_candidate_configure "$PROJECT_DIR"
LOG_DIR="${PFI_RUNTIME_DIR:-$PROJECT_DIR/data/cache}"
PORT="${PFI_STREAMLIT_PORT:-8501}"
HEARTBEAT_PORT="${PFI_HEARTBEAT_PORT:-$((PORT + 1000))}"
```

Replace direct `open "$OPEN_URL"` calls with one helper that does nothing when `PFI_START_OPEN_BROWSER=0`. Add candidate mode/app identity plus the exact shutdown-monitor PID and heartbeat port to an owner-only, atomically replaced active-service marker. The launcher must prove the monitor command/cwd/listener before writing that marker or reusing an existing candidate runtime.

- [ ] **Step 3: Stop refreshing `.venv/.pfi_os_app_ready` on every runtime resolution**

`pfi_os_ensure_app_python` must treat the ready marker as an input produced by `installLockedEnv.sh`, not rewrite it during candidate validation.

- [ ] **Step 4: Run focused tests and zsh syntax until GREEN**

```bash
zsh -n PFI/StartPFI.command PFI/scripts/pfiRuntime.sh PFI/scripts/v025/stage1_phase13_candidate_env.sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=PFI/src \
  PFI/.venv/bin/python -B -m pytest -p no:cacheprovider \
  PFI/tests/test_v025_stage1_isolated_app_acceptance.py -q
```

## Task 3: Build, inventory and clean a disposable signed App candidate

**Files:**

- Create: `PFI/scripts/v025/stage1_phase13_candidate.py`
- Test: `PFI/tests/test_v025_stage1_isolated_app_acceptance.py`

**Interfaces:**

- CLI `prepare --project-root PFI` prints the absolute disposable `state.json` path and creates no tracked file.
- CLI `inspect --state <state.json>` waits for the Finder-started isolated marker and emits a sanitized JSON record.
- CLI `finalize --state <state.json> --evidence-dir <external-root>` accepts only a pre-created owner-only `0700` `/private/tmp/pfi-v025-s1p13-evidence-*` staging root, stops only the uniquely grouped isolated runtime, unregisters the candidate, verifies before/after canonical equality, copies sanitized evidence and removes the temp root.

- [ ] **Step 1: Implement deterministic tree hashing and symbolic canonical inventory**

```python
CANONICAL_LABELS = {
    "applications": Path("/Applications/PFI.app"),
    "desktop": Path.home() / "Desktop/PFI.app",
    "downloads": Path.home() / "Downloads/PFI.app",
}

def snapshot_canonical_entries(home: Path | None = None) -> dict[str, dict[str, object]]:
    """Return kind, symbolic target, plist identity, executable/tree hashes and codesign status without mutation."""
```

- [ ] **Step 2: Implement `prepare_candidate`**

Required sequence: `mkdtemp` → canonical before snapshot → protected metadata snapshot → `ditto` source bundle → compile launcher with `-O2 -Wall -Wextra -Werror -Wl,-no_uuid -DPFI_STAGE1_ISOLATED_PROCESS_GROUP=1` → write checkout/isolation/port resources → ad-hoc codesign → strict verify → LaunchServices register → exact candidate-path presence in `lsregister -dump` → state JSON with root device/inode inside the temp root. Reject any root not matching `/private/tmp/pfi-v025-s1p13-*` and any reserved/live port.

- [ ] **Step 3: Implement inspect and cleanup with process ownership checks**

Only a runtime whose exact wrapper token, dedicated `isolated_candidate_app.py` token, project cwd, `--server.port` and `127.0.0.1` listener match may be owned. Bind the shutdown monitor separately to the exact directly executed `src/pfi_os/system/shutdown_monitor.py` token, project cwd, `127.0.0.1` heartbeat endpoint and Streamlit PID; `python -m pfi_os.system.shutdown_monitor` is forbidden. The candidate C launcher must create a unique process group whose PGID equals the exact `StartPFI.command` launcher PID; launcher, Streamlit and monitor must be the only three group members, and the group endpoint set must equal only the two prepared loopback endpoints. PPID-tree evidence remains auxiliary; PGID membership is the authoritative late-fork/reparent cleanup boundary. Inspect and finalize share one non-blocking `flock`; finalize publishes an owner-only tombstone, the launcher rechecks it before child launch, after monitor readiness and before marker publication, and root removal revalidates the original device/inode. Runtime and first LaunchServices before/post cleanup facts are persisted as retry checkpoints, so an evidence-write failure can safely converge without rewriting first-run truth. Root deletion requires the original group empty, launch lock quiescent, both ports free, external evidence staged, canonical/protected/git state unchanged and LaunchServices absent. Otherwise preserve the tombstoned root/state.

- [ ] **Step 4: Test prepare/finalize without Finder using a fake marker**

The test creates only a disposable candidate, uses either no marker or a stale non-live marker without signaling a real process, confirms LaunchServices cleanup, canonical equality and temp deletion, and leaves repository status unchanged. Separate tests prove unique PGID creation, exact loopback endpoint ownership, external evidence-root permissions, retry checkpoints and finalization locking.

## Task 4: Validate the Finder-started service in a fresh browser profile

**Files:**

- Create: `PFI/scripts/v025/browser_validate_stage1_phase13.mjs`
- Test: `PFI/tests/test_v025_stage1_isolated_app_acceptance.py`

**Interfaces:**

- CLI requires `--state`, `--output-dir`, cached `PFI_PLAYWRIGHT_MODULE_DIR`, and performs no install.
- Reads the Finder-created active marker; never starts its own service and rejects ports 8501/8502.

- [ ] **Step 1: Add syntax/contract tests before implementation**

Assert use of `launchPersistentContext`, `Network.clearBrowserCache`, trace sanitization, candidate-marker validation, reload/back-forward checks and no `npm`/`npx` execution.

- [ ] **Step 2: Implement actual-runtime browser checks**

Checks must include:

```javascript
const checks = {
  finder_started_runtime: true,
  new_profile_ready: false,
  manifest_identity_match: false,
  cache_policy_identity_match: false,
  ordinary_reload_same_identity: false,
  cache_cleared_reload_same_identity: false,
  back_forward_same_identity: false,
  no_console_or_page_errors: false,
  no_live_ports_8501_8502: false,
  candidate_profile_isolated: false,
};
```

Capture the real `pageshow.persisted` observation without converting a false result into a hit. Save `browser_candidate.png`, `browser_validation.json` and sanitized `playwright_trace.zip` to the declared owner-only external evidence root; do not mutate the repository while the candidate is active.

- [ ] **Step 3: Prove browser output contains no home path, credentials, private values or raw PID**

Scan JSON, screenshot metadata and every ZIP member after decompression.

## Task 5: Create release-content commit and bind the manifest

**Files:**

- Commit content files from Tasks 1-4 and this plan.
- Modify after content commit: `PFI/config/release_manifest.json`, embedded manifest in `PFI/web/index.html`.

- [ ] **Step 1: Run focused regressions before content commit**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=PFI/src \
  PFI/.venv/bin/python -B -m pytest -p no:cacheprovider \
  PFI/tests/test_v025_stage1_isolated_app_acceptance.py \
  PFI/tests/test_v025_stage1_cache_policy.py \
  PFI/tests/test_v025_stage1_release_identity.py -q
node --test PFI/web/tests/v025/stage1_cache_policy.test.mjs \
  PFI/web/tests/v025/stage1_release_identity.test.mjs
```

- [ ] **Step 2: Commit stable runtime/tooling content**

Commit message: `fix(PFI): isolate v0.2.5 stage 1 app candidate acceptance`.

- [ ] **Step 3: Bind release manifest to the full content commit**

Set `git_commit=<content-commit>` in JSON and embedded manifest. Recompute frontend/backend hashes with the established canonical algorithm; they may remain byte-identical only if the hashed source set is unchanged. Recompute cache key after commit identity changes.

## Task 6: Execute real Finder candidate and capture evidence

**Files:** Phase-local evidence only, plus Finder/browser binary artifacts.

- [ ] **Step 1: Prepare candidate and re-check canonical before state**

No canonical entry path may change between run-start census and prepare-time snapshot.

- [ ] **Step 2: Reveal the candidate in Finder and activate it**

Use Computer Use to open the run-created temp folder, select `PFI.app`, and double-click the candidate. Capture the Finder UI screenshot as `finder_launch.png`. Do not activate `/Applications`, Desktop or Downloads entries.

- [ ] **Step 3: Inspect the active marker and run browser validation**

Require the App path, project binding, content commit, manifest SHA, frontend/backend hash, cache key, non-live port and candidate-mode marker to match before browser navigation.

- [ ] **Step 4: Finalize and prove cleanup**

Stop only the candidate service, wait for its original identity and the bound shutdown monitor to exit, require both the Streamlit and heartbeat listeners to be absent, unregister the candidate, require the exact candidate path to disappear from LaunchServices, capture canonical after state, require byte-for-byte equality with before state, copy sanitized records, then delete the disposable root.

After finalization has recorded `git_status_unchanged=true`, independently validate every staged artifact, copy the approved set into `PFI/reports/pfi_v025/stage_1/phase_1_3/`, and delete the external evidence root.

### Mandatory remediation after the rejected first Task 6 execution

The first real candidate execution is explicitly rejected and none of its artifacts may be copied into the Phase report directory. Its review found candidate-mode Git-tree financial reads, SQLite creation, a third auxiliary Runtime API port, visible private financial state, unredacted trace cookie values and private Finder labels. Before the only acceptable rerun:

- Candidate cache identity must use the release-only `PFIV025Stage1IsolatedCandidateCachePolicyV1` namespace and must not read data, parameter, formula, FX or read-model inputs.
- Candidate Streamlit startup must not initialize `OperationalStore`, SQLite, homepage ingestion, Stage 4 read model, Stage 7 report schema or the auxiliary Runtime API.
- The Streamlit PID listener set must equal only the prepared App port; the shutdown-monitor PID listener set must equal only the prepared heartbeat port.
- Launcher release identity must validate from the complete Finder launcher query, embedded manifest SHA and release-only cache policy without any auxiliary API request.
- Browser checks must prove deterministic empty embedded data, no visible currency amount/private record state, exact request-port set `{app_port}`, and no ready real-data marker across all reload/history snapshots.
- Browser evidence must independently bind the marker PGID, the exact three-member process-group identity digest and the two loopback endpoint digest; a 20-second heartbeat keeps the inspected runtime alive throughout the reload/history/screenshot matrix.
- Trace must disable screenshots, DOM snapshots and sources, recursively redact cookie objects, reject binary resources, and fail closed on financial/private-data patterns.
- Finder must hide sidebar, path bar and status bar before the new screenshot; the new screenshot receives an independent visual privacy review and is never derived from the rejected image.

## Task 7: Bind evidence, verify and independently review

**Files:** Phase evidence, verifier and governance companions listed above.

- [ ] **Step 1: Build exact evidence and privacy records**

`evidence.json` must distinguish `isolated_candidate_finder_launch=true` from `canonical_app_install=false`; state the existing entries remain v0.2.3 and canonical install remains `S12-P2-T1`.

- [ ] **Step 2: Implement exact verifier**

`verify_stage1_phase13.py` checks pinned source hashes, exact changed paths, content/binding parentage, manifest/cache identity, source/candidate hash chain, Finder screenshot/trace, browser checks, canonical before/after equality, LaunchServices/process/temp cleanup, no private data, no 8501/8502, no canonical mutation, no push/install and all explicit not-done boundaries.

- [ ] **Step 3: Run full-tree shadow governance**

Require project governance and semantic sync `0 errors / 0 warnings` from a temporary full-tree worktree, then remove it.

- [ ] **Step 4: Create direct binding commit**

Commit message: `docs(PFI): bind v0.2.5 stage 1 phase 1.3 isolated app evidence`.

- [ ] **Step 5: Dispatch fresh core, Roadmap acceptance and evidence/privacy reviews**

Remediate every Critical/Important/Minor finding, rebuild the content/binding pair when tracked source changes, and re-review until all three independently report `C0/I0/M0`.

- [ ] **Step 6: Write external attestation and require it**

Store it outside Git under `<git-common-dir>/codex-review/pfi-v025/stage_1/phase_1_3/<binding-commit>/phase_1_3_attestation.json`, then run candidate verifier with `--require-attestation`.

## Validation Commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=PFI/src \
  PFI/.venv/bin/python -B -m pytest -p no:cacheprovider \
  PFI/tests/test_v025_stage1_isolated_app_acceptance.py \
  PFI/tests/test_v025_stage1_cache_policy.py \
  PFI/tests/test_v025_stage1_release_identity.py -q

node --test \
  PFI/web/tests/v025/stage1_cache_policy.test.mjs \
  PFI/web/tests/v025/stage1_release_identity.test.mjs

zsh -n PFI/StartPFI.command PFI/scripts/pfiRuntime.sh \
  PFI/scripts/v025/stage1_phase13_candidate_env.sh
node --check PFI/scripts/v025/browser_validate_stage1_phase13.mjs
PFI/.venv/bin/python -m py_compile \
  PFI/scripts/v025/stage1_phase13_candidate.py \
  PFI/scripts/v025/verify_stage1_phase13.py
plutil -lint PFI/macos/PFI.app/Contents/Info.plist
codesign --verify --deep --strict PFI/macos/PFI.app
git diff --check -- PFI
```

## Risk, Rollback and Stop Conditions

- **Canonical mutation:** any before/after delta under `/Applications/PFI.app`, Desktop or Downloads fails the Phase. Stop candidate, unregister/delete only the run-created temp root, preserve evidence and do not repair canonical entries here.
- **Wrong App source:** candidate must be copied from repository `PFI/macos/PFI.app`, bind the current checkout, and resolve the Phase content commit. Unknown source or identity fails closed.
- **Isolation escape:** any candidate write outside its temp root except read-only project module access, or any access to 8501/8502/private data, fails the Phase and triggers candidate-only cleanup.
- **Finder ambiguity:** if the activated App cannot be tied to the candidate path and isolated active marker, do not substitute an `open URL` result.
- **LaunchServices/process cleanup:** candidate registration, listener or temp root surviving finalize is a failed gate; cleanup may retry only the same deterministic unregistration/termination sequence, never an App install.
- **Browser truth:** record actual `persisted` behavior; cache clear is an explicit test action, not a product recovery prerequisite. The product must also pass ordinary reload/back-forward without manual user-history deletion.
- **Streamlit drift:** actual runtime 1.35 is tested now; lock 1.54 and final rebuilt environment remain a Stage 12 revalidation obligation, not a claim that 1.54 ran here.
- **Identity cycle:** any post-content change to hashed/runtime sources requires a new content commit and regenerated manifest/cache/evidence. Never amend or rewrite a reviewed pair.

Rollback is limited to stopping the isolated candidate service, unregistering the isolated candidate, deleting its run-created temp root, and reverting this Phase's local commits with new path-limited compensating commits if necessary. No canonical App, user data, remote ref or existing listener is modified, so no canonical/data rollback is authorized in this Phase.

## Completion Record

Phase 1.3 may be called `candidate_pass` only after the real Finder-started disposable candidate, fresh-profile browser matrix, canonical before/after equality, cleanup, exact verifier, three independent reviews and external attestation all pass. The final report must state:

- Phase 1.3 complete under the approved isolated-candidate override; Stage 1 remains `in_progress` pending its separate whole-stage review.
- Existing canonical entries remain the observed old v0.2.3 entries and were not promoted, repaired or relabeled.
- Canonical install/reinstall, canonical Finder UAT, final installed-runtime proof and GitHub main upload remain Stage 12 work.
- No financial data, SQLite, model/formula/parameter semantics, live 8501/8502, dependency install or remote Git state changed.
