# PFI v0.2.5 Stage 1 Phase 1.1 Release Identity Implementation Plan

> **For agentic workers:** Execute this plan as one bounded controlled run. Follow TDD, preserve the two-commit identity semantics, and do not enter Phase 1.2 or Phase 1.3.

**Goal:** Complete `S1-P1-T1` through `S1-P1-T4` so the repository App template, launcher URL, runtime API, and frontend embedded manifest share one verifiable v0.2.5 identity and any mismatch remains visibly blocked in Chinese.

**Acceptance target:** `ACC-PFI-V025-S1-P11-RELEASE-IDENTITY`

**Architecture:** `PFI/config/release_manifest.json` is the machine-readable release identity. The runtime API returns that file without financial-data access. Both launchers load it at runtime, validate the actual App plist, and place the identity in the browser query. `PFI/web/index.html` embeds the same JSON and starts with the existing UI hidden. `PFI/web/app/version.js` compares embedded, launcher, and backend identities, resolving the launcher query from the local URL or the Streamlit `srcdoc` iframe's parent/referrer without changing the out-of-scope Streamlit application source. It reveals the shell only on a complete match or on an explicitly declared static-source path with a valid embedded manifest; Finder-side identity failure uses a Chinese dialog. Otherwise it keeps the old UI hidden and presents a Chinese conflict/recovery surface.

**Tech stack:** zsh, C/macOS launcher, Python 3.12, `http.server`, JSON Schema 2020-12, browser JavaScript, Node `node:test`, pytest, `plutil`, `clang`, `openssl`, and Git commit-object verification.

## Global Constraints

- Execute exactly one Phase: Stage 1 / Phase 1.1. Do not implement Phase 1.2 cache policy or Phase 1.3 install/Finder acceptance.
- Do not push, fetch, merge, rebase, install an App, modify `/Applications`, Desktop, Downloads, ports 8501/8502, financial data, SQLite, model logic, formula logic, or parameter values.
- The user's exact standing authorization is `在最终验收前我全部都同意授权，不允许block`, SHA-256 `2c9fe289b301b229d5df677f8c16467177e5950098d2407f198dd99e699480ca`. It authorizes intermediate Stage transitions after their technical gates; it is not final Stage 12 human acceptance.
- Never create or impersonate `human_acceptance.json`. Final Stage 12 release/evidence-bound acceptance remains mandatory.
- Preserve Stage 0 immutable evidence and review artifacts. Record the new authorization in a new overlay; do not rewrite historical Stage 0 acceptance records.
- Preserve `PFI_APP_LAUNCH_DRY_RUN=1` output exactly. New launcher-path diagnostics must use a separate opt-in variable.
- Keep the existing `window.PFI_STAGE1_VERSION`, `window.PFI_READ_STAGE1_VERSION`, and `window.PFI_STAGE2_ENTRY_VERSION` compatibility interfaces.
- A missing, partial, invalid, unreachable, or mismatched runtime identity must stay fail-closed and show `版本冲突` plus restart, reinstall, and cache-clearing actions in Chinese. It must not visibly expose the old shell.
- Runtime API tests must use an ephemeral loopback port. Do not claim the Roadmap's illustrative Streamlit-port `8501/api/release-manifest` succeeds; the current release API belongs to the separate runtime API base URL.
- No model, financial formula, data schema, or parameter behavior changes occur in this Phase. Identity metadata must cite existing source identifiers and may not invent v0.2.5 model/data versions.
- The final tracked Phase state uses a content/binding pair: the manifest `git_commit` points to the latest content commit and a post-commit external attestation binds its successor binding commit without a tracked self-reference.
- Review remediation superseded the initial pair and the intermediate `71147c43.../9cc8e0f6...` pair. The final content commit is `a9592b8ce457492fd0e6817f74388f146ca657c6`; its successor binding commit binds runtime-config normalization, response-header manifest SHA comparison, sanitized manifest-load errors, Streamlit iframe launcher-source enforcement, static embedded-manifest validation, and a visible Chinese Finder recovery dialog.

## Release Identity Contract

The final manifest has exactly the Task Pack schema fields:

