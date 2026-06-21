# Project Governance Status

Generated: `DETERMINISTIC_GENERATION`
Commit: `CURRENT_CHECKOUT`
Source: generated from machine governance registries, Git metadata, and validation results. Do not hand-edit counts here.

## Current State

- Project: `EVA_OS`
- Path: `EVA_OS`
- CI mode: `required`
- Product version: `0.1.0`
- Model versions: `MOD-001:0.0.0-provisional, MOD-002:0.0.0-provisional, MOD-003:0.0.0-provisional, +13`
- Parameter profile versions: `default:param-profile-20260620`
- Current iteration: `ITER-20260620-EVA-002`
- Current phase: `A`
- Current gate: `GOV-P13-required-passed`
- Model count: `16`
- Formula count: `16`
- Parameter count: `189`
- Task count: `12`
- Unbound event count: `2`
- UNKNOWN/HUMAN_REVIEW_REQUIRED count: `266`

## Latest Run

- Event: `ITER-20260620-EVA-002`
- Task: `TASK-EVA-A-004`
- Summary: Validate EVA_OS governance baseline and promote EVA_OS from advisory to required without runtime logic changes.
- Model delta: UNKNOWN
- Parameter delta: UNKNOWN
- Tests: python3 scripts/validate_project_governance.py --project EVA_OS, PYTHONPATH=src python3 -m pytest focused EVA_OS subset -q, PYTHONPATH=src python3 -m pytest tests/test_strategy_templates.py -q, python3 scripts/validate_project_governance.py --all
- Evidence: EVA_OS/docs/governance/delivery_tasks.yaml, EVA_OS/docs/governance/DEVELOPMENT_LEDGER.md, governance/projects.yaml
- Result: `PASS_WITH_ENV_BLOCKER: project validator exit 0 warnings 0; focused executable subset 99 passed; strategy template collection blocked by missing docx; all validator exit 0 with advisory warnings only for unmigrated projects`
- Rollback: UNKNOWN

## Current Blockers

calibration/source rationale gaps tracked by `TASK-EVA-B-001` through `TASK-EVA-B-008`

## Next Task

`TASK-EVA-B-003` - Resolve source rationale for cross-source validation tolerance.

- Status: `blocked`
- Acceptance: ACC-EVA-B-003
- Selection rationale: status=blocked; phase=B; current_phase=A; unmet_dependencies=none; score=145
