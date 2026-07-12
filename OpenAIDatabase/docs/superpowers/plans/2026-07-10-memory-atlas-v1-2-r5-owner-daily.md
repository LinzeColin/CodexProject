# Memory Atlas v1.2 R5 Owner Daily Implementation Plan

> **For agentic workers:** Execute task-by-task with test-first checkpoints. This plan
> is bounded to R5 and inherits the approved R0-R8 remediation contract.

**Goal:** Deliver one real local Owner Daily product entry that sequentially executes
the fixed eight no-write maintenance checks, explains partial failure in Chinese and
retries only the failed fixed step.

**Architecture:** Add one shared Python runner consumed by `atlasctl.py` and a dedicated
same-origin loopback endpoint. Keep the R3 registry at exactly six commands. Add a
separate Home maintenance band and modal result workspace that presents conclusions
before collapsed machine details. The browser can send only `run` or one allowlisted
retry `step_id`.

**Tech Stack:** Python 3 standard library, React 19, TypeScript, Vite, Playwright,
`unittest`.

## Global Constraints

- Complete only `R5_OWNER_DAILY_PRODUCT_ENTRY` in this run.
- Work on canonical local `main`; create no branch, PR, merge or rebase.
- No GitHub push, app reinstall or Cloudflare deployment before R8.
- R3 command IDs remain exactly six; R4 proposal behavior remains unchanged.
- Hosted static remains read-only and emits zero Owner Daily POSTs.
- Browser requests cannot supply argv, paths, environment, URLs or arbitrary commands.
- Every child is fixed, dry-run, sequential and bounded; failures do not stop later
  steps.
- Acceptance must exercise rendered/runtime behavior at `1470x661`, `1440x900` and
  `390x844`.
- Release status remains `FAIL_REMEDIATION_REQUIRED` after R5.

---

### Task 1: Shared Fixed Eight-Step Runner

**Files:**

- Create: `scripts/memory_atlas_owner_daily.py`
- Create: `tests/test_memory_atlas_owner_daily.py`
- Modify: `scripts/atlasctl.py`
- Modify: `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s14_p1.cjs`

**Interfaces:**

- `owner_daily_profile_contract(python_executable=...) -> dict`
- `OwnerDailyRunner(context).run() -> dict`
- `OwnerDailyRunner(context).retry(step_id) -> dict`
- CLI: `atlasctl.py run --profile owner-daily --dry-run [--step FIXED_ID]`

- [ ] Write failing tests for exact ordered step IDs, immutable relative dry-run argv,
  aggregate safety and historical S14 compatibility fields.
- [ ] Run `python3 -m unittest tests.test_memory_atlas_owner_daily -q` and confirm the
  missing module/behavior fails.
- [ ] Add failing tests for eight-step PASS, continue-after-failure PARTIAL_FAILURE and
  one-step retry that invokes no other child.
- [ ] Add failing tests for unknown retry ID, malformed JSON, unsafe success payload,
  timeout and output-size limits.
- [ ] Implement the shared registry, scrubbed child environment, fixed process runner,
  JSON/safety validation, allowlisted metric extraction and bounded Chinese results.
- [ ] Delegate the historical `atlasctl.py` profile contract to the shared module and
  execute the runner for dry-run while keeping non-dry-run fail-closed.
- [ ] Upgrade the S14 P1 validator from plan-only assertions to eight real step results,
  aggregate safety and compatibility fields.
- [ ] Run focused Python and S14 tests until green.

### Task 2: Dedicated Endpoint And Shared Lock

**Files:**

- Modify: `scripts/memory_atlas_command_bridge.py`
- Modify: `scripts/memory_atlas_runtime_server.py`
- Modify: `tests/test_memory_atlas_app_runtime.py`

**Interfaces:**

- `CommandBridge.execute_owner_daily(payload) -> dict`
- Runtime endpoint: `POST /__memory_atlas_owner_daily`
- Exact bodies: `{"action":"run"}` or
  `{"action":"retry","step_id":"FIXED_ID"}`

