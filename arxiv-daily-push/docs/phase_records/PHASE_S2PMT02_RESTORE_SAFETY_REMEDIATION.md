# PHASE S2PMT02 Restore Safety Remediation

- phase: `S2PM`
- task_id: `S2PMT02-RESTORE-SAFETY`
- parent_task_id: `S2PMT02`
- acceptance_id: `ACC-S2PMT02-ATOMIC-RECOVERY`
- timestamp: `2026-06-26T18:45:00+10:00`
- status: `local_validation_passed_pending_pr_ci`
- inherited_findings_targeted: `A-001`, `A-002`
- fact_level: `EXTRACTED`

## Scope

This remediation hardens the existing Stage 1 runtime restore path that is part
of the S2PMT02 atomic backup/restore surface. It adds a backup-root constrained
manifest database path resolver and changes restore execution to copy the backup
database into a same-directory temporary file, fsync it, verify SHA256 and
SQLite readiness, pre-back up any existing target database, then publish with
`os.replace`.

## Evidence

- `arxiv-daily-push/src/arxiv_daily_push/stage1_runtime.py`
- `arxiv-daily-push/tests/test_stage1_runtime.py`
- `governance/run_manifests/ADP-S2PMT02-RESTORE-SAFETY-REMEDIATION-20260626.json`
- `arxiv-daily-push/docs/governance/formula_registry.yaml` (`FORM-ADP-043`)

## Boundary

No production restore was executed. No SMTP, scheduler, Release, public schema,
DB migration, queue mutation, ranking, source adapter, `CURRENT`, V7.1 baseline,
V7.2 contract, daily operation, or integrated production acceptance state was
changed.

## Validation

- `py_compile`: PASS
- focused `test_stage1_runtime.py`: 10 OK
- full arxiv-daily-push unittest: 457 OK
- V7.2 validator: PASS
- ADP project governance: 0 errors / 0 warnings
- lean check-render: drift_count 0 reference_issue_count 0
- changed-only semantic governance: 0 errors / 0 warnings
- semantic governance: targeted `FORM-ADP-043` fingerprint refreshed; full semantic extractor was interrupted after timeout during full-table AST parsing
- JSONL/YAML/CSV/manifest parse: OK
- `git diff --check`: PASS

## Remaining Risks

This records implementation remediation evidence for A-001 and A-002 only. The
inherited V7.1 blocker ledger remains P0=8 / P1=37 until independent S2PMT07
review reruns the required probes and explicitly closes findings.
