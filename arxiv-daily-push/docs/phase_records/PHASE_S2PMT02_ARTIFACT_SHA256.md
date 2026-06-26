# PHASE S2PMT02 Artifact SHA256 Remediation

- phase: `S2PM`
- task_id: `S2PMT02-ARTIFACT-SHA256`
- parent_task_id: `S2PMT02`
- acceptance_id: `ACC-S2PMT02-ATOMIC-RECOVERY`
- timestamp: `2026-06-26T20:20:00+10:00`
- status: `local_validation_passed_pending_pr_ci`
- inherited_findings_targeted: `A-011`
- fact_level: `EXTRACTED`

## Scope

This remediation hardens the Stage 1 B1 report/email artifact manifest for
S2PMT02. `artifact_files.sha256` now records the SHA-256 of the written file
bytes, so auditors can verify each artifact with standard byte-level hash tools.
The prior canonical content hash is preserved separately as `content_hash` for
internal deterministic comparison.

## Evidence

- `arxiv-daily-push/src/arxiv_daily_push/stage1_b1_report.py`
- `arxiv-daily-push/tests/test_stage1_b1_report.py`
- `governance/run_manifests/ADP-S2PMT02-ARTIFACT-SHA256-20260626.json`
- `arxiv-daily-push/docs/governance/formula_registry.yaml` (`FORM-ADP-042`)

## Boundary

No production email was sent. No SMTP, scheduler, Release, public schema, DB
migration, queue mutation, ranking, source adapter, `CURRENT`, V7.1 baseline,
V7.2 contract, daily operation, or integrated production acceptance state was
changed.

## Validation

- `py_compile`: PASS
- focused `test_stage1_b1_report.py`: 6 OK
- full arxiv-daily-push unittest: 459 OK
- V7.2 validator: PASS
- ADP project governance: 0 errors / 0 warnings
- changed-only semantic governance: 0 errors / 0 warnings
- lean check-render: drift_count 0 reference_issue_count 0
- JSONL/CSV/manifest parse: OK
- semantic governance: targeted `FORM-ADP-042` fingerprint refreshed; full semantic extractor was interrupted after timeout during full-table AST parsing

## Remaining Risks

This records implementation remediation evidence for A-011 only. The inherited
V7.1 blocker ledger remains P0=8 / P1=37 until independent S2PMT07 review reruns
the required probes and explicitly closes findings. A-010 remains open within
the S2PMT02 inherited surface.
