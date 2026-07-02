# IDS v0.1 BATCH-011-020 Upload Gate

- Batch ID: `IDS-V0_1-BATCH-011-020`
- Task ID: `IDS-V0_1-BATCH-011-020-UPLOAD-GATE`
- Stage range: `STAGE-011..STAGE-020`
- Acceptance range: `ACC-STAGE-011..ACC-STAGE-020`
- Gate checked at UTC: `2026-07-02T22:21:49Z`
- Target repository: `LinzeColin/CodexProject`
- Target branch: `main`
- IDS metadata raw root: `/Users/linzezhang/Downloads/IDS_MetaData`
- Review gate evidence: `BATCH011_020_REVIEW_GATE.md`
- Upload lock: `BATCH011_020_UPLOAD_LOCK.yaml`
- Current upload switch: `push_allowed=true`
- Decision: open a PR targeting `main`; No STAGE-021

## Goal

Upload the completed and reviewed local `STAGE-011..STAGE-020` batch to GitHub
`main` as one batch. This gate may push the batch branch, create a PR targeting
`main`, merge the PR, reinstall app entry launchers, and verify
GitHub/app/local governance parity. It does not start `STAGE-021` and does not
expand the sparse worktree.

## Local Gate Result

| Gate item | Result | Evidence |
|---|---|---|
| Ten-stage completion | Passed. `STAGE-011` through `STAGE-020` each have four completed phases in the batch lock. | `BATCH011_020_UPLOAD_LOCK.yaml` |
| Tenth-stage review | Passed. `BATCH011_020_REVIEW_GATE.md` records local review findings and fixes. | `BATCH011_020_REVIEW_GATE.md` |
| Acceptance status | Passed. `ACC-STAGE-011` through `ACC-STAGE-020` are `local_passed`. | `BATCH011_020_UPLOAD_LOCK.yaml` |
| Durable evidence files | Passed. Stage evidence refs and helper scripts are tracked under `KM_IDSystem/`; no raw database content is committed. | Stage evidence files; Stage005 validator |
| Owner render | Passed. `check-render --project KM_IDSystem` returned `drift_count=0` and `reference_issue_count=0`. | bundled Python `scripts/lean_governance.py check-render --project KM_IDSystem` |
| GitHub open PR/issue precheck | Passed. GitHub connector returned zero open PRs and zero open issues before creating this upload PR. | GitHub connector search |
| Remote main strategy | Passed. Branch and `origin/main` are diverged, so direct `HEAD:main` push is not allowed; merge-tree conflict scan returned no conflict markers. | `git rev-list --left-right --count origin/main...HEAD`; `git merge-tree` |
| app entry reinstall | Pending after GitHub merge. `scripts/install_app_entries.sh` was inspected and will rebuild/copy `.app` and `.command` launchers without reading raw metadata. | `KM_IDSystem/scripts/install_app_entries.sh` |
| IDS metadata raw data boundary | Passed. `/Users/linzezhang/Downloads/IDS_MetaData` remains a path-only read-only real-data source boundary; raw database content was not read, listed, scanned, hashed, copied, modified, deleted, moved, dumped, normalized, or committed. | `IDS_METADATA_RAW_DATA_BOUNDARY.md`; `BATCH011_020_UPLOAD_LOCK.yaml` |

## Remote Main Strategy

Current remote check before this upload gate:

- `origin/main` contains 83 commits not in this branch.
- this branch contains 41 batch commits not in `origin/main`.
- `origin/main`: `bdb0ce21f133f79f984f88602671769634b98999`
- local batch `HEAD`: `1656ac471c9cf286108184f181c808c7b3ddb357`
- merge base: `79b807fa93f591affc0fcb40237a463d2da99d64`

Therefore this run must not push `HEAD:main` directly. The safe upload strategy
is:

1. Push `codex/ids-v0-1-stages-001-010` to GitHub.
2. Open a PR targeting `main`.
3. Merge the PR if GitHub accepts the merge without conflict.
4. Reinstall app entries from the merged local tree.
5. Verify app entry paths, local branch, GitHub `main`, and owner records are
   consistent.
6. Verify no open PRs and no open issues remain.

## Validation Evidence Before Push

- GitHub precheck:
  - open PRs: `0`
  - open issues: `0`
- Stage005 governance regression:
  - RED failed as expected with 51 tests and 2 failures because this upload gate
    file did not exist and the upload-gate pending-merge state was not yet
    accepted.
  - GREEN after implementation passed: `Ran 51 tests ... OK`.
- Stage005 validator:
  - returned `valid=true` with no missing required files, no missing event IDs,
    no invalid JSONL lines, no forbidden changed paths, no unexpected changed
    paths, and all IDS metadata data-boundary checks true.
- Local validation already run before writing this gate:
  - Stage005 governance regression passed: `Ran 49 tests ... OK`.
  - Stage005 validator returned `valid=true`.
  - Full IDS v0.1 pursuing-goal unittest discover passed:
    `Ran 168 tests ... OK` after upload-gate coverage was added.
  - `check-render --project KM_IDSystem` returned `drift_count=0`.
  - `git diff --check` passed.
  - `events.jsonl` parsed with `events_jsonl_ok count=95`.
  - old underscored task-id scan returned no hits.
  - legacy pre-rename path added-line scan returned no hits.
  - semantic validate remains diagnostic-only in this sparse worktree: it exits
    1 with 29 known root-governance or registered-project missing-path errors
    and no `KM_IDSystem` semantic error.

## Remote Merge Evidence

- PR: `https://github.com/LinzeColin/CodexProject/pull/271`
- PR title: `IDS v0.1 STAGE-011..020 batch upload`
- PR head before merge: `85de9fd839a05e0bf4fc6ed06e2a92aed4326bbf`
- PR base before merge: `bdb0ce21f133f79f984f88602671769634b98999`
- GitHub merge SHA: `61fcb5295c6e0046059eba236c4cedbdaa2f2fed`
- Merge result: `merged=true`
- Post-merge open PRs in `LinzeColin/CodexProject`: `0`
- Post-merge open issues in `LinzeColin/CodexProject`: `0`
- Post-merge remote feature branch: deleted by GitHub after merge.
- App entry reinstall: passed.
  - `/Users/linzezhang/Downloads/IDS Industrial Data System.app`
  - `/Applications/IDS Industrial Data System.app`
  - `/Users/linzezhang/Downloads/IDS Industrial Data System.command`
  - `/Applications/IDS Industrial Data System.command`
- App launcher root: `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/KM_IDS/KM_IDSystem`
- Codesign verification: passed for both installed `.app` bundles.
- Verified at UTC: `2026-07-02T22:29:29Z`

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

If a later audit finds this upload invalid, revert the merged PR or apply a
targeted correction through GitHub main. Do not touch
`/Users/linzezhang/Downloads/IDS_MetaData`, runtime data, reports, outputs,
persisted manifests, evidence ledgers, audit logs, indexes, or app entries
unless the correction explicitly targets those installed launchers. `STAGE-021`
must remain a separate next run.
