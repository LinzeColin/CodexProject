# IDS v0.1 BATCH-021-030 Upload Gate

- Batch ID: `IDS-V0_1-BATCH-021-030`
- Task ID: `IDS-V0_1-BATCH-021-030-UPLOAD-GATE`
- Stage range: `STAGE-021..STAGE-030`
- Acceptance range: `ACC-STAGE-021..ACC-STAGE-030`
- Gate checked at UTC: `2026-07-03T08:06:10Z`
- Target repository: `LinzeColin/CodexProject`
- Target branch: `main`
- IDS metadata raw root: `/Users/linzezhang/Downloads/IDS_MetaData`
- Review gate evidence: `BATCH021_030_REVIEW_GATE.md`
- Upload lock: `BATCH021_030_UPLOAD_LOCK.yaml`
- Current upload switch: `push_allowed=true`
- Decision: open a PR targeting `main`; No STAGE-031

## Goal

Upload the completed and reviewed local `STAGE-021..STAGE-030` batch to GitHub
`main` as one batch. This gate may push the batch branch, use the existing PR
targeting `main`, merge the PR, reinstall app entry launchers, and verify
GitHub/app/local governance parity. It does not start `STAGE-031` and does not
expand the sparse worktree.

## Local Gate Result

| Gate item | Result | Evidence |
|---|---|---|
| Ten-stage completion | Passed. `STAGE-021` through `STAGE-030` each have four completed phases in the batch lock. | `BATCH021_030_UPLOAD_LOCK.yaml` |
| Tenth-stage review | Passed. `BATCH021_030_REVIEW_GATE.md` records local review findings and fixes. | `BATCH021_030_REVIEW_GATE.md` |
| Acceptance status | Passed. `ACC-STAGE-021` through `ACC-STAGE-030` are `local_passed`. | `BATCH021_030_UPLOAD_LOCK.yaml` |
| Durable evidence files | Passed. Stage evidence refs and helper scripts are tracked under `KM_IDSystem/`; no raw database content is committed. | Stage evidence files; Stage005 validator |
| Owner render | Passed. `check-render --project KM_IDSystem` returned `drift_count=0` and `reference_issue_count=0` before this gate. | `scripts/lean_governance.py check-render --project KM_IDSystem` |
| GitHub open PR/issue precheck | Passed. The pre-PR GitHub issue API and GitHub connector check found zero open issues and zero open PRs before creating this upload PR. | GitHub public API; GitHub connector search |
| Remote main strategy | Passed. Branch and `origin/main` are diverged, so direct `HEAD:main` push is not allowed. GitHub reports PR #272 as mergeable with `mergeable_state=unstable`, not a content conflict. | `git rev-list --left-right --count origin/main...HEAD`; GitHub pull API |
| app entry reinstall | Pending after GitHub merge. `scripts/install_app_entries.sh` will rebuild/copy `.app` and `.command` launchers without reading raw metadata. | `KM_IDSystem/scripts/install_app_entries.sh` |
| IDS metadata raw data boundary | Passed. `/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only read-only real-data source boundary; raw database content was not read, listed, scanned, hashed, copied, modified, deleted, moved, dumped, normalized, or committed. | `IDS_METADATA_RAW_DATA_BOUNDARY.md`; `BATCH021_030_UPLOAD_LOCK.yaml` |

## Remote Main Strategy

Current remote check before this upload gate:

- `origin/main` contains 28 commits not in this branch.
- this branch contains 41 batch commits not in `origin/main`.
- `origin/main`: `38c6975da8aca6adcfc82d937502a597da3c5871`
- local batch `HEAD`: `6fd50c189efc91df60b392132b71b6e667f860c2`
- merge base: `55bff8ed9ddd20cf6e375c95ab44d21602121409`
- PR: `https://github.com/LinzeColin/CodexProject/pull/272`
- PR mergeability before this evidence update: `mergeable=true`, `mergeable_state=unstable`

Therefore this run must not push `HEAD:main` directly. The safe upload strategy
is:

1. Push `codex/ids-v0-1-stages-001-010` to GitHub.
2. Use PR #272 targeting `main`.
3. Merge the PR if GitHub accepts the merge without conflict.
4. Reinstall app entries from the merged local tree.
5. Verify app entry paths, local branch, GitHub `main`, and owner records are
   consistent.
6. Verify no open PRs and no open issues remain.

## Validation Evidence Before Merge

- GitHub precheck:
  - open PRs before creating PR #272: `0`
  - open issues before creating PR #272: `0`
- PR creation:
  - PR #272: `https://github.com/LinzeColin/CodexProject/pull/272`
  - created as ready for review, not draft.
  - initial head SHA: `6fd50c189efc91df60b392132b71b6e667f860c2`
- Local validation already run before writing this gate:
  - Full IDS v0.1 pursuing-goal unittest discover passed:
    `Ran 355 tests ... OK`.
  - `check-render --project KM_IDSystem` returned `drift_count=0` and
    `reference_issue_count=0`.
  - `gh` is not installed locally, so GitHub validation used the public GitHub
    API and connector instead of installing new tooling.
- Stage005 governance regression for this gate:
  - RED failed as expected because this upload gate file did not exist and the
    upload-gate pending-merge state was not yet accepted.
  - GREEN after implementation passed: `Ran 97 tests ... OK`.
- Stage005 validator:
  - returned `valid=true` with no missing required files, no missing event IDs,
    no invalid JSONL lines, no forbidden changed paths, no unexpected changed
    paths, and all IDS metadata data-boundary checks true.
- Full IDS v0.1 pursuing-goal unittest discover:
  - returned `Ran 357 tests ... OK` after upload-gate compatibility coverage
    was added.
- Events JSONL parse:
  - returned `events_jsonl_ok count=139 duplicate_count=0`.

## Remote Merge Evidence

Pending. This section must be updated after the PR is merged and app entry
reinstall is verified.

## Stop Conditions

- Any focused test or validator fails for a product-scoped reason.
- `check-render` reports drift.
- changed scope escapes `KM_IDSystem/` or allowed root governance paths.
- GitHub reports open PRs/issues that must be resolved before upload.
- PR creation or merge fails.
- app entry reinstall fails or installed launchers do not point at this
  `KM_IDS/KM_IDSystem` worktree.
- The upload requires expanding Alpha, PFI, EEI, KMFA, Memory Atlas, Serenity,
  or other unrelated project directories.
- Any step requires reading, listing, hashing, opening, copying, moving,
  deleting, modifying, dumping, scanning, normalizing, or committing
  `/Users/linzezhang/Downloads/IDS_MetaData` raw database content.

## Rollback

If this gate fails before GitHub upload, revert this gate commit and leave
`BATCH021_030_UPLOAD_LOCK.yaml` at the prior reviewed no-upload state. If PR
#272 cannot be merged, close it or leave an explicit blocker; do not start
`STAGE-031` while upload is unresolved.
