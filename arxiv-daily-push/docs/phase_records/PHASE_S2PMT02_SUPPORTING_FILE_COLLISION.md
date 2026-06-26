# PHASE S2PMT02 Supporting File Collision Remediation

- phase: `S2PM`
- task_id: `S2PMT02-SUPPORTING-FILE-COLLISION`
- parent_task_id: `S2PMT02`
- acceptance_id: `ACC-S2PMT02-ATOMIC-RECOVERY`
- timestamp: `2026-06-26T19:30:00+10:00`
- status: `local_validation_passed_pending_pr_ci`
- inherited_findings_targeted: `A-014`
- fact_level: `EXTRACTED`

## Scope

This remediation hardens the Stage 1 runtime backup path for S2PMT02. Supporting
files are no longer copied to `files/<filename>`, which silently overwrote
different source files with the same basename. Each supporting file is copied to
`files/<source_path_hash>-<filename>`, and duplicate backup target paths fail
closed before writing a backup manifest.

## Evidence

- `arxiv-daily-push/src/arxiv_daily_push/stage1_runtime.py`
- `arxiv-daily-push/tests/test_stage1_runtime.py`
- `governance/run_manifests/ADP-S2PMT02-SUPPORTING-FILE-COLLISION-20260626.json`
- `arxiv-daily-push/docs/governance/formula_registry.yaml` (`FORM-ADP-043`)

## Boundary

No production backup or restore was executed. No SMTP, scheduler, Release,
public schema, DB migration, queue mutation, ranking, source adapter, `CURRENT`,
V7.1 baseline, V7.2 contract, daily operation, or integrated production
acceptance state was changed.

## Validation

- `py_compile`: PASS
- focused `test_stage1_runtime.py`: 11 OK
- full arxiv-daily-push unittest: 458 OK
- V7.2 validator: PASS
- ADP project governance: 0 errors / 0 warnings
- lean check-render: drift_count 0 reference_issue_count 0
- changed-only semantic governance: 0 errors / 0 warnings
- semantic governance: targeted `FORM-ADP-043` fingerprint refreshed; full semantic extractor not rerun because changed-only semantic governance is the local gate for this narrow run
- JSONL/YAML/CSV/manifest parse: OK
- `git diff --check`: PASS

## Remaining Risks

This records implementation remediation evidence for A-014 only. The inherited
V7.1 blocker ledger remains P0=8 / P1=37 until independent S2PMT07 review reruns
the required probes and explicitly closes findings. A-010 and A-011 remain open
within the S2PMT02 inherited surface.