```json
{
  "product": "PFI",
  "version": "v0.2.5",
  "build_id": "pfi-v025-s1p1-20260712.1",
  "git_commit": "<full release_content_commit A>",
  "frontend_bundle_hash": "<64 lowercase hex>",
  "backend_build_hash": "<64 lowercase hex>",
  "app_short_version": "0.2.5",
  "app_build_version": "20260712.1",
  "data_schema_version": "PFIV021HoldingsPersistenceV1",
  "formula_version": "v0.2.3",
  "parameter_version": "v0.2.2",
  "generated_at": "<UTC RFC3339 binding time>"
}
```

The three version-source fields above are existing source identifiers:

- data: `V021_HOLDINGS_PERSISTENCE_SCHEMA` in `stage_v021_holdings_persistence.py`;
- formula: `VERSION` in `stage_v023_formula_registry.py`;
- parameter: `parameter_version` in `config/pfi_parameters.yaml`.

`frontend_bundle_hash` is deterministic and cycle-free:

1. Enumerate the exact frontend files delivered by `web/index.html`: `index.html`, `styles/tokens.css`, `styles.css`, and every local JavaScript source referenced by a `<script src="./...">` element.
2. For `index.html` only, replace the contents of `<script type="application/json" id="pfi-release-manifest">...</script>` with the literal `{}` before hashing.
3. Compute SHA-256 for each byte payload.
4. Sort by repository-relative path and hash the UTF-8 records `path + "\0" + payload_sha256 + "\n"`.

`backend_build_hash` is the raw-file SHA-256 of `PFI/src/pfi_v02/stage_v021_runtime_api.py`. The manifest file itself is excluded from both hashes.

The launcher query must carry these keys and values from the manifest/plist:

```text
pfi_app_version
pfi_app_build
pfi_build
pfi_commit
pfi_frontend_hash
pfi_backend_hash
pfi_manifest_sha256
```

Absence of all launcher keys means direct-localhost mode and compares embedded/backend only. Presence of any launcher key requires all seven and compares all launcher fields.

## Planned Files

### Product and identity

- `PFI/VERSION`
- `PFI/config/release_manifest.json`
- `PFI/web/index.html`
- `PFI/web/app/version.js`
- `PFI/src/pfi_v02/stage_v021_runtime_api.py`
- `PFI/macos/PFI_launcher.c`
- `PFI/macos/PFI.app/Contents/MacOS/PFI`
- `PFI/macos/PFI.app/Contents/Info.plist`
- `PFI/macos/PFI.app/Contents/_CodeSignature/CodeResources`
- `PFI/StartPFI.command`
- `PFI/scripts/startPFI.sh`
- `PFI/scripts/pfiReleaseIdentity.sh`

### Contract, test, verifier, and evidence

- `PFI/docs/pfi_v025/stage_0/interim_stage_transition_authorization.json`
- `PFI/docs/pfi_v025/stage_1/PHASE_1_1_RELEASE_IDENTITY_IMPLEMENTATION_PLAN.md`
- `PFI/tests/test_v025_stage1_release_identity.py`
- `PFI/web/tests/v025/stage1_release_identity.test.mjs`
- `PFI/scripts/v025/verify_stage1_phase11.py`
- `PFI/reports/pfi_v025/stage_1/phase_1_1/evidence.json`
- `PFI/reports/pfi_v025/stage_1/phase_1_1/terminal.log`
- `PFI/reports/pfi_v025/stage_1/phase_1_1/changed_files.txt`
- `PFI/reports/pfi_v025/stage_1/phase_1_1/risk_and_rollback.md`
- `PFI/reports/pfi_v025/stage_1/phase_1_1/release_manifest_schema_validation.json`
- `PFI/reports/pfi_v025/stage_1/phase_1_1/app_info_plist.json`
- `PFI/reports/pfi_v025/stage_1/phase_1_1/asset_hashes.json`
- `PFI/reports/pfi_v025/stage_1/phase_1_1/identity_matrix.json`
- `PFI/reports/pfi_v025/stage_1/phase_1_1/backend_manifest_response.json`
- `PFI/reports/pfi_v025/stage_1/phase_1_1/browser_validation.json`
- `PFI/reports/pfi_v025/stage_1/phase_1_1/mismatch_chinese_error.png`
- `PFI/reports/pfi_v025/stage_1/phase_1_1/privacy_scan.txt`

