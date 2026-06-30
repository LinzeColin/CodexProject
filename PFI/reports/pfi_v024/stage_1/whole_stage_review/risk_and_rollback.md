# PFI v0.2.4 Stage 1 Whole-Stage Review Risk and Rollback

## Scope

This review adds only the Stage 1 whole-stage review contract, evidence, and
status records. It does not change business UI, app bundle, launcher, or data
logic.

## Risks

- Status files could over-claim GitHub main upload or Stage 2 entry.
- Evidence could drift from the current shell artifact hashes.
- Review findings could be recorded without tests that enforce them.

## Controls

- Contract tests assert Stage 2 is not started and GitHub main is not uploaded.
- Evidence stores current `shell.js` and `version.js` SHA256 hashes.
- The changed-files audit is kept in the review evidence directory.

## Rollback

Revert this review commit. That removes:

- `PFI/docs/pfi_v024/STAGE1_WHOLE_STAGE_REVIEW.md`
- `PFI/tests/test_v024_stage1_whole_review_contract.py`
- `PFI/reports/pfi_v024/stage_1/whole_stage_review/*`
- Stage 1 review status updates in README, HANDOFF, CHANGELOG, and root record files.
