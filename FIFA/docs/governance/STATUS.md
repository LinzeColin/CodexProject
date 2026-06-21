# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `FIFA`
- Path: `FIFA`
- CI mode: `required`
- Product version: `0.1.0`
- Model versions: `MOD-001:0.0.0-provisional, MOD-002:0.0.0-provisional, MOD-003:0.0.0-provisional, +8`
- Parameter profile versions: `active_profile:param-profile-20260620, legacy_profile:rules-v1.0.0`
- Current iteration: `ITER-20260620-001`
- Current phase: `A`
- Current gate: `GOV-P13-required-passed`
- Model count: `11`
- Formula count: `11`
- Parameter count: `117`
- Task count: `9`
- Unbound event count: `2`

## Latest Run

- Event: `EVT-FIFA-GOV-20260620-002`
- Task: `TASK-FIFA-A-001`
- Summary: Validated FIFA governance baseline and promoted FIFA ci_mode to required. Real HOME full suite exposed a missing external Downloads app entry; isolated temp HOME fixture with original user site-packages ran 206 tests OK.
- Model delta: `['MOD-001', 'MOD-002', 'MOD-003', 'MOD-004', 'MOD-005', 'MOD-006', 'MOD-007', 'MOD-008', 'MOD-009', 'MOD-010', 'MOD-011']`
- Parameter delta: `['PARAM-001..PARAM-117']`
- Tests: `['python scripts/validate_project_governance.py --project FIFA -> exit 127 python unavailable', 'python3 scripts/validate_project_governance.py --project FIFA -> exit 0', 'python3 -m py_compile run_daily_report.py scripts/tab_fifa_app_server.py tests/test_pipeline.py -> exit 0', 'bash -n scripts/run_tab_fifa_daily_automation.sh scripts/tab_real_refresh_smoke.sh -> exit 0', 'node --check scripts/refresh_tab_readonly.mjs -> exit 0', 'node --check scripts/discover_tab_live_boards.mjs -> exit 0', 'python3 -m unittest tests.test_pipeline -q -> exit 1 real HOME missing Downloads entry', 'PYTHONPATH=/Users/linzezhang/Library/Python/3.13/lib/python/site-packages HOME=<temp fixture home> python3 -m unittest tests.test_pipeline -q -> exit 0']`
- Evidence: `['FIFA/docs/governance/delivery_tasks.yaml', 'FIFA/docs/governance/DELIVERY_PLAN.md']`
- Result: `completed_with_external_downloads_entry_risk`
- Rollback: UNKNOWN

## Current Blockers

TASK-FIFA-B-001, TASK-FIFA-B-002, TASK-FIFA-C-001, TASK-FIFA-C-002, TASK-FIFA-D-001, TASK-FIFA-D-002, TASK-FIFA-E-001, TASK-FIFA-E-002

## Next Task

`TASK-FIFA-C-001`
