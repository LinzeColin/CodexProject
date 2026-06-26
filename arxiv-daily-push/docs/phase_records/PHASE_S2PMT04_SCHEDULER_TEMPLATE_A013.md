# PHASE S2PMT04 SCHEDULER TEMPLATE A013

## Summary

- phase: `S2PM`
- task_id: `S2PMT04-SCHEDULER-TEMPLATE-A013`
- parent_task_id: `S2PMT04`
- acceptance_id: `ACC-S2PMT04-LIFECYCLE`
- inherited_finding: `A-013`
- model_id: `MOD-ADP-041`
- formula_id: `FORM-ADP-043`
- status: local validation passed
- V7.2 contract: `ADP-PRODUCT-CONTRACT-V7.2`

This run hardens the Stage 1 scheduler dry-run template path for inherited audit finding A-013. The macOS launchd tick template is now generated with `plistlib` as a parseable XML plist, stores `WorkingDirectory` and `PYTHONPATH` as structured fields, and uses per-argument `ProgramArguments` instead of a `/bin/sh -lc` command string.

## Scope

- Replace handwritten macOS launchd XML in Stage 1 scheduler dry-run templates with `plistlib` generation.
- Preserve scheduler reports as template-only: `dry_run_only=true`, `applied=false`, `real_scheduler_install_allowed=false`.
- Add regression coverage for paths containing spaces, Chinese characters, semicolons, and `&`.
- Verify the generated plist parses with `plistlib` and preserves full path arguments.

## Non Scope

No real scheduler install, no launchd bootstrap, no SMTP send, no Release upload, no production restore, no public schema change, no DB migration, no production queue mutation, no ranking change, no source adapter change, no workflow enforcement change, no CURRENT pointer change, no V7.1/V7.2 contract-file edit, no inherited P0/P1 closure claim, no integrated production acceptance, and no daily-operation enablement.

## Evidence

- `arxiv-daily-push/src/arxiv_daily_push/stage1_runtime.py`
- `arxiv-daily-push/tests/test_stage1_runtime.py`
- `governance/run_manifests/ADP-S2PMT04-SCHEDULER-TEMPLATE-A013-20260626.json`

## Validation

- py_compile: PASS
- focused Stage 1 runtime tests: 12 OK
- full arxiv-daily-push unittest: 474 OK
- V7.2 validator: PASS
- ADP project governance: 0 errors / 0 warnings
- changed-only governance semantic: 0 errors / 0 warnings
- lean check-render: drift_count 0 reference_issue_count 0
- YAML/JSONL/CSV/manifest parse: OK
- git diff --check: PASS
- production-side-effect forbidden scan: no true/enabling hits

## Boundaries

This is local A-013 remediation evidence for the Stage 1 scheduler dry-run template only. It does not make the scheduler installable or installed, does not close inherited P0/P1 counters, and does not authorize production restore, real SMTP production, Release upload, or `INTEGRATED_PRODUCTION_ACCEPTED`.

## Next

Run final validation, commit, push, and open PR. After merge, independent `S2PMT07` still needs to review inherited A-013 closure together with the remaining P0/P1 blockers.
