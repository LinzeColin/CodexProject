# Memory Atlas v1.2 R4 Proposal Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a rendered, local-only human approval workflow that performs a real
structured proposal apply, fixed validation and automatic/manual rollback without
allowing raw, canonical-repository, path or argv injection.

**Architecture:** Add a focused proposal workflow service beside the R3 command
bridge. It reads server-side apply-ready bundles, issues one-use review tokens, applies
full-file replacements inside the installer source copy under a fixed target map, and
stores durable transaction snapshots under Application Support. The existing six
commands remain unchanged; a dedicated same-origin proposal-action endpoint handles
only token-bound approve/apply and rollback actions.

**Tech Stack:** Python 3 standard library, React 19, TypeScript, Vite, Playwright,
`unittest`.

## Global Constraints

- Complete only `R4_PROPOSAL_APPROVAL_APPLY_ROLLBACK_WORKFLOW` in this run.
- Work in the canonical local `main`; create no branch, PR, merge or rebase.
- No GitHub push, app reinstall or Cloudflare deployment before R8.
- R3 command IDs remain exactly six; hosted static remains read-only.
- Browser requests cannot supply target paths, file content, argv, validation commands,
  environment values or URLs.
- Raw/private/credential paths and the canonical checkout are never writable.
- Every production behavior is introduced by a failing test first.
- Acceptance must exercise rendered/runtime behavior at `1470x661`, `1440x900` and
  `390x844`.

---

### Task 1: Secure Bundle And Transaction Engine

**Files:**

- Create: `scripts/memory_atlas_proposal_workflow.py`
- Create: `tests/test_memory_atlas_proposal_apply.py`
- Modify: `scripts/build_memory_atlas_proposal_apply.py`
- Modify: `scripts/atlasctl.py`

**Interfaces:**

- Produces `ProposalWorkflow(context).review() -> dict`.
- Produces `ProposalWorkflow(context).approve_and_apply(...) -> dict`.
- Produces `ProposalWorkflow(context).rollback(...) -> dict`.
- Uses the installer-shaped `CommandContext` paths but never accepts paths from HTTP.

- [x] Write failing tests for schema identity, proposal ID format, bundle regular-file
  requirement, expiry, five Chinese narrator fields, operation/content size and fixed
  validator IDs.
- [x] Run `python3 -m unittest tests.test_memory_atlas_proposal_apply -q` and confirm
  failure because the workflow module does not exist.
- [x] Add failing tests for absolute/traversal/symlink targets, forbidden raw/private/
  credential fragments, unsupported target-type roots and expected SHA mismatch.
- [x] Implement the bundle parser and target policy with resolved-path containment,
  regular-file checks and no caller-supplied path fallback.
- [x] Add failing tests proving successful apply changes bytes, writes a durable
  transaction, and manual rollback restores the exact original bytes.
- [x] Add failing tests proving invalid JSON validation restores every target and
  records `rollback_or_needs_revision` before returning.
- [x] Implement atomic full-file replacement, durable snapshots, `utf8_nonempty` and
  `json_document` fixed validators, post-restore hash verification and metadata-only
  audit.
- [x] Add a failing test proving replayed/stale review and rollback tokens fail closed,
  then implement token TTL, bundle digest binding and one-use consumption.
- [x] Add a failing test proving direct non-dry-run `atlasctl apply --proposal sample`
  cannot write, then harden the historical builder/CLI to require the R4 UI workflow
  for real writes while preserving its historical dry-run report.
- [x] Run the focused Python test until all cases pass.

### Task 2: Same-Origin Proposal Endpoint And Shared Operation Lock

**Files:**

- Modify: `scripts/memory_atlas_command_bridge.py`
- Modify: `scripts/memory_atlas_runtime_server.py`
- Modify: `tests/test_memory_atlas_app_runtime.py`

**Interfaces:**

- `view_pending_proposals` returns sanitized `proposal_review` data from the workflow.
- `CommandBridge.execute_proposal_action(payload)` shares the R3 command lock.
- Runtime endpoint: `POST /__memory_atlas_proposal_action`.

