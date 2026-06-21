# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `PFI_BIG_DATA_SIMULATOR`
- Path: `PFI/大数据模拟器`
- CI mode: `required`
- Product version: `0.1.0`
- Model versions: `MOD-001:0.0.0-provisional, MOD-002:0.0.0-provisional, MOD-003:0.0.0-provisional, +12`
- Parameter profile versions: `default:param-profile-20260620`
- Current iteration: `ITER-20260620-PFI-002`
- Current phase: `A`
- Current gate: `GOV-P13-required-passed`
- Model count: `15`
- Formula count: `15`
- Parameter count: `213`
- Task count: `14`
- Unbound event count: `2`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `215`

## Latest Run

- Event: `ITER-20260620-PFI-002`
- Task: `TASK-PFI-A-004`
- Summary: Validate PFI/大数据模拟器 governance baseline and promote PFI_BIG_DATA_SIMULATOR from advisory to required without runtime logic changes.
- Model delta: UNKNOWN
- Parameter delta: UNKNOWN
- Tests: python3 scripts/validate_project_governance.py --project 'PFI/大数据模拟器', PYTHONPATH=. python3 -m pytest tests/test_core.py -q, python3 scripts/validate_project_governance.py --all
- Evidence: PFI/大数据模拟器/docs/governance/delivery_tasks.yaml, PFI/大数据模拟器/docs/governance/DEVELOPMENT_LEDGER.md, governance/projects.yaml
- Result: `PASS: project validator exit 0 warnings 0; focused tests 32 passed; all validator exit 0 with advisory warnings only for EEI and Serenity-Alipay`
- Rollback: UNKNOWN

## Current Blockers

calibration/source rationale gaps tracked by `TASK-PFI-B-001` through `TASK-PFI-B-010`

## Next Task

`TASK-PFI-B-001` - Resolve calibration evidence for strategy catalog rule constants and indicator thresholds.

- Status: `blocked`
- Acceptance: ACC-PFI-B-001
- Selection rationale: status=blocked; phase=B; current_phase=A; unmet_dependencies=none; score=138