- [ ] Add failing bridge tests for exact run/retry bodies, unknown/extra keys and
  bounded result/error behavior.
- [ ] Add a failing concurrency test proving R3, R4 and R5 use the same operation lock.
- [ ] Add failing runtime tests for API advertisement, exact endpoint body, remote
  Origin, unsupported fetch-site, non-JSON, oversized body and busy HTTP 409.
- [ ] Implement injectable Owner Daily runner integration and metadata-only local audit
  without changing the six-command registry.
- [ ] Implement the dedicated endpoint with existing loopback transport controls and
  bounded Chinese errors.
- [ ] Run `python3 -m unittest tests.test_memory_atlas_owner_daily tests.test_memory_atlas_app_runtime -q` until green.

### Task 3: Rendered Owner Daily Workspace

**Files:**

- Modify: `apps/memory-atlas/src/App.tsx`
- Modify: `apps/memory-atlas/src/styles.css`
- Create: `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_owner_daily_e2e.cjs`
- Modify: `apps/memory-atlas/package.json`

**Interfaces:**

- Home band: `[data-r5-owner-daily-entry]`
- Modal: `[data-r5-owner-daily-workspace]`
- Browser POSTs only exact server-known run/retry bodies.

- [ ] Create the Playwright validator first with a temporary installer-shaped fixture
  whose fixed `audit` step fails once and passes on retry.
- [ ] Run it and confirm failure because the product entry and endpoint are absent.
- [ ] Extend runtime state typing with the exact Owner Daily API version and availability
  flag; do not change the six R3 command IDs.
- [ ] Add the separate maintenance band, explicit no-write start action and a modal with
  Chinese conclusion/counts before the ordered step list.
- [ ] Add actionable failure text, fixed retry controls and UI merge/recalculation of a
  one-step retry result.
- [ ] Keep invocation/duration in collapsed details; never render raw child stdout or
  absolute paths.
- [ ] Keep static mode non-executable with zero POSTs and exact local handoff
  `http://127.0.0.1:4177`.
- [ ] Prove first run `7/1`, retry only `audit`, merged result `8/0`, unchanged source/
  runtime hashes and metadata-only audit.
- [ ] Verify modal keyboard reachability, no overlap and no horizontal overflow at all
  three required viewports.

### Task 4: Regression, Independent Review And R5 Closeout

**Files:**

- Create: `docs/remediation/memory_atlas_v1_2/R5_OWNER_DAILY_PRODUCT_ENTRY.md`
- Create: `机器治理/证据与日志/remediation/v1_2_r5/status.json`
- Create: `机器治理/证据与日志/remediation/v1_2_r5/requirements_gap_delta.csv`
- Modify: `docs/remediation/memory_atlas_v1_2/HANDOFF.md`
- Modify: `功能清单.md`
- Modify: `模型参数文件.md`
- Modify: `开发记录.md`
- Modify: `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`
- Modify: `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`
- Modify: `CHANGELOG.md`

- [ ] Run real canonical `owner-daily --dry-run` with before/after Git and source hash
  evidence and confirm eight bounded no-write results.
- [ ] Run focused Python tests, old S14 validator, `npm run lint`, production build and
  `npm run validate:v1.2-owner-daily-e2e`.
- [ ] Re-run R3 command workflows, R4 proposal E2E, Home multiviewport, Stage 7 visual,
  launcher/runtime tests and privacy guard.
- [ ] Obtain an independent security/correctness/UI review; reproduce every High/Medium
  finding with a failing test before fixing and re-review until none remain.
- [ ] Promote only `S14-AC04` from PARTIAL to VERIFIED; keep `S14-AC01` VERIFIED with
  stronger evidence. Expected aggregate: `VERIFIED 41 / PARTIAL 10 / FAILED 5 /
  NOT_VERIFIED 2`.
- [ ] Record online/installed app unchanged and release status
  `FAIL_REMEDIATION_REQUIRED`.
- [ ] Commit R5 locally, remove only reproducible frontend caches, verify clean
  worktree/ports/branch/stash and stop before R6.