- [x] Add failing bridge tests that the command registry is still the exact R3 six,
  proposal review is read-only and no operation content is returned.
- [x] Add failing server tests for exact approve/apply and rollback bodies, remote
  Origin, unknown/extra keys, wrong confirmation and oversized body.
- [x] Add a failing concurrency test proving a proposal action cannot run while an R3
  command holds the lock and vice versa.
- [x] Implement the workflow integration and proposal endpoint using the existing
  loopback/Host/Origin/fetch-site/no-CORS checks.
- [x] Ensure transport errors return bounded Chinese messages and never expose tokens,
  file content, absolute paths or exceptions.
- [x] Run `python3 -m unittest tests.test_memory_atlas_app_runtime tests.test_memory_atlas_proposal_apply -q` until green.

### Task 3: Rendered Approval Workspace

**Files:**

- Modify: `apps/memory-atlas/src/App.tsx`
- Modify: `apps/memory-atlas/src/styles.css`
- Create: `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_proposal_e2e.cjs`
- Modify: `apps/memory-atlas/package.json`

**Interfaces:**

- The existing `view_pending_proposals` execution result opens a modal proposal review.
- Apply body is constructed only from server-returned proposal ID/token plus the fixed
  confirmation phrase.
- Successful apply exposes a server-returned transaction ID/rollback token for a
  separately acknowledged rollback action.

- [x] Create the Playwright validator first with a temporary installer-shaped fixture
  containing one successful bundle, one validation-failure bundle and one raw-target
  bundle.
- [x] Run it and confirm failure because the proposal modal and endpoint are absent.
- [x] Add the modal with a proposal list, apply-ready/review-only labels, exact target
  scope, risk/expiry, five Chinese narrator sections and fixed validation labels.
- [x] Keep apply disabled until an explicit acknowledgement is checked; show state
  history and validation outcome after the server response.
- [x] Add a second explicit acknowledgement and action for manual rollback.
- [x] Keep static mode read-only: no proposal endpoint fetch and exact local handoff
  `http://127.0.0.1:4177`.
- [x] Exercise modal layout/scroll/no-overflow at all three required viewports; execute
  unauthorized, authorized apply, manual rollback and automatic rollback paths through
  the rendered UI.
- [x] Assert fixture target hashes, raw sentinel hashes, transaction audit metadata and
  static request counts from Node after browser execution.

### Task 4: Regression, Independent Review And R4 Closeout

**Files:**

- Create: `docs/remediation/memory_atlas_v1_2/R4_PROPOSAL_APPROVAL_APPLY_ROLLBACK_WORKFLOW.md`
- Create: `机器治理/证据与日志/remediation/v1_2_r4/status.json`
- Create: `机器治理/证据与日志/remediation/v1_2_r4/requirements_gap_delta.csv`
- Modify: `docs/remediation/memory_atlas_v1_2/HANDOFF.md`
- Modify: `功能清单.md`
- Modify: `模型参数文件.md`
- Modify: `开发记录.md`
- Modify: `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`
- Modify: `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`
- Modify: `CHANGELOG.md`

- [x] Run focused Python tests, `npm run lint`, production build and
  `validate:v1.2-proposal-e2e`.
- [x] Re-run `validate:v1.2-command-workflows`, `validate:v1.2-home-multiviewport`,
  `validate:stage7-visual` and privacy guard.
- [x] Obtain an independent security/correctness review; reproduce every High/Medium
  finding with a failing test before fixing and re-review until none remain.
- [x] Promote only `S13-AC02` and `S13-AC04` from PARTIAL to VERIFIED; keep
  `S13-AC01`, `S13-AC03`, `S13-AC05` VERIFIED with stronger evidence. The expected
  aggregate is `VERIFIED 40 / PARTIAL 11 / FAILED 5 / NOT_VERIFIED 2`.
- [x] Record that online/installed app remain unchanged and release status remains
  `FAIL_REMEDIATION_REQUIRED`.
- [ ] Commit R4 locally, remove only reproducible frontend caches, verify clean
  worktree/ports/branch/stash and stop before R5.
