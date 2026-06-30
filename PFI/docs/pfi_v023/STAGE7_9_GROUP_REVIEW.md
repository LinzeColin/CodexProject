# PFI v0.2.3 Stage 7-9 Group Review

## Scope

This group review covers only Stage 7, Stage 8, and Stage 9.

It does not start Stage 10-11, does not claim final closeout, and does not upload to GitHub main.

## Source Basis

- Repo docs: `STAGE7_REPORTS.md`, `STAGE8_DATA_SOURCE_GATE.md`, `STAGE9_VISUAL_FEEDBACK.md`
- Repo evidence: `PFI/reports/pfi_v023/stage_7`, `stage_8`, `stage_9`
- Real localhost/browser evidence: `PFI/reports/pfi_v023/group_reviews/stage_7_9/browser_audit.json`
- Current Downloads taskpack status: missing from `/Users/linzezhang/Downloads`; no data was fabricated to replace it.

## Findings And Fixes

1. Reports page overclaimed project-level review status with project review gate text and `20/20` style completion copy.
2. Stage 7 report blockers were not visible as the primary report center state.
3. Stage 9 settings showed feedback features, but the settings feedback console did not expose notification feedback as a first-class visible lane.

Fixes:

- `shell.js` now reapplies a Stage 7 report center contract after legacy Stage 6 dashboard data, so blocked and partial reports are visible and old project-closeout copy is not shown in the reports workspace.
- `index.html` now includes a `通知反馈` lane in the settings feedback console.
- Regression coverage now requires Stage 7-9 group evidence, browser audit cleanliness, Stage 7 blocked report visibility, Stage 8 source visibility, Stage 9 feedback visibility, and no feedback console on business pages.

## Verification Snapshot

- Stage 7-9 target tests: pass
- `node --check PFI/web/app/shell.js`: pass
- Real browser audit: pass, findings empty
- Full validation results are recorded in `PFI/reports/pfi_v023/group_reviews/stage_7_9/evidence.json`.

## Remaining

- Stage 10-11 group review
- Overall v0.2.3 project review
- GitHub main upload and backup after final acceptance