### Governance companions

- `PFI/CHANGELOG.md`
- `PFI/docs/governance/DEVELOPMENT_LEDGER.md`
- `PFI/docs/governance/development_events.jsonl`
- `PFI/docs/governance/delivery_tasks.yaml`
- `PFI/docs/governance/TRACEABILITY_MATRIX.csv`
- `PFI/docs/governance/VERSION_MATRIX.yaml`
- `PFI/docs/governance/STATUS.md`
- `PFI/docs/governance/OWNER_STATUS.md`

Do not edit model/formula/parameter registries merely to satisfy a filename classifier. If a generic governance validator classifies release config or `risk_and_rollback.md` as a model change, record the exact legacy classifier result and run the semantic/project validators in a temporary shadow without committing shadow modifications.

## Task 1: Execute the complete Phase 1.1 controlled run

### Step 1: Persist the standing transition authorization

Create `interim_stage_transition_authorization.json` with schema `PFIV025StandingInterimTransitionAuthorizationV1`. It must record:

- exact user text, SHA-256, UTC recording time, and `authority=latest_explicit_user_decision`;
- transitions `0->1` through `11->12`;
- `no_reprompt_before_final=true`;
- prerequisites: all Phase evidence, whole-stage independent review, remediation, re-review `C0/I0/M0`, Codex acceptance, clear stop conditions, and one Phase per run;
- Stage 0 review commit `9380fdf4a500f48a2b15859044ab7926b4924391`, evidence SHA-256 `f30cab259f84660ef18749288251198f3964720fc2af61e71d198f48fe92954a`, and external attestation SHA-256 `27d7596b4b41991d3e1749cc28447e41af501073e0343415b2f97ec9f421f0b2`;
- `stage_0_transition=authorized`, `stage_1_entry_authorized=true`;
- explicit statements that it is revocable, not final release acceptance, does not make v0.2.5 production accepted, and does not waive technical/review/evidence/privacy/no-push/no-install controls.

Validate the exact message hash independently with `printf %s ... | openssl dgst -sha256`.

### Step 2: Add tests and prove RED

Create `PFI/tests/test_v025_stage1_release_identity.py` with focused assertions for:

- Task Pack schema validation using `Draft202012Validator` and `FormatChecker`;
- manifest 64-hex frontend/backend hashes and exact existing source-version identifiers;
- deterministic frontend/backend hash recomputation;
- `VERSION`, plist, both launchers, and query keys matching the manifest;
- new launcher identity dry-run reporting the actual App path while legacy dry-run output stays byte-compatible;
- ephemeral `ThreadingHTTPServer(("127.0.0.1", 0), _handler_factory(None))` returning the exact manifest at `/api/release-manifest` without database access;
- embedded frontend manifest exactly matching the machine manifest;
- fail-visible Chinese gate source contract.

Create `PFI/web/tests/v025/stage1_release_identity.test.mjs` with Node built-ins only. Evaluate exported/published gate functions in a minimal fake DOM and cover:

- embedded/backend match passes;
- each identity field mismatch blocks;
- partial launcher query blocks;
- backend unreachable or invalid JSON blocks;
- direct-localhost mode may omit all launcher keys but still requires embedded/backend match;
- static-source mode is allowed only when runtime config explicitly sets `releaseManifestApi:false`;
- static-source opt-out still validates the complete embedded manifest and remains fail closed when it is missing or invalid;
- Streamlit `srcdoc` mode resolves launcher identity from accessible parent URL or `document.referrer`; partial, tampered, duplicate, or conflicting launcher sources block;
- Finder/App identity-init or native project-binding failure invokes a Chinese dialog containing restart, reinstall, and cache-clearing recovery actions;
- blocked state keeps the shell hidden and shows `版本冲突`, restart, reinstall, and cache-clearing actions.

Run exactly:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=PFI/src \
  PFI/.venv/bin/python -B -m pytest -p no:cacheprovider \
  PFI/tests/test_v025_stage1_release_identity.py -q
