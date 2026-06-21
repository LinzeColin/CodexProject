# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `Serenity-Alipay`
- Path: `Serenity-Alipay`
- CI mode: `required`
- Product version: `0.1.0`
- Model versions: `MOD-001:serenity-scoring-v1, MOD-002:serenity-ranking-v1, MOD-003:serenity-metrics-v1, +2`
- Parameter profile versions: `serenity-parameters:serenity-parameters-v1`
- Current iteration: `ITER-20260621-001`
- Current phase: `A`
- Current gate: `GOV-G3-SERENITY-BASELINE`
- Model count: `5`
- Formula count: `12`
- Parameter count: `49`
- Task count: `7`
- Unbound event count: `2`

## Latest Run

- Event: `EVENT-20260621-002`
- Task: `GOV-G3-SERENITY-MIGRATE-001`
- Summary: Recorded validation results for Serenity-Alipay governance baseline; exact python command is unavailable in this shell while python3 validation and focused tests pass.
- Model delta: `UNKNOWN`
- Parameter delta: `UNKNOWN`
- Tests: `['python scripts/validate_project_governance.py --project Serenity-Alipay -> exit 127 command not found', 'python3 scripts/validate_project_governance.py --project Serenity-Alipay -> exit 0 errors 0 warnings 0', 'python scripts/validate_project_governance.py --all -> exit 127 command not found', 'python3 scripts/validate_project_governance.py --all -> exit 0 errors 0 warnings 5 from EEI only', 'git diff --check -> exit 0', 'python -m pytest focused Serenity tests -> exit 127 command not found', 'python3 -m pytest focused Serenity tests -> exit 0 20 passed']`
- Evidence: `['Serenity-Alipay/docs/governance/DEVELOPMENT_LEDGER.md']`
- Result: `partial_environment_blocked`
- Rollback: UNKNOWN

## Current Blockers

validation not yet recorded in this file; see final run report for actual command results.

## Next Task

`TASK-A-001`
