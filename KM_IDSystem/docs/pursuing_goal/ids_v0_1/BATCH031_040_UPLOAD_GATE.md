# IDS v0.1 BATCH-031-040 Upload Gate

- Batch ID: `IDS-V0_1-BATCH-031-040`
- Task ID: `IDS-V0_1-BATCH-031-040-UPLOAD-GATE`
- Stage range: `STAGE-031..STAGE-040`
- Acceptance range: `ACC-STAGE-031..ACC-STAGE-040`
- Gate opened at UTC: `2026-07-14T11:26:17Z`
- Target repository: `LinzeColin/CodexProject`
- Target branch: `main`
- Review evidence: `BATCH031_040_REVIEW_GATE.md`
- Upload lock: `BATCH031_040_UPLOAD_LOCK.yaml`
- Current upload switch: `push_allowed=true`
- Decision: local gate passed; PR targeting `main` is authorized; merge and app evidence remain pending

## Goal

Upload the completed, independently reviewed, and repaired `STAGE-031..STAGE-040`
batch through one GitHub PR to `main`. After merge, reinstall the app entries and
verify GitHub/app/local parity. No STAGE-041 work is authorized by this gate.

## Local Gate Result

| Gate item | Result | Evidence |
|---|---|---|
| Ten-stage completion | Passed. All ten Stage records remain `completed_reviewed_local`. | `BATCH031_040_UPLOAD_LOCK.yaml` |
| Independent batch review | Passed with one Critical and two Important findings repaired. | `BATCH031_040_REVIEW_GATE.md` |
| Source and Git-index binding | Passed in the immediately preceding review commit. | `check_batch031_040_review.py`; review contract |
| GitHub open PR/issue precheck | Passed. Open PRs `0`; open issues `0`. | `gh pr list`; `gh issue list` |
| Remote main strategy | Passed. `origin/main` is 862 commits ahead and this branch is 52 commits ahead; no `KM_IDSystem` commits exist in `HEAD..origin/main`. Direct pre-merge `HEAD:main` push is prohibited. | `git rev-list`; project-scoped `git log` |
| IDS metadata boundary | Passed. `/Users/linzezhang/Downloads/IDS_MetaData` remains path-only and read-only. Its raw database content was not read, listed, opened, hashed, copied, moved, deleted, modified, dumped, scanned, or normalized. | `IDS_METADATA_RAW_DATA_BOUNDARY.md` |
| Real-data-only policy | Passed. No fake IDS business data or fabricated evidence was introduced. | Upload lock; changed files |

## Remote Strategy

Pre-upload repository identity:

- local batch head: `ac07280b03c12a4940491cb595f8a3c6b9d9acc6`
- `origin/main`: `87825b8429f70cc7c1bc734fcd868c554e14b4ad`
- merge base: `387f2bdd1e4cb06d3fced781417f057f854c2901`
- divergence (`origin/main...HEAD`): `862 52`
- precheck open PRs: `0`
- precheck open issues: `0`

The authorized sequence is:

1. Commit only BATCH031-040 upload-gate files; preserve owner dirty files.
2. Push `codex/ids-v0-1-stages-001-010`.
3. Create one ready PR targeting `main` and verify mergeability.
4. Merge the PR and delete its remote feature branch.
5. Reinstall `.app` and `.command` entries from this worktree.
6. Record the actual PR URL, merge SHA, app verification, and zero open PR/issue counts.
7. Publish the terminal evidence as a targeted `main` evidence commit.

## Validation Evidence Before Merge

- TDD RED: three focused Stage005 tests failed because this file and the two
  BATCH031-040 upload states did not exist.
- GREEN implementation adds only the pending and terminal batch state contracts;
  actual PR and merge values are not recorded before GitHub supplies them.
- Stage005 governance regression: `154/154` passed.
- Stage031-039 compatibility: `254/254` passed.
- Stage040 compatibility: `55/55` passed.
- Full IDS v0.1 discovery: `732/732` passed.
- Events JSONL: `194` records, `0` duplicate event IDs, `0` JSON errors.
- Owner render: `drift_count=0`, `reference_issue_count=0`.
- Changed-only governance: `errors=0`, `warnings=0`.
- `git diff --check`: passed.
- Direct Stage005 validator remains intentionally fail-closed only on the four
  preserved owner dirty paths; the regression suite verifies the governed state.
- The independent batch review remains the source-integrity gate for this upload.

## Pending Remote And App Evidence

- PR URL: pending GitHub creation
- PR merge SHA: pending GitHub merge
- post-merge open PRs: pending
- post-merge open issues: pending
- app entry reinstall: pending until the PR is merged
- app launcher root: `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/KM_IDS/KM_IDSystem`
- required app paths:
  - `/Users/linzezhang/Downloads/IDS Industrial Data System.app`
  - `/Applications/IDS Industrial Data System.app`
  - `/Users/linzezhang/Downloads/IDS Industrial Data System.command`
  - `/Applications/IDS Industrial Data System.command`

## Stop Conditions

- Any focused or full regression fails for a project-scoped reason.
- GitHub reports a content conflict or an unresolved open PR/issue.
- Staging includes owner dirty paths, root `.DS_Store`, runtime output, or raw data.
- App reinstall fails or a launcher points outside this `KM_IDS/KM_IDSystem` worktree.
- Any action reads or mutates `/Users/linzezhang/Downloads/IDS_MetaData` content.
- Any action expands sparse checkout, touches unrelated projects, or starts STAGE-041.

## Rollback

Before merge, revert only the upload-gate governance commit. After merge, use a
targeted GitHub revert or corrective evidence commit. Do not touch raw metadata,
runtime data, reports, outputs, databases, indexes, or unrelated app state.