node --test PFI/web/tests/v025/stage1_release_identity.test.mjs
```

The first run must be RED because the release manifest/endpoint/gate do not exist. Reject import, syntax, collection, or environment failures as invalid RED. Capture command, exit code, failing contract, and summary in the Phase terminal ledger.

### Step 3: Implement generic, commit-independent mechanics

Implement without writing final manifest values yet:

1. Add a read-only manifest loader in `stage_v021_runtime_api.py`, resolving `PFI/config/release_manifest.json` from the repository tree and returning a defensive copy. Add `/api/release-manifest` before any DB-backed route. A missing/invalid manifest returns a typed server error; do not read or initialize SQLite.
2. Add `pfiReleaseIdentity.sh`. It must parse the manifest, validate required fields, validate `PFI/VERSION`, validate the actual App plist path supplied by `PFI_LAUNCHER_APP_PATH` (or the repository template for direct script use), calculate the manifest SHA-256, export the seven query fields, and expose marker comparison/write helpers.
3. Source that helper from both launcher scripts. Reused services must match build, commit, frontend hash, backend hash, and manifest hash before reuse. Do not mutate live services in tests.
4. Set `PFI_LAUNCHER_APP_PATH` in `PFI_launcher.c` only for the real spawn path. Preserve the legacy dry-run output exactly and add `PFI_APP_LAUNCH_IDENTITY_DRY_RUN=1` for an identity diagnostic. Recompile only the repository App template binary and verify ad-hoc code-sign validity if the template is signed.
5. Add a release-conflict section and embedded manifest block to `index.html`. The existing shell begins hidden. The static source runtime config explicitly includes `releaseManifestApi:false`; the Streamlit-rendered config omits that opt-out and therefore enforces the API.
6. Replace `version.js` with a generic gate that preserves the legacy globals, publishes pure comparison helpers for Node tests, starts in pending/hidden state, fetches `${apiBaseUrl}/api/release-manifest`, and either reveals the shell or keeps it hidden and displays the Chinese conflict surface. It must not silently fall back after fetch/parse failure.
7. Set the deterministic `PFI/VERSION` and plist short/build versions to `v0.2.5`, `0.2.5`, and `20260712.1` before signing the repository launcher binary. These files belong to commit A so the manifest's content commit contains the final App identity and signature; commit B must not invalidate that signature.

Run the tests again. They may remain RED only because final binding values are not yet present. Fix all mechanics/syntax failures before commit A.

Create commit A with the plan, authorization overlay, tests, generic runtime/launcher/frontend mechanics, and any non-self-referential governance setup. Commit message:

```text
feat(PFI): add v0.2.5 release identity mechanics
```

Record the full commit SHA as `release_content_commit`.

### Step 4: Bind the final identity to commit A

After commit A exists:

1. Confirm commit A contains `PFI/VERSION=v0.2.5`, plist `0.2.5/20260712.1`, and a valid ad-hoc launcher signature.
2. Calculate the frontend/backend hashes using the algorithm above from commit-A content plus the index manifest-block canonicalization.
3. Create `release_manifest.json` with the exact contract fields and `git_commit=<commit A>`.
4. Copy the exact JSON object into `index.html#pfi-release-manifest`.
5. Do not modify VERSION, plist, launcher source/binary, runtime API code, or generic gate code in commit B; otherwise create a new content commit and recalculate the binding.
6. Do not hard-code commit/hash values into shell logic or launchers; they must continue to consume the machine manifest.

Run the Python and Node tests until GREEN, plus:

```bash
node --check PFI/web/app/version.js
zsh -n PFI/StartPFI.command PFI/scripts/startPFI.sh PFI/scripts/pfiReleaseIdentity.sh
clang -Wall -Wextra -Werror -fsyntax-only PFI/macos/PFI_launcher.c
plutil -lint PFI/macos/PFI.app/Contents/Info.plist
```

### Step 5: Generate a durable verifier and evidence

Create `verify_stage1_phase11.py` with a `--candidate` commit-object mode and `--task-pack` override. It must verify:

- exact Roadmap/Task Pack SHA-256 and ZIP integrity/schema SHA;
- exact allowed changed paths for this Phase;
- schema-valid manifest/evidence;
- identity equality and hash recomputation;
- runtime endpoint through an ephemeral server;
- source and binary launcher contracts;
- RED and GREEN records in `terminal.log`;
- authorization overlay semantics;
- no Phase 1.2/1.3 claims, no human acceptance, no push/install/data/DB mutation claims;
- privacy scan has zero private values, credentials, absolute home paths, PIDs, or financial rows;
- evidence artifact hashes and changed-file inventory.

The evidence status is `candidate_pass`. It must distinguish:

- `release_content_commit` = commit A and manifest `git_commit`;
- `identity_binding_commit` = pending until commit B exists;
- `production_accepted=false`;
- `requires_final_stage12_human_acceptance=true`;
- `interim_transition_authorization=active`.

Evidence must explicitly list Phase 1.2, Phase 1.3, canonical install, push, 8501 direct release endpoint, data/DB, and final human acceptance as not performed.

### Step 6: Update only current governance surfaces

Append or update one Phase 1.1 record in the listed governance companions. Preserve historical records and immutable Stage 0 files. Record:

- current iteration `ITER-20260712-PFI-V025-S1-P11`;
- acceptance target `ACC-PFI-V025-S1-P11-RELEASE-IDENTITY`;
- Phase status `candidate_pass_pending_identity_binding_commit_attestation` before commit B;
- Stage 1 remains in progress; Stage 2 remains not started;
- product/production/final human acceptance remain false;
- model/formula/parameter behavior unchanged;
- no push or App installation.

Do not close the whole Stage 1 gap; Phase 1.2 and 1.3 remain required.

### Step 7: Create commit B and post-commit attestation

Run the complete working-tree verifier, tests, syntax checks, and `git diff --check`. Commit all remaining identity binding, evidence, and governance files with:

```text
docs(PFI): bind v0.2.5 stage 1 phase 1.1 identity
```

Record commit B as `identity_binding_commit` in an external immutable attestation under the repository git common directory:

```text
<git-common-dir>/codex-review/pfi-v025/stage_1/phase_1_1/<commit-B>/phase_1_1_attestation.json
```

The external attestation must include commit A, commit B, manifest/evidence SHA-256, exact changed paths, verifier result, `C0/I0/M0` only after review, no push/install, and no final human acceptance. Verify commit B with `verify_stage1_phase11.py --candidate <commit-B>`.

### Step 8: Independent review and completion gate

Dispatch an independent reviewer over the exact commit range from the Phase base `9380fdf4a500f48a2b15859044ab7926b4924391` through commit B. Review against this plan, Roadmap Stage 1 / Phase 1.1, Task Pack release schema/spec, and repository rules.

Critical/Important/Minor findings must all be remediated in scope and independently re-reviewed to `C0/I0/M0`. If remediation creates a new tracked commit, regenerate the identity binding according to the same A/B semantics or explicitly create a new release-content/binding pair; never leave manifest `git_commit` pointing at content it does not identify. Refresh the external attestation after the final commit.

The Phase is accepted by Codex only when all are true:

- focused Python and Node tests pass;
- syntax/plist/C compile checks pass;
- manifest schema/hash/identity matrix pass;
- commit-object verifier passes exact scope;
- independent re-review is `C0/I0/M0`;
- worktree is clean;
- no push, App install, live-port, financial-data, or DB mutation occurred;
- Stage 1 stays `in_progress`, with Phase 1.2 next.

## Rollback

- Before commit A: revert only uncommitted Phase paths.
- After commit A but before B: reset only by a new revert commit if history must be preserved; the branch is not pushed.
- After B: revert B, then A; remove only the external Phase attestation. Do not touch user data or installed Apps.
- A launch-time identity mismatch is fail-closed: keep the conflict page visible and do not reuse a marker whose hashes differ.

## Stop Conditions

Stop implementation scope expansion, not the overall authorized workflow, if any of these occurs:

- satisfying Phase 1.1 would require cache-control/Service Worker/bfcache work from Phase 1.2;
- satisfying Phase 1.1 would require real App installation/Finder execution from Phase 1.3;
- a required identity value has no existing source and would need fabrication;
- tests would need financial data, SQLite writes, or live 8501/8502 mutation;
- the launcher cannot establish the actual App bundle path without changing the historical dry-run contract.

When a stop condition appears, retain truthful candidate evidence, keep the fail-closed gate, and route the unresolved item to its named later task. Do not widen this run.
